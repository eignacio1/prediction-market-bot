# Box task `nba_engine_cron_install` — 20261030T1430Z_w95_1_nba_engine_cron_install

- request: `04_EXECUTION/BOX_TASKS/requests/20261030T1430Z_w95_1_nba_engine_cron_install.toml`
- note: W95.1: install NBA engine refresh + v1/v2 runner lines (budget_read 14:23Z: only own NOT INSTALLED reds, healthcheck HEALTHY)
- ran: 2026-10-30T14:34:37Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/nba_engine_cron_install.py install`

```
SURFACE BUDGET: RED (box HEAD 026caa5c, as of 2026-10-30T14:34:30Z)
  exempt (own first-run state): NOT INSTALLED cron|2,12,22,32,42,52 16-23,0-4 * * *|--no-refresh --no-refresh --raw exp_output/NBA_EVENTS/raw --raw exp_output/NBA_EVENTS/raw
  exempt (own first-run state): NOT INSTALLED cron|33 12 * * *|cmd:10bda36275
BACKUP: /opt/prediction-market-bot/logs/crontab_backups/crontab_20261030T143437Z.bak
  + 33 12 * * * cd /opt/prediction-market-bot && flock -n /tmp/nba_engine_live.lock env PYTHONPATH=/opt/prediction-market-bo
  + 2,12,22,32,42,52 16-23,0-4 * * * cd /opt/prediction-market-bot && flock -n /tmp/nba_engine_live.lock env PYTHONPATH=/opt
INSTALLED: 2 NBA engine line(s) appended; every prior crontab line preserved

```
