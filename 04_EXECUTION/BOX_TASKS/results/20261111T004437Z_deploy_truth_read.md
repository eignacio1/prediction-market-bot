# Box task `deploy_truth_read` — 20261111T004437Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261111T004437Z_deploy_truth_read.toml`
- note: operator-approved install sequence 2026-11-10 16:27 PT (SW-9)
- ran: 2026-11-11T00:44:55Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD fb84178a 2026-11-10T16:42:46-08:00 Install sequence step 2: prop archive entries live again for their install (ride board installed 00:35Z)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: docs_only at 2026-11-11T00:43:06Z
  OK box HEAD fb84178a = origin/main
  OK t4-mlb runs box HEAD code (fb84178a; started 2026-11-06T05:43:33Z)
  OK pmbot-web-dashboard runs box HEAD code (fb84178a; started 2026-11-10T06:18:34Z)

```
