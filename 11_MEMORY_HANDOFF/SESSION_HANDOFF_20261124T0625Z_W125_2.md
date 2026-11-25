<!-- session-meta
task_id: W125.2
tier: STANDARD
timestamp: 2026-11-24T06:25:00Z
commit: 7570238
one_line_summary: W125.2 PARTIAL: #556 merged (install not run, gate REFUSE 86.2%); #559 healthcheck counts both order paths + router_error_read; A/C open.
gg_touched: GG-2006, GG-2007
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH, EXECUTION
gap_measure: D6, E1
gap_delta: none yet (D6 stays 17 of 117: NBA 7, NFL 4, NHL 6, MLB 0; d6_read 20261124T0025Z; post-deploy re-run not done)
pattern_sweep: grep shadow_order in src/ scripts/ deploy/ -> healthcheck 11 and demo_fill_stall.py counted one path only, fixed in #559; other consumers not yet swept
surface_delta: +1 read-only box task (router_error_read, allowlisted); #556 cron deploy/cron.archive_dense registered but NOT installed
-->
# SESSION HANDOFF W125.2 - PARTIAL (operator asleep)

## Strategic Decisions This Session
| Decision | Rationale | Ref | Owner |
|---|---|---|---|
| Do not install dense capture | Gate dry run REFUSE: 30-day disk 86.2% vs 80% limit (now 67.0%, +0.64 pct/day) | box result 20261124T0550Z_archive_dense_readback | Earl |
| NFL per-leaf NO_BET left as is | W117.1 A3 is operator-approved; NFL layer 7 gap is that decision, not a bug | arm_orders.py NFL_PER_LEAF_REASON | Earl |

## Landed
- #556 (124.4 dense capture) merged, install NOT run. #559 merged: router_error_read.py (read-only, by cause/cell/sport/day), healthcheck 11 counts shadow_order + arm_order and WARNs only when both are zero (both directions tested).

## Open (not done)
- Part A GG-2007: box result for router_error_read not read (box had not deployed #559 on first run; retry pushed). Trace shows 0 ERROR rows in last 3 days for NFL/NHL, so likely historical.
- Part C B-104: Fable's branch session/20261117T010353Z-w115-3-d6-one-game (1ce79c5) not read. Findings: NBA_MONEYLINE and NBA_PLAYER_POINTS have no model p; NFL_MONEYLINE T1-T3 and NHL_MONEYLINE T1 routed rows with arm 0; trace host showed arm_orders_mode "off" (verify cron). D6 re-run after deploy not done.
- GG-2006/GG-2007 statuses and ACTIVE_QUEUE row not updated.

## operator decisions
- archive_dense_install: gate REFUSE (86.2% > 80%). Shrink capture or raise limit by superseding decision. Recommend no install. No approval line given.

## One thing pending
Read newest results/*router_error_read.md, fix or register each cause, then Part C.
Resume: git fetch; read this file; run scripts/session_delta.sh.
