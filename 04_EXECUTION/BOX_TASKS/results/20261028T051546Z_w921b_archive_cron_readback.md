# Box task `archive_cron_readback` — 20261028T051546Z_w921b_archive_cron_readback

- request: `04_EXECUTION/BOX_TASKS/requests/20261028T051546Z_w921b_archive_cron_readback.toml`
- note: W92.1 post-merge read
- ran: 2026-10-28T05:16:04Z on root@157.230.91.33:/opt/prediction-market-bot
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

LOG TAIL (logs/price_archive_cron.log), 429s in last 500 lines: 1
2026-10-28T05:11:02Z  wrote 507 snapshots -> exp_output/PRICE_ARCHIVE/prices_2026-10-28.jsonl
  depth         GAME_TOTAL: sampled 1 across 1 series, usable 1
  depth        GAME_WINNER: sampled 1 across 1 series, usable 1
  depth           RUN_LINE: sampled 1 across 1 series, usable 0
  depth         TEAM_TOTAL: sampled 1 across 1 series, usable 0
2026-10-28T05:11:02Z  wrote 4 depth samples -> exp_output/PRICE_ARCHIVE/depth_2026-10-28.jsonl

PRICE_ARCHIVE rows by prefix (most recent 2 day files):
  prices_2026-10-27.jsonl  7499560 bytes  {}
  prices_2026-10-28.jsonl  1612405 bytes  {"KXNBAGAME": 66, "KXNBASPREAD": 429, "KXNBATEAMTOTAL": 459, "KXNBATOTAL": 380, "KXNHLGAME": 98, "KXNHLSPREAD": 78, "KXNHLTEAMTOTAL": 160, "KXNHLTOTAL": 171}

```
