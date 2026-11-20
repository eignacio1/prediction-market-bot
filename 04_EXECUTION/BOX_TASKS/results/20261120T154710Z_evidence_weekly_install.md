# Box task `evidence_weekly_install` — 20261120T154710Z_evidence_weekly_install

- request: `04_EXECUTION/BOX_TASKS/requests/20261120T154710Z_evidence_weekly_install.toml`
- note: Operator approved evidence_weekly_install 2026-11-20 07:46 PT (I approve evidence_weekly_install.)
- ran: 2026-11-20T15:47:41Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/evidence_weekly_install.py install`

```
SURFACE BUDGET: GREEN (box HEAD b41d682c, as of 2026-11-20T15:47:37Z)
BACKUP: /opt/prediction-market-bot/logs/crontab_backups/crontab_20261120T154741Z.bak
  + 0 10 * * 2 ( flock -n 9 || exit 0; cd /opt/prediction-market-bot && PYTHONPATH=/opt/prediction-market-bot/src:/opt/predi
INSTALLED: 1 evidence-weekly line(s) appended; every prior crontab line preserved

```
