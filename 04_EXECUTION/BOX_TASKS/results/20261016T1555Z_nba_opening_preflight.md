# Box task `nba_opening_preflight` — 20261016T1555Z_nba_opening_preflight

- request: `04_EXECUTION/BOX_TASKS/requests/20261016T1555Z_nba_opening_preflight.toml`
- note: W80R.1 step 3 rerun after #284; NBA opens 2026-10-20
- ran: 2026-10-16T15:56:14Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI'; echo '--- ledgers'; ls -l --time-style=+%FT%T exp_output/PREGAME_SHADOW/NBA_*.jsonl exp_output/PREGAME_SHADOW_PRESEASON/*.jsonl exp_output/PREGAME_SHADOW_EXP040/*.jsonl 2>&1 | tail -n 60; echo '--- flip check (regular-season ledgers)'; PYTHONPATH=src:. venv/bin`

```
box HEAD 5564ba81 2026-10-16T15:48:48+00:00
--- ledgers
ls: cannot access 'exp_output/PREGAME_SHADOW/NBA_*.jsonl': No such file or directory
ls: cannot access 'exp_output/PREGAME_SHADOW_EXP040/*.jsonl': No such file or directory
-rw-r--r-- 1 root root 10417025 2026-10-16T13:57:07 exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_GAME_TOTAL_T1.jsonl
-rw-r--r-- 1 root root  2917689 2026-10-15T19:57:04 exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_GAME_TOTAL_T2.jsonl
-rw-r--r-- 1 root root   276116 2026-10-15T23:57:04 exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_GAME_TOTAL_T3.jsonl
-rw-r--r-- 1 root root  3020757 2026-10-16T13:57:04 exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_MONEYLINE_T1.jsonl
-rw-r--r-- 1 root root   277306 2026-10-15T19:57:04 exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_MONEYLINE_T2.jsonl
-rw-r--r-- 1 root root    26306 2026-10-15T23:57:03 exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_MONEYLINE_T3.jsonl
-rw-r--r-- 1 root root 12396750 2026-10-16T13:57:06 exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_SPREAD_T1.jsonl
-rw-r--r-- 1 root root  3473050 2026-10-15T19:57:04 exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_SPREAD_T2.jsonl
-rw-r--r-- 1 root root   328938 2026-10-15T23:57:04 exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_SPREAD_T3.jsonl
--- flip check (regular-season ledgers)
NO-ROWS  NBA_MONEYLINE/T1_MULTI_DAY: 0 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_MONEYLINE/T2_SAME_DAY: 0 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_MONEYLINE/T3_PRE_TIP: 0 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_SPREAD/T1_MULTI_DAY: 0 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_SPREAD/T2_SAME_DAY: 0 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_SPREAD/T3_PRE_TIP: 0 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_GAME_TOTAL/T1_MULTI_DAY: 0 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_GAME_TOTAL/T2_SAME_DAY: 0 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_GAME_TOTAL/T3_PRE_TIP: 0 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_TEAM_TOTAL/T1_MULTI_DAY: 0 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_TEAM_TOTAL/T2_SAME_DAY: 0 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_TEAM_TOTAL/T3_PRE_TIP: 0 rows, 0 valid -> leave NOT_IMPLEMENTED
--- flip check (preseason ledgers)
NO-ROWS  NBA_MONEYLINE/T1_MULTI_DAY: 3228 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_MONEYLINE/T2_SAME_DAY: 296 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_MONEYLINE/T3_PRE_TIP: 28 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_SPREAD/T1_MULTI_DAY: 13250 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_SPREAD/T2_SAME_DAY: 3700 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_SPREAD/T3_PRE_TIP: 350 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_GAME_TOTAL/T1_MULTI_DAY: 11130 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_GAME_TOTAL/T2_SAME_DAY: 3108 rows, 0 valid -> leave NOT_IMPLEMENTED
NO-ROWS  NBA_GAME_TOTAL/T3_PRE_TIP: 294 rows, 0 valid -> leave NOT_IMPLEMENTED
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
skipped: {'NBA_MONEYLINE:outside_band_windows': 32, 'NBA_MONEYLINE:no_kickoff': 24, 'NBA_SPREAD:no_kickoff': 300, 'NBA_GAME_TOTAL:no_kickoff': 252}
run_id=20261016T121103Z ledger_dir=/opt/prediction-market-bot/exp_output/PREGAME_SHADOW
written: {}
skipped: {'NBA_MONEYLINE:outside_band_windows': 32, 'NBA_MONEYLINE:no_kickoff': 24, 'NBA_SPREAD:no_kickoff': 300, 'NBA_GAME_TOTAL:no_kickoff': 252}
== logs/nba_pregame_shadow_preseason.log
skipped: {'NBA_MONEYLINE:no_kickoff': 32, 'NBA_MONEYLINE:outside_band_windows': 18, 'NBA_SPREAD:outside_band_windows': 225, 'NBA_GAME_TOTAL:outside_band_windows': 189}
run_id=20261016T145703Z ledger_dir=/opt/prediction-market-bot/exp_output/PREGAME_SHADOW_PRESEASON
written: {}
skipped: {'NBA_MONEYLINE:no_kickoff': 32, 'NBA_MONEYLINE:outside_band_windows': 24, 'NBA_SPREAD:outside_band_windows': 300, 'NBA_GAME_TOTAL:outside_band_windows': 252}
== logs/nba_player_points_shadow_t1.log
skipped: {}
EXP-040 ledger_dir=/opt/prediction-market-bot/exp_output/PREGAME_SHADOW_EXP040
EXP-040 written: {}
EXP-040 skipped: {}
== logs/nba_autoflip.log
AUTOFLIP: 2026-10-13 < 2026-10-20, no-op
AUTOFLIP: 2026-10-14 < 2026-10-20, no-op
AUTOFLIP: 2026-10-15 < 2026-10-20, no-op
AUTOFLIP: 2026-10-16 < 2026-10-20, no-op
--- CORRUPT_READ counts
logs/nba_autoflip.log:0
logs/nba_player_points_backfill.log:0
logs/nba_player_points_backfill_2026_w70.log:0
logs/nba_player_points_shadow_preseason.log:0
logs/nba_player_points_shadow_settle.log:0
logs/nba_player_points_shadow_t1.log:0
logs/nba_player_points_shadow_t2.log:0
logs/nba_player_points_shadow_t3.log:0
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
[IDLE   ] NHL shadow: no games in the last 12h, nothing expected
[IDLE   ] NBA preseason shadow: no games in the last 12h, nothing expected
[IDLE   ] NBA regular-season shadow: no games in the last 12h, nothing expected
[IDLE   ] NBA player points shadow: no games in the last 12h, nothing expected
[IDLE   ] NBA player points minutes+injury challenger (EXP-040): no games in the last 12h, nothing expected
[OK     ] T1 MLB paper pipeline: 2 game(s) started in the last 30h, rows written
[IDLE   ] T4 MLB live: no games in the last 3h, nothing expected
[OK     ] nba_player_box_2026: data/raw/nba/players_2026.json ok (1231 games)

```
