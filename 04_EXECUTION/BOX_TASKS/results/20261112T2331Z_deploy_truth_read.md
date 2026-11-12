# Box task `deploy_truth_read` — 20261112T2331Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261112T2331Z_deploy_truth_read.toml`
- note: W113.1: read box HEAD and deploy truth before PR 493 merge
- ran: 2026-11-12T23:31:31Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD fac52dd0 2026-11-12T15:11:56-08:00 Model tag per block (Sonnet / Haiku) from W114; W55 logged; D-34 (docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: noop at 2026-11-12T23:28:04Z
  OK box HEAD fac52dd0 = origin/main
  OK t4-mlb runs box HEAD code (fac52dd0; started 2026-11-12T05:33:44Z)
  OK pmbot-web-dashboard runs box HEAD code (fac52dd0; started 2026-11-12T23:16:14Z)

```
