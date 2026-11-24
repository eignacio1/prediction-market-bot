# Session handoff W125.2 (PARKED mid-block, session limit) - 2026-11-23 ~17:20 PT
Block: W125.2 D6 / router, every routed row reaches a leaf. Measure: D6 (17 of 117 before: NBA 7, NFL 4, NHL 6, MLB 0), E1 (router ERROR rows/day).
Worktree: PM-worktrees/20261124T011321Z-w125-2-every-row-leaf, branch session/20261124T011321Z-w125-2-every-row-leaf (pushed, head 6cd7cad).

## Done
- PR #559 (this branch): scripts/router_error_read.py + box task `router_error_read` + test (Part A reader, GG-2007); Part B healthcheck-11 counts shadow_order AND arm_order, WARN only if both zero (GG-2006), tests both directions.
- PR #556 (124.4 dense capture): rebased, CI was pending. Not merged. Install NOT run.
- Box requests pushed to main: 20261124T0117Z_a_d6_trace_read, _b_d6_read. Results not yet on main when parked.

## Not done (resume here, in order)
1. `gh pr checks 556` and `559`; merge #556 on green (my own PR), then rebase #559 on main (box_tasks.py will conflict: keep both task sets), CI green, merge.
2. Part 0: add read-only `gate` subcommand to scripts/archive_dense_install.py + task `archive_dense_gate_read` (+ RUNTIME_REGISTRY entry), run on box at 67% disk; put projected % and approval line under `operator decisions:`.
3. Part A: after #559 merges push a request toml for `router_error_read`; break down ERROR skips by exception/cell/date; fix each with a regression test or register a GG. Report rows recovered per sport.
4. Part C: read the 0117Z d6_trace_read result, Fable branch session/20261117T010353Z-w115-3-d6-one-game (1ce79c5). NFL cells missing layer 7 are likely from W117.1 A3 (NFL per-leaf orders routed NO_BET, operator-approved): do not change silently, register/surface it. Re-run d6_read after deploy; report D6 per sport before/after.
5. Update GG-2006/GG-2007 status, ACTIVE_QUEUE row, final handoff.

## Footing
surface_delta: +1 box task (router_error_read, read-only), registry unchanged so far. pattern_sweep: none yet. directive_conflicts: none known. operator decisions: none yet (budget-gate % pending step 2).
