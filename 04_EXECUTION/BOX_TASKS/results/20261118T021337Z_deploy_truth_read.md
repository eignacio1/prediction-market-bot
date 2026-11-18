# Box task `deploy_truth_read` — 20261118T021337Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261118T021337Z_deploy_truth_read.toml`
- note: W117.0: after merges of PR 505 (a795d84), 506 (5ddaf0d), 507; record t4-mlb decision
- ran: 2026-11-18T02:13:54Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 5ddaf0d7 2026-11-17T18:05:39-08:00 W116.1 (B-094): pooled + sequential evidence design, router v2 map behind PM_LEAF_MAP_VERSION (default v1), frozen v2 pre-registration (#506)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: noop at 2026-11-18T02:13:04Z
  OK box HEAD 5ddaf0d7 = origin/main
  OK t4-mlb runs box HEAD code (5ddaf0d7; started 2026-11-18T01:58:45Z)
  OK pmbot-web-dashboard runs box HEAD code (5ddaf0d7; started 2026-11-18T02:08:38Z)

```
