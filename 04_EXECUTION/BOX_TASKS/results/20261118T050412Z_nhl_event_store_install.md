# Box task `nhl_event_store_install` — 20261118T050412Z_nhl_event_store_install

- request: `04_EXECUTION/BOX_TASKS/requests/20261118T050412Z_nhl_event_store_install.toml`
- note: Operator approved nhl_event_store_install 11-17 17:45 PT. Box HEALTHY 05:01Z (disk 87%, store 325 MB).
- ran: 2026-11-18T05:04:54Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/nhl_event_store_install.py install`

```
SURFACE BUDGET: GREEN (box HEAD 8f8b560d, as of 2026-11-18T05:04:46Z)
BACKUP: /opt/prediction-market-bot/logs/crontab_backups/crontab_20261118T050454Z.bak
  + 29 13 * * * ( flock -n 9 || { printf '{"ts":"\%s","runner":"nhl_event_store_refresh","event":"SKIP_LOCKED","reason":"pre
INSTALLED: 1 store-refresh line(s) appended; every prior crontab line preserved

```
