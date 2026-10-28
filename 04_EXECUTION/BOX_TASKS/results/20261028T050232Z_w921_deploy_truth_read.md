# Box task `deploy_truth_read` — 20261028T050232Z_w921_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261028T050232Z_w921_deploy_truth_read.toml`
- note: W92.1 pre-install read
- ran: 2026-10-28T05:02:55Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD c0e88719 2026-10-27T21:55:44-07:00 W92.1 Part A: archive_cron_install (NBA/NHL archive lines onto the box crontab) (#358)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-10-28T04:58:34Z
  OK t4-mlb runs box HEAD code (c0e88719; started 2026-10-27T04:58:35Z)
  OK pmbot-web-dashboard runs box HEAD code (c0e88719; started 2026-10-28T04:58:33Z)

```
