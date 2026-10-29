# Box task `deploy_truth_read` — 20261029T051555Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261029T051555Z_deploy_truth_read.toml`
- note: #376 pulled?
- ran: 2026-10-29T05:15:59Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 8f17be3a 2026-10-29T05:11:53+00:00 Box tasks: results 2026-10-29T05:11Z
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: docs_only at 2026-10-29T05:13:03Z
  OK t4-mlb runs box HEAD code (8f17be3a; started 2026-10-27T04:58:35Z)
  OK pmbot-web-dashboard runs box HEAD code (8f17be3a; started 2026-10-29T05:08:34Z)

```
