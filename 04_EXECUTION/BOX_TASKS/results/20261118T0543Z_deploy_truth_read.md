# Box task `deploy_truth_read` — 20261118T0543Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261118T0543Z_deploy_truth_read.toml`
- note: W118.4 confirm disk_read deployed
- ran: 2026-11-18T05:44:14Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD f6f7df41 2026-11-17T21:26:17-08:00 GA-6 tick 1: close GG-230 (resolved), GG-1452 (dup of GG-1462); OPEN 272 -> 270 (docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: noop at 2026-11-18T05:43:02Z
  OK box HEAD f6f7df41 = origin/main
  OK t4-mlb runs box HEAD code (f6f7df41; started 2026-11-18T04:55:12Z)
  OK pmbot-web-dashboard runs box HEAD code (f6f7df41; started 2026-11-18T05:28:44Z)

```
