# Box task `deploy_truth_read` — 20261029T011653Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261029T011653Z_deploy_truth_read.toml`
- note: W94.Q: is proof_calendar.py on the box yet
- ran: 2026-10-29T01:16:57Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 03e71631 2026-10-28T17:47:46-07:00 Session close: T-1440 — CLOSED
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-10-29T01:06:07Z
  OK t4-mlb runs box HEAD code (03e71631; started 2026-10-27T04:58:35Z)
  OK pmbot-web-dashboard runs box HEAD code (03e71631; started 2026-10-29T01:05:56Z)

```
