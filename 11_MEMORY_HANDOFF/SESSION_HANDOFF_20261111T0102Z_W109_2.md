<!-- session-meta
task_id: W109.2
tier: STANDARD
timestamp: 2026-11-11T01:02:00Z
commit: 38c85dc
one_line_summary: W109.2 NHL architecture D5(a) 2->7/8 (PR #465); applied totals path abstains, gate fails 3/3 seasons
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D5(a) NHL; D5(b) NHL
gap_delta: D5(a) NHL 2/8 -> 7/8; D5(b) NHL applied 3 -> 3 (scripts/distance_to_optimum.py d5() on merged checkout)
pattern_sweep: n/a (no defect fixed)
surface_delta: 0
-->

## Strategic Decisions This Session
None - implementation-only session.

# SESSION HANDOFF W109.2 - NHL betting architecture

**Status:** DONE | **B-067:** done for the scaffold half (7/8, clusters capped); the applied half is open | **PR:** #465 merged as 9d0aaaf, CI green on head 1cab573 | branch session/20261111T003858Z-w109-2-nhl-arch

**One line:** five NHL architecture components now have a scaffold and a test, and the one applied path (NHL totals) abstains: its stability gate fails in 2023, 2024 and 2025, and the ungated shift is also null.

```
vision_pillar: DEPTH
gap_measure: D5(a) NHL; D5(b) NHL
gap_delta: D5(a) NHL 2/8 -> 7/8 (decision_trees, filtering_mechanisms, temporal_evolution, structural_tensions, seat_interface); D5(b) NHL applied 3 -> 3 (unchanged), source scripts/distance_to_optimum.py d5() on the merged checkout
pattern_sweep: n/a (no defect fixed). One stale record found: ARCHITECTURE_COMPONENTS nhl seat_interface said "none" though SEATS/nhl.toml (W83.3/W84.3) and tests/test_seat_interface.py existed; swept all nhl rows, only that one was stale.
surface_delta: none (no running component, no cron, no service; one exploratory script under 12_EXPLORATORY)
```

## MEASURE MOVED
D5(a) NHL 2 -> 7 of 8. Clusters stay none: NHL has no player archetypes (PAM absent), so 7 is the cap until that exists (NHL-T7).
D5(b) NHL applied 3 -> 3. I did not relabel a seat factor to applied: the totals path ran end to end but the factor has no usable signal.

## Stage per factor
- Rest-state split of regulation goals (granularity index: split, rank vs history, matchup cross, market map, application all built): **interpreted**; applied path built, abstains.
- Depth ladder (tree): **interpreted**. Temporal evolution: **interpreted**. Tensions: registered (7).

## Measured results (held out 2023-2025, walk-forward, n = 3,936 games, TOTAL 4.5/5.5/6.5, game-clustered bootstrap)
- Stability gate (train seasons only): fails 3/3 seasons (split-half CI lower bounds -1.55, -1.51, -0.53). Share of games shifted: 0.
- Applied minus baseline: exactly 0.0000 (gate abstains). Ungated minus baseline: -0.00007 [-0.00022, +0.00009] (null).
- Depth steps: d1-d0 -0.00012 [-0.0014, +0.0012]; d2-d1 -0.00014 [-0.00031, +0.00004]; **d3-d2 +0.00061 [+0.00001, +0.00125]** (full depth slightly worse for totals).
- Regulation-goal bias (predicted minus actual): -0.149 (2023), -0.095 (2024), +0.006 (2025): unstable sign.
- Temporal (gf, 2022-25): within-season slope +0.0003/game [-0.0004, +0.0013] flat; reliability gap -0.05 [-0.17, +0.06]; weight on this season rises 0.18 -> 0.55 across games 10-25 -> 51-82, prior season falls 0.47 -> 0.10.
- vs market: **unavailable** for 2023-2025 (no price history). Only market comparison remains W99.1: n=33 games, advantage -0.0057 [-0.0126, +0.0013]. No "net" computed. No fills or P&L read, so the NO-side epoch note does not apply.

## Notes for the next window
- The Part A premise "seats missing" was stale (SEATS/nhl.toml existed); only the component row was wrong.
- Per-technique when-it-applies lines are in each module docstring. The frame used is a gitignored scratch parquet; rebuild with 12_EXPLORATORY/nhl_engine/w97_4_build.py.
- t4-mlb decision: no restart needed (no imported module touched). Box HEAD fbada7d = origin/main, deploy truth OK.
- Installs: none prepared. Operator decisions: none.
- Strongest next DEPTH move: a different NHL factor through the same gate, or NHL-T3 (starter source) since the goalie proxy is why depth 3 is worse.
