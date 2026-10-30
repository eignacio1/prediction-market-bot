# Box task `nba_engine_cron_readback` — 20261030T1440Z_w95_1_nba_engine_cron_readback

- request: `04_EXECUTION/BOX_TASKS/requests/20261030T1440Z_w95_1_nba_engine_cron_readback.toml`
- note: W95.1: post-install readback
- ran: 2026-10-30T14:35:15Z on root@157.230.91.33:/opt/prediction-market-bot
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
  "as_of": "2026-10-30T13:53:14Z",
  "season": 2027,
  "games_ingested": 67,
  "last_game_date": "2026-10-28",
  "source_last_modified": {
    "schedule": "Thu, 29 Oct 2026 14:15:29 GMT",
    "pbp": "Thu, 29 Oct 2026 14:15:35 GMT",
    "espn_box": "Fri, 30 Oct 2026 12:03:24 GMT"
  },
  "dropped": {
    "no_espn_box": 0,
    "score_mismatch": 0,
    "no_pbp": 1,
    "games_kept": 67
  },
  "known_answer": {
    "games_checked": 10,
    "max_abs_total_diff": 0.0,
    "max_abs_pace_diff": 0.0
  }
}


ARM v1 (EXP-044): rows=0 families={}
  status: {   "as_of": "2026-10-30T13:53:21.283051+00:00",   "rows_logged_this_run": 0,   "events_logged_total": 0,   "skipped": [],   "params_hash": "9019981832b8b15d" } 

ARM v2 (EXP-044b): rows=0 families={}
  status: (none)

LOG TAIL (logs/nba_engine_live_cron.log), error lines in last 500: no log
  (no log yet)

```
