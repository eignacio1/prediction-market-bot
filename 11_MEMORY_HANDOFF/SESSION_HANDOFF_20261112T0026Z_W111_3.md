# Session handoff: W111.3 / B-079 (TREES - D6)

```
vision_pillar: DEPTH
gap_measure: D6 (and D5a decision trees), PROOF P1 groundwork
gap_delta: D6 wired end to end 0 -> 0 of 117 (honest: layers 3, 6, 7 absent everywhere). Layers present now, by sport (1/2/3/4/5/6/7): MLB 3/12/0/3/0/0/0; NBA 9/12/0/7/7/0/0; NFL 9/12/0/9/9/0/0; NHL 9/9/0/8/7/0/0. Router now logs the leaf arm (was 27 of 117 cells with a logged arm, 25,263 NO_BET in replay). Arms scored per leaf 4 -> 6.
pattern_sweep: n/a (no defect fixed)
surface_delta: none (no cron, service or workflow added; router fields are log-only)
directive_conflicts: none
```

**Status:** Parts A, B, C done | B-079 | PR #483 merged (de8b003, CI green); PR #484 (Parts B+C) open, CI pending at write time.

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
- Scratch: `PM-scratch/w111_3/`. Box deploy read-back for #483 and #484 not done at write time.

## Operator decisions
None (a new pre-registration, not a change to a frozen one).
