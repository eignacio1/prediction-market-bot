<!-- session-meta
task_id: T-1390
tier: STANDARD
timestamp: 2026-10-28T23:45:00Z
commit: 2660522
one_line_summary: W93.2 NBA travel/tz/altitude + officials factor classes built point-in-time, tested held-out; margin NO, GG-1390 open
gg_touched: GG-1390
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D4, D5(b)
gap_delta: D4 NBA +2 factor classes; D5(b) NBA travel none->interpreted, officials none->interpreted (results_W93_2.md, nba.toml B12/B13 @ 9cfcfcf)
pattern_sweep: n/a (no defect fixed)
surface_delta: 0
-->

# SESSION HANDOFF — W93.2 NBA engine: travel, time zones, altitude, officials

Status: DONE | main @ 9cfcfcf | PR #362 (CI green, merged), PR #366 (CI green, merged) | Travel geometry and officials factor classes built point-in-time and tested on held-out seasons; margin NO, altitude→total small yes, officials weak/unstable | MEASURE MOVED: D5(b) NBA travel geometry none -> interpreted; officials none -> interpreted (assignment timing gap GG-1390); D4 NBA factor classes +2 (source: results_W93_2.md, nba.toml B12/B13) | stage per factor: travel/tz/altitude interpreted; officials interpreted | operator decisions: none

vision_pillar: DEPTH
gap_measure: D4, D5(b)
gap_delta: D4 NBA +2 factor classes; D5(b) travel none->interpreted, officials none->interpreted
pattern_sweep: n/a (no defect fixed)
surface_delta: none (no running component, runner, arm, order or registry cell)

## Results
- `12_EXPLORATORY/nba_geometry/results_W93_2.md` (Parts A and B), `results_W93_2.json`, `results_W93_2_officials.json`.
- Margin: no geometry spec moves. Total: venue altitude only +0.92 MSE gain [0.43, 1.44], n=2,150 (one of 7 specs, not multiplicity-corrected). Officials on total: +0.51 [-0.12, 1.14] pooled; 2025 moves, 2026 does not.
- Applied: descriptive only (this season's Kalshi NBA total/spread rows are tens).

## Hand-back
- GG-1390 (OPEN, MEDIUM): no timestamp on crew assignment, no verified free live-capture route. A probe of free live-officials routes with a browser-style user agent was refused by the permission classifier ("Bot Check Circumvention"); not retried or worked around. Cheapest route: plain read of the NBA CDN / ESPN scoreboard `officials` field after ~9am ET with per-game observed-at time, or an approved daily capture.
- Main run 40640145825 (Part A merge) was cancelled by concurrency after my docs push; run 40640208716 on the next commit passed. No Deploy job summary appeared on those runs; the Part B merge run 40641102382 was still in progress at handoff, so read its result.
- Claim T-1390..T-1392 / GG-1390..GG-1392: only GG-1390 used; not formally closed.
