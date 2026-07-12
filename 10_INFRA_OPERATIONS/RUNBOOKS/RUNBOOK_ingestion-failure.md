# Runbook: Ingestion Failure (FM-01, C1)

**Purpose:** Diagnose and recover from C1 data-ingestion failures — MLB Stats API unavailability, Kalshi market-fetch gaps, schema/contract violations, and the "0 players matched" false-floor pattern (GG-110).
**Owner (role):** Infrastructure Operator (IO)
**Last reviewed:** 2026-07-12
**Next review:** After next real FM-01 incident, or if PIPE-05/PIPE-05.5/run_mlb_pregame.py retry/contract constants change
**Staleness triggers:** MLB Stats API contract change; Kalshi market-publish timing shift; `MLB_FEATURE_CSV_CONTRACT` schema change; PIPE-05 retry constants change
**Upstream links:** `02_ARCHITECTURE_DESIGN/RESILIENCE_FAILURE_MODES.md` (FM-01), `03_DECISIONS/GOVERNANCE_GAP_LOG.md` (GG-092, GG-110, GG-059)
**Downstream links:** `10_INFRA_OPERATIONS/INCIDENTS_POSTMORTEMS/`
**Decision references:** T-343/GG-110 (bounded retry), T-212/GG-059 (data contract validation)
**Confidence:** 7/10 — grounded directly in current source; not yet drilled live

---

## Overview

C1 ingestion in this system is not one code path — there are two materially different failure surfaces that both route through "FM-01" and must not be conflated when diagnosing:

1. **MLB Stats API ingestion** (`c1_signal_ingestion/mlb_ingestion.py`, `MLBIngestionClient`) — feeds `run_mlb_pregame.py`, which writes the feature CSV that `run_mlb_paper_trade.py` (PIPE-05) later loads. Failures here are per-HTTP-call, handled by `_get()`'s internal linear retry.
2. **Kalshi market-snapshot fetch** (inside PIPE-05 itself, `run_mlb_paper_trade.py`) — a single snapshot taken at a fixed cron time (11:00 UTC). Failures here manifest as "0 players matched" even though games are scheduled, because Kalshi has not yet published same-day markets at that instant (GG-110, observed 2026-07-11: 55/44 markets published vs. 383/317 confirmed live hours later).

Both are governed by the same downstream floor check (`SemanticFloorGuard.assert_floor`), but the retry logic that runs *before* that floor check is specific to (2) and lives inline in `run_mlb_paper_trade.py`, not in a shared C1 module.

---

## Trigger Conditions

| Symptom | Which surface | Where you'll see it |
|---|---|---|
| `mlb_schedule_api_failed` WARNING logged | MLB Stats API (schedule endpoint) | `logs/audit_mlb.jsonl` |
| `_get()` exhausts `MAX_RETRIES=3` and returns `None` | MLB Stats API (any `MLBIngestionClient.fetch_*` call) | Caller-dependent — `_get` returns `None` silently, no exception raised; check whichever `fetch_*` call site handles the `None` |
| `semantic_floor_retry` INFO logged (1-3 times) | Kalshi market fetch, PIPE-05 | `logs/audit_mlb.jsonl`, stdout of `logs/paper_mlb_cron.log` |
| `semantic_floor_violation` CRITICAL logged, process exits 2 | Kalshi market fetch, PIPE-05 (retries exhausted or 0 scheduled games misdetected) | `logs/audit_mlb.jsonl`, `logs/paper_mlb_cron.log` |
| `DataContractViolation` raised, process exits 1 | Feature CSV schema/cardinality/freshness (T-212/GG-059) | `logs/paper_mlb_cron.log` stderr: `ERROR: <contract violation detail>` |
| `0 players in live MLB markets` printed but games ARE scheduled | Kalshi market fetch, PIPE-05 — same underlying issue as GG-110 | `logs/paper_mlb_cron.log` |

**Severity:** CRITICAL during MLB season (March–October) if it results in 0 bets on a real game day. Recoverable/expected outside season.

---

## Diagnostics

```bash
# 1. Confirm today actually has scheduled MLB games (rules out false alarm)
curl -s "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=$(date -u +%F)" | python3 -c "import json,sys; d=json.load(sys.stdin); print(sum(len(x['games']) for x in d.get('dates',[])))"

# 2. Check PIPE-05's own run log for the retry sequence and final outcome
ssh prediction-market-vps "tail -100 /opt/prediction-market-bot/logs/paper_mlb_cron.log"

# 3. Check audit log for the structured events (semantic_floor_retry / semantic_floor_violation / mlb_schedule_api_failed)
ssh prediction-market-vps "grep -E 'semantic_floor_retry|semantic_floor_violation|mlb_schedule_api_failed' /opt/prediction-market-bot/logs/audit_mlb.jsonl | tail -20"

# 4. Confirm whether the false-floor scenario (GG-110) is recurring: Kalshi market count at PIPE-05's fixed 11:00 UTC run time vs. later same-day
ssh prediction-market-vps "grep 'kalshi_markets_total' /opt/prediction-market-bot/logs/audit_mlb.jsonl | tail -5"
```

| What to check | Where | What to look for |
|---|---|---|
| Retry exhaustion | `logs/audit_mlb.jsonl`, `semantic_floor_retry` events | `attempt` reaches `max_attempts` (3) without `markets_by_player` ever becoming non-empty |
| Contract violation detail | `logs/paper_mlb_cron.log` stderr | Which check failed — `validate_schema` (column drift), `validate_cardinality` (row-count collapse/explosion), or `validate_staleness` (feature CSV >7 days stale) |
| Upstream feature CSV freshness | `run_mlb_pregame.py`'s own log/cron output | Did `run_mlb_pregame.py` (the job that *produces* the feature CSV PIPE-05 loads) run and succeed today? A stale-CSV contract violation in PIPE-05 is often actually an FM-01 failure one hop upstream, in `run_mlb_pregame.py`, not in PIPE-05 itself |
| MLB Stats API health | Direct curl (Diagnostic 1) | Non-200 response, empty `dates` array, or `games` count of 0 when games are known to be scheduled |

---

## Mitigations

### Mitigation A: Kalshi false-floor (GG-110 pattern) — bounded retry already covers most cases

PIPE-05 already retries automatically (3 attempts, linear backoff `PIPE05_FLOOR_RETRY_DELAY_SEC * attempt`, default 300s/600s/900s ≈ 30 min total) before raising `SemanticFloorViolation`. If the retry window is genuinely too short for a given day (Kalshi publishing later than usual):

```bash
# One-off manual re-run later in the day, after confirming markets are now published
ssh prediction-market-vps "cd /opt/prediction-market-bot && export \$(grep -v '^#' .env | xargs) && BOT_ENV=paper MLB_PAPER_YES_ONLY=false PYTHONPATH=\$PYTHONPATH python3 src/prediction_market_bot/run_mlb_paper_trade.py >> logs/paper_mlb_cron.log 2>&1"
```

**Do not re-run blindly** — first confirm via Diagnostic 1 that games are actually scheduled and via Diagnostic 4 that Kalshi has since published markets, otherwise a second run against the same 0-market state just reproduces the same violation.

If this pattern recurs on multiple days, the fix is raising `PIPE05_FLOOR_RETRY_ATTEMPTS` / `PIPE05_FLOOR_RETRY_DELAY_SEC` (env vars, no code change needed) or moving PIPE-05's cron trigger later than 11:00 UTC — either requires a DECISION_LOG entry, since it changes when the day's T1 bets are placed.

### Mitigation B: MLB Stats API outage (schedule or game-log endpoints)

`_get()` in `mlb_ingestion.py` already retries 3x with linear backoff (1s/2s/3s) and a 15s timeout per attempt, and returns `None` rather than raising on exhaustion — so a transient outage does not crash the pipeline, it silently degrades (fewer players/rows). There is no automated alert on this degradation; it must be caught by reading logs (Diagnostic 3) or noticing an unusually small feature CSV row count in PIPE-05's own startup log line (`[FEATURE CSV] {rows} rows | {players} players ...`).

```bash
# Confirm MLB Stats API is actually down (not just this host)
curl -sI https://statsapi.mlb.com/api/v1/schedule?sportId=1

# If down: no mitigation available beyond waiting — this is a third-party dependency.
# Do NOT retry manually faster than the built-in backoff; that does not help and
# risks rate-limiting once the API recovers.
```

### Mitigation C: Data contract violation (schema/cardinality/staleness)

```bash
# Read the exact violation reason
ssh prediction-market-vps "grep -A3 'ERROR:' /opt/prediction-market-bot/logs/paper_mlb_cron.log | tail -20"
```

- **Staleness (feature CSV >7 days old):** `run_mlb_pregame.py` did not run successfully recently — diagnose that job first (it is its own FM-01 instance, upstream of PIPE-05). Do not attempt to relax the 7-day staleness threshold in `MLB_FEATURE_CSV_CONTRACT` without a DECISION_LOG entry — it exists specifically to prevent PIPE-05 from silently trading on stale rolling stats.
- **Schema/column drift:** almost always means an upstream feature-generation change (new/renamed/removed column) shipped without updating `MLB_FEATURE_CSV_CONTRACT` in `data_contracts.py`. This is a code-level fix, not an operational one — halt PIPE-05 (it already halts itself via `sys.exit(1)`) until the contract or the feature generator is reconciled.
- **Cardinality collapse/explosion:** row count deviates sharply from the previous run's row count (state tracked via `validate_cardinality`'s persisted row-count file). Check whether `run_mlb_pregame.py` partially failed (e.g., hit the MLB Stats API mid-run and truncated the cohort).

---

## Rollback

There is no "rollback" in the traditional sense — PIPE-05 halts itself (exit 1 or exit 2) rather than placing bets on suspect data, so the failure mode is fail-closed by design. "Recovery" means:

1. Fix the root cause (upstream API, contract, or retry-window issue).
2. Re-run PIPE-05 manually for the affected `game_date` if the fixed-time cron window has already passed (Mitigation A command above).
3. Confirm via `logs/paper_mlb_cron.log` that the manual run completed with `paper_run_start` → normal bet-placement flow (not another halt).

**Verification:** `grep "players in live MLB markets" logs/paper_mlb_cron.log | tail -1` shows a non-zero player count matching expectation for the day's schedule size.

---

## Known Failure Modes

| Failure | Likelihood | Response |
|---|---|---|
| Kalshi hasn't published same-day markets yet at PIPE-05's fixed 11:00 UTC run (GG-110) | MEDIUM — observed at least once (2026-07-11) | Bounded retry (built in); manual re-run later in day if retry window insufficient |
| MLB Stats API transient outage during `run_mlb_pregame.py` | LOW-MEDIUM | Built-in 3x retry; if sustained, feature CSV goes stale and PIPE-05 self-halts on the 7-day contract check rather than trading on old data |
| `_get()` returns `None` on a 4xx (no retry) for a single player/game, silently reducing cohort size with no alert | MEDIUM — this is a genuine gap, not fully covered by any runbook mitigation | No current automated detection; must be caught by manually comparing feature CSV row count day-over-day. Candidate for a new governance gap if it causes a real incident. |
| `_count_scheduled_mlb_games` schedule-endpoint call itself fails during the floor-retry loop | LOW | Function returns 0 on failure (permissive) — this could cause PIPE-05 to break out of the retry loop early on a real game day if the schedule endpoint fails at exactly the wrong moment. Treat any `semantic_floor_violation` with `scheduled_preview_games: 0` on a day you know has games as a schedule-endpoint failure, not a genuine 0-game day. |

---

## References

- `02_ARCHITECTURE_DESIGN/RESILIENCE_FAILURE_MODES.md` — FM-01
- `03_DECISIONS/GOVERNANCE_GAP_LOG.md` — GG-110 (bounded retry origin), GG-059 (data contract origin), GG-092 (this runbook)
- `src/prediction_market_bot/run_mlb_paper_trade.py` — PIPE-05, lines ~140-155 (retry constants), ~690-814 (retry loop + floor guard + contract validation call site)
- `src/prediction_market_bot/c1_signal_ingestion/mlb_ingestion.py` — `MLBIngestionClient._get()`, lines ~214-230
- `src/prediction_market_bot/c1_signal_ingestion/validators.py` — `assert_contract`, `validate_schema`, `validate_cardinality`, `validate_staleness`
- `src/prediction_market_bot/c7_monitoring/semantic_contracts.py` — `SemanticFloorGuard`, `SemanticFloorViolation`
- `deploy/cron.conf` — PIPE-05 cron schedule (11:00 UTC daily)
