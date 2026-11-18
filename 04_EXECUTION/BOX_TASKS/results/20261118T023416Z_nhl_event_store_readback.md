# Box task `nhl_event_store_readback` — 20261118T023416Z_nhl_event_store_readback

- request: `04_EXECUTION/BOX_TASKS/requests/20261118T023416Z_nhl_event_store_readback.toml`
- note: Operator approved nhl_event_store_install 2026-11-17 17:45 PT (yes approve on all 3). PR #507 merged 02:13Z.
- ran: 2026-11-18T02:35:16Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/nhl_event_store_install.py readback`

```
CRONTAB BLOCK: not installed
  exp_output/NHL_EVENTS: (none yet)

LOG TAIL (logs/nhl_event_store_refresh.log), error lines in last 500: no log
  (no log yet)

```
