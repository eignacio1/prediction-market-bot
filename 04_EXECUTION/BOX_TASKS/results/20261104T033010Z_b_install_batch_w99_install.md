# Box task `install_batch_w99_install` — 20261104T033010Z_b_install_batch_w99_install

- request: `04_EXECUTION/BOX_TASKS/requests/20261104T033010Z_b_install_batch_w99_install.toml`
- note: retry after #412 (each step reads its own conf); operator approved 2026-11-03 19:16 PT
- ran: 2026-11-04T03:30:30Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/install_batch_w99.py install`

```
== step t3_lock ==
ALREADY INSTALLED (or no T3 lines present): nothing changed
SURFACE BUDGET: RED (box HEAD 10e5b359, as of 2026-11-04T03:30:26Z)
  batch step nba_events_refresh   would add 1 line(s)
  batch step nba_engine_v3        would add 1 line(s)
  batch step picks_builder        would add 1 line(s)
  exempt (belongs to this batch): NOT INSTALLED cron|3,13,23,33,43,53 16-23,0-4 * * *|--no-refresh --raw exp_output/NBA_EVENTS/raw
  exempt (belongs to this batch): NOT INSTALLED cron|37 5,22 * * *|scripts/build_picks_sheet.py
  exempt (belongs to this batch): NOT INSTALLED cron|46 15 * * *|cmd:10bda36275
== step nba_events_refresh ==
SURFACE BUDGET: GREEN (box HEAD 10e5b359, as of 2026-11-04T03:30:26Z)
BACKUP: /opt/prediction-market-bot/logs/crontab_backups/crontab_20261104T033030Z.bak
  + 46 15 * * * cd /opt/prediction-market-bot && flock -n /tmp/nba_engine_live.lock env PYTHONPATH=/opt/prediction-market-bo
INSTALLED: 1 NBA engine line(s) appended; every prior crontab line preserved
== step nba_engine_v3 ==
SURFACE BUDGET: GREEN (box HEAD 10e5b359, as of 2026-11-04T03:30:26Z)
BACKUP: /opt/prediction-market-bot/logs/crontab_backups/crontab_20261104T033030Z.bak
  + 3,13,23,33,43,53 16-23,0-4 * * * cd /opt/prediction-market-bot && flock -w 240 /tmp/nba_engine_live.lock env PYTHONPATH=
INSTALLED: 1 NBA engine v3 line(s) appended; every prior crontab line preserved
== step picks_builder ==
SURFACE BUDGET: GREEN (box HEAD 10e5b359, as of 2026-11-04T03:30:26Z)
BACKUP: /opt/prediction-market-bot/logs/crontab_backups/crontab_20261104T033030Z.bak
  + 37 5,22 * * * cd /opt/prediction-market-bot && PYTHONPATH=/opt/prediction-market-bot/src:/opt/prediction-market-bot nice
INSTALLED: 1 picks-sheet line(s) appended; every prior crontab line preserved
BATCH COMPLETE: t3_lock, nba_events_refresh, nba_engine_v3, picks_builder

```
