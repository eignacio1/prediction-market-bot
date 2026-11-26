# Box task `nfl_inplay_install` — 20261126T0246Z_nfl_inplay_install

- request: `04_EXECUTION/BOX_TASKS/requests/20261126T0246Z_nfl_inplay_install.toml`
- note: Operator approved nfl_inplay_install by name 2026-11-25 (W130.1; re-filed, prior run cancelled by a newer push; paused NFL in-play shadow cron, no orders, kelly 0).
- ran: 2026-11-26T02:52:17Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/nfl_inplay_install.py install`

```
SURFACE BUDGET: GREEN (box HEAD 5f75bee9, as of 2026-11-26T02:52:05Z)
BACKUP: /opt/prediction-market-bot/logs/crontab_backups/crontab_20261126T025217Z.bak
  + */2 17-23,0-6 * * * ( flock -n 9 || { printf '{"ts":"\%s","runner":"nfl_inplay_shadow","event":"SKIP_LOCKED","reason":"p
INSTALLED: 1 in-play line(s) appended; every prior crontab line preserved

```
