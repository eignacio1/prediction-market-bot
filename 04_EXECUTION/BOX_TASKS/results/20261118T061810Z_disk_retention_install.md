# Box task `disk_retention_install` — 20261118T061810Z_disk_retention_install

- request: `04_EXECUTION/BOX_TASKS/requests/20261118T061810Z_disk_retention_install.toml`
- note: Operator approved disk_retention_install 2026-11-17 22:18 PT (Yes). Disk 87%, 90% in ~2 days.
- ran: 2026-11-18T06:26:14Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/disk_retention_install.py install`

```
SURFACE BUDGET: GREEN (box HEAD b4a2d927, as of 2026-11-18T06:26:03Z)
BACKUP: /opt/prediction-market-bot/logs/crontab_backups/crontab_20261118T062614Z.bak
  + 17 14 * * * ( flock -n 9 || exit 0; cd /opt/prediction-market-bot && PYTHONPATH=/opt/prediction-market-bot/src:/opt/pred
INSTALLED: 1 retention line(s) appended; every prior crontab line preserved

```
