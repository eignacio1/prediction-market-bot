# Box task `deploy_truth_read` — 20261126T0258Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261126T0258Z_deploy_truth_read.toml`
- note: W130.5: wait for #606 deploy
- ran: 2026-11-26T02:58:06Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD e3a53a35 2026-11-26T02:52:55+00:00 Box tasks: results 2026-11-26T02:52Z
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: docs_only at 2026-11-26T02:53:10Z
  OK box HEAD e3a53a35 = origin/main
  OK t4-mlb runs box HEAD code (e3a53a35; started 2026-11-26T02:30:34Z)
  OK pmbot-web-dashboard runs box HEAD code (e3a53a35; started 2026-11-26T02:42:49Z)

```
