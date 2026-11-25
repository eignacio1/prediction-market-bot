# Session handoff W127.2 (DEPTH / MLB: land the engine, dry run, count it)
Last reviewed: 2026-11-25. Branch `w127-2-part-a`. Model: Sonnet.

vision_pillar: DEPTH. gap_measure: D4 MLB (engine stage), D5(a) MLB (n of 8). Source: `scripts/distance_to_optimum.py` on the `[[engine]]` / `[[component]]` rows.
gap_delta: D4 MLB none -> data layer (store manifest) + engine scaffold (`joint_board.py`) + engine test (`test_mlb_engine_sim.py`). D5(a) MLB 3/8 -> 4/8 (adds cross_reference_compatibility).

## Done
- Part 0: #572 (EXP-MLBSIM-001) merged, 11e1e07. Needed an ALLOW entry for `run_w126_3.py` in `tests/test_w119_4_readers.py`.
- Part A: `mlb_engine/forecaster.py` (`MLBEngineForecaster`, no order path) and `tests/test_mlb_engine_dry_run_w127.py` (3 tests). LAD v ATL at T1/T2/T3 through `pregame_shadow.runner.run_once`: 12 of 12 MLB game cells log an engine-priced row. Offline only. No cron, no registry status change.
- Part B: `scripts/mlb_engine_manifest.py` + `MLB_ENGINE/event_store_manifest.json` (2024 2429 games / 711,899 pitches; 2025 2430 / 712,528; 2026 2429 / 716,792; 0 duplicates, full lineups, both starters).
  Counted component tests: decision_trees + filtering_mechanisms -> `test_decision_router.py`; momentum_looping -> `test_w90_3_momentum_j.py`; cross_reference_compatibility -> `test_mlb_engine_sim.py`.
  NOT counted: cluster_designs, temporal_evolution, structural_tensions, seat_interface (MLB seat is a stub, `test_seat_interface.py`).
- Part C: DESCRIPTIVE, no verdict. `12_EXPLORATORY/mlb_engine/RESULT_W127_2_C.md`. 0 of 22 look-back games can carry an engine price: they are 2026 postseason (10-05..10-28), the pitch store ends 09-27, Savant returns header-only files for October 2026 (regular-season and postseason filters). No imputed price was scored. Named the 2027 test: EXP-MLBENGINE-SPLIT-2027 (engine_gap terciles as a leaf split, router v2, net after exact fee, 2027 rows only). Not authored or frozen.

## Caveats
- The manifest's pitch-count check is store-internal (same pitches), not an independent box-score reconcile.
- EXP-037: 2026 rows are not evidence; Part C stays descriptive.
- Dry run uses a league-average tile board, not real lineups; it proves the wiring and the rung mapping, not a price level.

directive_conflicts: none found (OPERATOR_DIRECTIVES read at start; user override honored: ran locally, one PR and one CI at the end).
pattern_sweep: PRICE_ARCHIVE readers in `src/ scripts/ tests/ 12_EXPLORATORY/` against the io_jsonl test; one ALLOW entry added.
surface_delta: +0 services, +0 crons, +1 module (`forecaster.py`, unwired), +1 offline script (`mlb_engine_manifest.py`).
Pushback: the block's Part C assumed postseason games were priceable; they are not. Surface: Savant has no 2026 postseason pitches; nothing else in the store covers October. Dependencies: a 2027 box job to fetch Savant daily and build lineup-based boards (needs a named `*_install`, operator approval).
operator decisions: none needed now. Before opening day: approve writing EXP-MLBENGINE-SPLIT-2027 and the daily-board install task.
Next: write the pre-registration, wire `MLBEngineForecaster` behind a flag on the box after approval, re-run the manifest after each Savant refresh.
