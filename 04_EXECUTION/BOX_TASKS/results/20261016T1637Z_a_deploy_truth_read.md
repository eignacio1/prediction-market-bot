# Box task `deploy_truth_read` — 20261016T1637Z_a_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261016T1637Z_a_deploy_truth_read.toml`
- note: window: after manual deploy dispatch restarted t4-mlb 16:30Z (no MLB game live)
- ran: 2026-10-16T16:37:36Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 9a279d37 2026-10-16T09:26:31-07:00 W80R.2/.3 tools: thin-market efficiency table + NBA totals applied-factor test (no results yet) (#286)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: noop at 2026-10-16T16:33:03Z
  OK t4-mlb runs box HEAD code (9a279d37; started 2026-10-16T16:30:17Z)
  OK pmbot-web-dashboard runs box HEAD code (9a279d37; started 2026-10-16T16:30:15Z)

```
