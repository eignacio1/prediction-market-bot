# Box task `deploy_truth_read` — 20261125T061033Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261125T061033Z_deploy_truth_read.toml`
- note: W128.2 post-merge deploy read
- ran: 2026-11-25T06:10:36Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 525184dd 2026-11-24T22:04:06-08:00 Session claim: W128.5 — W128.5 data offload: Muse file/API families to server crons; PURPOSE: moves D4 data layers per sport + Muse queue chunks retired
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: docs_only at 2026-11-25T06:08:04Z
  OK box HEAD 525184dd = origin/main
  OK t4-mlb runs box HEAD code (525184dd; started 2026-11-24T06:43:46Z)
  OK pmbot-web-dashboard runs box HEAD code (525184dd; started 2026-11-25T05:28:44Z)

```
