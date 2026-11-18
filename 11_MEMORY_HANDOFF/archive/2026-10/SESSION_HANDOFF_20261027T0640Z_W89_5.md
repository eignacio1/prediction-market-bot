<!-- session-meta
task_id: T-1280
tier: STANDARD
timestamp: 2026-10-27T06:40:00Z
commit: 5b07cf0
one_line_summary: W89.5 joined 2,409 KXNBAPTS strikes to actual points and tested 22 PAM roles against the price; null, none survives BH
gg_touched: GG-1064 (superseded for this cross), GG-1280..GG-1283 registered
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D5(b) NBA PAM factors applied; NBA points props with settled actuals joined
gap_delta: D5(b) NBA PAM applied 0 -> 22 roles tested via a tested path (null); points props joined 0 -> 2,409 (1,820 usable first anchor, 1,640 last_pretip). Source 12_EXPLORATORY/nba_pam_mass_tier/results/w89/{join_summary,cross_first}.json
pattern_sweep: (1) write-shaped .replace() in 12_EXPLORATORY: grep found 0 other instances. (2) Kalshi candlestick window-400 cap: 9 other callers listed (12_EXPLORATORY/nfl_engine/granularity_index/part_b_apply.py, thin_markets/efficiency.py, scripts/{demo_fill_markout_collector,kalshi_history_build,thin_market_depth_capture,w63_3_fetch_candles,board_survey_*}.py) NOT audited for window span; registered GG-1284. Full CLAUDE.md Steps 1-4/Q1-Q7 not individually run; governance hook only (stub scan CLEAN, no duplicate GG ids). Deploy summary for #348 not read.
surface_delta: 0
-->

# SESSION_HANDOFF W89.5 — NBA PAM roles vs the points-prop price (DONE)

PR #348 merged as 5b07cf0, CI green. Exploratory only; nothing live.

## Strategic Decisions This Session
None.

## Result
- Part A: 2,409 settled strikes joined, 0 unmatched players, 0 result disagreements. Premise correction: markets mostly open pre-tip (median about 19h), so two anchors reported.
- Part B: PRF-1 223 strikes, mean(y-p) -0.009 [-0.092, +0.070]; PRF-4 597, +0.001 [-0.049, +0.052]. Out-of-sample Brier gain indistinguishable from 0. 22 roles, none survives BH q=0.10.
- Power: PRF-4 reaches a detectable n about mid-November 2026, PRF-1 about mid-December.
- Detail: `12_EXPLORATORY/nba_pam_mass_tier/results_W89.md`. Proposed seat rows are in that file, not in SEATS/nba.toml.

## Next
Refresh PAM roles to 2026-27 season-to-date (GG-1282); re-run `w89_join.py` and `w89_cross.py` mid-November.
