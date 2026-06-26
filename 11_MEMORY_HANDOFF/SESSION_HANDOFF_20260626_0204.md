# Session Handoff — 2026-06-26T02:04Z

**Trigger:** Context window near limit (Earl called /session-end)
**Last commit:** `2f13a35` (main) — pushed to GitHub + VPS deployed

---

## Status

- **Phase:** 6/7 ACTIVE — G0–G5 ✅ ALL CLOSED; MLB accumulation LIVE; NBA dark period
- **Tests:** 1947/1947 passing (1 skipped)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — 7 MLB cron entries ACTIVE; NBA cron running (dark period)
- **NBA paper bets:** 158 resolved — G6 gate (30 bets numeric floor MET; binding blocker = GG-004 EXP-017 + positive P&L)
- **MLB paper bets:** 0 resolved — accumulation just restarted (first T1 cron 03:00 UTC Jun 26)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| T1 cron moved 23:30→03:00 UTC; same-day UTC targeting | `timedelta(days=1)` targeted tomorrow. VPS log confirmed Kalshi doesn't publish next-day markets at 23:30 UTC; markets available by ~01:58 UTC. 0 bets placed since MLB arm launched. | `run_mlb_paper_trade.py` module docstring; `deploy/cron.conf` | DS |
| T2 pool = T1 shared pool (`paper_portfolio_mlb.json`) | T1 and T2 are both pre-game bets; capital should aggregate under the same reserve mandate. PaperTrader idempotency guard prevents double-betting same ticker. T4 stays isolated. | `run_t2_mlb_sameday.py` constants | DS |
| T2 uses per-game contamination guard (not global) | Afternoon live games would block all evening bets under T1's global guard. T2 has per-game lineup data via `game_pk`, so per-game check is precise. | `run_t2_mlb_sameday.py:_fetch_live_game_pks()` | DS |
| DS-04 MLB = MLB Stats API `hydrate=lineups,team`; SP overlay deferred | SP quality already captured by T1's `opp_sp_era_l5` feature. Adding SP overlay to T2 would double-count. T2's unique value: confirmed lineup + batting slot AB adjustment. | `03_DECISIONS/DS-04_mlb-t2-lineup-source.md` | DS |
| T4 `MIN_EDGE_T4=0.02` dead constant removed | Never referenced in any filter. Actual pre-C4 filter was `gross_edge <= 0.0`. C4 independently gates at `MIN_EDGE_TO_APPROVE=0.04`. Dead code at a different value than C4 was documentation confusion. | `run_t4_mlb_live.py` — constant removed | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| T4 stat group filter bug | ✅ `!= "batting"` (was `not in ("batting", "")` — empty-name groups were passing through as batting, corrupting hit counts) |
| T4 `MIN_EDGE_T4` dead constant | ✅ Removed — never referenced; C4 gates at `MIN_EDGE_TO_APPROVE=0.04` |
| T4 NFR-03 kill switch | ✅ Moved inside `game_pk` for-loop; worst-case halt reduced from ~195s to ≤45s + ESPN timeout |
| T1 PIPE-05 timing fix | ✅ Same-day UTC at 03:00 UTC; `timedelta(days=1)` removed; cron updated 23:30→03:00 |
| T3 MLB cron gate breach resolved | ✅ Two missing cron entries added (`*/15 20-23` + `*/15 0-3`) — S85 left these out despite declaring T-190 complete |
| T2 MLB build — `run_t2_mlb_sameday.py` | ✅ 280+ lines, PIPE-05.5, Binomial slot adjustment, per-game contamination guard, lineup-scratch filter, PaperTrader idempotency |
| `MLBIngestionClient.fetch_lineups()` | ✅ New method in `c1_signal_ingestion/mlb_ingestion.py`; `hydrate=lineups,team`; returns `{player_id: {batting_slot, game_pk, team_id}}` |
| DS-04 MLB designation document | ✅ `03_DECISIONS/DS-04_mlb-t2-lineup-source.md` — source, adjustment methodology, availability constraints, known issues, gate checklist |
| T2 tests | ✅ `tests/test_t191_mlb_t2.py` — 29 tests: `TestSlotAdjust` (9), `TestFetchLineupsParser` (8), `TestScratchFilter` (4), `TestPerGameContaminationGuard` (3), `TestT2Idempotency` (4), `TestDS04DocumentExists` (2) |
| `test_t189_mlb_pipe05_fixes.py` updated | ✅ `TestGameDateIsTomorrow` → `TestGameDateIsToday` (4 test methods inverted to match same-day UTC logic) |
| DECISION_LOG updated | ✅ S87 entry written (all 5 decisions above) |
| Git pushed + VPS deployed | ✅ HEAD `2f13a35`; crontab reinstalled on VPS; 7 MLB cron entries active |
| Tests | ✅ 1918 → 1947/1947 (+29) |

---

## ONE THING PENDING

**The first T1 bet hasn't fired yet.** Cron 03:00 UTC Jun 26 is the first eligible window with the fixed same-day targeting. MLB book is $1,000 fresh, 0 open, 0 closed — accumulation has not yet started in earnest. The next session's first act should be to ssh to VPS and check `logs/paper_mlb_cron.log` to confirm bets were placed.

If T1 fires clean at 03:00 UTC → T2 fires at 19:30 UTC → T3 fires at 20:00 UTC → T4 fires at 22:00 UTC: all four bands are confirmed working. If any band is silent, diagnose before doing anything else.

---

## Current Paper Portfolio

**NBA book (dark period):**
- Bankroll: $751.10 (−24.9% drawdown from 158 resolved bets)
- Open: 0 (dark period, kill switch active at >20% drawdown)
- Closed: 158 | G6 numeric floor: MET (>30) | **Binding blocker: GG-004 + positive P&L gate FAILING**

**MLB book (fresh start):**
- Bankroll: $1,000 fresh | Open: 0 | Closed: 0
- Target: ≥150 resolved bets → EXP-017 MLB Tier 1 run; ≥500 → Tier 2

---

## Active Cron on VPS (157.230.91.33)

```
16:30 UTC      — PIPE-06pre MLB (run_mlb_pregame.py — generates pregame context)
03:00 UTC      — PIPE-05 T1 MLB (run_mlb_paper_trade.py — bets on today's games)
19:30 UTC      — PIPE-05.5 T2 MLB (run_t2_mlb_sameday.py — batting lineup overlay)
*/15 20-23 UTC — PIPE-06 T3 MLB (run_t3_mlb_pretip.py — momentum scan)
*/15 0-3 UTC   — PIPE-06 T3 MLB (run_t3_mlb_pretip.py — midnight wrap)
22:00 UTC      — PIPE-07 T4 MLB (run_t4_mlb_live.py — 45s live in-play loop)
06:30 UTC      — PIPE-05R MLB (run_resolve_mlb.py — settle closed positions)
22:30 UTC      — PIPE-05FX MLB (feature refresh — current season only)
Mon 14:10 UTC  — PIPE-05C MLB (calibration monitor — ECE per threshold)
21:00 UTC      — Health check
23:00 UTC      — PIPE-07 NBA (run_t4_live.py — dark period, 0 games, no-op)
22:00 UTC      — PIPE-03 NBA early (dark period, no bets)
01:30 UTC      — PIPE-03 NBA late (dark period, no bets)
06:00 UTC      — PIPE-03R NBA resolve (dark period)
```

---

## Key Constraints to Remember

1. **GG-004 OPEN** — EXP-017 MLB commercial validation requires ≥150 closed positions (Tier 1) or ≥500 (Tier 2). Nothing else gates G6 faster.
2. **No live capital** until G6 (30 resolved paper bets with positive P&L — APR-0016; P&L gate currently FAILING at −24.9% NBA)
3. **T5 is explicitly out of scope** per CLAUDE.md — "Not built. Future; requires real-time infrastructure." Do not attempt to build.
4. **NBA dark period** through October 2026. No NBA bets. Kill switch active at 25.12% > 20%.
5. **MLB CDN block:** MLB Stats API accessible for 2026 season from VPS; 2024/2025 historical blocked via Fastly CDN.
6. **VPS deploy alias:** `prediction-market-vps` = `root@157.230.91.33`; bot lives at `/opt/prediction-market-bot`

---

## ⚙️ DECISION AUDIT

**Governance scan ran:** `grep -rn "decisions_logged: false"` — CLEAN, no matches.

| Document | Decisions logged | DECISION_LOG entries | Status |
|----------|-----------------|---------------------|--------|
| `run_t2_mlb_sameday.py` (NEW) | N/A (code, not design doc) | S87 entry covers T2 architecture decisions | ✅ |
| `DS-04_mlb-t2-lineup-source.md` (NEW) | N/A (no decisions_logged field in DS docs) | DS-04 designation = decision; S87 entry written | ✅ |
| `deploy/cron.conf` (MODIFIED) | N/A | T1 timing + T2/T3 entries logged in S87 | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
ssh prediction-market-vps "cat /opt/prediction-market-bot/logs/paper_mlb_cron.log | tail -50"
# Look for bets placed at 03:00 UTC Jun 26. If clean, all 4 MLB bands are on-auto.
# Then: Tell Claude: "Read MEMORY_BANK.md and SESSION_HANDOFF_20260626_0204.md, confirm 1947 tests, check VPS MLB logs"
```
