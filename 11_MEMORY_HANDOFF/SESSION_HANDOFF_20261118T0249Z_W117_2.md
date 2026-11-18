# Session Handoff — 2026-11-18 — W117.2 (B-099, QUANT, Sonnet)

<!-- session-meta
task_id: B-099
tier: STANDARD
timestamp: 2026-11-18T03:00:00Z
commit: see PR
one_line_summary: W117.2 NHL consensus prior, momentum closed, Kalshi vs books gap, family-vs-leaf power calendar
gg_touched: GG-1936
adr_touched: none
plan_deliverable_moved: no
vision_pillar: PROOF, DEPTH
gap_measure: P3 (first-arm dates per sport), D5 (history as a prior)
gap_delta: NFL +0.02 first arm 7 weeks earlier with nflverse; NHL +0.02 3 weeks earlier with the consensus prior; +0.05 1 week each
pattern_sweep: write-shaped .replace() flagged by the exploratory isolation scan was datetime.replace; swapped for strptime %z, grep 12_EXPLORATORY/ -> no other hit
surface_delta: 0
-->

**Status:** PR open, merge on green CI of the current head. Common rules first line quoted: "# Wave 117 common rules".

## Results (RESULT.md in 12_EXPLORATORY/nhl_consensus/)
- Prior: NHL ML fav -0.033 (se 0.015), puck line +0.04 to +0.05, total +0.021. One season; transfer SD 0.03.
- Momentum: hypothesis closed (EXP-W117.2-MOM-moneyline / -puck_line / -total, parked for R&D); all intervals contain 0.
- Kalshi vs books, ML n=1,312: gap +0.0016 [+0.0011,+0.0020]; ride at ask plus fee -0.0548 [-0.0773,-0.0314].
- Puck line and total: no 2025-26 Kalshi history. Need 722 games per market from 2026-27; on TO_MUSE.md for Monday.
- Calendar: prior moved first arm 1-7 weeks earlier; coarse leaves 6-40 weeks later. Prior is the bigger lever. No first arm before 2027.

## Caveats
- Local corpus 108,439 rows vs 106,430 in W116.1 RESULT.md; dates differ 1-2 weeks; the nfl-only run is the baseline.
- Kalshi cache is in the w84-3 worktree, not on main. Candle is the hour before start, not the exact close.
- Cross-sport pooling: one sport's prior shifts the other's date up to 2 weeks.

## Next
- Muse: 2026-27 free consensus (TO_MUSE.md). Then rerun the puck line and total Kalshi tests.
- Queue row 117.2 updated by a docs-only push after merge.
