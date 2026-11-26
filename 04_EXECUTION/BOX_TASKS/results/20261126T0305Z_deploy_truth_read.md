# Box task `deploy_truth_read` — 20261126T0305Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261126T0305Z_deploy_truth_read.toml`
- note: W130.5: recheck for #606 deploy
- ran: 2026-11-26T03:05:31Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD b29e1e02 2026-11-25T18:59:50-08:00 W130.2: handoff updated, #601 merged, t4-mlb not needed, dry run pending
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: docs_only at 2026-11-26T03:03:08Z
  OK box HEAD b29e1e02 = origin/main
  OK t4-mlb runs box HEAD code (b29e1e02; started 2026-11-26T02:30:34Z)
  OK pmbot-web-dashboard runs box HEAD code (b29e1e02; started 2026-11-26T02:59:21Z)

```
