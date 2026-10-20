# Box task `nba_opening_preflight` — 20261020T0005Z_c_nba_opening_preflight

- request: `04_EXECUTION/BOX_TASKS/requests/20261020T0005Z_c_nba_opening_preflight.toml`
- note: window: state read before writing the last wave (10-19)
- ran: 2026-10-20T00:05:59Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI'; echo '--- ledgers'; ls -l --time-style=+%FT%T exp_output/PREGAME_SHADOW/NBA_*.jsonl exp_output/PREGAME_SHADOW_PRESEASON/*.jsonl exp_output/PREGAME_SHADOW_EXP040/*.jsonl 2>&1 | tail -n 60; echo '--- flip check (regular-season ledgers)'; PYTHONPATH=src:. venv/bin`

```
box HEAD 5f9714dc 2026-10-16T09:49:24-07:00
--- ledgers
-rw-r--r-- 1 root root   280913 2026-10-19T18:11:58 exp_output/PREGAME_SHADOW/NBA_NBA_GAME_TOTAL_T1.jsonl
-rw-r--r-- 1 root root    19152 2026-10-19T18:11:07 exp_output/PREGAME_SHADOW/NBA_NBA_MONEYLINE_T1.jsonl
-rw-r--r-- 1 root root   332748 2026-10-19T22:21:24 exp_output/PREGAME_SHADOW/NBA_NBA_PLAYER_POINTS_T1.jsonl
-rw-r--r-- 1 root root   318920 2026-10-19T18:11:35 exp_output/PREGAME_SHADOW/NBA_NBA_SPREAD_T1.jsonl
-rw-r--r-- 1 root root   331937 2026-10-19T18:15:07 exp_output/PREGAME_SHADOW/NBA_NBA_TEAM_TOTAL_T1.jsonl
-rw-r--r-- 1 root root    97457 2026-10-19T22:21:25 exp_output/PREGAME_SHADOW_EXP040/NBAMIN_NBA_PLAYER_POINTS_T1.jsonl
-rw-r--r-- 1 root root 10417025 2026-10-16T13:57:07 exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_GAME_TOTAL_T1.jsonl
-rw-r--r-- 1 root root  3864313 2026-10-16T21:57:11 exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_GAME_TOTAL_T2.jsonl
-rw-r--r-- 1 root root   295832 2026-10-17T01:57:11 exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_GAME_TOTAL_T3.jsonl
-rw-r--r-- 1 root root  3020757 2026-10-16T13:57:04 exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_MONEYLINE_T1.jsonl
-rw-r--r-- 1 root root   367217 2026-10-16T21:57:03 exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_MONEYLINE_T2.jsonl
-rw-r--r-- 1 root root    28177 2026-10-17T01:57:03 exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_MONEYLINE_T3.jsonl
-rw-r--r-- 1 root root 12396750 2026-10-16T13:57:06 exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_SPREAD_T1.jsonl
-rw-r--r-- 1 root root  4599573 2026-10-16T21:57:08 exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_SPREAD_T2.jsonl
-rw-r--r-- 1 root root   352500 2026-10-17T01:57:08 exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_SPREAD_T3.jsonl
--- flip check (regular-season ledgers)
FLIP-OK  NBA_MONEYLINE/T1_MULTI_DAY: 22/22 valid rows -> promote_cell_status(MarketType.NBA_MONEYLINE, ExecutionBand.T1_MULTI_DAY, CellStatus.SHADOW, superseding_reference="EXP-038")
NO-ROWS  NBA_MONEYLINE/T2_SAME_DAY: 0 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_MONEYLINE/T3_PRE_TIP: 0 rows, 0 valid -> leave NOT_IMPLEMENTED
FLIP-OK  NBA_SPREAD/T1_MULTI_DAY: 363/363 valid rows -> promote_cell_status(MarketType.NBA_SPREAD, ExecutionBand.T1_MULTI_DAY, CellStatus.SHADOW, superseding_reference="EXP-038")
NO-ROWS  NBA_SPREAD/T2_SAME_DAY: 0 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_SPREAD/T3_PRE_TIP: 0 rows, 0 valid -> leave NOT_IMPLEMENTED
FLIP-OK  NBA_GAME_TOTAL/T1_MULTI_DAY: 319/319 valid rows -> promote_cell_status(MarketType.NBA_GAME_TOTAL, ExecutionBand.T1_MULTI_DAY, CellStatus.SHADOW, superseding_reference="EXP-038")
NO-ROWS  NBA_GAME_TOTAL/T2_SAME_DAY: 0 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_GAME_TOTAL/T3_PRE_TIP: 0 rows, 0 valid -> leave NOT_IMPLEMENTED
FLIP-OK  NBA_TEAM_TOTAL/T1_MULTI_DAY: 374/374 valid rows -> promote_cell_status(MarketType.NBA_TEAM_TOTAL, ExecutionBand.T1_MULTI_DAY, CellStatus.SHADOW, superseding_reference="EXP-038")
NO-ROWS  NBA_TEAM_TOTAL/T2_SAME_DAY: 0 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_TEAM_TOTAL/T3_PRE_TIP: 0 rows, 0 valid -> leave NOT_IMPLEMENTED
--- flip check (preseason ledgers)
NO-ROWS  NBA_MONEYLINE/T1_MULTI_DAY: 3228 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_MONEYLINE/T2_SAME_DAY: 392 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_MONEYLINE/T3_PRE_TIP: 30 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_SPREAD/T1_MULTI_DAY: 13250 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_SPREAD/T2_SAME_DAY: 4900 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_SPREAD/T3_PRE_TIP: 375 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_GAME_TOTAL/T1_MULTI_DAY: 11130 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_GAME_TOTAL/T2_SAME_DAY: 4116 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_GAME_TOTAL/T3_PRE_TIP: 315 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_TEAM_TOTAL/T1_MULTI_DAY: 0 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_TEAM_TOTAL/T2_SAME_DAY: 0 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_TEAM_TOTAL/T3_PRE_TIP: 0 rows, 0 valid -> leave NOT_IMPLEMENTED
--- nba cron lines
3:# Timezone: All times are UTC. NBA games typically start 23:00–03:00 UTC (7pm–11pm ET).
103:#   23:00 UTC — covers full NBA game window (7pm–11pm ET = 23:00–03:00 UTC)
144:#   NBA anti-predictive finding (edge>0 winrate 0.356) warrants unbiased MLB
433:#   uncaptured -- zero rows, unbackfillable once passed. Confirmed via direct
524:# BEGIN EXP-038 NBA
525:# EXP-038 / W58.2 -- NBA game-market pregame SHADOW (evaluate-and-log). APPEND-ONLY block in the VPS crontab.
529:# exp_output/PREGAME_SHADOW/ and data/raw/nba/ only. No order, position, fill, stake or kelly (tests/test_nba_shadow_safety.py).
532:# NBA only has regular-season markets from 2026-10-20; preseason markets are skipped (no_kickoff) by design.
534:47 9 * * * cd /opt/prediction-market-bot && PYTHONPATH=/opt/prediction-market-bot/src:/opt/prediction-market-bot /opt/prediction-market-bot/venv/bin/python scripts/nba_backfill.py --seasons 2026 2027 >> logs/nba_shadow_backfill.log 2>&1
536:11 */6 * * * cd /opt/prediction-market-bot && export $(grep -v '^#' .env | xargs) && export $(grep -sv '^#' deploy/demo_fill.env | xargs) && BOT_ENV=paper PYTHONPATH=/opt/prediction-market-bot/src:/opt/prediction-market-bot /opt/prediction-market-bot/venv/bin/python scripts/run_nba_pregame_shadow.py --bands T1 >> logs/nba_pregame_shadow_t1.log 2>&1
538:16 * * * * cd /opt/prediction-market-bot && export $(grep -v '^#' .env | xargs) && export $(grep -sv '^#' deploy/demo_fill.env | xargs) && BOT_ENV=paper PYTHONPATH=/opt/prediction-market-bot/src:/opt/prediction-market-bot /opt/prediction-market-bot/venv/bin/python scripts/run_nba_pregame_shadow.py --bands T2 >> logs/nba_pregame_shadow_t2.log 2>&1
540:9,19,29,39,49,59 * * * * cd /opt/prediction-market-bot && export $(grep -v '^#' .env | xargs) && export $(grep -sv '^#' deploy/demo_fill.env | xargs) && BOT_ENV=paper PYTHONPATH=/opt/prediction-market-bot/src:/opt/prediction-market-bot /opt/prediction-market-bot/venv/bin/python scripts/run_nba_pregame_shadow.py --bands T3 >> logs/nba_pregame_shadow_t3.log 2>&1
542:23 10 * * * cd /opt/prediction-market-bot && PYTHONPATH=/opt/prediction-market-bot/src:/opt/prediction-market-bot /opt/prediction-market-bot/venv/bin/python scripts/run_nba_pregame_shadow_settle.py >> logs/nba_pregame_shadow_settle.log 2>&1
543:# END EXP-038 NBA
544:# BEGIN EXP-038 NBA PRESEASON
545:# W59.3 -- NBA PRESEASON pipeline smoke test (evaluate-and-log). Own marked block; edits no other crontab line.
550:57 * * * * cd /opt/prediction-market-bot && PYTHONPATH=/opt/prediction-market-bot/src:/opt/prediction-market-bot /opt/prediction-market-bot/venv/bin/python scripts/run_nba_pregame_shadow.py --preseason >> logs/nba_pregame_shadow_preseason.log 2>&1
551:# END EXP-038 NBA PRESEASON
577:# BEGIN EXP-039 NBA PLAYER POINTS
578:# EXP-039 / W65.1 -- NBA player-points (KXNBAPTS) pregame SHADOW (evaluate-and-log). APPEND-ONLY block in the VPS crontab.
582:# exp_output/PREGAME_SHADOW/ and data/raw/nba/ only. No order, position, fill, stake or kelly (tests/test_nba_player_points_safety.py).
584:# NFL, MLB, NHL and EXP-038 NBA jobs (11,16,9x,23,47,57) (GG-477 OOM stagger). All times UTC.
586:4 10 * * * cd /opt/prediction-market-bot && PYTHONPATH=/opt/prediction-market-bot/src:/opt/prediction-market-bot /opt/prediction-market-bot/venv/bin/python scripts/nba_player_box_backfill.py --seasons 2027 >> logs/nba_player_points_backfill.log 2>&1
588:21 4,10,16,22 * * * cd /opt/prediction-market-bot && export $(grep -v '^#' .env | xargs) && export $(grep -sv '^#' deploy/demo_fill.env | xargs) && BOT_ENV=paper PYTHONPATH=/opt/prediction-market-bot/src:/opt/prediction-market-bot /opt/prediction-market-bot/venv/bin/python scripts/run_nba_player_points_shadow.py --bands T1 >> logs/nba_player_points_shadow_t1.log 2>&1
590:27 * * * * cd /opt/prediction-market-bot && export $(grep -v '^#' .env | xargs) && export $(grep -sv '^#' deploy/demo_fill.env | xargs) && BOT_ENV=paper PYTHONPATH=/opt/prediction-market-bot/src:/opt/prediction-market-bot /opt/prediction-market-bot/venv/bin/python scripts/run_nba_player_points_shadow.py --bands T2 >> logs/nba_player_points_shadow_t2.log 2>&1
592:14,24,44,54 * * * * cd /opt/prediction-market-bot && export $(grep -v '^#' .env | xargs) && export $(grep -sv '^#' deploy/demo_fill.env | xargs) && BOT_ENV=paper PYTHONPATH=/opt/prediction-market-bot/src:/opt/prediction-market-bot /opt/prediction-market-bot/venv/bin/python scripts/run_nba_player_points_shadow.py --bands T3 >> logs/nba_player_points_shadow_t3.log 2>&1
594:35 10 * * * cd /opt/prediction-market-bot && PYTHONPATH=/opt/prediction-market-bot/src:/opt/prediction-market-bot /opt/prediction-market-bot/venv/bin/python scripts/run_nba_player_points_shadow_settle.py >> logs/nba_player_points_shadow_settle.log 2>&1
595:# END EXP-039 NBA PLAYER POINTS
597:# BEGIN EXP-039 NBA PLAYER POINTS PRESEASON
598:# W65.1 -- NBA player-points PRESEASON pipeline smoke test (evaluate-and-log). Own marked block; edits no other crontab line.
603:37 * * * * cd /opt/prediction-market-bot && PYTHONPATH=/opt/prediction-market-bot/src:/opt/prediction-market-bot /opt/prediction-market-bot/venv/bin/python scripts/run_nba_player_points_shadow.py --preseason >> logs/nba_player_points_shadow_preseason.log 2>&1
604:# END EXP-039 NBA PLAYER POINTS PRESEASON
619:# BEGIN W69.2 NBA AUTOFLIP
620:# W69.2 / EXP-038: flips NBA game cells NOT_IMPLEMENTED -> SHADOW once a cell holds >=1 valid regular-season row (no-op before 2026-10-20).
621:# AUTHORIZATION: [REDACTED] shadow-cron authorization (NEW lines only). Reads exp_output/PREGAME_SHADOW, appends nba_promotions.jsonl. No order, stake or kelly.
622:40 12 * * * cd /opt/prediction-market-bot && PYTHONPATH=/opt/prediction-market-bot/src:/opt/prediction-market-bot /opt/prediction-market-bot/venv/bin/python scripts/nba_cell_autoflip.py >> logs/nba_autoflip.log 2>&1
623:# END W69.2 NBA AUTOFLIP
625:# BEGIN W69.2 NBA PRESEASON RETIRE
626:# Removes both NBA PRESEASON blocks from the live crontab (and this block) once now >= 2026-10-21 10:00 UTC; no-op before; idempotent. Crontab only.
627:50 13 * * * cd /opt/prediction-market-bot && PYTHONPATH=/opt/prediction-market-bot/src:/opt/prediction-market-bot /opt/prediction-market-bot/venv/bin/python scripts/remove_nba_preseason_cron.py --auto >> logs/nba_preseason_retire.log 2>&1
628:# END W69.2 NBA PRESEASON RETIRE
630:# BEGIN W71.2 NBA PLAYERS 2026 REFRESH
631:# W71.2 / GG-621: re-creates data/raw/nba/players_2026.json (2025-26 player box scores) if absent; resumable, a no-op once complete.
633:# AUTHORIZATION: [REDACTED] shadow-cron authorization (NEW lines only, 2026-10-02). Public read-only, <=2 req/s; writes data/raw/nba/ only. No order, stake or kelly.
635:18 11 * * 0 cd /opt/prediction-market-bot && PYTHONPATH=/opt/prediction-market-bot/src:/opt/prediction-market-bot /opt/prediction-market-bot/venv/bin/python scripts/nba_player_box_backfill.py --seasons 2026 >> logs/nba_players_2026_refresh.log 2>&1
636:# END W71.2 NBA PLAYERS 2026 REFRESH
638:# Forward order-book capture for the thinner NFL/NBA Kalshi families (Kalshi keeps no historical book; W78.2 manifest).
--- nba log tails
== logs/nba_pregame_shadow_t1.log
skipped: {'NBA_MONEYLINE:outside_band_windows': 80, 'NBA_SPREAD:outside_band_windows': 495, 'NBA_GAME_TOTAL:outside_band_windows': 435}
run_id=20261019T181104Z ledger_dir=/opt/prediction-market-bot/exp_output/PREGAME_SHADOW
written: {'NBA_MONEYLINE:T1': 6, 'NBA_SPREAD:T1': 99, 'NBA_GAME_TOTAL:T1': 87, 'NBA_TEAM_TOTAL:T1': 114}
skipped: {'NBA_MONEYLINE:outside_band_windows': 80, 'NBA_SPREAD:outside_band_windows': 495, 'NBA_GAME_TOTAL:outside_band_windows': 435}
== logs/nba_pregame_shadow_preseason.log
skipped: {'NBA_MONEYLINE:no_kickoff': 86, 'NBA_SPREAD:no_kickoff': 594, 'NBA_GAME_TOTAL:no_kickoff': 522, 'NBA_TEAM_TOTAL:no_kickoff': 114}
run_id=20261019T235704Z ledger_dir=/opt/prediction-market-bot/exp_output/PREGAME_SHADOW_PRESEASON
written: {}
skipped: {'NBA_MONEYLINE:no_kickoff': 94, 'NBA_SPREAD:no_kickoff': 594, 'NBA_GAME_TOTAL:no_kickoff': 522, 'NBA_TEAM_TOTAL:no_kickoff': 304}
== logs/nba_player_points_shadow_t1.log
skipped: {}
EXP-040 ledger_dir=/opt/prediction-market-bot/exp_output/PREGAME_SHADOW_EXP040
EXP-040 written: {'NBA_PLAYER_POINTS:T1': 18}
EXP-040 skipped: {'NBA_PLAYER_POINTS:raw_filter': 68}
== logs/nba_autoflip.log
AUTOFLIP: 2026-10-16 < 2026-10-20, no-op
AUTOFLIP: 2026-10-17 < 2026-10-20, no-op
AUTOFLIP: 2026-10-18 < 2026-10-20, no-op
AUTOFLIP: 2026-10-19 < 2026-10-20, no-op
--- CORRUPT_READ counts
logs/nba_autoflip.log:0
logs/nba_player_points_backfill.log:0
logs/nba_player_points_backfill_2026_w70.log:0
logs/nba_player_points_shadow_preseason.log:0
logs/nba_player_points_shadow_settle.log:0
logs/nba_player_points_shadow_t1.log:0
logs/nba_player_points_shadow_t2.log:0
logs/nba_player_points_shadow_t3.log:0
logs/nba_players_2026_refresh.log:0
logs/nba_pregame_shadow_preseason.log:0
logs/nba_pregame_shadow_settle.log:0
logs/nba_pregame_shadow_t1.log:0
logs/nba_pregame_shadow_t2.log:0
logs/nba_pregame_shadow_t3.log:0
logs/nba_preseason_retire.log:0
logs/nba_shadow_backfill.log:0
--- silent arms
[IDLE   ] MLB game-market shadow: no games in the last 12h, nothing expected
[IDLE   ] NFL shadow: no games in the last 12h, nothing expected
[IDLE   ] NFL QB challenger shadow: no games in the last 12h, nothing expected
[OK     ] NHL shadow: 3 game(s) started in the last 12h, rows written
[IDLE   ] NBA preseason shadow: no games in the last 12h, nothing expected
[IDLE   ] NBA regular-season shadow: no games in the last 12h, nothing expected
[IDLE   ] NBA player points shadow: no games in the last 12h, nothing expected
[IDLE   ] NBA player points minutes+injury challenger (EXP-040): no games in the last 12h, nothing expected
[OK     ] T1 MLB paper pipeline: 1 game(s) started in the last 30h, rows written
[IDLE   ] T4 MLB live: no games in the last 3h, nothing expected
[OK     ] nba_player_box_2026: data/raw/nba/players_2026.json ok (1231 games)

```
