# Box task `deploy_truth_read` — 20261120T1621Z_a_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261120T1621Z_a_deploy_truth_read.toml`
- note: W122.2: is PR 545 (pot_of_gold candidate) on the box
- ran: 2026-11-20T16:21:28Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD ce63a821 2026-11-20T08:16:52-08:00 W122.4: handoff + queue row (docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-11-20T16:18:50Z
  OK box HEAD ce63a821 = origin/main
  OK t4-mlb runs box HEAD code (ce63a821; started 2026-11-19T04:24:51Z)
  OK pmbot-web-dashboard runs box HEAD code (ce63a821; started 2026-11-20T16:18:49Z)

```
