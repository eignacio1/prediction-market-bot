# Box task `nhl_event_store_install` — 20261118T023414Z_nhl_event_store_install

- request: `04_EXECUTION/BOX_TASKS/requests/20261118T023414Z_nhl_event_store_install.toml`
- note: Operator approved nhl_event_store_install 2026-11-17 17:45 PT (yes approve on all 3). PR #507 merged 02:13Z.
- ran: 2026-11-18T02:35:16Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/nhl_event_store_install.py install`

```
SURFACE BUDGET: RED (box HEAD 6d5a1120, as of 2026-11-18T02:35:12Z)
REFUSED: Hard Rule 14 -- no new live component while the budget is RED. Red items:
  - healthcheck: UNHEALTHY: 1 fault(s), 1 warning(s)

```
