# Session handoff W113.2 (2026-11-12)

**Status:** DONE and merged. **B-089:** NFL wired for Sunday. **PR:** #495 squash-merged as 9b3e25a, CI `test` green on the current head. **Box:** `deploy_truth_read` 2026-11-12T23:53Z shows box HEAD 6f40c9a7 (descends from 9b3e25a) = origin/main, all OK; t4-mlb runs box HEAD code (MLB idle, no restart needed).
**Result:** every NFL shadow row this weekend carries weather forecast, matchup, market-state and 26 split leaves. Dry call of `filter_supply.nfl_adapter` on the 14 week-10 games (2026-11-12): 14 of 14 return 31 filter keys, 26 of them `<entry>@total` / `<entry>@side`, `note=None`. Weather: indoor 3, calm 4, wet 2, unknown 5 (outside the forecast horizon or no capture yet; recorded as `unknown`, not dropped).

## MEASURE MOVED
- D6 layer 3 NFL: 0 to 13 routed cells (all 13 NFL routed cells receive the split leaves through the adapter; local and box code). D6 wired end to end stays 0 of 117 (layers 6 and 7 are still not joined; 113.1's).
- NFL index entries: 0 to 25 with split, rank vs history at the same games-played point, stability, matchup cross and market map; application scored for 13 of 25, pending for 12 (thin n).
- D5(b) NFL applied: 12 to 14 of 23 factors in `SEATS/nfl.toml` (N5 rush/pass split, N6 blitz/pressure moved aggregated to applied). The earlier "of 21" denominator was stale; the file has 23.
- D1 NFL: adds the point-in-time weather forecast, MatchupBook terms, and box / coverage / personnel / motion splits.
- Application result (`12_EXPLORATORY/granularity_index_nfl/leaf_scores.json`): 18,317 deduped 2026 shadow rows, 87 games (fit 60 earliest, test 27 latest), net after taker fee, game-clustered 90% bootstrap. 130 leaves, 88 thin, 21 routed and scored held out, 0 pass BH q=0.10. **Moneyline RIDE family held out +0.167 [+0.073, +0.258], n=81, 27 games** (W110.5 lead +0.134 [+0.017, +0.236]). Inside it the gain sits in the `neutral` leaves of every split (+0.11 to +0.22); no split localises it. The fit window routed moneyline leaves to FADE, which scored -0.15 to -0.23 held out: a time-regime flip. Verdict: hypothesis closed (EXP-W113.2-NFL-SPLITS-01, parked for R&D). The splits stay in the tree as routing leaves.

## Caveats
- The EXP-id above is mine; register it or rename it.
- Schedule `spread_line` / `total_line` in the snapshot are snapshot-time (mild look-ahead when scoring history). Market-state leaves are coarse buckets.
- Box / coverage / personnel splits use the 2025 prior-season percentile for 2026 games. 2026 participation is not published (404); route trees by alignment, motion direction, boundary side and pre-snap distances are paid-only: registered gaps.
- Thin n: 27 held-out games. Shadow rows are paper rows (GG-527). Cover-6 vs 3-WR set is thin (n=23 in 2025, stability false); built, not exported.
- Stability false for 7 entries: rush_success_vs_loaded_box, pass_success_allowed_vs_man, pass_success_allowed_cover6_vs_3wr, red_zone_td_rate, red_zone_td_rate_allowed, third_down_success_allowed, explosive_pass_rate_allowed.
- CI: main's `test_w109_3_props_shadow_install` was red (registry live after the approved install). PR #495 carries the minimal fix (accepts paused or live) and a regenerated `NFL_SEAT.md`. This unblocks PR #493 (113.1) once it rebases; GG-1898's stale-test part is closed by it.

## Window follow-ups
1. Refresh the NFL snapshots weekly: `scripts/nfl_build_snapshots.py` (committed CSVs in `decision_trees/filter_data/`, data through 2026-11-10); the box only gets them by main auto-deploy.
2. Re-look the 12 thin entries as rows accumulate; add the NHL-style box-side reader if GG-1898 asks for it.
3. Read `exp_output/NFL_WEATHER/forecast_captures.jsonl` on the box once Sunday's rows exist, to check live captures land with lead >= 12h.
4. No install in this block, so no operator approval is needed.

vision_pillar: DEPTH (D1, D5b, D6 layer 3); gap_measure: D6 layer 3 NFL, D5(b) NFL applied, index entries; gap_delta: layer 3 NFL 0 to 13 cells, D5(b) 12 to 14 of 23, entries 0 to 25 (13 scored). D6 wired unchanged at 0.
pattern_sweep: swept `src/ scripts/ tests/ deploy/ .claude/` for writes outside `safe_out` in `12_EXPLORATORY` (pandas `.rename` trips the isolation scanner; replaced with `set_axis`) and for realised-weather uses (`assert_priceable` refuses them); the NBA and NHL adapters already pass their own PIT checks.
surface_delta: 0 new crons or services. One new outbound HTTP dependency (Open-Meteo, 6s timeout) inside the existing `run_pregame_shadow` T2 cron, one capture file `exp_output/NFL_WEATHER/forecast_captures.jsonl`, `RUNTIME_REGISTRY.toml` `writes` updated.
directive_conflicts: (1) D-06 asks for machinery, not examples: built one generic Situation engine, the operator's loaded-box and cover-6 questions are two of 25 entries. (2) "Of 21" factors vs 23 in the toml: reported 23. (3) None with doctrine otherwise.
