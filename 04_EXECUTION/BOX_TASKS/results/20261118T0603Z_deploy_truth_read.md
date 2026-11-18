# Box task `deploy_truth_read` — 20261118T0603Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261118T0603Z_deploy_truth_read.toml`
- note: W118.4: confirm box deployed 628b0e4 before disk_retention_dryrun
- ran: 2026-11-18T06:03:42Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 6e5bf419 2026-11-17T21:52:37-08:00 GA-6 tick 5: resolve GG-1462 (OPEN 265 -> 264, docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: noop at 2026-11-18T05:58:03Z
  OK box HEAD 6e5bf419 behind origin/main 572f5af2, no file a service uses differs
  OK t4-mlb runs box HEAD code (6e5bf419; started 2026-11-18T04:55:12Z)
  OK pmbot-web-dashboard runs box HEAD code (6e5bf419; started 2026-11-18T05:48:47Z)

```
