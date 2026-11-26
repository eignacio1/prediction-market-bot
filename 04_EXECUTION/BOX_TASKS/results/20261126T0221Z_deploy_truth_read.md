# Box task `deploy_truth_read` — 20261126T0221Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261126T0221Z_deploy_truth_read.toml`
- note: W130.5: confirm box HEAD has #602 before the fresh D6 / silent-arms / state reads
- ran: 2026-11-26T02:21:34Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD b32d59b8 2026-11-25T18:06:16-08:00 Session claim: W130.1 — W130.1 NFL in-play shadow runner. PURPOSE: B1 +8 shadow, B3, live feed lag
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: noop at 2026-11-26T02:18:03Z
  OK box HEAD b32d59b8 = origin/main
  OK t4-mlb runs box HEAD code (b32d59b8; started 2026-11-26T01:05:36Z)
  OK pmbot-web-dashboard runs box HEAD code (b32d59b8; started 2026-11-26T02:07:31Z)

```
