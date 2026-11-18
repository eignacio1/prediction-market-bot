# W118.3 handoff (PARTIAL, stopped at session limit). Last reviewed: 2026-11-18
Common rules read (first line "# Wave 118 common rules"), W117.3 handoff and nhl_consensus RESULT read.
## Done
- Part B (IT-12): PREREG 9702cfe (before outcomes); 12_EXPLORATORY/nhl_goalie_timing/{run_timing.py,RESULT.md,results.json}, merged #520.
  58 confirmations, 14 eligible (2 informative). Move vs placebo: +40m 0.7c, +60m 0.7c, lag (+40 to +120) 0.2c [0.07,0.43], below one round cost
  (half-spread 0.5c + fee). Unsigned. Routing result: NO BET on the split; hypothesis closed (EXP-W118.3-GOALIE lag arm, parked for R&D).
- Box task nhl_event_store_refresh_once (one pass of the approved refresh job). #520 had a bug (PYTHONPATH after nice); fixed in #524, merged green.
- Local store already holds partial parquet (events/box_players 2021-26); nhl_adapter in filter_supply.py already serves shot quality, deployment, schedule.
## NOT done (next window)
1. Confirm box deployed #524 (deploy_truth_read), then read result of request 20261118T0613Z_nhl_event_store_refresh_once; repeat until the store is built
   (900s timeout, resumable). Then nhl_event_store_readback, budget_read, health_read (size, disk % vs 90%, log clean). Nothing measured yet.
2. Part A: goalie and special-teams classes as tested splits in filter_supply.py (shot quality/xG, rest exist); d6_read for NHL.
3. Part C: NHL router v2 with consensus prior, leaf_maps/nhl_v2.json behind PM_LEAF_MAP_VERSION, PR on green, d6_read recount.
## Reporting
MEASURE MOVED: D6 NHL 0 -> 0 (no change this block); NHL layer-3 classes built: 0 new; goalie lag 0.2c with n 14 (2 informative).
pattern_sweep: exploratory-isolation guard (no datetime.replace in 12_EXPLORATORY) and env-before-nice in box_tasks swept; no other hits found in box_tasks.py.
surface_delta: +1 allowlisted box task (one-off run of an already approved job); no new cron or service.
directive_conflicts: none found; OPERATOR_DIRECTIVES.md NOT re-read after compaction, verify next window.
new GGs: none appended. Caveat: gap-index CI guard goes stale whenever the gap burner ticks; regenerate with scripts/generate_gap_arm_index.py.
