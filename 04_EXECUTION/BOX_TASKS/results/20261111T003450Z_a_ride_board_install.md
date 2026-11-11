# Box task `ride_board_install` — 20261111T003450Z_a_ride_board_install

- request: `04_EXECUTION/BOX_TASKS/requests/20261111T003450Z_a_ride_board_install.toml`
- note: operator approved by name 2026-11-10 16:27 PT; prop archive entries paused for this step only
- ran: 2026-11-11T00:35:12Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/ride_board_install.py install`

```
SURFACE BUDGET: RED (box HEAD e8024bfb, as of 2026-11-11T00:35:08Z)
  exempt (own first-run state): NOT INSTALLED cron|3-58/5 0-5,17-23 * * *|scripts/run_ride_board.py
BACKUP: /opt/prediction-market-bot/logs/crontab_backups/crontab_20261111T003512Z.bak
  + 3-58/5 0-5,17-23 * * * cd /opt/prediction-market-bot && flock -n /tmp/ride_board.lock env PYTHONPATH=/opt/prediction-mar
INSTALLED: 1 ride-board line(s) appended; every prior crontab line preserved

```
