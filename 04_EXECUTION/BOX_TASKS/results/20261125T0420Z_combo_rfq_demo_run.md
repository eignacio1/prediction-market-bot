# Box task `combo_rfq_demo_run` — 20261125T0420Z_combo_rfq_demo_run

- request: `04_EXECUTION/BOX_TASKS/requests/20261125T0420Z_combo_rfq_demo_run.toml`
- note: W127.3 Part A rerun with per-stage counts
- ran: 2026-11-25T04:24:55Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `export $(grep -v '^#' .env | xargs); BOT_ENV=paper PM_COMBO_RFQ_DEMO=on PYTHONPATH=src:. venv/bin/python scripts/combo_rfq_demo.py`

```
{"event": "COMBO_RFQ_DEMO_RUN", "day": "2026-11-25", "candidates": 0, "sampled": 0, "nightly_budget": 12, "created": 0, "quoted": 0, "no_quote": 0, "accepted": 0, "executed": 0, "not_listed_on_demo": 0, "none_reason": null, "stages": {"fetched": 80000, "same_game": 24545, "rows": 0, "engine_p": 0, "resolved": 0, "mc_se_ok": 0, "flagged": 0, "unpriced": 0, "window_min": [30.0, 1800.0], "min_to_tip": []}}

```
