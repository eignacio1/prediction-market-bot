# Box task `deploy_truth_read` — 20261125T0401Z_a_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261125T0401Z_a_deploy_truth_read.toml`
- note: W127.4: is the dense-capture cut on the box
- ran: 2026-11-25T04:05:22Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD c9859b5e 2026-11-24T20:01:40-08:00 W127.4: box requests deploy_truth_read + archive_dense_gate_read (docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-11-25T04:04:59Z
  OK box HEAD c9859b5e = origin/main
  OK t4-mlb runs box HEAD code (c9859b5e; started 2026-11-24T06:43:46Z)
  OK pmbot-web-dashboard runs box HEAD code (c9859b5e; started 2026-11-25T04:04:56Z)

```
