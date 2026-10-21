# Box task `forward_report_read` — 20261021T0439Z_c_forward_report_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261021T0439Z_c_forward_report_read.toml`
- note: Wave 81 close: window verification
- ran: 2026-10-21T04:49:58Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 255
- command (allowlisted, scripts/box_tasks.py): `mkdir -p exp_output/FORWARD_TEST/w81_1 && PYTHONPATH=src:. venv/bin/python scripts/demo_fill_forward_report.py --out exp_output/FORWARD_TEST/w81_1/demo_fill_forward_report.json --no-act; echo; python3 -c "import json;r=json.load(open('exp_output/FORWARD_TEST/w81_1/demo_fill_forward_report.json'));pr`

```

[stderr]
client_loop: send disconnect: Broken pipe

```
