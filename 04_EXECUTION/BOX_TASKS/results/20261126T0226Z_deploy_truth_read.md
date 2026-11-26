# Box task `deploy_truth_read` — 20261126T0226Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261126T0226Z_deploy_truth_read.toml`
- note: W130.5: recheck box HEAD for #602 (222df43)
- ran: 2026-11-26T02:26:31Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 0dbffccd 2026-11-26T02:21:34+00:00 Box tasks: results 2026-11-26T02:21Z
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-11-26T02:25:00Z
  OK box HEAD 0dbffccd = origin/main
  OK t4-mlb runs box HEAD code (0dbffccd; started 2026-11-26T01:05:36Z)
  OK pmbot-web-dashboard runs box HEAD code (0dbffccd; started 2026-11-26T02:24:58Z)

```
