# Box task `archive_dense_readback` — 20261124T0542Z_a_archive_dense_readback

- request: `04_EXECUTION/BOX_TASKS/requests/20261124T0542Z_a_archive_dense_readback.toml`
- note: W125.2 Part 0: read-only budget gate dry run at today disk; install NOT run (retry, #556 now merged)
- ran: 2026-11-24T05:43:04Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 2
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/archive_dense_install.py readback`

```

[stderr]
venv/bin/python: can't open file '/opt/prediction-market-bot/scripts/archive_dense_install.py': [Errno 2] No such file or directory

```
