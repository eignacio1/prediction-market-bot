# Session handoff W113.1 (2026-11-12)

**Status:** PARTIAL (code done and tested; PR #493 NOT merged: CI red on a stale test unrelated to this change; layer 6/7 evidence unread because no allowlisted box task reads the arm order log)
**B-084:** in progress. **Branch:** session/20261112T230401Z-w113-1-d6-wired @ rebased head on origin/main. **PR:** #493, CI `test` failed: 1 failed, 5707 passed. The one failure is `tests/test_w109_3_props_shadow_install.py::test_registry_entry_is_paused_and_task_is_allowlisted` (registry says live after the 11-12 15:04 PT install approval); main's own run 43326790475 fails the same way. Not my file; Rule 11, logged in GG-1898.
**Result:** every arm order is sized by `arm_sizing.size_for` via `decision_trees/row_sizing.py`; NHL has a per-row filter adapter and 20 kept splits; D6 counting rules for layers 6/7 are in `coverage.py`.

## MEASURE MOVED
- D6 wired: 0 to 0 of 117 (local recount). Honest reason: layers 6 and 7 need the box order log, which no allowlisted task reads. No cell is missing exactly one layer.
- Layer 3 NHL: 0 to 9 cells (local, where `exp_output/NHL_EVENTS` exists; 0 on the box until GG-1898). NFL stays 113.2's. NBA 9 unchanged.
- Per sport [L1..L7] registered/wired: MLB 42/0 [3,12,0,3,0,0,0]; NBA 25/0 [9,12,9,7,7,0,0]; NFL 29/0 [9,12,0,9,9,0,0]; NHL 21/0 [9,9,9,8,7,0,0].
- NHL splits: 72 leaves scored, 20 kept (held-out games >= 10, net > 0), 1 survives BH (KXNHLGAME deployment@side away_edge, MOMENTUM, held-out +0.133, 19 games). Interval source: `nhl_factors_w112/leaf_scores.json` (test_lo/test_hi).
- 14-day replay 2026-10-30..11-12 (13,508 decisions): NBA 7034 decisions, 719 NO_BET to RIDE; NHL 3147 decisions, 0 to 401 NO_BET to RIDE (before: all NO_BET); NFL 0 changed (113.2). Overall changed 1,120.
- E1-E3 per arm: not measured. No arm_order rows readable (see below). Epoch rule stays: post-2026-11-06T01:03:42Z all sides, pre-epoch YES-only, never mixed.
- Box deploy (`deploy_truth_read`, 2026-11-12T23:31Z): box HEAD fac52dd0 = origin/main, all OK. This PR is not deployed. `arm_order` rows: no allowlisted box task reads `arm_orders/orders.jsonl`; the window should add a read task (a PR to `scripts/box_tasks.py` with a test).

## Stage per factor (NHL)
rest, travel, density, venue, shot_quality, deployment: aggregated, interpreted, applied (tested split per leaf; local only until GG-1898). Quant bar for the adapter: known-answer test of `nhl_game_id`, applies/doesn't-apply note and the replay measurement above are in `tests/test_nhl_filter_adapter_w113_1.py`.

## Operator decisions
None.

vision_pillar: DEPTH (D6); gap_measure: D6 layers 3, 6, 7; gap_delta: layer 3 NHL +9 local, D6 wired 0 to 0; GG-1896..1898 opened.
pattern_sweep: arm vocabulary and Kelly-0 sizing grepped across `src/ scripts/ tests/`; only arm_orders consumed `size_for`. Label "fade arm closed" swept in `scripts/claude_md_now.py` (now "untradeable (no book / data)").
surface_delta: 0 new runtime components. Dependency noted: NHL event store has no box job (GG-1898).
directive_conflicts: (1) `nhl_filters_for_row` did not exist, built here. (2) Shadow rows cannot carry size_for (GG-1896); evidence from the arm order log instead. (3) arm vocabularies differ, mapped. (4) No joint draws until 113.3 (GG-1897). (5) Merge on green not possible: main CI red.
Next: when main CI is fixed, rebase PR #493 and merge on green; read box arm_order rows; recount D6.
