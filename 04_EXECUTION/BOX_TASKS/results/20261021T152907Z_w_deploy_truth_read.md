# Box task `deploy_truth_read` — 20261021T152907Z_w_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261021T152907Z_w_deploy_truth_read.toml`
- note: Window: confirm PR #308 (aggregation web, f43e3fa) reaches the box and the dashboard regenerates
- ran: 2026-10-21T15:29:25Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 168f0dbe 2026-10-21T08:05:51-07:00 Window log 2026-10-21 morning in the sitrep; Muse add-in M83-C (PAM layer 1, backlog order)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: noop at 2026-10-21T15:28:02Z
  OK t4-mlb runs box HEAD code (168f0dbe; started 2026-10-21T06:25:21Z)
  OK pmbot-web-dashboard runs box HEAD code (168f0dbe; started 2026-10-21T15:08:25Z)

```
