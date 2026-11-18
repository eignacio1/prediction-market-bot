# Box task `disk_retention_readback` — 20261118T061812Z_disk_retention_readback

- request: `04_EXECUTION/BOX_TASKS/requests/20261118T061812Z_disk_retention_readback.toml`
- note: Operator approved disk_retention_install 2026-11-17 22:18 PT (Yes). Disk 87%, 90% in ~2 days.
- ran: 2026-11-18T06:26:16Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/disk_retention_install.py readback`

```
CRONTAB BLOCK (1 lines):
# BEGIN W118.4 DISK RETENTION LINE
17 14 * * * ( flock -n 9 || exit 0; cd /opt/prediction-market-bot && PYTHONPATH=/opt/prediction-market-bot/src:/opt/prediction-market-bot nice -n 15 ionice -c3 /opt/predi
# END W118.4 DISK RETENTION LINE
DISK: 86.3% used, 3.4 GB free
COMPRESSED FILES (*.gz under exp_output/KALSHI_HISTORY): 0

LOG TAIL (logs/disk_retention.log), error lines in last 500: no log
  (no log yet)

```
