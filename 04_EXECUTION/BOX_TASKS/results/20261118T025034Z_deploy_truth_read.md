# Box task `deploy_truth_read` — 20261118T025034Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261118T025034Z_deploy_truth_read.toml`
- note: W117.3: is #511 on the box before d6_read
- ran: 2026-11-18T02:50:50Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD dc39a49e 2026-11-17T18:45:29-08:00 W117.4 Part A: docs_guard workflow runs backlog, GG-id, gap-index and registry checks on every push to main (docs-only included) (#510)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-11-18T02:48:45Z
  OK box HEAD dc39a49e = origin/main
  OK t4-mlb runs box HEAD code (dc39a49e; started 2026-11-18T01:58:45Z)
  OK pmbot-web-dashboard runs box HEAD code (dc39a49e; started 2026-11-18T02:48:45Z)

```
