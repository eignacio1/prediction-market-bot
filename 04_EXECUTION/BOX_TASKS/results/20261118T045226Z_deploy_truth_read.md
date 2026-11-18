# Box task `deploy_truth_read` — 20261118T045226Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261118T045226Z_deploy_truth_read.toml`
- note: W117.1 A1: read back ARM_BOOK_CAPS=raised deploy (#514) and t4-mlb restart.
- ran: 2026-11-18T04:52:45Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 123037ad 2026-11-17T20:45:07-08:00 Session close: B-099 — CLOSED
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: docs_only at 2026-11-18T04:48:05Z
  OK box HEAD 123037ad = origin/main
  OK t4-mlb runs box HEAD code (123037ad; started 2026-11-18T02:55:02Z)
  OK pmbot-web-dashboard runs box HEAD code (123037ad; started 2026-11-18T04:38:58Z)

```
