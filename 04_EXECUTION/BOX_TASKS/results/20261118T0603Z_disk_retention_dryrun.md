# Box task `disk_retention_dryrun` — 20261118T0603Z_disk_retention_dryrun

- request: `04_EXECUTION/BOX_TASKS/requests/20261118T0603Z_disk_retention_dryrun.toml`
- note: W118.4 Part B: read-only dry run, what would be compressed and bytes saved
- ran: 2026-11-18T06:04:12Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 2
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/run_disk_retention.py --dry-run`

```

[stderr]
venv/bin/python: can't open file '/opt/prediction-market-bot/scripts/run_disk_retention.py': [Errno 2] No such file or directory

```
