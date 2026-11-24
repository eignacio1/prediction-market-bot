# Box task `forward_report_read` — 20261124T0055Z_forward_report_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261124T0055Z_forward_report_read.toml`
- note: SW-9: demo-fill stall WARN - orders per day since 11-20
- ran: 2026-11-24T00:48:55Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 124
- command (allowlisted, scripts/box_tasks.py): `mkdir -p exp_output/FORWARD_TEST/w81_1 && PYTHONPATH=src:. venv/bin/python scripts/demo_fill_forward_report.py --out exp_output/FORWARD_TEST/w81_1/demo_fill_forward_report.json --no-act; echo; python3 -c "import json;r=json.load(open('exp_output/FORWARD_TEST/w81_1/demo_fill_forward_report.json'));pr`

```

```
