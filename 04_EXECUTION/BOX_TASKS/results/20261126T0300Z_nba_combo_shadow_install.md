# Box task `nba_combo_shadow_install` — 20261126T0300Z_nba_combo_shadow_install

- request: `04_EXECUTION/BOX_TASKS/requests/20261126T0300Z_nba_combo_shadow_install.toml`
- note: Operator approved nba_combo_shadow_install by name 2026-11-25 (W130.3 re-file: first run cancelled by a newer push). Installs hourly combo shadow + daily demo RFQ line.
- ran: 2026-11-26T02:53:25Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/nba_combo_shadow_install.py install`

```
SURFACE BUDGET: GREEN (box HEAD e3a53a35, as of 2026-11-26T02:53:13Z)
BACKUP: /opt/prediction-market-bot/logs/crontab_backups/crontab_20261126T025325Z.bak
  + 41 * * * * ( flock -n 9 || exit 0; cd /opt/prediction-market-bot && BOT_ENV=paper PM_COMBO_SHADOW=on PYTHONPATH=/opt/pre
  + 17 18 * * * ( flock -n 8 || exit 0; cd /opt/prediction-market-bot && export $(grep -v '^#' .env | xargs) && BOT_ENV=pape
INSTALLED: 2 combo line(s) appended (shadow + demo RFQ); every prior crontab line preserved

```
