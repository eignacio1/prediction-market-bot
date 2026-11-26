# Box task `nhl_muse_fetch` — 20261126T0044Z_nhl_muse_fetch

- request: `04_EXECUTION/BOX_TASKS/requests/20261126T0044Z_nhl_muse_fetch.toml`
- note: 129.1 Part A/C
- ran: 2026-11-26T00:45:20Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 1
- command (allowlisted, scripts/box_tasks.py): `systemd-run --scope -q -p MemoryMax=150M -p MemorySwapMax=0 PYTHONPATH=src:. venv/bin/python scripts/nhl_muse_fetch.py`

```

[stderr]
Failed to find executable PYTHONPATH=src:.: No such file or directory

```
