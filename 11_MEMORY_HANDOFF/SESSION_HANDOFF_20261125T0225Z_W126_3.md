<!-- session-meta
task_id: W126.3
tier: STANDARD
timestamp: 2026-11-25T02:25:00Z
commit: 99f9e37
one_line_summary: W126.3: MLB PA model + game sim + one-draw joint board built with 12 known-answer tests; 2026 held-out report trails market on all four families; dry run and registry row NOT done.
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D4, D5a
gap_delta: D4 MLB stage: engine code + tests exist but registry row still none (not claimed); D5a MLB 3/8 -> 3/8 until the manifest row lands
pattern_sweep: grep asof_prior / lineup_aware consumers in src/ scripts/ tests/ -> reused unchanged; no shared contract patched
surface_delta: 0 (no cron/service/workflow; 3 new src modules, 1 offline runner)
-->

# Handoff W126.3 — MLB engine to a priced board (Last reviewed 2026-11-25)

**Branch:** `session/20261125T002628Z-w126-3-mlb-engine`. Tests: 15 pass (12 new + dry-run w122). Full suite not run.

## Strategic Decisions This Session
None — implementation/report session. EXP-MLBSIM-001 pre-registered (f596ff0) before any 2026 outcome join.

## Done
- A inventory; B `pa_model.py`, `sim.py`, `joint_board.py`, `tests/test_mlb_engine_sim.py` (planted run env, monotone ladders, correlation signs).
- C scoring on 2,429 games: `RESULT_W126_3.md` / `RESULTS_W126_3.json`. Trails Kalshi mid: ML -0.0037, total -0.0073, spread -0.0019, team total -0.0051 Brier.

## NOT done (honest)
- Opening-day dry run with engine prices on shadow rows.
- `ARCHITECTURE_COMPONENTS.toml` MLB engine row + MLB_ENGINE manifest (so D5(a) stays 3/8, D4 unmoved).
- HYPOTHESIS_DOCTRINE rows; KXMLBHIT market comparison; F3/F5/F7; park/home-field terms.
- PR/CI/merge: not opened at close (see below).

directive_conflicts: none
Pushback: Part C asked a dry run + registry in-PR; deferred to stay in session budget rather than ship them untested.
Surface: engine under-prices home/team runs, over-prices hits — add home-field/park split next.
Dependencies: player-name->batter-id bridge for KXMLBHIT.

**One thing pending:** open PR, add dry-run test + MLB engine manifest row, rerun CI.
**Resume:** worktree `PM-worktrees/20261125T002628Z-w126-3-mlb-engine`, read this file + `RESULT_W126_3.md`.
