<!-- session-meta
task_id: W121.1
tier: STANDARD
timestamp: 2026-11-20T15:25:00Z
commit: 6b274cc
one_line_summary: W121.1 weekly evidence look runner merged (PR 538); first box look: 0 leaves with an arm, install awaits approval.
gg_touched: GG-1959
adr_touched: none
plan_deliverable_moved: no
vision_pillar: PROOF
gap_measure: P1, P3
gap_delta: leaves with an arm per map = 0 at first look (exp_output/EVIDENCE_WEEKLY cut 2026-11-17, box result 20261120T1511Z); next look 2026-11-24
pattern_sweep: grep pipeline.run consumers in src/ scripts/ tests/ 12_EXPLORATORY -> signature unchanged, 346 selected tests pass; box-deploy gap registered as GG-1959
surface_delta: +1 paused cron (cron|0 10 * * 2|scripts/run_evidence_weekly.py, registered), +4 box tasks, 0 live
-->

# Session handoff — W121.1 PROOF: weekly looks, e-process carried forward

- common rules quoted first: `# Wave 121 common rules` (from origin/main COMMON_RULES_W121.md)
- vision_pillar: PROOF (P1 / P3)
- PR: #538 merged (squash 8255f4c), CI green (guard + test)

## Built
- `decision_trees/evidence/weekly.py` + `pipeline.py` State/advance/result_of (`run` unchanged, bit-identical).
  Per sport and per map (v1, router_v2, nba_depth, nhl_v2, board): pooled posterior + e-process, carried from `state.json`.
- Missed weeks reported (`missed_looks`, `catch_up`), never filled. Late rows counted, never scored.
- Box tasks: `evidence_weekly_run`, `_install`, `_readback`, `_uninstall`. Entry `scripts/run_evidence_weekly.py`.
- `deploy/cron.evidence_weekly` (Tue 10:00 UTC) + PAUSED registry entry. Install NOT run.
- Tests: carried == single pass (float tol 1e-9); planted effect earns RIDE <= 6 wks; planted null earns nothing in 14 wks;
  missed week reported; late row counted; same cut is a no-op; schema mismatch refused; installer gated/idempotent/reversible.

## First look on box rows (result 20261120T1511Z, cut 2026-11-17T10:00Z, 140,223 rows, looks 38-44)
- Leaves with an arm: 0 on every map. Earned 0, lost 0.
- Candidate maps (router_v2, nba_depth, nhl_v2): 0 settled games so far (candidate logging began 11-19; nothing has settled yet).
  They enter the series as their rows settle; this look cannot score them.
- v1: NBA 36 games / 3 leaves, NFL 14 / 4, NHL 0. Board: NBA 205 games, NFL 101, NHL 311, MLB 25 (103/87/99/81 leaves).
- E-value leaders (all below the 10 bar and far below P(net>0) 0.9): NHL board T3 moneyline MODEL_FADE e=2.71 (P 0.27),
  MLB board run line T2 MODEL_FADE e=1.81 (P 0.05). Both are routed to no bet in these leaves yet.
- Power calendar: only NHL board has a date (45 weeks to first arm at the last-4-weeks game rate); others None.

## Next look
- Tue 2026-11-24 10:00Z (cut 11-24). Expected modal outcome: still 0 leaves with an arm; candidate series start to appear.

## Pushback / Surface / Dependencies
- Pushback: the weekly look cannot judge a candidate map until its rows settle; do not read this first look as a verdict on any map.
- Surface: +1 cron entry (paused), +4 allowlisted box tasks, +1 wrapper script; live components +0.
- Dependencies: box needs `git pull` before a new box task works (no deploy task exists; I pulled over ssh). Operator approval of
  `evidence_weekly_install` (queue "Needs your decision") is the only thing between now and the cron running.

## Measures
- gap_measure: P1/P3 leaves with an arm per map = 0 at first look. next look = 2026-11-24. e-value leaders above.
- pattern_sweep: swept src/ scripts/ tests/ 12_EXPLORATORY for consumers of `pipeline.run`; unchanged signature, 346 selected tests pass.
- surface_delta: +1 paused cron, +4 box tasks, 0 live.
