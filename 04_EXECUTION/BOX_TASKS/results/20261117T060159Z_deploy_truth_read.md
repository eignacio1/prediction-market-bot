# Box task `deploy_truth_read` — 20261117T060159Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261117T060159Z_deploy_truth_read.toml`
- note: W115.3: after merge of PR 502 (b8e0750); record t4-mlb decision
- ran: 2026-11-17T06:02:14Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 9caa073d 2026-11-16T17:18:46-08:00 W115.1 PARTIAL: handoff and queue row (docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: noop at 2026-11-17T05:58:02Z
  OK box HEAD 9caa073d = origin/main
  OK t4-mlb runs box HEAD code (9caa073d; started 2026-11-14T06:18:11Z)
  OK pmbot-web-dashboard runs box HEAD code (9caa073d; started 2026-11-17T01:03:56Z)

```
