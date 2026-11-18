# Session Handoff — 2026-09-30T05:52Z

<!-- session-meta
task_id: T-598
tier: STANDARD
timestamp: 2026-09-30T05:52:00Z
commit: aa713fd
one_line_summary: T-598 EXP-030: shallow T4M-PROJ structure candidate scored once on sealed holdout; NO DETECTABLE DIFFERENCE; GG-323 opened.
gg_touched: GG-323
adr_touched: none
plan_deliverable_moved: no
-->

**Trigger:** clean cutover. **Last commit:** `aa713fd` (main).

## Strategic Decisions This Session
None beyond the DECISION_LOG T-598 row: pre-registered split, C selection on validation, permutation control on validation only, holdout run once.

## What changed
- New module `c3_forecasting/t4_structure_model.py`, tests (5 pass), runner `scripts/run_exp030_t4_structure.py`; incumbent untouched.
- EXP-030 prereg, D1 inventory, results summary in `05_RESEARCH_EXPERIMENTS/`.
- Holdout (40 games): Brier gain -0.0063 [-0.0203, +0.0091] = NO DETECTABLE DIFFERENCE. Permutation control not passed.
- GG-323 registered (state fields 0.9% of rows; clean window ends 07-30; no outcomes after 08-19).
- Paper bet count not re-checked this close-out. No ADR, no VPS writes, no orders.

## Stray branches
Not swept before this line; Step 9 output is in the session transcript.

## One thing pending
Decoupled outcomes for 2026-08-20..09-29 (`scripts/build_t4_outcome_store.py`) would widen the window; separate task, not started.

## Resume
`scripts/session_delta.sh "$(cat 04_EXECUTION/.last_session_checkpoint)"`
