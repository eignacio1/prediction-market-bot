# Box task `deploy_truth_read` — 20261118T050331Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261118T050331Z_deploy_truth_read.toml`
- note: W117.1 readback after #514 (caps) and #519 (policy on): box HEAD, t4-mlb restart.
- ran: 2026-11-18T05:03:51Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 8f8b560d 2026-11-18T05:02:44+00:00 Box tasks: results 2026-11-18T05:02Z
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-11-18T05:03:42Z
  OK box HEAD 8f8b560d = origin/main
  OK t4-mlb runs box HEAD code (8f8b560d; started 2026-11-18T04:55:12Z)
  OK pmbot-web-dashboard runs box HEAD code (8f8b560d; started 2026-11-18T05:03:42Z)

```
