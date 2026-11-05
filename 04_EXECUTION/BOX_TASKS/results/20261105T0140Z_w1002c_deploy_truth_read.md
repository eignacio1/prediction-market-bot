# Box task `deploy_truth_read` — 20261105T0140Z_w1002c_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261105T0140Z_w1002c_deploy_truth_read.toml`
- note: W100.2 retry c, after box pull
- ran: 2026-11-05T01:37:02Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD c476bb06 2026-11-05T01:27:42+00:00 Box tasks: results 2026-11-05T01:27Z
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-11-05T01:36:55Z
  OK box HEAD c476bb06 = origin/main
  OK t4-mlb runs box HEAD code (c476bb06; started 2026-11-04T02:53:40Z)
  OK pmbot-web-dashboard runs box HEAD code (c476bb06; started 2026-11-05T01:36:52Z)

```
