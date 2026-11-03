# Box task `deploy_truth_read` — 20261103T033816Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261103T033816Z_deploy_truth_read.toml`
- note: W98.2: has the box deployed PR 396?
- ran: 2026-11-03T03:38:34Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 184483af 2026-11-02T19:28:34-08:00 Session claim: T-1610..T-1612 / GG-1610..GG-1612 — STANDARD — W98.1 engine lane: NBA v1 arm logs every game, NHL engine v2 end-of-game model, v3 factors fully indexed (B-030/B-029/B-031) — FOR DEPTH+PROOF: NBA v1 events/games 69v81->100%; NHL totals bias->noise; v3 factors with 5 granularity parts 0->2
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: docs_only at 2026-11-03T03:33:09Z
  OK box HEAD 184483af behind origin/main fa48644a, no file a service uses differs
  OK t4-mlb runs box HEAD code (184483af; started 2026-10-30T16:06:33Z)
  OK pmbot-web-dashboard runs box HEAD code (184483af; started 2026-11-03T01:41:19Z)

```
