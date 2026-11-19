# Box task `deploy_truth_read` — 20261119T0546Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261119T0546Z_deploy_truth_read.toml`
- note: W120.2: after candidate-arm logging ON (96e9790)
- ran: 2026-11-19T05:49:56Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 9ece917f 2026-11-18T21:46:35-08:00 W120.2: box requests - deploy_truth_read, candidate_arms_read, d6_read (docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-11-19T05:48:49Z
  OK box HEAD 9ece917f = origin/main
  OK t4-mlb runs box HEAD code (9ece917f; started 2026-11-19T04:24:51Z)
  OK pmbot-web-dashboard runs box HEAD code (9ece917f; started 2026-11-19T05:48:48Z)

```
