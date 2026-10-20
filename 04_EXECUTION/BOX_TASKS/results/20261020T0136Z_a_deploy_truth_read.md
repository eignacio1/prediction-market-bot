# Box task `deploy_truth_read` — 20261020T0136Z_a_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261020T0136Z_a_deploy_truth_read.toml`
- note: window handoff: confirm box has #296
- ran: 2026-10-20T01:37:01Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD b7100315 2026-10-19T18:24:54-07:00 Session close: W80.1 — CLOSED
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: noop at 2026-10-20T01:33:03Z
  OK t4-mlb runs box HEAD code (b7100315; started 2026-10-16T16:30:17Z)
  OK pmbot-web-dashboard runs box HEAD code (b7100315; started 2026-10-20T01:18:29Z)

```
