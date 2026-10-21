<!-- session-meta
task_id: T-1044
tier: STANDARD
timestamp: 2026-10-21T06:40:00Z
commit: 5bc3572 (Part B code, PR #307), a974892 (Part A, PR #305); docs-only close on top
one_line_summary: Coverage/pressure gap, bot-side: man share, 5+ rusher rate and pressure are team traits at six games, but crossed with QB response they add no measurable yards beyond the frozen passyds model; Muse prior-season coverage values are null, QB time-to-throw FAILED on level
gg_touched: none (GG-995..997 and T-1045 unused)
adr_touched: none
plan_deliverable_moved: W82.3 Parts A and B
vision_pillar: DEPTH
gap_measure: D5(b) NFL (index entries) + charter §5 Muse grades
gap_delta: D5(b) NFL +1 index entry (INDEX_ENTRY_COVERAGE_PRESSURE.md, five parts, stage interpreted for seat factors N20/N21); Muse §5: no class VERIFIED; sub-class QB time-to-throw FAILED on level (r 0.962, mean diff -0.161 s); coverage/blitz/pressure/MOF/personnel ungradeable (96 of 96 prior values null). The "0 -> 1 graded" target is met only as one FAILED sub-class
pattern_sweep: Part A CI failed once on the exploratory fence scan (.rename()/.replace()); self-inflicted, fixed before merge; no defect fixed in existing code, so n/a
surface_delta: none
-->

# W82.3 handoff — coverage / pressure gap, bot-side

**Status:** DONE | branch docs-w823 (docs) over main | PR #305 (merged a974892) and PR #307 (merged 5bc3572), CI green on both | man share, 5+ rusher rate and pressure are TRAIT; crossed with QB response, no yards beyond the frozen model (not supported)

**MEASURE MOVED:** D5(b) NFL +1 index entry, stage interpreted (not applied). Charter §5: no class VERIFIED; QB time-to-throw FAILED on level; the rest cannot be graded (null priors). Source: `12_EXPLORATORY/nfl_engine/coverage_gap/results/part_b_verdict.json`, Part A verdict JSON, TO_MUSE.md GRADE entry.

**Stage per factor:** N20 man/zone x QB EPA response: interpreted. N21 pressure/blitz x QB response: interpreted. Neither reached applied: the test was a residual against the frozen passyds_strike_v1, not against a Kalshi price.

**Numbers:** split-half at six games, 2018-25 (n=256 team-seasons): man 0.79, 5+ rushers 0.64, pressure 0.31. Cross on held-out gameday >= 2024-01-01 (1,060 QB-games, 559 games): d_man -2.6 yds/sd [-7.2, +1.5]; d_press -0.3 [-4.1, +3.7]; residual sd ~80 yds, so effects above ~4-7 yds/sd are ruled out.

**t4-mlb deploy decision:** #305 post-merge run 39549342332 was cancelled by the concurrency group; the PR touched only `12_EXPLORATORY` and docs, so no t4-mlb impact. #307 post-merge run 39550671806 was still in progress at close; the PR touched only `12_EXPLORATORY`, so the expected decision is no impact. The Deploy job summary for it was NOT read; the next session should confirm.

**Operator decisions:** none required. For information: Muse's 2023-25 coverage/pressure values are null, so grading that class needs a play-level 2026 source (TO_MUSE R-014) or prior-season values with definitions. GG-730: no 2026 participation file exists. League man rate swings .41/.48/.31 over 2023/24/25 (source vintage), flagged to Muse.

**Not done:** governance Steps 1-4 and Q1-Q7 were not run in detail (claim + isolation only). Pre-game bet placement and the mid-game design questions are in the index entry.
