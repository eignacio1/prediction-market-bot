# Box task `deploy_truth_read` — 20261030T141438Z_w95_2b_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261030T141438Z_w95_2b_deploy_truth_read.toml`
- note: W95.2: retry, box HEAD must include 893e3b5
- ran: 2026-10-30T14:15:04Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD d9c4a08b 2026-10-30T14:10:07+00:00 Box tasks: results 2026-10-30T14:10Z
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-10-30T14:13:40Z
  OK box HEAD d9c4a08b = origin/main
  OK t4-mlb runs box HEAD code (d9c4a08b; started 2026-10-27T04:58:35Z)
  OK pmbot-web-dashboard runs box HEAD code (d9c4a08b; started 2026-10-30T14:13:39Z)

```
