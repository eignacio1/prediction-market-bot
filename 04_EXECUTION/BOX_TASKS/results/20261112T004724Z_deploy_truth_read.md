# Box task `deploy_truth_read` — 20261112T004724Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261112T004724Z_deploy_truth_read.toml`
- note: W111 close (SW-9): confirm box deploy of #482 #483 #484 #485 and service restarts
- ran: 2026-11-12T00:47:53Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD e30adfe6 2026-11-11T16:42:48-08:00 W111.2 session-end: meta block, generated chain/closure/digest/checkpoint (docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-11-12T00:44:58Z
  OK box HEAD e30adfe6 = origin/main
  OK t4-mlb runs box HEAD code (e30adfe6; started 2026-11-12T00:44:57Z)
  OK pmbot-web-dashboard runs box HEAD code (e30adfe6; started 2026-11-12T00:44:55Z)

```
