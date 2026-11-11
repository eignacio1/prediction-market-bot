# Box task `deploy_truth_read` — 20261111T0129Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261111T0129Z_deploy_truth_read.toml`
- note: W109.5: post-#468 deploy read
- ran: 2026-11-11T01:29:49Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 123ff62d 2026-11-10T17:27:23-08:00 W109.6: epoch-gate markout turn-off to GG-1771; demo-fill zero-orders healthcheck alarm (#469)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-11-11T01:28:34Z
  OK box HEAD 123ff62d = origin/main
  OK t4-mlb runs box HEAD code (123ff62d; started 2026-11-11T01:23:45Z)
  OK pmbot-web-dashboard runs box HEAD code (123ff62d; started 2026-11-11T01:28:34Z)

```
