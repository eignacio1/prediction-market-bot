# Box task `deploy_truth_read` — 20261112T2353Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261112T2353Z_deploy_truth_read.toml`
- note: W113.2: re-read after deploy timer; box should carry PR 495
- ran: 2026-11-12T23:53:34Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 6f40c9a7 2026-11-12T23:47:19+00:00 Box tasks: results 2026-11-12T23:47Z
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: noop at 2026-11-12T23:53:04Z
  OK box HEAD 6f40c9a7 = origin/main
  OK t4-mlb runs box HEAD code (6f40c9a7; started 2026-11-12T05:33:44Z)
  OK pmbot-web-dashboard runs box HEAD code (6f40c9a7; started 2026-11-12T23:48:53Z)

```
