# Box task `deploy_truth_read` — 20261111T0113Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261111T0113Z_deploy_truth_read.toml`
- note: W109.5 post-merge read of #462/#464
- ran: 2026-11-11T01:15:36Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 7887009e 2026-11-10T17:13:03-08:00 W109.5 A: dashboard memory - failed rebuild logged (last good page kept), /api/data encoded without str+bytes copy (#464)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-11-11T01:13:56Z
  OK box HEAD 7887009e = origin/main
  OK t4-mlb runs box HEAD code (7887009e; started 2026-11-06T05:43:33Z)
  OK pmbot-web-dashboard runs box HEAD code (7887009e; started 2026-11-11T01:13:55Z)

```
