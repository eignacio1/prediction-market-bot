# W119.1 handoff (CLOSED). Last reviewed: 2026-11-18
Common rules read (first line "# Wave 119 common rules"); W118.3 handoff read.
## Part A (store on the box)
- 1,737 of 1,737 finished games fetched; 50 failures repeat on pass 2 (fetch_failures.json). NHL_EVENTS 84.6 MB, seasons 2025+2026. Disk 74% (18 of 24 GB).
## Part B (layer 3), PR #530 merged ea75451
- Goalie (last completed starter, season save rate shrunk 300 shots to an EXPANDING league rate, NaN < 100 shots) and special teams (PP goals, PIM, 20-game roll) as splits in nhl adapter + filter_supply (12 splits total). PREREG_W119_1_GOALIE_ST.md committed before scoring.
- Scored per leaf per arm, 226 fit / 98 held-out games: 42 new leaves, 23 reportable, 8 held-out positive (goalie 2, special teams 6), 0 pass BH, 0 DRAFT. Routing result: leads for the next look.
- Defect fixed: shrinkage used the whole-season league rate (leaked later games). tests/test_nhl_goalie_st_w119_1.py pins no-leak.
- Goalie covers 178 of 324 games (100-shot minimum on a 343-game box). No pre-game lineup feed: registered gap, proxy is last starter.
## Part C (router v2)
- 12_EXPLORATORY/nhl_router_v2/run.py, consensus prior (transfer sd 0.03). 99 seen leaves, 9 cells: all NO_BET, 0 armed; held-out 98 games, no bets. Routed to no bet in these leaves; hypothesis closed (EXP-W119.1-NHL-V2, parked for R&D).
- leaf_maps/nhl_v2.json + MAP_VERSIONS["nhl_v2"]. Opt-in via PM_LEAF_MAP_VERSION=nhl_v2. Default stays v1. NOT flipped on the box.
## D6 recount (box, 04:53Z, HEAD 9eed2933 contains ea75451)
- NHL 6 -> 6 of 21. Wired: NHL_{GAME_TOTAL,MONEYLINE,PUCK_LINE} x T2,T3. Layers 1-7 per layer: 9,9,6,9,7,8,8.
- Unwired, one cause each: T4, T4NHL-ARITH, T4NHL-FLOW, T5 x 3 markets (12 cells) = layer 1, no model p built. T1 x 3 markets = layer 3, no kept split on box rows.
- Why no move: wiring counts box rows with the active map (v1); new splits need a kept leaf on box rows, and the new classes are scored on shadow rows locally.
## Notes
- CI failure on first push was main's stale RUNTIME_MAP.md (not this change); fixed by re-render, which main had also landed.
- OPERATOR_DIRECTIVES.md not read this block (directive_conflicts: unchecked, none known).
- Worktree PM-worktrees/20261119T0120Z-w119-1-nhl; shared tree has others' uncommitted edits.
MEASURE MOVED: D6 NHL 6 -> 6 (named above); NHL layer-3 classes tested 2 (4 splits, 42 leaves), kept 8 leaves, 0 BH; store on box 84.6 MB, disk 74%.
pattern_sweep: league-rate-from-full-sample checked in goalie only; other rollers use _through_rolling (prior games). Not swept in nba/nfl adapters.
surface_delta: 0 (opt-in map file, no new job or service).
