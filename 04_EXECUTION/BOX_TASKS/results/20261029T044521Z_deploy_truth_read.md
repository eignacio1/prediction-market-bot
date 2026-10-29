# Box task `deploy_truth_read` — 20261029T044521Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261029T044521Z_deploy_truth_read.toml`
- note: has box pulled #375
- ran: 2026-10-29T04:45:25Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD f224f6b4 2026-10-29T04:36:24+00:00 Box tasks: results 2026-10-29T04:36Z
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: noop at 2026-10-29T04:43:02Z
  OK t4-mlb runs box HEAD code (f224f6b4; started 2026-10-27T04:58:35Z)
  OK pmbot-web-dashboard runs box HEAD code (f224f6b4; started 2026-10-29T01:43:41Z)

```
