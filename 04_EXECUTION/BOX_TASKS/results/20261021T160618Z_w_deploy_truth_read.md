# Box task `deploy_truth_read` — 20261021T160618Z_w_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261021T160618Z_w_deploy_truth_read.toml`
- note: Window: confirm #309 (aggregation graph) is on the box
- ran: 2026-10-21T16:06:38Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 44af240e 2026-10-21T09:01:15-07:00 Visual Dashboard: aggregation web as an expandable graph (Obsidian-style) (#309)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-10-21T16:03:26Z
  OK t4-mlb runs box HEAD code (44af240e; started 2026-10-21T06:25:21Z)
  OK pmbot-web-dashboard runs box HEAD code (44af240e; started 2026-10-21T16:03:25Z)

```
