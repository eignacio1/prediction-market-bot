# Box task `install_batch_w99_install` — 20261104T031634Z_a_install_batch_w99_install

- request: `04_EXECUTION/BOX_TASKS/requests/20261104T031634Z_a_install_batch_w99_install.toml`
- note: Wave 99 held installs (T3 lock, NBA events refresh, NBA v3, picks); operator approved 2026-11-03 19:16 PT
- ran: 2026-11-04T03:16:55Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/install_batch_w99.py install`

```
== step t3_lock ==
ALREADY INSTALLED (or no T3 lines present): nothing changed
SURFACE BUDGET: RED (box HEAD 2d7d0696, as of 2026-11-04T03:16:49Z)
  batch step nba_events_refresh   would add 1 line(s)
  batch step nba_engine_v3        would add 1 line(s)
  batch step picks_builder        would add 0 line(s)
  exempt (belongs to this batch): NOT INSTALLED cron|3,13,23,33,43,53 16-23,0-4 * * *|--no-refresh --raw exp_output/NBA_EVENTS/raw
  exempt (belongs to this batch): NOT INSTALLED cron|46 15 * * *|cmd:10bda36275
REFUSED: Hard Rule 14 -- a red NOT explained by this batch still blocks. Red items:
  - NOT INSTALLED cron|37 5,22 * * *|scripts/build_picks_sheet.py
t3_lock was applied; nba_events_refresh, nba_engine_v3, picks_builder were NOT attempted.

```
