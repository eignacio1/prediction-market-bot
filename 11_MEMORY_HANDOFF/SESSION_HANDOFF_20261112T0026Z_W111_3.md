# Session handoff: W111.3 / B-079 (TREES - D6)


<!-- session-meta
task_id: B-079
tier: STANDARD
timestamp: 2026-11-12T00:45:00Z
commit: 7846dec
one_line_summary: W111.3 B-079: router reads per-leaf arm map, pot of gold and momentum scored per leaf, D6 scorecard (0/117), forward test frozen
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D6 (cells wired end to end), D5a decision trees
gap_delta: D6 0/117 -> 0/117 (layers 1,2,4,5 measured per sport; 3,6,7 open); arms scored per leaf 4 -> 6 (scripts/distance_to_optimum.py @ 7846dec)
pattern_sweep: n/a (no defect fixed)
surface_delta: 0
-->

**Status:** Parts A, B, C done | B-079 | PR #483 merged (de8b003, CI green); PR #484 (Parts B+C) merged 7846dec, CI green; box deploy rc=0 at 7846dec1.

## What changed
- **A (merged):** router reads `decision_trees/leaf_map.json` (110.5 fit-window arm per leaf); shadow rows log `leaf_id`, `arm`, `arm_source`, `thin`, `move_source`, `orders:"off"`. Replay script uses the map.
- **B:** `quant/retro_route.py` `extra_nets` / `extra_leaf_table`: POT_OF_GOLD (buy the lottery side in 1-15c / 85-99c buckets) and MOMENTUM_OPEN (follow move since first shadow row), same split, fee, bootstrap. `results_extra.json`, ROUTING.md section. Held-out family results: pot of gold negative in NBA totals/team totals and NHL totals (intervals below zero), no family positive; MOMENTUM_OPEN +0.130 [+0.033, +0.227] on NHL moneyline (574 rows / 59 games), negative on NFL spread. Routed to those arms in these leaves, nothing ruled out. Leaf-level leads carry no multiplicity correction.
- **C:** `coverage.d6_layers` / `d6_summary`; `scripts/distance_to_optimum.py` prints D6. Forward pre-registration `12_EXPLORATORY/retro_route/LEAF_MAP_FORWARD_PREREGISTRATION_2026-11-12.md` (map sha256 inside; 113 routed leaves + 3 family leads, 116 tests, BH q=0.10, shadow only).

## Limits (stated, not fixed)
- Data epoch N/A (shadow rows are not fills).
- Momentum archive: the 20-minute `PRICE_ARCHIVE` join (2 GB) not done; NFL/MLB have 1-2 pre-start prices; NBA/NHL archive-only tickers have no settlement cache. Move comes from the ticker's own shadow rows. NHL runner writes to `data/shadow/nhl`, so its move bin falls to "na" (flagged).
- Factor filters (NFL `filters.py`, NBA `granularity_filter.py`) are logged only if a caller supplies per-row inputs; no runner does, so D6 layer 3 is 0.
- D0 tickers have no resolvable band in the archive replay and stay NO_BET.
- `leaf_map.json` is not in package-data (loads from the source tree, like `longshot_cells.toml`).
- Re-running run.py on current scratch gives fit_games 380 / test 163 vs committed 375 / 161 (box has more rows); committed results.json untouched.
- Scratch: `PM-scratch/w111_3/`. Box deploy read back: HEAD 7846dec1, rc=0.

## Operator decisions
None (a new pre-registration, not a change to a frozen one).
