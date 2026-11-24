# SESSION HANDOFF — W124.2 H-MEAS-1 (closing price calibrated per family?)
Branch session/20261124T002032Z-w124-2-meas-close. Result: `12_EXPLORATORY/edge_location/meas_close/RESULT.md` (+ results.json, tables.md, PREREG.md).

## Verdict
- 85,229 settled markets joined to a close (50 sport x family cells). **LICENSED 1** (MLB period F3, thin: slope 0.90 [0.21, 1.67], 90 games); **NOT LICENSED 19** (10 miscalibrated: NBA ML/team total/alt total, NHL ML/team total/alt spread/alt total, NFL team total/alt total, MLB alt total; 9 noise-limited); **UNDERPOWERED 30** (all `*_main` lines, all NBA/NHL/NFL props, MLB/NFL ML).
- Favourite-longshot slope above 1: NHL ML 1.72 [1.21, 2.21], NBA ML 1.26 [1.03, 1.47], NHL team total 1.10 [1.04, 1.16].
- Variance ratio (settlement sd^2 / CLV sd^2): median 410x at 6 h, 444x at 24 h; usable only where LICENSED (today MLB F3, idle until 2027).
- Orders claim: 1,335 orders, 58 games, slope 0.52 [-1.27, 2.11]: PASS by the frozen rule, uninformative (spans 0 and 1). Filled-only line not run (no fill status in the Mac log; log ends 11-18 20:23Z, all post-epoch).

## measure_moved
PROOF: families licensed for CLV 0 -> 1 of 50 cells (MLB F3 only); effective-sample multiplier per family in the table.

## For the window
- Next cheapest licenses are the 9 noise-limited cells (need games, not models): `games_needed_for_floor` in results.json. Re-run at the weekly look; code is `run_meas1.py <archive> <cache> <orders>`.
- Registry row H-MEAS-1 updated in HYPOTHESIS_DOCTRINE II.1. No ROLLING_BACKLOG edits.
- local_helper: bootstrap code in run_meas1.py is local; swap to 124.1's `quant/inference.py` when merged (not on main at start).
- Fix noted: milestone type for hockey is `hockey_match` (first fetch used `hockey_game`, dropped all NHL; fixed before any verdict was read). Fence resolves relative paths under 12_EXPLORATORY/ (fetchers wrote there; moved to meas_close/cache, gitignored).
- Rule note: the pre-registered rule licenses on interval-contains-1, so a very wide interval (MLB F3) licenses; consider a max-width clause in a successor PREREG (not applied here, rule was frozen).

## Hygiene
- pattern_sweep: start-time source (`start_date`, not `occurrence_datetime`) is stated in PREREG; other edge_location code uses archive run_ts only; no other consumer of `occurrence_datetime` found in meas_close.
- surface_delta: 0 (no cron / service; two fetch scripts and one analysis script run by hand).
- directive_conflicts: none.
- tests: tests/test_meas1.py (5 known-answer tests) pass; precheck_changed 220 passed.
