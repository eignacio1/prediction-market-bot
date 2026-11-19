<!-- session-meta
task_id: W119.3
tier: STANDARD
timestamp: 2026-11-19T04:45:00Z
commit: 30e6acb
one_line_summary: W119.3: ride-board log cut, FADE inside-spread 50/50 forward test (EXP-W119.3), GG-1943 fixed; merged, on box
gg_touched: GG-1943
adr_touched: none
plan_deliverable_moved: no
vision_pillar: EXECUTION, PLUMBING
gap_measure: E1/E2/E3, FADE fill rate, ride-board bytes/day
gap_delta: FADE fill rate 6/111 (5.4%) -> touch 22/342 (6.4%), inside 2/17 (11.8%), counts only (arm_orders_read 20261119T0420Z); bytes/day not yet measurable
pattern_sweep: grep decisions.jsonl readers in src/ scripts/ tests/ -> only tests/test_run_ride_board.py; cancel_rule guard applied in option_table and option_net_clustered
surface_delta: 0 components; +1 state file in RUNTIME_REGISTRY writes
-->
---
task_id: W119.3 (code merged; deploy + Part C reads OPEN)
vision_pillar: EXECUTION (E1/E2/E3, FADE fill rate)
gap_measure: GG-1943 (rest_inside evidence cancel rule); ride-board bytes/day
gap_delta: GG-1943 fixed in code (status line NOT edited - burner owns it); bytes/day modeled 20.9MB -> 1.07MB (synthetic), real after-number NOT read
pattern_sweep: only in-repo reader of decisions.jsonl is tests/test_run_ride_board.py; cancel_rule guard applied in option_table and option_net_clustered
surface_delta: 0 new components; 1 new state file logs/ride_board/last_state.json (check RUNTIME_REGISTRY writes list); 1 FADE cell in placement table
directive_conflicts: none found (OPERATOR_DIRECTIVES.md grepped for placement / log / ride-board; no directive)
---
# W119.3 handoff
## Merged
#528 regenerated gaps-by-arm index (main guard was red after GA-6 triage; generated file only). #526 ride-board log cut (12 kept fields, repeated NO_BET once/hour, order rows never skipped), EXP-W119.3 prereg frozen 2026-11-19T01:08:53Z, FADE rest_inside 50/50 hash split vs rest_touch control (60 s cancel), GG-1943 guard. Both CI green on own head.
## Decision made
"Mid when spread >= 2 ticks" built as mid snapped toward own touch (2-tick spread = bid+1). Changes the old one-tick rule on wider spreads.
## Box reads (20261119T0420Z, box HEAD 9b527446 contains #526)
- Deploy: box HEAD = origin/main. t4-mlb still runs 43e3d10c, so the arm-order policy line may load only at its next restart; yet FADE|rest_inside orders already exist in the log (17), so it is loading.
- FADE (post-epoch, real orders): rest_touch 342 orders, 22 fills, fill rate 6.4% (before: 6 of 111 = 5.4%); rest_inside 17 orders, 2 fills, 11.8%. n far below judged n (100 orders and 20 games per option): COUNTS ONLY, no look read. Settled: inside 0, touch 16 -> E2 +0.2017/contract after fees (touch only).
- E1 fills/orders: RIDE 39/428 (E2 -0.0081, E3 fills 0.692 vs non-fills 0.825), MOMENTUM 57/340 (E2 +0.0568, 0.491 vs 0.438), MODEL_FADE 7/213 (E2 -0.3064, 2 settled).
- Day-cap skips after raise: RIDE 5,073 / FADE 2,083 / MOMENTUM 2,110 (before: 5,039 / 2,040 / 2,046) - the day cap still binds; raised caps did not remove it. Surface this to the strategic window.
- Part C re-fit: not done - no cell has the minimum n of spread-logged orders (FADE cross: 202 logged, 105 archive, 6 none, 31 games, cross-minus-rest +0.0008 [-0.101, +0.103]); every cell keeps today's rule.
- Disk: ride_board/decisions.jsonl still 1.1 GB (existing file, not rotated); disk 74%, flat. Real bytes/day after the cut needs a disk_read in about 2 days on the file's growth; not measurable yet.
## OPEN
1. Re-read arm_orders_read when FADE inside reaches 100 orders / 20 games; read the pre-registered look then.
2. Real bytes/day: disk_read ~2026-11-21, compare growth vs ~145 MB/day.
3. Day cap still binds (see above).
