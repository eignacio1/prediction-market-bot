# Box task `budget_read` — 20261021T0439Z_a_budget_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261021T0439Z_a_budget_read.toml`
- note: Wave 81 close: window verification
- ran: 2026-10-21T04:40:13Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/runtime_registry.py live --refresh; echo; tail -n 40 logs/health.log | grep '^===' | tail -1`

```
  as of 2026-10-21T04:40:09Z · box HEAD 44363847 · 77 live components · 0 unreviewed · 1 stale/down/behind · no alarm: 0 unexplained, 10 with a written reason
  registry vs box: 0 installed-but-unmirrored · 1 mirrored-but-not-installed · units 0/0
    NOT INSTALLED (live entry, nothing on box): cron|2,22,42 * * * *|scripts/passyds_prekickoff_snapshot.py
  healthcheck: UNHEALTHY: 1 fault(s), 0 warning(s) · deploy: noop @ 2026-10-21T04:38:02Z
  systemd|pmbot-web-dashboard.service    active/running   run 1791ea98 · 0.0h behind HEAD · restarts 0
  systemd|t4-mlb.service                 active/running   run 9a279d37 · 0.0h behind HEAD · restarts 0
  STALE     cron|2,22,42 * * * *|scripts/passyds_prekickoff_snapshot.py  no write found
  SURFACE BUDGET RED: STALE cron|2,22,42 * * * *|scripts/passyds_prekickoff_snapshot.py: no write found; healthcheck: UNHEALTHY: 1 fault(s), 0 warning(s)

=== UNHEALTHY: 1 fault(s), 0 warning(s) ===

```
