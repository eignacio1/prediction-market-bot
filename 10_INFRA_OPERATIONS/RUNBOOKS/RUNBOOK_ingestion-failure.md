# Runbook: Data Ingestion Failure (FM-01)

**Purpose:** Diagnose and remediate C1 ingestion failures — network errors, source API outages, schema mismatches, or malformed data from ESPN/MLB Stats API/Kalshi feeds.
**Owner (role):** Architecture Owner (AO)
**Last reviewed:** 2026-07-13
**Next review:** On any C1 module change, new data source, or repeat FM-01 incident
**Staleness triggers:** New C1 ingestion module added; source API contract change; repeat incident with a new root cause not covered here
**Upstream links:** `RESILIENCE_FAILURE_MODES.md` (FM-01 definition)
**Downstream links:** `04_EXECUTION/TODO_NEXT.md`, `03_DECISIONS/GOVERNANCE_GAP_LOG.md`
**Decision references:** T-343 (PIPE-05 floor-retry fix), GG-049 (dark-pipeline detection gap), GG-108 (Step 4 NBA log path fix)
**Confidence:** 8/10 — grounded directly in shipped code (`SemanticFloorGuard`, PIPE-05 retry-backoff, real cron/systemd schedule) rather than aspirational process.

---

## Overview

FM-01 is failure in the ingestion layer (C1): `c1_signal_ingestion/` for MLB/NBA game and player data, plus the Kalshi market-data client. Per `RESILIENCE_FAILURE_MODES.md`, severity is Research LOW / Live HIGH — in paper/live trading, a silent ingestion gap means the bot either places bets on stale/wrong data or silently produces zero bets while appearing to run cleanly (this second case is exactly what GG-049 exists to catch — see CLAUDE.md Step 4).

Real C1 modules: `ingestion.py`, `mlb_ingestion.py`, `validators.py`, `team_stats_store.py`, `mlb_team_stats_store.py`, `mlb_pitcher_stats_store.py`, `data_contracts.py`, `ds02_nba_live.py` (all under `src/prediction_market_bot/c1_signal_ingestion/`).

---

## Trigger Conditions

### Automatic

| Signal | Where | What it means |
|--------|-------|----------------|
| `SemanticFloorViolation` raised | `c7_monitoring/semantic_contracts.py`, `SemanticFloorGuard` — fires when `matched_players == 0 and games_fetched > 0` | Games were fetched from the source, but the player-name/ticker matching pipeline produced zero matches — a downstream C1/C2 join broke even though the raw fetch succeeded |
| PIPE-05 floor-retry exhausted | `run_mlb_paper_trade.py:793`, `PIPE05_FLOOR_RETRY_ATTEMPTS=3` / `PIPE05_FLOOR_RETRY_DELAY_SEC=300` (T-343) | 3 retries at 300/600/900s linear backoff all still hit the semantic floor — this is a real, not transient, ingestion failure |
| `0 players in live MLB markets` in cron log during MLB season | `logs/paper_mlb_cron.log` (VPS) | CLAUDE.md Step 4's canonical health-check line; healthy expectation is ≥1 player matched per run when games are scheduled |
| Missing Snapshot ID in `DATA_SNAPSHOTS_INDEX.md` | Manual/periodic check | A run that should have registered a data snapshot didn't — ingestion silently no-op'd |

### Manual

- Source API contract change (ESPN scoreboard schema change, MLB Stats API field rename) — these arrive with no warning; the first symptom is usually a `KeyError`/`schema mismatch` in the cron log, not an alert.
- Network partition or DNS failure between the VPS and the source (ESPN, `statsapi.mlb.com`, Kalshi).
- MLB Stats API's known IP-blocking constraint (`deploy/cron.conf`'s PIPE-05FX comment): `statsapi.mlb.com` returns HTTP 406 for historical seasons (≤2025) from DigitalOcean IPs — this is a **known, permanent** constraint, not a transient failure; do not treat a 406 on a historical-season request as an incident, only a 406 on a **current-season** (2026) request.

---

## Diagnostic Procedure

**Step 1 — Confirm the scope: is this systemic or one-source?** ≤5 minutes.
```bash
ssh prediction-market-vps "tail -100 /opt/prediction-market-bot/logs/paper_mlb_cron.log"
ssh prediction-market-vps "tail -100 /opt/prediction-market-bot/logs/pregame_mlb_cron.log"
ssh prediction-market-vps "systemctl is-active t4-mlb && journalctl -u t4-mlb -n 100 --no-pager"
```
If only one pipeline (e.g. T1 MLB) is failing while T4 MLB is healthy, the failure is localized to that pipeline's specific ingestion call, not a systemic network/VPS issue. If all MLB pipelines show gaps simultaneously, suspect network/DNS or a shared upstream source (ESPN or MLB Stats API itself down).

**Step 2 — Run the semantic-oracle checks (CLAUDE.md Step 4).** ≤2 minutes.
```bash
grep -c "SemanticFloorViolation" /opt/prediction-market-bot/logs/paper_mlb_cron.log
```
Non-zero confirms a matching-pipeline failure (games fetched, but zero players matched) rather than a raw-fetch failure (games not fetched at all — that would show as an HTTP error or exception in the cron log instead, not a `SemanticFloorViolation`).

**Step 3 — Isolate raw fetch vs. downstream matching.** ≤10 minutes.
```bash
ssh prediction-market-vps "cd /opt/prediction-market-bot && venv/bin/python -c \"
from prediction_market_bot.c1_signal_ingestion.mlb_ingestion import MLBIngestionClient
c = MLBIngestionClient()
games = c.fetch_todays_games()
print(f'games fetched: {len(games)}')
print(games[:2])
\""
```
(Adjust the exact client class/method name if it has since changed — verify against `c1_signal_ingestion/mlb_ingestion.py` first if this errors.) If `games` is empty or the call raises, the failure is at the raw-fetch layer (network, source API down, schema mismatch on the top-level response). If games are returned but non-empty and the pipeline still logs `SemanticFloorViolation`, the failure is downstream in the player-name/ticker matching join — check `validators.py` and whatever join keys the pipeline uses (player name normalization is a common silent-break point when a source renames a player or changes name formatting).

**Step 4 — Check for a known, permanent constraint before treating as an incident.** ≤2 minutes.
- Is this a request for **historical** (≤2025) MLB Stats API data from the VPS? → Expected 406, not a bug (see Trigger Conditions above).
- Is this during the daily PIPE-05FX cache-bust window (22:30 UTC)? A fresh 2026-only pull briefly has thinner rolling-stat coverage right after the cache bust — confirm the failure persists past that window before escalating.

**Step 5 — Remediate.**
- **Transient network/API blip:** the PIPE-05 floor-retry (T-343) already handles this automatically for the T1 MLB path (3 attempts, 300/600/900s backoff) — if it's still failing after all 3 attempts, this is not transient; proceed to schema/source investigation.
- **Schema mismatch:** compare the actual API response shape against what `mlb_ingestion.py`'s parsing expects. A source contract change requires a code fix, not a retry — register in `GOVERNANCE_GAP_LOG.md` if the fix isn't immediate, and add a T-NNN.
- **Name-matching break:** check whether a player's display name changed format at the source (e.g. suffix added/removed, accented character encoding). This is the most common FM-01-adjacent silent break historically (per the class of bug T-343/PIPE-05's floor-retry exists to catch, even though the retry itself doesn't fix a persistent name-format break — it only survives transient ones).
- **Full source outage:** no ingestion fix available; the correct action is to confirm the pipeline degrades gracefully (0 bets, no crash, no stale/wrong data used) rather than to force a fix. Verify via Step 1's logs that the pipeline logged the failure and exited cleanly rather than silently continuing with partial/stale data.

**Step 6 — Escalate.**
Any FM-01 incident that (a) persists past the PIPE-05 floor-retry, or (b) is caused by a real source-contract change requiring a code fix, must be registered in `03_DECISIONS/GOVERNANCE_GAP_LOG.md` and given a T-NNN in `TODO_NEXT.md` before the session ends (Hard Rule 7). If the incident caused the bot to place a bet on bad data (rather than cleanly producing 0 bets), treat it as a P1 — this is a live capital risk mechanism even in paper trading, since paper-trading integrity underpins the G6 evidence base.

---

## Known Failure Modes

| Failure mode | Cause | Detection signal | Mitigation |
|---|---|---|---|
| Silent zero-players-matched | Games fetched OK, name/ticker join fails | `SemanticFloorViolation`; `0 players in live MLB markets` in cron log | PIPE-05 floor-retry (T-343, 3× linear backoff); Step 4 health check catches persistent cases |
| Source schema change | ESPN/MLB Stats API changes a field name or response shape without notice | Exception/`KeyError` in cron log; raw fetch in Step 3 raises | No automated protection — requires manual diagnosis and a code fix; register as GG if recurring |
| Historical-season 406 mistaken for an incident | DigitalOcean IP block on `statsapi.mlb.com` for seasons ≤2025 (known, permanent, documented in `deploy/cron.conf`) | 406 response on a historical-date request | Not a bug — do not "fix"; confirm the request was for the 2026 season before investigating further |
| Dark pipeline with no visible alert (GG-049 class) | A pipeline runs 0 bets for multiple consecutive game days with no ingestion exception at all | CLAUDE.md Step 4 operational health check is the only place this becomes visible — it does not self-alert | Run Step 4 every session; do not rely on the absence of exceptions as evidence of health |
| NBA off-season log path confusion (GG-108 class) | Grepping a stale/renamed log filename returns empty output, visually indistinguishable from "0 games today" | CLAUDE.md Step 4 command references the exact current NBA log files (`paper_early_cron.log`, `paper_late_cron.log`) plus the `No .* markets available` match | Keep CLAUDE.md Step 4 in sync if VPS log filenames change again — do not let this drift a second time |

---

## References

- `RESILIENCE_FAILURE_MODES.md` — FM-01 canonical definition
- `src/prediction_market_bot/c1_signal_ingestion/` — real ingestion modules
- `src/prediction_market_bot/c7_monitoring/semantic_contracts.py` — `SemanticFloorGuard`, `SemanticFloorViolation`
- `src/prediction_market_bot/run_mlb_paper_trade.py:793` — PIPE-05 floor-retry (T-343)
- `deploy/cron.conf` — PIPE-05/PIPE-05FX schedule and MLB Stats API IP-blocking note
- CLAUDE.md — Step 4 operational health check (semantic oracle checks)
- `03_DECISIONS/GOVERNANCE_GAP_LOG.md` — GG-049 (dark-pipeline detection), GG-092, GG-108
