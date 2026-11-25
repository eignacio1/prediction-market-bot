# Box task `data_offload_probe` — 20261125T061943Z_data_offload_probe

- request: `04_EXECUTION/BOX_TASKS/requests/20261125T061943Z_data_offload_probe.toml`
- note: 128.5 reachability + RSS/runtime per scraper
- ran: 2026-11-25T06:20:10Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 2
- command (allowlisted, scripts/box_tasks.py): `systemd-run --scope -q -p MemoryMax=150M -p MemorySwapMax=0 /bin/true; echo systemd_run_rc=$?; PYTHONPATH=src:. venv/bin/python scripts/data_offload.py probe`

```
systemd_run_rc=0

[stderr]
venv/bin/python: can't open file '/opt/prediction-market-bot/scripts/data_offload.py': [Errno 2] No such file or directory

```
