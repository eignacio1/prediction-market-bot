# Box task `nhl_live_probe` — 20261126T0030Z_nhl_live_probe

- request: `04_EXECUTION/BOX_TASKS/requests/20261126T0030Z_nhl_live_probe.toml`
- note: 129.7 read-only: NHL live feed latency, staleness, clock advance and goal-vs-Kalshi-mid-move timing on the box
- ran: 2026-11-26T01:00:57Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 2
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/nhl_live_probe.py --games 8 --samples 30 --interval 10 --market-move --jump 2`

```

[stderr]
venv/bin/python: can't open file '/opt/prediction-market-bot/scripts/nhl_live_probe.py': [Errno 2] No such file or directory

```
