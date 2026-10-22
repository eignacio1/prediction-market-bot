# Box task `deploy_truth_read` — 20261022T000722Z_w_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261022T000722Z_w_deploy_truth_read.toml`
- note: Window: /visual live after #312
- ran: 2026-10-22T00:08:54Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 1cbe7094 2026-10-21T17:07:34-07:00 Box tasks: deploy truth + dashboard pages after #312
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-10-22T00:08:54Z
  OK t4-mlb runs box HEAD code (1cbe7094; started 2026-10-21T06:25:21Z)
  OK pmbot-web-dashboard runs box HEAD code (1cbe7094; started 2026-10-22T00:08:53Z)

```
