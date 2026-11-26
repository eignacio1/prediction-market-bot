# Box task `deploy_truth_read` — 20261126T0101Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261126T0101Z_deploy_truth_read.toml`
- note: 129.1 Part A retry
- ran: 2026-11-26T01:01:43Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD cbed3114 2026-11-25T16:57:14-08:00 Session close: W129.2 — CLOSED
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-11-26T00:59:08Z
  OK box HEAD cbed3114 = origin/main
  OK t4-mlb runs box HEAD code (cbed3114; started 2026-11-24T06:43:46Z)
  OK pmbot-web-dashboard runs box HEAD code (cbed3114; started 2026-11-26T00:59:07Z)

```
