# Box task `deploy_truth_read` — 20261016T1648Z_a_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261016T1648Z_a_deploy_truth_read.toml`
- note: window: reinstall at :51 once the box has pulled #287
- ran: 2026-10-16T16:48:53Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD c25d8792 2026-10-16T09:47:14-07:00 80.1: capture running at 21,51 (box had not pulled #287); find why
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-10-16T16:48:25Z
  OK t4-mlb runs box HEAD code (c25d8792; started 2026-10-16T16:30:17Z)
  OK pmbot-web-dashboard runs box HEAD code (c25d8792; started 2026-10-16T16:48:25Z)

```
