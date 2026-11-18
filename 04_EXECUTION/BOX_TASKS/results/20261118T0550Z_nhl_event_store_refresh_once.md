# Box task `nhl_event_store_refresh_once` — 20261118T0550Z_nhl_event_store_refresh_once

- request: `04_EXECUTION/BOX_TASKS/requests/20261118T0550Z_nhl_event_store_refresh_once.toml`
- note: W118.3 part A one pass of approved refresh job (resumable)
- ran: 2026-11-18T05:51:13Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `( flock -n 9 || { echo LOCKED; exit 0; }; BOT_ENV=paper nice -n 10 PYTHONPATH=src:. venv/bin/python scripts/run_nhl_event_store_refresh.py >> logs/nhl_event_store_refresh.log 2>&1; tail -n 3 logs/nhl_event_store_refresh.log ) 9>/tmp/nhl_event_store_refresh.lock`

```
nice: ‘PYTHONPATH=src:.’: No such file or directory

```
