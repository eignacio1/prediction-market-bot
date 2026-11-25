# Box task `combo_rfq_demo_run` — 20261125T0511Z_combo_rfq_demo_run

- request: `04_EXECUTION/BOX_TASKS/requests/20261125T0511Z_combo_rfq_demo_run.toml`
- note: W127.3 Part A rerun after tip-lookup fix
- ran: 2026-11-25T05:16:14Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 255
- command (allowlisted, scripts/box_tasks.py): `export $(grep -v '^#' .env | xargs); BOT_ENV=paper PM_COMBO_RFQ_DEMO=on PYTHONPATH=src:. venv/bin/python scripts/combo_rfq_demo.py`

```

[stderr]
Traceback (most recent call last):
  File "/opt/prediction-market-bot/scripts/combo_rfq_demo.py", line 238, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/opt/prediction-market-bot/scripts/combo_rfq_demo.py", line 231, in main
    summary = run(R.DemoRfqClient.from_env(), rows, combos, now, Path(a.out))
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/prediction-market-bot/scripts/combo_rfq_demo.py", line 163, in run
    ac = client.accept(rid, v["quote"]["id"], side)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/prediction-market-bot/src/prediction_market_bot/c5_execution/kalshi_rfq.py", line 95, in accept
    raise RfqRefused("per-run accept cap reached")
prediction_market_bot.c5_execution.kalshi_rfq.RfqRefused: per-run accept cap reached

```
