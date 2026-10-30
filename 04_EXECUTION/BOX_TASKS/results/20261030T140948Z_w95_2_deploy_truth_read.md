# Box task `deploy_truth_read` — 20261030T140948Z_w95_2_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261030T140948Z_w95_2_deploy_truth_read.toml`
- note: W95.2: confirm box HEAD has PR 377 (893e3b5)
- ran: 2026-10-30T14:10:06Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD c3053b51 2026-10-30T07:05:41-07:00 W95.3: results, handoff, GG-1480/1481, queue row (docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-10-30T14:08:41Z
  OK box HEAD c3053b51 = origin/main
  OK t4-mlb runs box HEAD code (c3053b51; started 2026-10-27T04:58:35Z)
  OK pmbot-web-dashboard runs box HEAD code (c3053b51; started 2026-10-30T14:08:40Z)

```
