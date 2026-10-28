# Box task `deploy_truth_read` — 20261028T004533Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261028T004533Z_deploy_truth_read.toml`
- note: W91.3: confirm box applied #347 locks + #354 cron lines; t4-mlb decision
- ran: 2026-10-28T00:48:03Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 631c74e8 2026-10-27T17:39:24-07:00 W89.6: GG-452 align requirements-base pins to VPS venv and pyproject (pandas 2.2.3, scikit-learn 1.8.0, scipy 1.12.0) (#347)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-10-28T00:44:52Z
  OK t4-mlb runs box HEAD code (631c74e8; started 2026-10-27T04:58:35Z)
  OK pmbot-web-dashboard runs box HEAD code (631c74e8; started 2026-10-28T00:44:51Z)

```
