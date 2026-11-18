# Session Handoff — 2026-09-30T05:20Z

<!-- session-meta
task_id: T-594
tier: STANDARD
timestamp: 2026-09-30T05:20:00Z
commit: fb0587c
one_line_summary: EXP-028 pre-game MLB hit model: skill over climatology detected (dBrier +0.0052), market edge NOT TESTABLE (0 price overlap)
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
-->

**Trigger:** wave complete. **Last commit:** `fb0587c` on `session/20260930T050100Z-pregame-model-mlb` (pushed; not merged to main).

## Strategic Decisions This Session
None beyond the frozen EXP-028 pre-registration (`90e96c2`). DECISION_LOG / GG log not edited (wave read-only rule); findings live in the results summary.

## What changed
- New `c3_forecasting/pregame_hits_model.py`, `tests/test_pregame_hits_model.py` (7 pass), `exp_output/EXP-028/`, prereg + results summaries.
- Holdout scored once. P1/P2/P4/P6 hit; P3 missed; **P5 permutation control failed its literal criterion** (results void-flagged; sign argues mis-specified control, not leak).
- Matrix has no prices; priced archive starts after matrix ends (overlap 0) → market edge untestable.

## Not done / for operator routing
- Nav-file "Last reviewed" chain generator (`generate_session_artifacts.py`) deliberately NOT run: it edits shared TODO_NEXT/MEMORY_BANK/PLAN, outside this wave's ownership. Run at merge time.
- Suggested GG: P5 control mis-specification (two-sided test on a noise-fit model is biased negative); GG/T for extending the matrix over 2026-08-01→09-30 and running `run_gate` unmodified.
- `bfd4c4d` (40.3) still unmerged (41.1's job).

## One thing pending
Land branch via PR review (src changed); then extend matrix over the priced window for the market comparison.

## Resume
`cd PM-worktrees/20260930T050100Z-pregame-model-mlb && git log --oneline -3`
