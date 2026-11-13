# Box task `deploy_truth_read` — 20261113T0031Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261113T0031Z_deploy_truth_read.toml`
- note: W114.2: has the box deployed e8e06a1 (arm_orders_read, d6_read)?
- ran: 2026-11-13T00:31:26Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 1528943d 2026-11-12T16:23:37-08:00 Session claim: B-086 — W114.4 NBA joint teammate legs one usage pool per team. PURPOSE: D4 NBA / teammate joint error
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: docs_only at 2026-11-13T00:28:22Z
  OK box HEAD 1528943d = origin/main
  OK t4-mlb runs box HEAD code (1528943d; started 2026-11-12T05:33:44Z)
  OK pmbot-web-dashboard runs box HEAD code (1528943d; started 2026-11-13T00:26:55Z)

```
