# Box task `evidence_weekly_readback` — 20261120T154712Z_evidence_weekly_readback

- request: `04_EXECUTION/BOX_TASKS/requests/20261120T154712Z_evidence_weekly_readback.toml`
- note: Operator approved evidence_weekly_install 2026-11-20 07:46 PT (I approve evidence_weekly_install.)
- ran: 2026-11-20T15:47:42Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/evidence_weekly_install.py readback`

```
CRONTAB BLOCK (1 lines):
# BEGIN W121.1 EVIDENCE WEEKLY LINE
0 10 * * 2 ( flock -n 9 || exit 0; cd /opt/prediction-market-bot && PYTHONPATH=/opt/prediction-market-bot/src:/opt/prediction-market-bot nice -n 15 /opt/prediction-market
# END W121.1 EVIDENCE WEEKLY LINE
DISK: 63.6% used, 9.1 GB free
COMPRESSED FILES (*.gz under exp_output/KALSHI_HISTORY): 3

LOG TAIL (logs/evidence_weekly.log), error lines in last 500: no log
  (no log yet)

```
