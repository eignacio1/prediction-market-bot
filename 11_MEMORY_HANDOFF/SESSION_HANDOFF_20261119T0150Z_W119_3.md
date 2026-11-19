---
task_id: W119.3 (code merged; deploy + Part C reads OPEN)
vision_pillar: EXECUTION (E1/E2/E3, FADE fill rate)
gap_measure: GG-1943 (rest_inside evidence cancel rule); ride-board bytes/day
gap_delta: GG-1943 fixed in code (status line NOT edited - burner owns it); bytes/day modeled 20.9MB -> 1.07MB (synthetic), real after-number NOT read
pattern_sweep: only in-repo reader of decisions.jsonl is tests/test_run_ride_board.py; cancel_rule guard applied in option_table and option_net_clustered
surface_delta: 0 new components; 1 new state file logs/ride_board/last_state.json (check RUNTIME_REGISTRY writes list); 1 FADE cell in placement table
directive_conflicts: OPERATOR_DIRECTIVES.md NOT read this session - check before next build
---
# W119.3 handoff
## Merged
#528 regenerated gaps-by-arm index (main guard was red after GA-6 triage; generated file only). #526 ride-board log cut (12 kept fields, repeated NO_BET once/hour, order rows never skipped), EXP-W119.3 prereg frozen 2026-11-19T01:08:53Z, FADE rest_inside 50/50 hash split vs rest_touch control (60 s cancel), GG-1943 guard. Both CI green on own head.
## Decision made
"Mid when spread >= 2 ticks" built as mid snapped toward own touch (2-tick spread = bid+1). Changes the old one-tick rule on wider spreads.
## OPEN (not done)
1. Deploy check: deploy_truth_read; the placement policy loads at next restart of the arm-order service.
2. Real bytes/day: request disk_read after a day of logs.
3. Part C: arm_orders_read for E1/E2/E3 per arm and option, FADE fill rate (before 6/111), day-cap skips. Inside option has no data until orders exist; no re-fit possible yet; cells under 20 games keep today's rule.
4. ACTIVE_QUEUE 119.3 row not updated; runtime-registry entry for last_state.json not checked.
