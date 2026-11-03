# Box task `nba_engine_cron_readback` — 20261103T063449Z_w_nba_engine_cron_readback

- request: `04_EXECUTION/BOX_TASKS/requests/20261103T063449Z_w_nba_engine_cron_readback.toml`
- note: Wave 98 close read (strategic window, read-only)
- ran: 2026-11-03T06:35:44Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/nba_engine_cron_install.py readback`

```
CRONTAB BLOCK (2 lines):
# BEGIN W95.1 NBA ENGINE LINES
33 12 * * * cd /opt/prediction-market-bot && flock -n /tmp/nba_engine_live.lock env PYTHONPATH=/opt/prediction-market-bot/src:/opt/prediction-market-bot /opt/prediction-m
2,12,22,32,42,52 16-23,0-4 * * * cd /opt/prediction-market-bot && flock -n /tmp/nba_engine_live.lock env PYTHONPATH=/opt/prediction-market-bot/src:/opt/prediction-market-
# END W95.1 NBA ENGINE LINES

STORE (exp_output/NBA_EVENTS/current/status.json):
{
  "as_of": "2026-11-02T12:33:10Z",
  "season": 2027,
  "games_ingested": 88,
  "last_game_date": "2026-10-31",
  "source_last_modified": {
    "schedule": "Sun, 01 Nov 2026 15:15:51 GMT",
    "pbp": "Sun, 01 Nov 2026 15:15:57 GMT",
    "espn_box": "Sun, 01 Nov 2026 12:30:01 GMT"
  },
  "dropped": {
    "no_espn_box": 0,
    "score_mismatch": 0,
    "no_pbp": 0,
    "games_kept": 88
  },
  "known_answer": {
    "games_checked": 10,
    "max_abs_total_diff": 0.0,
    "max_abs_pace_diff": 0.0
  }
}


ARM v1 (EXP-044): rows=1645 families={"NBA_GAME_TOTAL": 522, "NBA_MONEYLINE": 40, "NBA_SPREAD": 627, "NBA_TEAM_TOTAL": 456}
  status: {   "as_of": "2026-11-03T04:52:08.052467+00:00",   "rows_logged_this_run": 0,   "events_logged_total": 69,   "skipped": [],   "params_hash": "9019981832b8b15d",   "unlogged_past_tip": 47 } 

ARM v2 (EXP-044b): rows=2008 families={"NBA_GAME_TOTAL": 580, "NBA_MONEYLINE": 46, "NBA_SPREAD": 660, "NBA_TEAM_TOTAL": 722}
  status: {   "as_of": "2026-11-03T04:52:20.748354+00:00",   "rows_logged_this_run": 0,   "events_logged_total": 82,   "skipped": [],   "unlogged_past_tip": 23,   "params_hash": "d50932902832762d",   "rho": 0.251,   "hca": 1.867 } 

LOG TAIL (logs/nba_engine_live_cron.log), error lines in last 500: 0
  "skipped": [],
  "unlogged_past_tip": 23,
  "params_hash": "d50932902832762d",
  "rho": 0.251,
  "hca": 1.867
}

```
