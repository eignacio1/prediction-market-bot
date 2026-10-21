# Box task `deploy_truth_read` — 20261021T153548Z_w_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261021T153548Z_w_deploy_truth_read.toml`
- note: Window: second check that #308 (f43e3fa) is on the box
- ran: 2026-10-21T15:36:05Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD cacab7ef 2026-10-21T15:29:25+00:00 Box tasks: results 2026-10-21T15:29Z
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-10-21T15:33:26Z
  OK t4-mlb runs box HEAD code (cacab7ef; started 2026-10-21T06:25:21Z)
  OK pmbot-web-dashboard runs box HEAD code (cacab7ef; started 2026-10-21T15:33:26Z)

```
