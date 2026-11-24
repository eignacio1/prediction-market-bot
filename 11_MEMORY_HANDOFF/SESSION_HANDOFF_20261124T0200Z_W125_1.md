# SESSION HANDOFF W125.1 (parked, session limit) - placement as a decision
vision_pillar: EXECUTION E2 / E3 (net per filled bet, adverse selection)
gap_measure: PARTIAL - Part A code built; no box read yet; Parts B, C, RESULT.md not started
surface_delta: +1 read-only box task (placement_fill_read); no cron, no service
pattern_sweep: model_records gained fee_per_contract + markout (consumers: tests/test_placement_join.py passes)
directive_conflicts: none

## State
- Worktree: PM-worktrees/20261124T011318Z-w125-1-placement, branch session/20261124T011318Z-w125-1-placement.
- PR #554 (124.3 H-EXEC-4 prereg): rebased, guard pass, `test` was pending at park. Merge when green. PREREG untouched.
- PR #560 (Part A): placement/fill_model.py, scripts/placement_fill_read.py, box_tasks allowlist entry, tests/test_w125_1_fill_model.py. Local tests green; CI not yet reported.
- Box deploy (deploy_truth_read) and the t4-mlb decision: NOT checked.

## Next, in order
1. Merge #554 then #560 on green CI. 2. Push request TOML for `placement_fill_read`, read result in BOX_TASKS/results.
3. Part B: rules in placement/policy.py behind ARM_PLACEMENT_POLICY=current (default; "on" keeps today's table behaviour); known-answer tests; stays OFF; dated activation proposal line. EXP-W119.3 FADE rest_inside 50/50 stays frozen.
4. Part C: skip-reason counts come from the same task (`skips.by_reason`). Audit ride_orders.py:40-41 (DEMO_BOOK_EVENT_CAP_USD 500, DAY_CAP 150 = copies of real-money values; arm path uses asz.demo_book_caps) - fix or register a GG.
5. RESULT.md in 12_EXPLORATORY/placement/, H-EXEC rows in HYPOTHESIS_DOCTRINE II.3, ACTIVE_QUEUE row (docs-only push).
