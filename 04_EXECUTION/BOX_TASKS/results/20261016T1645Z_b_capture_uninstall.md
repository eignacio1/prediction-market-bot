# Box task `capture_uninstall` — 20261016T1645Z_b_capture_uninstall

- request: `04_EXECUTION/BOX_TASKS/requests/20261016T1645Z_b_capture_uninstall.toml`
- note: window: reinstall at :51 after #287 reached the box (first install raced the deploy)
- ran: 2026-10-16T16:45:54Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/thin_capture_install.py uninstall`

```
UNINSTALLED: W80P.1 block removed; every other crontab line preserved

```
