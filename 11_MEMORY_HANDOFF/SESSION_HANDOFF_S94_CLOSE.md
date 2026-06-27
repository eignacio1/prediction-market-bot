# SESSION HANDOFF — S94 CLOSE

**Date:** 2026-06-26  
**Session:** 94  
**Operator:** Earl Ignacio  
**Context at close:** ~80%+ — handoff triggered  

---

## What happened this session

### T-203 — Edge calibration ADR (ADR-0033) COMPLETE

`MIN_EDGE_TO_APPROVE = 0.04` (system default, C4, ADR-0020) adopted for MLB T4. No separate `MIN_EDGE_T4` variable introduced. ADR-0033 ACCEPTED. GG-007 NOT closed (GG-007 is NBA Phase 8 skeleton constants, unrelated). Provisional: empirically calibrate after ≥30 resolved MLB T4 bets.

### T-204 — Full MLB arm enabled COMPLETE

`deploy/cron.conf` three changes:
- T4 MLB: `T4_MLB_DRY_RUN=true` removed → T4 live, C4 active, positions open
- PIPE-05 (T1 MLB, `0 11 * * *`) uncommented → first bets fire June 27 at 11:00 UTC
- PIPE-05.5 (T2 MLB, `30 19 * * *`) uncommented → lineup overlay fires June 27 at 19:30 UTC

All 7 MLB crons confirmed active on VPS.

### Gap 1 SESSION 93 error correction (documented in ADR-0033)

SESSION 93 DECISION_LOG stated `_espn_poll_once_mlb()` returns current-batter state only. Wrong. The function iterates `stat_group.get("athletes", [])` from the ESPN boxscore endpoint — all batting athletes, both teams. ADR-0033 is the authoritative correction. DECISION_LOG entry is immutable; correction lives in ADR-0033.

### ARE WE COMPROMISED? protocol — RUN

All watchdog Q1–Q6 checks complete. T4 MLB arm confirmed live with all safety gates active (C4, kill switch, 27% band budget cap). No new critical gaps beyond those already registered before this session.

### `scripts/run_session_report.py` — BUILT

SSH-based session-start self-assessment. 8 sections: VPS git HEAD, cron state (7 MLB crons + DRY_RUN detection + kill switch), pregame freshness, portfolio state (4 pools: MLB T1/T2, MLB T4, NBA T1, NBA T4), T4 throughput, recent bets, resolutions, cron error scan. Usage: `python3 scripts/run_session_report.py [--days N]`.

### T4 sub-segment scoping — DOCUMENTED

Phase 8 blocked (GG-038/039/040). Throughput already ~1,680 evals/game structural (3.5 Kalshi-covered players/game × 1.8 thresholds × 240 cycles at 45s). Design target (~1,000/game) already met structurally. Strategy: watch tonight's T4 log (`logs/t4_mlb_live_cron.log`); reduce `POLL_INTERVAL_S` 45s→15s only if materially below 1,000/game.

### Strategic framing — DOCUMENTED

Four structural observations from external assessment, added to DECISION_LOG as SESSION 94 ongoing factors:
1. Market efficiency context: NBA Finals = worst-case (sharpest money, highest volume). MLB mid-week regular season = structurally different. G6 MLB evidence is genuinely different data.
2. T4 edge claim is microstructure bet (market slowness), not forecasting accuracy. Requires separate validation from T1.
3. Capital ceiling: Kalshi market depth constrains effective Kelly independent of bankroll math. → GG-045
4. Methodology as product: the calibration regime for probabilistic thinking is the deeper structural value.

### GG-045 + GG-046 registered

**GG-045:** Maximum Effective Bankroll Constrained by Kalshi Market Depth — Capital Ceiling Unanalyzed. LOW now, MEDIUM at G6 ($1K–$5K), HIGH at G8–G9 ($10K+). OPEN.

**GG-046:** T4 Commercial Validation — Independent Alpha Hypothesis Untested. T4 thesis (market microstructure / reaction speed) ≠ T1 thesis (forecast accuracy). EXP-017 only tests T1. Resolution: define EXP-T4-01 with ≥30 resolved T4 bets. OPEN LOW.

---

## Current system state

| Item | State |
|------|-------|
| VPS | 157.230.91.33 (ssh alias: `prediction-market-vps`) |
| VPS base | `/opt/prediction-market-bot` |
| Active crons | 7 MLB: T1 (11:00), T2 (19:30), T4 (22:00), PIPE-06pre (16:30), PIPE-05R (06:30), PIPE-05FX (22:30), T3 (*/15) |
| T4 DRY_RUN | REMOVED — T4 live |
| MLB bankroll | $1,000 fresh (0 open, 0 closed at session start; first bets fire June 27) |
| NBA bankroll | $958.99 (paper; drawdown kill switch active) |
| Test suite | 2083 tests (all pass) |
| ADR-0033 | ACCEPTED — MLB T4 edge threshold provisional |
| GG-045 | OPEN LOW — market depth capital ceiling |
| GG-046 | OPEN LOW — T4 commercial validation |

---

## What to watch / verify next session

| Milestone | When | Where to check |
|-----------|------|----------------|
| First MLB T4 bets (live) | June 26, 22:00 UTC | `logs/t4_mlb_live_cron.log` |
| T4 evaluation count | After first game tonight | `grep 'total_evaluated\|evaluated=' logs/t4_mlb_live_cron.log` |
| PIPE-06pre (pregame) | June 27, 16:30 UTC | `logs/pregame_mlb_YYYYMMDD.json` exists + size |
| First MLB T1 bets | June 27, 11:00 UTC | `logs/paper_mlb_cron.log` + Kalshi order book |
| First MLB T2 lineup | June 27, 19:30 UTC | `logs/t2_mlb_cron.log` |
| First MLB bet resolution | June 28, 06:30 UTC | `logs/resolve_mlb_cron.log` |

**T4 throughput decision rule (from session):** If `total_evaluated` in tonight's T4 log is materially below 1,000/game, reduce `POLL_INTERVAL_S` from 45s to 15s in `run_t4_mlb_live.py`. One-line change. Do not do this preemptively — wait for data.

---

## Priority queue for next session

1. Run `python3 scripts/run_session_report.py` — read the output before anything else
2. Check T4 throughput (`total_evaluated=` in `logs/t4_mlb_live_cron.log`) — if <1,000/game, reduce POLL_INTERVAL_S 45s→15s
3. Verify first MLB T1 bets landed on Kalshi (`logs/paper_mlb_cron.log`)
4. Watch PIPE-05R first resolution (June 28, 06:30 UTC)
5. After ≥30 MLB T4 bets resolved: define EXP-T4-01 (GG-046 requirement)
6. Pre-G8: market depth analysis for GG-045

---

## Open governance gaps (condensed)

| Gap | Description | Priority |
|-----|-------------|----------|
| GG-004 | Commercial validation (EXP-017) — model has no demonstrated edge vs Kalshi price | G6 blocker |
| GG-007 | NBA Phase 8 ADR-0029 skeleton constants | LOW (Phase 8 pre-activation) |
| GG-038 | T4 kill switch ≤5s SLA (Phase 8 prereq) | Phase 8 blocked |
| GG-039 | T4 price cache / staleness (Phase 8 prereq) | Phase 8 blocked |
| GG-040 | T4 real-time data sources (Phase 8 prereq) | Phase 8 blocked |
| GG-043 | MLB Kelly fraction 0.10 inherited from NBA (needs MLB-specific derivation) | LOW |
| GG-044 | C7 drift baselines are NBA G4 values | LOW (calib monitor not enabled) |
| GG-045 | Kalshi market depth capital ceiling unanalyzed | LOW now, HIGH at G8–G9 |
| GG-046 | T4 commercial validation — independent alpha hypothesis untested | LOW (paper phase) |

---

## Artifacts modified this session

| File | Change |
|------|--------|
| `03_DECISIONS/ADR-0033_mlb-t4-edge-threshold-provisional.md` | CREATED — T-203 |
| `deploy/cron.conf` | T-204 — T4 live, PIPE-05 + PIPE-05.5 re-enabled |
| `scripts/run_session_report.py` | CREATED — session self-assessment |
| `03_DECISIONS/DECISION_LOG/DECISION_LOG.md` | Two new entries: strategic framing + ADR-0033/T-204 |
| `03_DECISIONS/GOVERNANCE_GAP_LOG.md` | GG-045 + GG-046 added |
| `04_EXECUTION/TODO_NEXT.md` | SESSION 94 COMPLETE block added |
| `11_MEMORY_HANDOFF/MEMORY_BANK.md` | Last reviewed + Last major milestone updated |
| `11_MEMORY_HANDOFF/SESSION_HANDOFF_S94_CLOSE.md` | CREATED (this file) |
