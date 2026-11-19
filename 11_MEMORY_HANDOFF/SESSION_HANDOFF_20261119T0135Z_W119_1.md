# W119.1 handoff (PARTIAL, parked by operator at dinner). Last reviewed: 2026-11-18
Common rules read (first line "# Wave 119 common rules"); W118.3 handoff read.
## Done (Part A)
- deploy_truth_read: box HEAD dd2f46c = origin/main, #524 deployed.
- nhl_event_store_refresh_once (20261119T0112Z): 1,737 of 1,737 finished games fetched; 50 failures repeat on pass 2 (fetch_failures.json), so more passes will not help.
- Readback: NHL_EVENTS 84.6 MB, seasons 2025+2026 compiled (games 1394/1344). Disk 74% (18 of 24 GB). Health HEALTHY 0 faults, surface budget GREEN, refresh log 0 errors.
- d6_read (box, 01:2xZ): NHL 6 of 21 wired, l3_kept 6, l3_stump 6. Starting point is 6, not 0. NHL_PUCK_LINE T1 is missing exactly layer 3.
## NOT done
1. Part B: goalie (shrunk SV% of team's most-used goalie, prior games only, from box_players) and special teams (PP goals for/against rolling) as splits in nhl_engine/filters.py + filter_supply.py; score per leaf per arm held out (pattern: 12_EXPLORATORY/nhl_factors_w112/score_leaves.py; needs fresh nhl/ + nhl_settled/ pulled from the box).
2. Part C: NHL through router v2 with 12_EXPLORATORY/nhl_consensus prior; leaf_maps/nhl_v2.json + MAP_VERSIONS entry in leaf_map.py; PR, merge on green; d6_read recount with one cause per unwired cell.
## Notes
- Worktree: PM-worktrees/20261119T0120Z-w119-1-nhl (branch w119-1-nhl-layer3). Shared tree was switched to another session's branch.
- Shared tree has uncommitted edits to scripts/run_ride_board.py and tests/test_run_ride_board.py that are not mine.
MEASURE MOVED: D6 NHL 6 -> 6 (no change yet); layer-3 classes tested 0 new; store on box 84.6 MB, disk 74%.
surface_delta: 0 (read tasks and one one-shot run of an approved job).
