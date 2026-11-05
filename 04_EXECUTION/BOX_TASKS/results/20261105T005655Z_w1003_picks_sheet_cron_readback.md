# Box task `picks_sheet_cron_readback` — 20261105T005655Z_w1003_picks_sheet_cron_readback

- request: `04_EXECUTION/BOX_TASKS/requests/20261105T005655Z_w1003_picks_sheet_cron_readback.toml`
- note: W100.3 read-only
- ran: 2026-11-05T00:57:35Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/picks_sheet_cron_install.py readback`

```
CRONTAB BLOCK (1 lines):
# BEGIN W98.3 PICKS SHEET LINE
37 5,22 * * * cd /opt/prediction-market-bot && PYTHONPATH=/opt/prediction-market-bot/src:/opt/prediction-market-bot nice -n 10 /opt/prediction-market-bot/venv/bin/python 
# END W98.3 PICKS SHEET LINE
  picks_2026-10-30.json  1788491 bytes  mtime 2026-10-30T19:13Z
  picks_2026-11-02.json  2711089 bytes  mtime 2026-11-03T00:28Z
  picks_2026-11-04.json  2021186 bytes  mtime 2026-11-04T22:47Z
  picks_latest.json  2021186 bytes  mtime 2026-11-04T22:48Z

LOG TAIL (logs/picks_sheet_cron.log), error lines in last 500: 0
picks sheet 2026-11-04: 1170 picks in 90 games
picks sheet 2026-11-04: 2614 picks in 134 games

```
