# Box task `budget_read` — 20261016T1604Z_x_budget_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261016T1604Z_x_budget_read.toml`
- note: GG-920: budget after the deploy-log SHA fix; expect RED on t4-mlb
- ran: 2026-10-16T16:04:42Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/runtime_registry.py live --refresh; echo; tail -n 40 logs/health.log | grep '^===' | tail -1`

```
  as of 2026-10-16T16:04:39Z · box HEAD 8b1a56d3 · 74 live components · 0 unreviewed · 0 stale/down/behind · no alarm: 0 unexplained, 10 with a written reason
  registry vs box: 0 installed-but-unmirrored · 0 mirrored-but-not-installed · units 0/0
  healthcheck: HEALTHY: 0 faults, 0 warning(s) · deploy: noop @ 2026-10-16T16:03:03Z
  systemd|pmbot-web-dashboard.service    active/running   run 8b1a56d3 · 0.0h behind HEAD · restarts 0
  systemd|t4-mlb.service                 active/running   run 03ad6df9 · 0.0h behind HEAD · restarts 0
  SURFACE BUDGET GREEN

=== HEALTHY: 0 faults, 0 warning(s) ===

```
