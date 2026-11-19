# Box task `deploy_truth_read` — 20261119T0106Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261119T0106Z_deploy_truth_read.toml`
- note: W119.1: is #524 deployed before refresh_once
- ran: 2026-11-19T01:04:40Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD dd2f46c9 2026-11-17T22:30:03-08:00 Operator: no paid capacity; $0 capacity plan (B-103: evidence off the box to the Mac) (docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: noop at 2026-11-19T01:03:06Z
  OK box HEAD dd2f46c9 = origin/main
  OK t4-mlb runs box HEAD code (dd2f46c9; started 2026-11-18T04:55:12Z)
  OK pmbot-web-dashboard runs box HEAD code (dd2f46c9; started 2026-11-18T06:14:40Z)

```
