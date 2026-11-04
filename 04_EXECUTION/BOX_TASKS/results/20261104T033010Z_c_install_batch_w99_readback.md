# Box task `install_batch_w99_readback` — 20261104T033010Z_c_install_batch_w99_readback

- request: `04_EXECUTION/BOX_TASKS/requests/20261104T033010Z_c_install_batch_w99_readback.toml`
- note: readback after the batch install retry
- ran: 2026-11-04T03:30:31Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/install_batch_w99.py readback`

```
== readback t3_lock ==
T3 LINES WRAPPED: 6
  nhl_staked_t3            6,16,26,36,46,56 17-23 * * *
  nhl_staked_t3            6,16,26,36,46,56 0-2 * * *
  pregame_shadow_t3        8,18,28,38,48,58 * * * *
  mlb_pregame_shadow_t3    3,13,23,33,43,53 * * * *
  nba_pregame_shadow_t3    1,11,21,31,41,51 * * * *
  nba_player_points_t3     14,24,44,54 * * * *
T3 LINES NOT WRAPPED: 0
SKIP ROWS (logs/t3_skips.jsonl): 0  by runner: {}  last: none
== readback nba_events_refresh ==
CRONTAB BLOCK (2 lines):
# BEGIN W95.1 NBA ENGINE LINES
33 12 * * * cd /opt/prediction-market-bot && flock -n /tmp/nba_engine_live.lock env PYTHONPATH=/opt/prediction-market-bot/src:/opt/prediction-market-bot /opt/prediction-m
2,12,22,32,42,52 16-23,0-4 * * * cd /opt/prediction-market-bot && flock -n /tmp/nba_engine_live.lock env PYTHONPATH=/opt/prediction-market-bot/src:/opt/prediction-market-
# END W95.1 NBA ENGINE LINES

STORE (exp_output/NBA_EVENTS/current/status.json):
{
  "as_of": "2026-11-03T12:33:10Z",
  "season": 2027,
  "games_ingested": 92,
  "last_game_date": "2026-11-01",
  "source_last_modified": {
    "schedule": "Mon, 02 Nov 2026 15:15:36 GMT",
    "pbp": "Mon, 02 Nov 2026 15:15:44 GMT",
    "espn_box": "Mon, 02 Nov 2026 12:39:29 GMT"
  },
  "dropped": {
    "no_espn_box": 0,
    "score_mismatch": 0,
    "no_pbp": 0,
    "games_kept": 92
  },
  "known_answer": {
    "games_checked": 10,
    "max_abs_total_diff": 0.0,
    "max_abs_pace_diff": 0.0
  }
}


ARM v1 (EXP-044): rows=1645 families={"NBA_GAME_TOTAL": 522, "NBA_MONEYLINE": 40, "NBA_SPREAD": 627, "NBA_TEAM_TOTAL": 456}
  status: {   "as_of": "2026-11-04T03:22:10.569442+00:00",   "rows_logged_this_run": 0,   "events_logged_total": 69,   "skipped": [],   "params_hash": "9019981832b8b15d",   "unlogged_past_tip": 47 } 

ARM v2 (EXP-044b): rows=2008 families={"NBA_GAME_TOTAL": 580, "NBA_MONEYLINE": 46, "NBA_SPREAD": 660, "NBA_TEAM_TOTAL": 722}
  status: {   "as_of": "2026-11-04T03:22:20.499821+00:00",   "rows_logged_this_run": 0,   "events_logged_total": 82,   "skipped": [],   "unlogged_past_tip": 23,   "params_hash": "d50932902832762d",   "rho": 0.251,   "hca": 1.867 } 

LOG TAIL (logs/nba_engine_live_cron.log), error lines in last 500: 0
  "skipped": [],
  "unlogged_past_tip": 23,
  "params_hash": "d50932902832762d",
  "rho": 0.251,
  "hca": 1.867
}
== readback nba_engine_v3 ==
CRONTAB BLOCK (1 lines):
# BEGIN W97.1 NBA ENGINE V3 LINE
3,13,23,33,43,53 16-23,0-4 * * * cd /opt/prediction-market-bot && flock -w 240 /tmp/nba_engine_live.lock env PYTHONPATH=/opt/prediction-market-bot/src:/opt/prediction-mar
# END W97.1 NBA ENGINE V3 LINE

STORE (exp_output/NBA_EVENTS/current/status.json):
{
  "as_of": "2026-11-03T12:33:10Z",
  "season": 2027,
  "games_ingested": 92,
  "last_game_date": "2026-11-01",
  "source_last_modified": {
    "schedule": "Mon, 02 Nov 2026 15:15:36 GMT",
    "pbp": "Mon, 02 Nov 2026 15:15:44 GMT",
    "espn_box": "Mon, 02 Nov 2026 12:39:29 GMT"
  },
  "dropped": {
    "no_espn_box": 0,
    "score_mismatch": 0,
    "no_pbp": 0,
    "games_kept": 92
  },
  "known_answer": {
    "games_checked": 10,
    "max_abs_total_diff": 0.0,
    "max_abs_pace_diff": 0.0
  }
}


ARM v3 (EXP-044c): rows=0 families={}
  rows per game per family: {}
  injury snapshots logged: 0
  status: (none)

LOG TAIL (logs/nba_engine_live_cron.log), error lines in last 500: 0
  "skipped": [],
  "unlogged_past_tip": 23,
  "params_hash": "d50932902832762d",
  "rho": 0.251,
  "hca": 1.867
}
== readback picks_builder ==
CRONTAB BLOCK (1 lines):
# BEGIN W98.3 PICKS SHEET LINE
37 5,22 * * * cd /opt/prediction-market-bot && PYTHONPATH=/opt/prediction-market-bot/src:/opt/prediction-market-bot nice -n 10 /opt/prediction-market-bot/venv/bin/python 
# END W98.3 PICKS SHEET LINE
  picks_2026-10-30.json  1788491 bytes  mtime 2026-10-30T19:13Z
  picks_2026-11-02.json  2711089 bytes  mtime 2026-11-03T00:28Z
  picks_latest.json  2711089 bytes  mtime 2026-11-03T00:28Z

LOG TAIL (logs/picks_sheet_cron.log), error lines in last 500: no log
  (no log yet)

```
