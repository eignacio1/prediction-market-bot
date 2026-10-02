# Session Handoff — 2026-10-02T23:50Z

<!-- session-meta
task_id: T-607
tier: STANDARD
timestamp: 2026-10-02T23:50:00Z
commit: 08834e9
one_line_summary: T-607/EXP-036: NHL pregame shadow (9 cells) built, prereg pushed, cron installed live on VPS; n=0 scored, no edge claim.
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
-->

**Trigger:** operator-initiated close-out. **Last commit:** `08834e9` (main).

## Strategic Decisions This Session
| Decision | Status |
|---|---|
| Model class deviates from ADR-0004 LR+Platt (documented equivalent) | NEEDS OPERATOR DECISION; not written to DECISION_LOG (47.1 owns it) |
| Cron install for NHL shadow lines | executed under operator authorization 2026-10-02 |

## What changed
- D1-D4 on main: `nhl_ingest/features/pregame`, `nhl_train/backfill/shadow_eval/shadow_settle`, model `nhl_pregame_v1`, safety test. Suite 3521 passed/28 skipped.
- D3 prereg `0902d32` on branch `exp036-prereg-2026-10-02` (NOT on main).
- 7 NHL cron lines live on VPS (`deploy/cron.nhl_shadow`, 6a44430); first firing 23:30 UTC wrote 15 T3 rows. No existing cron line touched; no service restarted.
- D5 summary: `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/EXP036_NHL_PREGAME_SHADOW_RESULTS_2026-10-02.md` (gaps list for 47.1/wave 48).

## One thing pending
Check tonight's settle (hourly :15) produced first scored rows; investigate T1 abstentions (195 vs 240 rows); merge prereg branch.

## Resume
`ssh prediction-market-vps "tail -20 /opt/prediction-market-bot/logs/nhl_shadow_cron.log; wc -l /opt/prediction-market-bot/data/shadow/nhl/*.jsonl"`
