# Box task `deploy_truth_read` — 20261120T1702Z_a_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261120T1702Z_a_deploy_truth_read.toml`
- note: W122.2: is c334dbf on the box
- ran: 2026-11-20T17:02:39Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 3e469a37 2026-11-20T08:22:28-08:00 W122.2: handoff + queue row (docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: noop at 2026-11-20T16:58:03Z
  OK box HEAD 3e469a37 = origin/main
  OK t4-mlb runs box HEAD code (3e469a37; started 2026-11-19T04:24:51Z)
  OK pmbot-web-dashboard runs box HEAD code (3e469a37; started 2026-11-20T16:23:50Z)

```
