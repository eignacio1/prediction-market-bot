# Box task `forward_report_read` — 20261105T062538Z_w102_2b_forward_report_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261105T062538Z_w102_2b_forward_report_read.toml`
- note: W102.2 re-check after #424 pull
- ran: 2026-11-05T06:30:18Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 255
- command (allowlisted, scripts/box_tasks.py): `mkdir -p exp_output/FORWARD_TEST/w81_1 && PYTHONPATH=src:. venv/bin/python scripts/demo_fill_forward_report.py --out exp_output/FORWARD_TEST/w81_1/demo_fill_forward_report.json --no-act; echo; python3 -c "import json;r=json.load(open('exp_output/FORWARD_TEST/w81_1/demo_fill_forward_report.json'));pr`

```

[stderr]
Read from remote host 157.230.91.33: Connection reset by peer
client_loop: send disconnect: Broken pipe

```
