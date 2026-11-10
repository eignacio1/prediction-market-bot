# Box task `deploy_truth_read` — 20261110T032445Z_a_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261110T032445Z_a_deploy_truth_read.toml`
- note: W107 close (SW-9)
- ran: 2026-11-10T03:25:07Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 53f604bc 2026-11-09T18:58:12-08:00 W107.2: session-end close-out (generated nav chain, closure row, digest)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: noop at 2026-11-10T03:23:03Z
  OK box HEAD 53f604bc = origin/main
  OK t4-mlb runs box HEAD code (53f604bc; started 2026-11-06T05:43:33Z)
  OK pmbot-web-dashboard runs box HEAD code (53f604bc; started 2026-11-10T02:43:48Z)

```
