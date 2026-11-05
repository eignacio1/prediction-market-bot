# Box task `deploy_truth_read` — 20261105T064004Z_a_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261105T064004Z_a_deploy_truth_read.toml`
- note: box HEAD before the catch-up install
- ran: 2026-11-05T06:40:21Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD b950bfb4 2026-11-05T06:37:08+00:00 Box tasks: results 2026-11-05T06:37Z
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: docs_only at 2026-11-05T06:38:08Z
  OK box HEAD b950bfb4 = origin/main
  OK t4-mlb runs box HEAD code (b950bfb4; started 2026-11-05T06:15:47Z)
  OK pmbot-web-dashboard runs box HEAD code (b950bfb4; started 2026-11-05T06:34:12Z)

```
