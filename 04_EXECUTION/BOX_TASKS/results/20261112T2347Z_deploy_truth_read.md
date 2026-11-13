# Box task `deploy_truth_read` — 20261112T2347Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261112T2347Z_deploy_truth_read.toml`
- note: W113.2: confirm box HEAD carries PR 495 (NFL splits + snapshots)
- ran: 2026-11-12T23:47:18Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 3673d755 2026-11-12T15:32:09-08:00 W113.1 handoff, queue row, GG-1896..1898 (docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: noop at 2026-11-12T23:43:06Z
  OK box HEAD 3673d755 = origin/main
  OK t4-mlb runs box HEAD code (3673d755; started 2026-11-12T05:33:44Z)
  OK pmbot-web-dashboard runs box HEAD code (3673d755; started 2026-11-12T23:16:14Z)

```
