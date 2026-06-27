# SESSION 93 CLOSE — Handoff

**Date:** 2026-06-26  
**Phase:** 6/7 ACTIVE — MLB T4 dry-run mode LIVE; T1/T2 MLB betting PAUSED pending T4  
**Git HEAD:** `863eccc` (T-202 COMPLETE — MLB T4 dry-run mode)  
**Tests:** 2083/2083 passing  
**VPS:** 157.230.91.33 — HEAD confirmed at `863eccc`

---

## What Happened This Session

### Governance Correction (CRITICAL)
SESSION 90 re-enabled PIPE-05 (T1 MLB) and PIPE-05.5 (T2 MLB) while T4 was still unbuilt — violating Earl's SESSION 88 directive that NO MLB bets fire until the ENTIRE arm (including T4) is complete. SESSION 93 corrected this:
- PIPE-05 and PIPE-05.5 commented out in `deploy/cron.conf`
- Reason string: "SESSION 93 PAUSED — MLB arm not complete until T4 live (T-204)"
- Committed `7b0730b`, deployed to VPS, crontab verified
- 3 DECISION_LOG entries written (governance failure + T-202 + throughput gap)

**STANDING RULE:** T1/T2 MLB crons must remain PAUSED until T-204 is complete. T-204 requires T-203 ADR signed, which requires ≥1 real game night of T4 dry-run JSONL data.

### T-202 COMPLETE — MLB T4 Dry-Run Mode
`run_t4_mlb_live.py` now accepts `T4_MLB_DRY_RUN=true/1/yes` env var:
- All evaluations computed normally (mip check, Binomial model, edge formula)
- JSONL logged to `logs/t4_mlb_dryrun_YYYYMMDD.jsonl` — one record per evaluation with valid mip
- `trader.open_position()` skipped — no positions open
- C4 not called, budget cap not enforced (want unfiltered distribution for T-203)
- `would_fire = net_edge > 0` as dry-run fire indicator
- 13 new tests in `TestDryRunMode` class

T4 MLB cron (`0 22 * * *`) is NOW ENABLED in `deploy/cron.conf` with `T4_MLB_DRY_RUN=true`. First dry-run fires tonight. JSONL will begin accumulating real evaluation data.

### T4 Throughput Gap Analysis (TEXT ONLY — no code changes)
Three structural gaps identified between ~1,000 evals/game design target and current ~15-50 actual:
1. **Gap 1 (ESPN):** `_espn_poll_once_mlb()` returns current-batter state only, not all batters who have appeared. Needs ESPN box score endpoint query. This is a targeted code fix.
2. **Gap 2 (decision tree):** Single `net_edge > 0` condition, no sub-bands. Phase 8 blocked (ADR-0029/0030).
3. **Gap 3 (`already_open`):** Caps fires at ~95/game (correct risk behavior). ~10-50 fires/game is the intended outcome.

The 477 evals/day figure from the MC was a simulation artifact (1 eval/inning/player). Real T4 with Gap 1 fixed: ~259,200 raw evaluations/session.

### Monte Carlo (4 Scenarios, T4 Included)
Run against real June 26 pregame data (96 forecasts, 53 players). Results at `scratchpad/mc_mlb_four_scenarios.py`. T4 contributed 36–44 bets/day across scenarios. MC simulation understated T4 throughput by ~100x (known limitation, documented).

---

## Current VPS Cron State

| Cron | Script | Status |
|------|--------|--------|
| PIPE-05FX (22:30 UTC) | Feature refresh | ACTIVE |
| PIPE-06pre (16:30 UTC) | Pregame MLB context | ACTIVE |
| PIPE-05 (11:00 UTC) | T1 MLB betting | **PAUSED — S93** |
| PIPE-05.5 (19:30 UTC) | T2 MLB lineup overlay | **PAUSED — S93** |
| PIPE-05R (06:30 UTC) | MLB resolution | ACTIVE |
| PIPE-06 MLB (*/15 20-23, */15 0-3) | T3 signal scan | ACTIVE |
| PIPE-07 MLB (22:00 UTC) | T4 in-play | **ACTIVE — DRY-RUN** |

---

## MLB T4 Iteration Plan Status

| Task | Status | Notes |
|------|--------|-------|
| T-200 | ✅ S92 | Inning-aware `ab_remaining` formula |
| T-201 | ✅ S92 | Dual-pool PIPE-05R resolution |
| T-202 | ✅ S93 | Dry-run mode, JSONL logging, cron live |
| T-203 | 🔲 NEXT | Requires ≥1 real game night of JSONL. Analyze distribution → MIN_EDGE_T4 → ADR (GG-007 resolution). Consider fixing Gap 1 (ESPN box score) first for higher-fidelity corpus. |
| T-204 | 🔲 FUTURE | Remove `T4_MLB_DRY_RUN=true`. Re-enable PIPE-05 + PIPE-05.5. Requires T-203 ADR signed. |

**CLEAN, GREEN, ON AUTO is NOT achieved until T-204 complete.**

---

## Portfolio State

- **MLB bankroll:** $751.10 (VPS live book, 0 open, 0 T1/T2 bets since crons paused)
- **NBA book:** Dark period; no active positions
- **G6 gate:** NOT MET — GG-004 (EXP-017) open; P&L negative (−$248.90 / −24.9%)

---

## Next Session Priorities

1. **Wait for T4 dry-run JSONL.** First cron fires tonight at 22:00 UTC. MLB games start ~17:05-23:10 UTC. Check `logs/t4_mlb_dryrun_20260626.jsonl` for evaluation records.
2. **T-203 (after ≥1 real game night of data).** Pull JSONL from VPS, analyze edge distribution, calibrate MIN_EDGE_T4, write ADR closing GG-007.
3. **Gap 1 (optional pre-T-203).** Fix `_espn_poll_once_mlb()` to query ESPN box score endpoint for all batters, not just current batter. Increases JSONL corpus size ~18x per cycle. Decision: fix before or alongside T-203.
4. **T-204 (after T-203 ADR signed).** Remove dry-run flag, re-enable PIPE-05 + PIPE-05.5. MLB arm fully live.

---

## Open Governance Gaps (Relevant to Next Session)

- **GG-007:** T4/T5 threshold uncalibrated — LOW now; closes with T-203 ADR.
- **GG-043:** MLB Kelly 0.10 inherited from NBA — deferred to pre-MLB G6.
- **GG-044:** C7 Brier/ECE baselines are NBA G4 values — deferred to post-first-MLB-resolutions.
- **GG-004:** Commercial validation (EXP-017) — binding G6 blocker; requires ≥150 resolved MLB bets.
