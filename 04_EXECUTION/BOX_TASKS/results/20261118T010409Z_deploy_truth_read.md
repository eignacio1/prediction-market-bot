# Box task `deploy_truth_read` — 20261118T010409Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261118T010409Z_deploy_truth_read.toml`
- note: W116.3: post-#503 read (prior 005231Z d6_read ran 34s before the deploy) - wired cells by name, ERROR rows after
- ran: 2026-11-18T01:05:48Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 53c83e86 2026-11-17T17:01:39-08:00 W116.2 C2: ADR-0072 placement/caps addendum PROPOSAL; GG-1942..1944, GG-1955; GG-1934 resolved; queue decisions; handoff (docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: docs_only at 2026-11-18T01:03:05Z
  OK box HEAD 53c83e86 = origin/main
  OK t4-mlb runs box HEAD code (53c83e86; started 2026-11-14T06:18:11Z)
  OK pmbot-web-dashboard runs box HEAD code (53c83e86; started 2026-11-18T00:54:50Z)

```
