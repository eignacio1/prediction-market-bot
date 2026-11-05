# Box task `nba_engine_catchup_install` — 20261105T064004Z_b_nba_engine_catchup_install

- request: `04_EXECUTION/BOX_TASKS/requests/20261105T064004Z_b_nba_engine_catchup_install.toml`
- note: operator named approval 2026-11-04 22:39 PT
- ran: 2026-11-05T06:40:27Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/nba_engine_catchup_install.py install`

```
SURFACE BUDGET: RED (box HEAD b950bfb4, as of 2026-11-05T06:40:22Z)
  exempt (own first-run state): NOT INSTALLED cron|7,17,27,37,47,57 16-23,0-4 * * *|--raw exp_output/NBA_EVENTS/raw
BACKUP: /opt/prediction-market-bot/logs/crontab_backups/crontab_20261105T064027Z.bak
  + 7,17,27,37,47,57 16-23,0-4 * * * cd /opt/prediction-market-bot && flock -w 240 /tmp/nba_engine_live.lock env PYTHONPATH=
INSTALLED: 1 NBA engine catch-up line(s) appended; every prior crontab line preserved

```
