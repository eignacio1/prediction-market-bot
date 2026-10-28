# Box task `deploy_truth_read` — 20261028T051546Z_w921b_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261028T051546Z_w921b_deploy_truth_read.toml`
- note: W92.1 post-merge read
- ran: 2026-10-28T05:16:15Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD cb8942a0 2026-10-27T22:10:40-07:00 Session close: T-1360 — CLOSED
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-10-28T05:13:32Z
  OK t4-mlb runs box HEAD code (cb8942a0; started 2026-10-27T04:58:35Z)
  OK pmbot-web-dashboard runs box HEAD code (cb8942a0; started 2026-10-28T05:13:31Z)

```
