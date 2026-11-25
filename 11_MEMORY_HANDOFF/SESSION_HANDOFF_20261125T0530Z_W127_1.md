<!-- session-meta
task_id: W127.1
tier: STANDARD
timestamp: 2026-11-25T05:15:00Z
commit: 4fa2fce
one_line_summary: W127.1: prop ticker parse fixed, GG-2007 closed, PM_PROPS_C2 default ON (shadow); D6 unchanged 18/129
gg_touched: GG-2007, GG-2009, GG-2010, GG-2011, GG-2012
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D6
gap_delta: none - D6 18/129 before and after (d6_read 20261125T0039Z vs 20261125T0500Z_w1271)
pattern_sweep: grep parse_event_ticker decision_trees/ -> only the two NBA adapters (nba_adapter, nba_depth_adapter), both fixed via nba_game_teams
surface_delta: 0 components (+1 ledger dir PREGAME_SHADOW_EXP047_C2)
-->

# Session handoff W127.1 (Sonnet 5.5) - D6 / router layer breaks, GG-2007 closed, PM_PROPS_C2 ON

session-meta: block 127.1; PR #573 merged on green CI (test + guard); deploy confirmed (box HEAD c9859b5e = origin/main, deploy_truth_read 20261125T0401Z_a).
MEASURE MOVED: D6 per sport - NOT re-read. Before (d6_read 20261125T0039Z): NBA 7, NHL 7, NFL 4, MLB 0 = 18 of 129. After (d6_read 20261125T0500Z_w1271, ran 04:34Z): NBA 7/28, NHL 7/21, NFL 4/32, MLB 0/42, multi 0/6 = 18 of 129. NO MOVE, as expected
(logging and registration only).
C2 forward rows logging: UNVERIFIED. No allowlisted box task reads the C2 ledger; registered as GG-2012 (add a read-only props_c2_read task via PR).

## Done
- PART A: GG-2007 RESOLVED. Cause KeyError('market_ticker') on MODEL_FADE leaf rows, fixed by #503 (11-17); 0 ERROR rows since 11-18 (router_error_read per_day).
- PART B: prop ticker parse fixed (filter_supply.nba_game_teams; KXNBAPTS/REB/AST/3PT) with regression test tests/test_w127_1_prop_ticker.py (GG-2009 RESOLVED).
  Registered, not routed: GG-2010 (NBA/NFL moneyline leaf_not_in_map: v1 frozen, v2 covers the leaves but all NO_BET, so only the reason string would change; promotion is the operator's call),
  GG-2011 (NBA_PLAYER_POINTS has no v1 leaves; candidate leaves cannot reach D6 layers 6/7 because candidates place no orders). NFL NO_BET kept per 11-24 18:33 PT authorization.
- PART C: PM_PROPS_C2 default ON in scripts/run_nba_engine_props_shadow.py (shadow logging only; PM_PROPS_C2=off is the off-switch; W120.2 precedent). No install task run.

## Not done
- C2 row readback (GG-2012). D6 after-read is done.
- The 0300Z requests were skipped by the box (sorted before its 0401Z watermark); future requests need names later than the newest result.
- Flag: d6_trace_read host section shows arm_orders_mode "off" on the box; not investigated.
- OPERATOR_DIRECTIVES.md not read this session.

Pushback: none. Surface: Hard Rule 14 check - health_read 20261124T0025Z HEALTHY (0 faults, 1 warning); no new cron or service.
Dependencies: box request processing; next props cron run.
operator decisions: none needed. (GG-2010 promotion of leaf map v2 is open whenever the operator wants it.)
directive_conflicts: none.
pattern_sweep: swept src/ scripts/ tests/ for other NBA event_ticker parsers using only parse_event_ticker; filter_supply's two NBA adapters were the only consumers (both switched).
surface_delta: +1 ledger dir (PREGAME_SHADOW_EXP047_C2), 0 components.
