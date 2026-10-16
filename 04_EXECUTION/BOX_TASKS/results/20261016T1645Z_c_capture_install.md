# Box task `capture_install` — 20261016T1645Z_c_capture_install

- request: `04_EXECUTION/BOX_TASKS/requests/20261016T1645Z_c_capture_install.toml`
- note: window: reinstall at :51 after #287 reached the box (first install raced the deploy)
- ran: 2026-10-16T16:45:58Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/thin_capture_install.py install`

```
SURFACE BUDGET: GREEN (box HEAD 3b01d2e4, as of 2026-10-16T16:45:55Z)
INSTALLED: W80P.1 block appended; every prior crontab line preserved

```
