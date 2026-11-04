# Box task `t3_lock_stagger_install` — 20261104T015437Z_b_t3_lock_stagger_install

- request: `04_EXECUTION/BOX_TASKS/requests/20261104T015437Z_b_t3_lock_stagger_install.toml`
- note: GG-1581 lock + stagger; operator approved 2026-11-03 17:54 PT
- ran: 2026-11-04T01:54:58Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/t3_lock_stagger.py install`

```
BACKUP: /opt/prediction-market-bot/logs/crontab_backups/crontab_20261104T015458Z.bak
INSTALLED: 6 T3 line(s) wrapped with flock + skip row; every other crontab line preserved (line count 661 -> 661)

```
