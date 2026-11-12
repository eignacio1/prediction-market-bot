# Session Handoff — 2026-11-12T05:35Z (W112.1 B-081)

<!-- session-meta
task_id: B-081
tier: STANDARD
timestamp: 2026-11-12T05:35:00Z
commit: 1633d19
one_line_summary: W112.1 filter splits as router leaves (D6 layer 3): NBA wired, layer 3 cells 0->9; NFL/NHL log why not (PR #488).
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D6 layer 3, D5(a) decision trees
gap_delta: D6 layer 3 cells NBA 0->9 of 25 registered, NFL/NHL/MLB 0; D6 wired 0->0 of 117 (coverage.d6_layers @ 1633d19)
pattern_sweep: n/a (no defect fixed; own regression KeyError 'family' in coverage.py fixed pre-push, grep d6_layers/router_fields consumers: distance_to_optimum.py, tests only)
surface_delta: 0 (no cron/service; new data files filter_splits.json, filter_data/nba_team_percentiles.json)
-->

**Status:** PR #488 (branch session/20261112T005606Z-w112-1-trees-d6-layer3). CI on head 1633d19 was pending at close; merge only when green, then read box deploy and record t4-mlb decision.

## Strategic Decisions This Session
None — implementation-only (kept-split rule fixed a priori: not thin, arm != NO_BET, held-out games >= 10, held-out net > 0).

## What changed
- filter_supply.py: per-sport adapters, point-in-time asserts; NBA wired, NFL `nfl_weather_forecast_and_matchup_book_not_wired`, NHL `filters_unavailable:nhl_engine.filters_not_merged`.
- leaf_map/router: leaf = market-state leaf x filter split; only KEPT splits change arm; split path logged; orders untouched.
- 113 splits tested, 7 kept (all NBA, none BH-surviving: likely chance-level). Replay 14d (10-30..11-12): NBA 6390 decisions, 626 NO_BET->RIDE; NFL/NHL unchanged.
- Closest to wired: 9 NBA cells (layers 1-5; lack 6, 7).

directive_conflicts: none found.

## One thing pending
Merge #488 on green; NFL weather-forecast storage + MatchupBook provider (candidate GG-1910..1912); NHL awaits 112.4.

## Resume
`git fetch && gh pr checks 488`
- Box deploy read 05:38Z: box at c2b3664d, #488 (d536a9c) not yet deployed; t4-mlb decision for #488 to be read next session.
- Follow-up: 112.4 (74d0527) merged after #488; NHL adapter should call nhl_filters_for_row next (currently logs filters_unavailable).
