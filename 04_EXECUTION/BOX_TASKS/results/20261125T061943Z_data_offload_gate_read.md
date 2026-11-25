# Box task `data_offload_gate_read` — 20261125T061943Z_data_offload_gate_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261125T061943Z_data_offload_gate_read.toml`
- note: 128.5 gate read
- ran: 2026-11-25T06:20:09Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 2
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/data_offload_install.py gate`

```

[stderr]
venv/bin/python: can't open file '/opt/prediction-market-bot/scripts/data_offload_install.py': [Errno 2] No such file or directory

```
