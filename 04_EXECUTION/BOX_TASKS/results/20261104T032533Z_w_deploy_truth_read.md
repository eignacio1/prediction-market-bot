# Box task `deploy_truth_read` — 20261104T032533Z_w_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261104T032533Z_w_deploy_truth_read.toml`
- note: is #412 on the box before the batch install retry
- ran: 2026-11-04T03:25:53Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 20b5d097 2026-11-04T03:17:01+00:00 Box tasks: results 2026-11-04T03:17Z
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: noop at 2026-11-04T03:23:03Z
  OK box HEAD 20b5d097 = origin/main
  OK t4-mlb runs box HEAD code (20b5d097; started 2026-11-04T02:53:40Z)
  OK pmbot-web-dashboard runs box HEAD code (20b5d097; started 2026-11-04T03:13:36Z)

```
