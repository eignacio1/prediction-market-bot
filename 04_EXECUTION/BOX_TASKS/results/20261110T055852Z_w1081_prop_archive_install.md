# Box task `archive_cron_install` — 20261110T055852Z_w1081_prop_archive_install

- request: `04_EXECUTION/BOX_TASKS/requests/20261110T055852Z_w1081_prop_archive_install.toml`
- note: W108.1 install NBA/NHL/NFL prop archive lines (operator approved by name in chat)
- ran: 2026-11-10T05:59:20Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/archive_cron_install.py install`

```
SURFACE BUDGET: RED (box HEAD a8003f6f, as of 2026-11-10T05:59:11Z)
  exempt (own first-run state): NOT INSTALLED cron|14,44 0-5,17-23 * * *|scripts/archive_market_prices.py --out exp_output/PRICE_ARCHIVE --series KXNBAPTS
  exempt (own first-run state): NOT INSTALLED cron|17,47 0-5,17-23 * * *|scripts/archive_market_prices.py --out exp_output/PRICE_ARCHIVE --series KXNHLGOAL
  exempt (own first-run state): NOT INSTALLED cron|23,53 0-3,17-23 * * *|scripts/archive_market_prices.py --out exp_output/PRICE_ARCHIVE --series KXNFLPASSYDS
REFUSED: Hard Rule 14 -- no new live component while the budget is RED. Red items:
  - NOT INSTALLED cron|3-58/5 0-5,17-23 * * *|scripts/run_ride_board.py
  - NOT INSTALLED cron|55 21,22,23 * * *|scripts/news_burst_capture.py --interval 20 --minutes 30

```
