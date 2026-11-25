# Box task `combo_rfq_demo_run` — 20261125T0401Z_combo_rfq_demo_run

- request: `04_EXECUTION/BOX_TASKS/requests/20261125T0401Z_combo_rfq_demo_run.toml`
- note: W127.3 Part A: demo-only RFQs on NBA same-game combos; caps in code, Kelly 0
- ran: 2026-11-25T04:05:00Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `export $(grep -v '^#' .env | xargs); BOT_ENV=paper PM_COMBO_RFQ_DEMO=on PYTHONPATH=src:. venv/bin/python scripts/combo_rfq_demo.py`

```
{"event": "COMBO_RFQ_DEMO_RUN", "day": "2026-11-25", "candidates": 0, "sampled": 0, "nightly_budget": 12, "created": 0, "quoted": 0, "no_quote": 0, "accepted": 0, "executed": 0, "not_listed_on_demo": 0, "none_reason": null}

```
