# Box task `deploy_truth_read` — 20261113T0035Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261113T0035Z_deploy_truth_read.toml`
- note: W114.2: recheck box deploy of e8e06a1
- ran: 2026-11-13T00:36:13Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 1528943d 2026-11-12T16:23:37-08:00 Session claim: B-086 — W114.4 NBA joint teammate legs one usage pool per team. PURPOSE: D4 NBA / teammate joint error
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: docs_only at 2026-11-13T00:28:22Z
  OK box HEAD 1528943d behind origin/main ae7562b9: 5 file(s) a service uses (src/prediction_market_bot/archive_intake/__init__.py, src/prediction_market_bot/archive_intake/archive.py, src/prediction_market_bot/archive_intake/fetch.py) unpulled for 6.7 min (alarm > 45 min; check logs/vps_deploy.log for a red gate or dirty-tree abort)
  OK t4-mlb runs box HEAD code (1528943d; started 2026-11-12T05:33:44Z)
  OK pmbot-web-dashboard runs box HEAD code (1528943d; started 2026-11-13T00:26:55Z)

```
