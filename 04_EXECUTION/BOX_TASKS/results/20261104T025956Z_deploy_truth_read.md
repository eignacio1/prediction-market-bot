# Box task `deploy_truth_read` — 20261104T025956Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261104T025956Z_deploy_truth_read.toml`
- note: W99.3 post-merge deploy read (#405/#407/#409); record t4-mlb decision
- ran: 2026-11-04T03:00:50Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD e23c9445 2026-11-03T18:53:06-08:00 W99.1 Part C results, queue row, decision log, handoff (docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-11-04T02:58:39Z
  OK box HEAD e23c9445 = origin/main
  OK t4-mlb runs box HEAD code (e23c9445; started 2026-11-04T02:53:40Z)
  OK pmbot-web-dashboard runs box HEAD code (e23c9445; started 2026-11-04T02:58:38Z)

```
