# Box task `deploy_truth_read` — 20261016T1645Z_a_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261016T1645Z_a_deploy_truth_read.toml`
- note: window: reinstall at :51 after #287 reached the box (first install raced the deploy)
- ran: 2026-10-16T16:45:53Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 3b01d2e4 2026-10-16T16:37:40+00:00 Box tasks: results 2026-10-16T16:37Z
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: noop at 2026-10-16T16:43:02Z
  OK t4-mlb runs box HEAD code (3b01d2e4; started 2026-10-16T16:30:17Z)
  OK pmbot-web-dashboard runs box HEAD code (3b01d2e4; started 2026-10-16T16:30:15Z)

```
