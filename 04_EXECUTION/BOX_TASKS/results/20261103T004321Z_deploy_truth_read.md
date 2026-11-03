# Box task `deploy_truth_read` — 20261103T004321Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261103T004321Z_deploy_truth_read.toml`
- note: W97.1 retry: confirm deploy of PR 391 + t4-mlb decision
- ran: 2026-11-03T00:43:30Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 50b07ee9 2026-11-02T16:27:45-08:00 Box request: frozen_resume_step (W97.2, docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: noop at 2026-11-03T00:33:14Z
  OK box HEAD 50b07ee9 behind origin/main 5ec8ff5f: 1 file(s) a service uses (src/prediction_market_bot/pregame_shadow/silent_arms.py) unpulled for 7.9 min (alarm > 45 min; check logs/vps_deploy.log for a red gate or dirty-tree abort)
  OK t4-mlb runs box HEAD code (50b07ee9; started 2026-10-30T16:06:33Z)
  OK pmbot-web-dashboard runs box HEAD code (50b07ee9; started 2026-10-30T19:31:41Z)

```
