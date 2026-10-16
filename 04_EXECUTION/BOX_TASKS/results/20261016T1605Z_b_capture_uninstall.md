# Box task `capture_uninstall` — 20261016T1605Z_b_capture_uninstall

- request: `04_EXECUTION/BOX_TASKS/requests/20261016T1605Z_b_capture_uninstall.toml`
- note: GG-920 retry after the box pulls #285
- ran: 2026-10-16T16:06:04Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 2
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/thin_capture_install.py uninstall`

```
W80R.1: install the W80P.1 thin-market depth capture cron block on the box -- ONLY when the SURFACE BUDGET reads
GREEN (Hard Rule 14) -- and read back what it has written. Runs ON the box (via scripts/box_tasks.py).

  install    fresh budget probe; RED -> prints REFUSED + every red reason and changes nothing. GREEN -> appends the
             `# BEGIN/END W80P.1 THIN MARKET DEPTH CAPTURE` block from deploy/cron.thin_capture to the crontab
             (idempotent: an existing block is left exactly as it is; no other crontab line is touched).
  readback   the crontab block, the log tail, the store files and tracked-ticker count. Read-only.

Exit code is 0 in every outcome except a crontab write that did not verify (the bridge reports stdout either way).


```
