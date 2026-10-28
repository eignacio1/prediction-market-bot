# Box task `deploy_truth_read` — 20261028T001810Z_w_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261028T001810Z_w_deploy_truth_read.toml`
- note: Wave 90 close read (strategic window)
- ran: 2026-10-28T00:18:43Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD ce78de49 2026-10-27T16:52:02-07:00 W90.2 Part B: decision router (pure fn), tests, replay, D5(a) MLB 0->2/8, GG-1330..1334 (#350)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-10-28T00:07:28Z
  OK t4-mlb runs box HEAD code (ce78de49; started 2026-10-27T04:58:35Z)
  OK pmbot-web-dashboard runs box HEAD code (ce78de49; started 2026-10-28T00:09:53Z)

```
