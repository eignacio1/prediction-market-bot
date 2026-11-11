# Box task `ride_board_install` — 20261111T002915Z_a_ride_board_install

- request: `04_EXECUTION/BOX_TASKS/requests/20261111T002915Z_a_ride_board_install.toml`
- note: operator approved by name 2026-11-10 16:27 PT; prop archive entries paused for this step only (install deadlock: each install exempts only its own reds)
- ran: 2026-11-11T00:29:36Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/ride_board_install.py install`

```
SURFACE BUDGET: RED (box HEAD 6215c2ed, as of 2026-11-11T00:29:33Z)
  exempt (own first-run state): NOT INSTALLED cron|3-58/5 0-5,17-23 * * *|scripts/run_ride_board.py
REFUSED: Hard Rule 14 -- no new live component while the budget is RED. Red items:
  - NOT INSTALLED cron|14,44 0-5,17-23 * * *|scripts/archive_market_prices.py --out exp_output/PRICE_ARCHIVE --series KXNBAPTS
  - NOT INSTALLED cron|17,47 0-5,17-23 * * *|scripts/archive_market_prices.py --out exp_output/PRICE_ARCHIVE --series KXNHLGOAL
  - NOT INSTALLED cron|23,53 0-3,17-23 * * *|scripts/archive_market_prices.py --out exp_output/PRICE_ARCHIVE --series KXNFLPASSYDS

```
