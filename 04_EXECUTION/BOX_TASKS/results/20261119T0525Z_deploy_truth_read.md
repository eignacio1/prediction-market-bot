# Box task `deploy_truth_read` — 20261119T0525Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261119T0525Z_deploy_truth_read.toml`
- note: W120.1: is the PR 532 merge (NFL split verdicts) on the box
- ran: 2026-11-19T05:27:30Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD f1380fb9 2026-11-18T21:23:00-08:00 W120.1: box requests - deploy_truth_read and d6_read after PR 532 (docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-11-19T05:24:02Z
  OK box HEAD f1380fb9 = origin/main
  OK t4-mlb runs box HEAD code (f1380fb9; started 2026-11-19T04:24:51Z)
  OK pmbot-web-dashboard runs box HEAD code (f1380fb9; started 2026-11-19T05:24:00Z)

```
