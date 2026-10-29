# Box task `deploy_truth_read` — 20261029T012551Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261029T012551Z_deploy_truth_read.toml`
- note: W94.Q: has box pulled main
- ran: 2026-10-29T01:25:58Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD ec926126 2026-10-28T18:03:07-07:00 W94.2 Part C: NFL play callers (N11), interpreted, null on totals (#371)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-10-29T01:22:38Z
  OK t4-mlb runs box HEAD code (ec926126; started 2026-10-27T04:58:35Z)
  OK pmbot-web-dashboard runs box HEAD code (ec926126; started 2026-10-29T01:22:32Z)

```
