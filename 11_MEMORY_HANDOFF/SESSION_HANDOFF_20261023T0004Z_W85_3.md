# SESSION HANDOFF — W85.3 (kill switch sees all stake; install gate refuses on RED)

<!-- session-meta
task_id: W85.3
tier: STANDARD
timestamp: 2026-10-23T00:04:00Z
commit: 40a0a1c
one_line_summary: W85.3 PARTIAL: install gate refuses on RED, 3 NBA preseason entries retired, exposure gate built and wired to T1 only (GG-441 open).
gg_touched: GG-441, GG-1080, GG-1081, GG-1082
adr_touched: none
plan_deliverable_moved: no
vision_pillar: PLUMBING
gap_measure: PLUMBING (operator call 3, 2026-10-21 19:15 PT, GG-441; Hard Rule 14)
gap_delta: surface -3 retired entries; GG-441 input now includes settled-unresolved stake for T1 MLB (exposure_gate.py, main @ 40a0a1c)
pattern_sweep: substring-filter-on-red-reasons swept across scripts/ src/ .claude/ deploy/ tests/; only the two fixed installers had it; the other two installers already refuse on any non-GREEN.
surface_delta: -3 (NBA preseason entries retired), 0 added
-->


Status: PARTIAL | main @ 40a0a1c | PR #325 (CI `test` green on 87a87be, squash-merged; main run on 40a0a1c green) | Part A done; Part B built and wired to T1 only, GG-441 stays OPEN (GG-1082)

vision_pillar: PLUMBING
gap_measure: none of B/D/E/P; Hard Rule 14 (surface) and the operator's call (3), 2026-10-21 19:15 PT: "The kill switch counts open and settled-but-unresolved stake and persists its state (GG-441), built as a block before any real capital."
gap_delta: surface -3 registered-but-uninstalled entries; GG-441 kill-switch input now includes settled-unresolved stake for T1 MLB; order-path check not yet in
surface_delta: 3 NBA preseason entries retired (status=retired), 0 added. Registry check clean (84/84, 0 unreviewed).
pattern_sweep: substring-filter-on-red-reasons swept across scripts/, src/, .claude/, deploy/, tests/; only the two fixed installers had it. `thin_capture_install.install` and `source_capture_install.install` already refuse on any non-GREEN.

## Part A
Root cause: both installers exempted any RED reason containing the job name as a substring (`SILENT ARM nfl_passyds_snap` passed), and RED with an empty reasons list passed. Fix: `thin_capture_install.gate()` exempts only `^STALE cron\|[^|]*\|<script>: no write found$`; empty-RED blocks. Tests in test_w83_2_nba_lineup_window.py and test_passyds_prekickoff.py. Registered GG-1080 (RESOLVED), GG-1081 (RESOLVED).
Before budget_read: GREEN at 2026-10-22T22:22Z, 80 live, 0 behind, 3 mirrored-not-installed. After: not read from the box (no box task run this session).

## Part B
`c4_risk_engine/exposure_gate.py`: exposure = realized loss + open stake + settled-unresolved stake, per book and SYSTEM. Drawdown input = (realized loss + settled-unresolved)/initial, compared with the unchanged `max_drawdown_pct`. Atomic state `logs/exposure_gate_state.json`; `check_before_order` reloads it; missing/corrupt/unreadable = halt. A trip writes the existing global flag, reusing the <=60 s path. Tests (7): resolution-dark, live open stake, system-wide, restart mid-day, missing, corrupt, zero bankroll. Wired: `run_mlb_paper_trade.py` raises (never lowers) its drawdown input from this; gate error counts as breach.
NOT done (GG-1082, OPEN HIGH): `submit_order` does not call `check_before_order` (needs a writer on every book first, else it halts all demo orders); no settled-ticker feed, so production settled-unresolved is 0 today; T4/NFL/NHL books do not call `update`. No limit value, kelly, stake, order or ledger row changed.

## Consumers of the kill switch / risk state (GG-072 / Hard Rule 13)
- run_mlb_paper_trade.py: CHANGED (exposure input). Cron-run, not imported by t4-mlb.
- run_paper_trade.py (NBA frozen), run_t1_mlb_game_market.py, run_t1_nfl_game_market.py, run_t2_mlb_sameday.py, run_mlb_pregame.py: unchanged; read flags/cell state only. Not yet fed by the gate (GG-1082).
- run_t4_mlb_live.py, run_t4_live.py, t4_live_runner.py, run_t4_inplay.py: unchanged; flag-file check only. t4-mlb imports no changed file.
- kalshi_client.submit_order, shadow_flat_stake.py, paper_trader.py, market_type_registry.py: unchanged (GG-1082 for submit_order).
- c7_monitoring/monitor.py, c8_dashboard: unchanged; still realized-loss alerts. They would read the new flag on a trip.
- Scripts run_mlb_dashboard.py, run_session_report.py, run_monte_carlo.py: unchanged.

## Deploy / restart
The merge's main run (40a0a1c) had only the `test` job (success); no Deploy job summary was present to read. t4-mlb imports none of the changed files, so no restart is needed. Box HEAD was not read this session.

## Protocol gaps to state plainly
Abbreviated CLAUDE.md session-start: only the guard and claim ran; Steps 1-4 and Q1-Q7 were not run and the hook scan was 20h stale. Local pytest cannot collect test_seat_interface/test_tensions (Python 3.9 has no `tomllib`); CI is the authority and was green.

Operator decisions: none.
