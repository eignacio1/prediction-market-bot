# Box task `nba_combo_shadow_readback` — 20261126T0330Z_nba_combo_shadow_readback

- request: `04_EXECUTION/BOX_TASKS/requests/20261126T0330Z_nba_combo_shadow_readback.toml`
- note: W130.3: confirm both combo lines are in the crontab after the approved install (re-file: 0312Z used a non-allowlisted name)
- ran: 2026-11-26T03:10:58Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/nba_combo_shadow_install.py readback`

```
CRONTAB BLOCK (2 lines):
# BEGIN W127.3 NBA COMBO SHADOW LINE
41 * * * * ( flock -n 9 || exit 0; cd /opt/prediction-market-bot && BOT_ENV=paper PM_COMBO_SHADOW=on PYTHONPATH=/opt/prediction-market-bot/src:/opt/prediction-market-bot 
17 18 * * * ( flock -n 8 || exit 0; cd /opt/prediction-market-bot && export $(grep -v '^#' .env | xargs) && BOT_ENV=paper PM_COMBO_RFQ_DEMO=on PYTHONPATH=/opt/prediction-
# END W127.3 NBA COMBO SHADOW LINE
  exp_output/COMBO_SHADOW: (none yet)

LOG TAIL (logs/nba_combo_shadow.log), error lines in last 500: no log
  (no log yet)

RFQ LEDGERS (exp_output/COMBO_RFQ_DEMO):
  COMBO_RFQ_DEMO.jsonl  8267 bytes  mtime 2026-11-25T05:13Z
RFQ LOG TAIL (logs/combo_rfq_demo.log):
  (no log yet)

```
