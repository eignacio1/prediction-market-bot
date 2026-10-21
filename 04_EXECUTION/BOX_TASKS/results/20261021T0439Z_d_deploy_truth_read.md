# Box task `deploy_truth_read` — 20261021T0439Z_d_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261021T0439Z_d_deploy_truth_read.toml`
- note: Wave 81 close: window verification
- ran: 2026-10-21T04:50:00Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 9c236aa2 2026-10-20T21:39:53-07:00 Box tasks: Wave 81 close reads
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: noop at 2026-10-21T04:48:03Z
  OK t4-mlb runs box HEAD code (9c236aa2; started 2026-10-16T16:30:17Z)
  OK pmbot-web-dashboard runs box HEAD code (9c236aa2; started 2026-10-20T05:38:26Z)

```
