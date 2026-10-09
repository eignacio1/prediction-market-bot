<!-- session-meta
task_id: T-772
tier: MICRO
timestamp: 2026-10-09T18:12:00Z
commit: 4101d7b
one_line_summary: W64.1 NFL QB-shrunk challenger beats frozen in backtest (Brier -0.0027, 6/7 seasons); PROPOSED pre-reg drafted, D3 0->1.
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D3, D1
gap_delta: D3 0 -> 1 (scripts/distance_to_optimum.py @ 4101d7b); D1 unchanged
-->

# SESSION HANDOFF — W64.1 NFL deep challenger (QB-shrunk) — 2026-10-09

**Status:** DONE (Parts A + B) | PRs #205, #209 merged, CI green
**Result:** challenger (frozen recipe + EB team rates + QB-shrunk EPA) beats frozen EXP-037 in backtest: Brier -0.0027, 99.375% CI [-0.0050, -0.0006], 6/7 seasons (2025 worse). Gain is all mechanism 1 (QB); EB does nothing. Neither model beats the 2025 Kalshi mid (n=182). Scoped to this feature set and 2019-2025.
**vision_pillar:** DEPTH
**gap_measure:** D3 (pre-registered challengers ready); D1 (nfl_pregame)
**gap_delta:** D3 0 -> 1 (`scripts/distance_to_optimum.py`, D3 line: "1 (nfl_pregame (team -> team+personnel): 1)"). D1 unchanged: nfl_pregame_v1 still "team" because the challenger is PROPOSED, not a live model; it moves only if the operator accepts and it ships.
**MEASURE MOVED:** yes, D3.
**t4-mlb restart:** Part A push: not_needed (no t4-mlb import changed). Part B is docs/12_EXPLORATORY only: expected not_needed.
**Operator decisions:** accept or reject `12_EXPLORATORY/NFL_QB_SHRUNK_CHALLENGER_PREREGISTRATION_2026-10-09.md` (PROPOSED). Judged n ~984 games (~3.6 seasons) vs frozen; market comparison cannot be judged at feasible n.
**Notes:** step-0 finding: VPS has NFL_FIRST_LOOK_EXPECTATIONS.md; 63.3's UNAVAILABLE was deploy timing. Next mechanism: injury-report QB-only (needs point-in-time snapshots). GG-548/549 not used.

**Strategic Decisions This Session:** None (pre-registration is PROPOSED, awaiting operator).
**One thing pending:** operator accepts/rejects the PROPOSED pre-reg.
**Resume:** read 12_EXPLORATORY/W64_1_nfl_qb_challenger_results.md.
