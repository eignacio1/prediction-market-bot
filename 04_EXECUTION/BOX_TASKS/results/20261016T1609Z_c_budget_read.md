# Box task `budget_read` — 20261016T1609Z_c_budget_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261016T1609Z_c_budget_read.toml`
- note: GG-920 retry 2: budget with the deploy-log SHA
- ran: 2026-10-16T16:10:08Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/runtime_registry.py live --refresh; echo; tail -n 40 logs/health.log | grep '^===' | tail -1`

```
  as of 2026-10-16T16:10:00Z · box HEAD 08e8a056 · 74 live components · 0 unreviewed · 1 stale/down/behind · no alarm: 0 unexplained, 10 with a written reason
  registry vs box: 0 installed-but-unmirrored · 0 mirrored-but-not-installed · units 0/0
  healthcheck: HEALTHY: 0 faults, 0 warning(s) · deploy: deployed @ 2026-10-16T16:08:24Z
  systemd|pmbot-web-dashboard.service    active/running   run 08e8a056 · 0.0h behind HEAD · restarts 0
  systemd|t4-mlb.service                 active/running   run dc84fa6c · 11.22h behind HEAD · restarts 0  <<< BEHIND
  SURFACE BUDGET RED: BEHIND systemd|t4-mlb.service: running dc84fa6c, 11.22h behind box HEAD

=== HEALTHY: 0 faults, 0 warning(s) ===

```
