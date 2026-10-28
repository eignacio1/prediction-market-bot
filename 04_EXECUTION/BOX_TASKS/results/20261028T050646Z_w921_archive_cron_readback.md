# Box task `archive_cron_readback` — 20261028T050646Z_w921_archive_cron_readback

- request: `04_EXECUTION/BOX_TASKS/requests/20261028T050646Z_w921_archive_cron_readback.toml`
- note: W92.1 readback first rows NBA/NHL
- ran: 2026-10-28T05:07:11Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/archive_cron_install.py readback`

```
CRONTAB BLOCK (6 lines):
# BEGIN W92.1 ARCHIVE LINES
8,28,48 17-23 * * * cd $PROJ && export $(grep -v '^#' .env | xargs) && PYTHONPATH=$PYTHONPATH $PYTHON scripts/archive_market_prices.py --series KXNBAG
8,28,48 0-5   * * * cd $PROJ && export $(grep -v '^#' .env | xargs) && PYTHONPATH=$PYTHONPATH $PYTHON scripts/archive_market_prices.py --series KXNBAG
18 12-16 * * * cd $PROJ && export $(grep -v '^#' .env | xargs) && PYTHONPATH=$PYTHONPATH $PYTHON scripts/archive_market_prices.py --series KXNBAGAME K
11,31,51 17-23 * * * cd $PROJ && export $(grep -v '^#' .env | xargs) && PYTHONPATH=$PYTHONPATH $PYTHON scripts/archive_market_prices.py --series KXNHL
11,31,51 0-5   * * * cd $PROJ && export $(grep -v '^#' .env | xargs) && PYTHONPATH=$PYTHONPATH $PYTHON scripts/archive_market_prices.py --series KXNHL
21 12-16 * * * cd $PROJ && export $(grep -v '^#' .env | xargs) && PYTHONPATH=$PYTHONPATH $PYTHON scripts/archive_market_prices.py --series KXNHLGAME K
# END W92.1 ARCHIVE LINES

LOG TAIL (logs/price_archive_cron.log), 429s in last 500 lines: 0
  depth        GAME_WINNER: sampled 0 across 1 series, usable 0
  depth PARTIAL_GAME_WINNER: sampled 0 across 3 series, usable 0
  depth        PLAYER_PROP: sampled 0 across 1 series, usable 0
  depth           RUN_LINE: sampled 0 across 2 series, usable 0
  depth         TEAM_TOTAL: sampled 0 across 1 series, usable 0
2026-10-28T05:00:02Z  wrote 0 depth samples -> exp_output/PRICE_ARCHIVE/depth_2026-10-28.jsonl

PRICE_ARCHIVE rows by prefix (most recent 2 day files):
  prices_2026-10-27.jsonl  7499560 bytes  {}
  prices_2026-10-28.jsonl  695199 bytes  {}

```
