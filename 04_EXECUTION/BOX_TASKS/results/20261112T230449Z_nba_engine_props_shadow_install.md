# Box task `nba_engine_props_shadow_install` — 20261112T230449Z_nba_engine_props_shadow_install

- request: `04_EXECUTION/BOX_TASKS/requests/20261112T230449Z_nba_engine_props_shadow_install.toml`
- note: Operator approved 2026-11-12 15:04 PT (Yes I approve). EXP-047 NBA props shadow cron line.
- ran: 2026-11-12T23:05:19Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/nba_engine_props_shadow_install.py install`

```
SURFACE BUDGET: GREEN (box HEAD b7a2117b, as of 2026-11-12T23:05:08Z)
BACKUP: /opt/prediction-market-bot/logs/crontab_backups/crontab_20261112T230518Z.bak
  + 39 * * * * ( flock -n 9 || { printf '{"ts":"\%s","runner":"nba_engine_props_shadow","event":"SKIP_LOCKED","reason":"prev
INSTALLED: 1 props-shadow line(s) appended; every prior crontab line preserved

```
