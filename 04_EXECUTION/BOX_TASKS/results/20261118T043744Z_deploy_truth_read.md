# Box task `deploy_truth_read` — 20261118T043744Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261118T043744Z_deploy_truth_read.toml`
- note: W117.3: is #511 on the box
- ran: 2026-11-18T04:38:07Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD daff214b 2026-11-17T18:51:38-08:00 W117.1: parked handoff + queue row (docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: noop at 2026-11-18T04:33:04Z
  OK box HEAD daff214b behind origin/main 55250ba5: 1 file(s) a service uses (src/prediction_market_bot/archive_intake/closing_lines.py) unpulled for 0.6 min (alarm > 45 min; check logs/vps_deploy.log for a red gate or dirty-tree abort)
  OK t4-mlb runs box HEAD code (daff214b; started 2026-11-18T02:55:02Z)
  OK pmbot-web-dashboard runs box HEAD code (daff214b; started 2026-11-18T02:55:00Z)

```
