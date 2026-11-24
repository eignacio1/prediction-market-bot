# Box task `archive_dense_readback` — 20261124T0550Z_archive_dense_readback

- request: `04_EXECUTION/BOX_TASKS/requests/20261124T0550Z_archive_dense_readback.toml`
- note: W125.2 Part 0-gate-dryrun
- ran: 2026-11-24T05:50:30Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/archive_dense_install.py readback`

```
CRONTAB BLOCK: not installed
GATE (would REFUSE now): {'disk_now_pct': 67.0, 'existing_pct_per_day': -3.6763767264928897, 'new_pct_per_day': 0.64, 'new_mb_per_day': 159.2, 'projected_pct_30d': 86.2, 'burst_rps': 8.12, 'avg_req_per_min': 25.7, 'burst_req_per_min': 487.3, 'half_limit_req_per_min': 600.0}
  - projected disk after 30 days is 86.2% (limit 80%): now 67% + (0.00 existing + 0.64 new) pct/day
PRICE_ARCHIVE_DENSE: none yet
TRADE_PRINTS: none yet

LOG: no log yet

```
