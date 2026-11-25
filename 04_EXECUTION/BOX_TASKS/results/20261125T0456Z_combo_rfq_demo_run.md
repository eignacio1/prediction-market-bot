# Box task `combo_rfq_demo_run` — 20261125T0456Z_combo_rfq_demo_run

- request: `04_EXECUTION/BOX_TASKS/requests/20261125T0456Z_combo_rfq_demo_run.toml`
- note: W127.3 Part A rerun with tips diagnostics 2
- ran: 2026-11-25T04:59:03Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `export $(grep -v '^#' .env | xargs); BOT_ENV=paper PM_COMBO_RFQ_DEMO=on PYTHONPATH=src:. venv/bin/python scripts/combo_rfq_demo.py`

```
{"event": "COMBO_RFQ_DEMO_RUN", "day": "2026-11-25", "candidates": 0, "sampled": 0, "nightly_budget": 12, "created": 0, "quoted": 0, "no_quote": 0, "accepted": 0, "executed": 0, "not_listed_on_demo": 0, "none_reason": null, "stages": {"fetched": 80000, "same_game": 17870, "rows": 0, "engine_p": 0, "resolved": 0, "mc_se_ok": 0, "flagged": 0, "unpriced": 0, "window_min": [30.0, 1800.0], "games_seen": 9, "tips_loaded": 10, "tips_keys": [["2026-11-24", ["DAL", "DEN"]], ["2026-11-25", ["MIA", "PHI"]], ["2026-11-25", ["CHA", "CHI"]], ["2026-11-25", ["CLE", "NYK"]], ["2026-11-25", ["MIN", "OKC"]], ["2026-11-25", ["LAC", "MEM"]]], "tips_file_bytes": 430, "games_no_tip": ["26NOV24DALDEN", "26NOV25BKNMIL", "26NOV25CHICHA", "26NOV25LACMEM", "26NOV25MIAPHI", "26NOV25MINOKC", "26NOV25PHXHOU", "26NOV25SACGSW"], "tips_sample": {"26NOV24DALDEN": null, "26NOV25BKNMIL": null, "26NOV25CHICHA": null, "26NOV25LACMEM": null, "26NOV25MIAPHI": null, "26NOV25MINOKC": null, "26NOV25PHXHOU": null, "26NOV25SACGSW": null}, "min_to_tip": []}}

```
