# Box task `deploy_truth_read` — 20261126T0022Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261126T0022Z_deploy_truth_read.toml`
- note: 129.1 confirm box has PR 589
- ran: 2026-11-26T00:22:44Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD c0e0556e 2026-11-25T16:16:25-08:00 Session claim: TBD — W129.6 NFL in-play live feed + shadow cells. PURPOSE: B1 NFL in-play cells able to log 0->n, B3 T4NFL-ARITH/FLOW bands have a logging cell, feed latency measured
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-11-26T00:19:43Z
  OK box HEAD c0e0556e = origin/main
  OK t4-mlb runs box HEAD code (c0e0556e; started 2026-11-24T06:43:46Z)
  OK pmbot-web-dashboard runs box HEAD code (c0e0556e; started 2026-11-26T00:19:41Z)

```
