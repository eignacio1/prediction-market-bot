# Box task `frozen_inventory_read` — 20261030T140948Z_w95_2_frozen_inventory_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261030T140948Z_w95_2_frozen_inventory_read.toml`
- note: W95.2 Part A: archive inventory
- ran: 2026-10-30T14:10:07Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 2
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python 12_EXPLORATORY/frozen_evidence_check/repro.py inventory --archive exp_output/PRICE_ARCHIVE`

```

[stderr]
venv/bin/python: can't open file '/opt/prediction-market-bot/12_EXPLORATORY/frozen_evidence_check/repro.py': [Errno 2] No such file or directory

```
