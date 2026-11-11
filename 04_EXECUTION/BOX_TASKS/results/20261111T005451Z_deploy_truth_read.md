# Box task `deploy_truth_read` — 20261111T005451Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261111T005451Z_deploy_truth_read.toml`
- note: PR 460 live terminal deploy check (SW-9)
- ran: 2026-11-11T00:55:11Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD b4613c06 2026-11-11T00:49:26+00:00 Box tasks: results 2026-11-11T00:49Z
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-11-11T00:53:43Z
  OK box HEAD b4613c06 = origin/main
  OK t4-mlb runs box HEAD code (b4613c06; started 2026-11-06T05:43:33Z)
  OK pmbot-web-dashboard runs box HEAD code (b4613c06; started 2026-11-11T00:53:42Z)

```
