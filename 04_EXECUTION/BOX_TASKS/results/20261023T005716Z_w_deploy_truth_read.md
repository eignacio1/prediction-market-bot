# Box task `deploy_truth_read` — 20261023T005716Z_w_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261023T005716Z_w_deploy_truth_read.toml`
- note: Window: Wave 86 close
- ran: 2026-10-23T00:57:37Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 7b8bebdd 2026-10-22T17:52:32-07:00 W86.2 closed: queue row (docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: docs_only at 2026-10-23T00:53:03Z
  OK t4-mlb runs box HEAD code (7b8bebdd; started 2026-10-22T02:28:37Z)
  OK pmbot-web-dashboard runs box HEAD code (7b8bebdd; started 2026-10-23T00:48:28Z)

```
