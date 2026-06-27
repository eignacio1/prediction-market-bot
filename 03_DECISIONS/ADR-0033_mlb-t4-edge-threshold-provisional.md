# ADR-0033 — MLB T4 Edge Threshold: Provisional Adoption of System Default

**Status:** ACCEPTED  
**Date:** 2026-06-26  
**Session:** S94  
**Operator:** Earl Ignacio  
**Scope:** MLB T4 in-play band — minimum edge threshold for bet approval

---

## Context

MLB T4 (`run_t4_mlb_live.py`, PIPE-07 MLB) uses C4 (`BOT_C4_ACTIVE=true`) to gate each bet evaluation. C4's `MIN_EDGE_TO_APPROVE` (set to `0.04` in `risk.py`, established by ADR-0020) is the active edge gate for all C4-routed bets across the system.

The MLB T4 dry-run mode (T-202, S93) was designed to accumulate JSONL evaluation data to empirically calibrate a separate `MIN_EDGE_T4` value before going live. Earl's SESSION 94 directive supersedes this: proceed with T4 live now using the system default, defer empirical calibration to the post-paper period.

T-203 (this ADR) closes the provisional calibration question and unblocks T-204 (cron live enablement).

---

## Decision

**MLB T4 will use `MIN_EDGE_TO_APPROVE = 0.04` (system default, risk.py) as the edge gate.** No separate `MIN_EDGE_T4` variable is introduced.

Rationale:
1. C4 is already the active gate — removing `T4_MLB_DRY_RUN=true` causes C4 to enforce `MIN_EDGE_TO_APPROVE` automatically with no code change required.
2. `0.04` (4%) was calibrated for the overall system at ADR-0020. It covers Kalshi taker fee (`0.07 × P × (1−P)`) at any market price: at `P=0.50`, fee = `$0.0175` per contract; 4% gross edge = `$0.04` − `$0.0175` fee = `$0.0225` net minimum. This is structurally positive.
3. MLB T4 operates at flat 1-contract sizing (ADR-0023 paper policy) with a 27% band budget cap. Kelly scaling is not applied to T4 sizing, so threshold sensitivity to over-sizing is low.
4. The provisional nature is explicit: empirical MLB T4 edge distribution calibration is deferred to the post-paper period (≥30 resolved MLB T4 bets). If the threshold proves materially wrong (false fire rate >20% or kill switch triggers within 3 sessions), register a governance gap and revise via superseding ADR.

---

## Gap 1 Correction (SESSION 93 Text-Only Error)

SESSION 93 DECISION_LOG (T4 throughput gap entry) stated:

> "Gap 1: `_espn_poll_once_mlb()` returns current-batter state only, not all batters who have appeared."

This was incorrect. The function calls `_ESPN_MLB_SUMMARY` (ESPN boxscore endpoint, `event=game_id`) and iterates `stat_group.get("athletes", [])` — all batting athletes in both teams. It returns `MLBLiveBatterState` for every player who matches pregame context, not just the current batter. The SESSION 93 analysis was text-only and did not read the code. The actual per-cycle evaluation count is `N_matched_players × N_thresholds` per game, not `1 × N_thresholds`.

The DECISION_LOG entry for SESSION 93 T4 throughput gap (line 333) contains this error. It is documented here as a correction. The DECISION_LOG entry is not amended (immutable log). The correction is the authoritative record going forward.

Practical implication: T4 MLB evaluation throughput is higher than SESSION 93 estimated. Gap 3 (`already_open` guard capping fires at ~95/game) remains the correct characterization of the fire limit.

---

## Cron Changes (T-204)

Authorized by this ADR:

1. **Remove `T4_MLB_DRY_RUN=true`** from T4 MLB cron line → T4 goes live, C4 active, positions open
2. **Re-enable PIPE-05** (T1 MLB, `0 11 * * *`) → first MLB T1 bets fire June 27 at 11:00 UTC
3. **Re-enable PIPE-05.5** (T2 MLB, `30 19 * * *`) → lineup overlay fires June 27 at 19:30 UTC

---

## Consequences

- MLB T4 opens real paper positions starting June 26 at 22:00 UTC (tonight's cron window)
- MLB T1 bets fire June 27 at 11:00 UTC
- MLB T2 lineup overlay fires June 27 at 19:30 UTC
- `paper_portfolio_mlb_t4.json` accumulates real resolved positions starting tonight
- Post-paper calibration: after ≥30 resolved T4 bets, analyze edge distribution; revise threshold via superseding ADR if materially off
- GG-007 does NOT close with this ADR. GG-007 refers to NBA Phase 8 ADR-0029/ADR-0030 skeleton threshold constants (`T4_MIN_DELTA_P`, `T5_YES_CERTAINTY`, `T5_NO_CERTAINTY`) — unrelated to MLB T4 edge gate. GG-007 remains OPEN (LOW severity, Phase 8 pre-activation gate).
