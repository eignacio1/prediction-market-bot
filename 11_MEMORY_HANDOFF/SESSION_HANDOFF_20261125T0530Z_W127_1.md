# Session handoff W127.1 (Sonnet 5.5) - D6 / router layer breaks, GG-2007 closed, PM_PROPS_C2 ON

session-meta: block 127.1; PR #573 merged on green CI (test + guard); deploy confirmed (box HEAD c9859b5e = origin/main, deploy_truth_read 20261125T0401Z_a).
MEASURE MOVED: D6 per sport - NOT re-read. Before (d6_read 20261125T0039Z): NBA 7, NHL 7, NFL 4, MLB 0 = 18 of 129. After: pending, the box had not run the
resubmitted request (requests/20261125T0500Z_w1271_d6_read.toml) when this was written. Expected: no move (this block changed logging and registration only).
C2 forward rows logging: yes/no NOT yet read back; needs the next hourly props run (cron 39 * * * *) plus a read request.

## Done
- PART A: GG-2007 RESOLVED. Cause KeyError('market_ticker') on MODEL_FADE leaf rows, fixed by #503 (11-17); 0 ERROR rows since 11-18 (router_error_read per_day).
- PART B: prop ticker parse fixed (filter_supply.nba_game_teams; KXNBAPTS/REB/AST/3PT) with regression test tests/test_w127_1_prop_ticker.py (GG-2009 RESOLVED).
  Registered, not routed: GG-2010 (NBA/NFL moneyline leaf_not_in_map: v1 frozen, v2 covers the leaves but all NO_BET, so only the reason string would change; promotion is the operator's call),
  GG-2011 (NBA_PLAYER_POINTS has no v1 leaves; candidate leaves cannot reach D6 layers 6/7 because candidates place no orders). NFL NO_BET kept per 11-24 18:33 PT authorization.
- PART C: PM_PROPS_C2 default ON in scripts/run_nba_engine_props_shadow.py (shadow logging only; PM_PROPS_C2=off is the off-switch; W120.2 precedent). No install task run.

## Not done
- Part D after-read of D6 per sport, and the C2 row readback. First box action: a result for requests/20261125T0500Z_w1271_d6_read.toml, then a read of exp_output/PREGAME_SHADOW_EXP047_C2/.
- The 0300Z requests were skipped by the box (sorted before its 0401Z watermark); future requests need names later than the newest result.
- Flag: d6_trace_read host section shows arm_orders_mode "off" on the box; not investigated.
- OPERATOR_DIRECTIVES.md not read this session.

Pushback: none. Surface: Hard Rule 14 check - health_read 20261124T0025Z HEALTHY (0 faults, 1 warning); no new cron or service.
Dependencies: box request processing; next props cron run.
operator decisions: none needed. (GG-2010 promotion of leaf map v2 is open whenever the operator wants it.)
directive_conflicts: none.
pattern_sweep: swept src/ scripts/ tests/ for other NBA event_ticker parsers using only parse_event_ticker; filter_supply's two NBA adapters were the only consumers (both switched).
surface_delta: +1 ledger dir (PREGAME_SHADOW_EXP047_C2), 0 components.
