<!-- session-meta
task_id: B-120 (W128.3)
tier: STANDARD
timestamp: 2026-11-25T07:00:00Z
commit: 8dbcab7
one_line_summary: W128.3 NFL play-level personnel x coverage crosses: 74 judged rows, 0 arms earned, routed to ride / no bet (proxy prices).
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D5(b) NFL
gap_delta: 3 play-level crosses (N24-N26) none -> applied (tested null); stages before 15 applied / 5 interpreted / 2 aggregated / 1 none, after 18 / 5 / 2 / 1 (12_EXPLORATORY/nfl_playlevel/RESULT.md @ 8dbcab7)
pattern_sweep: exploratory writes not via safe_out (to_csv inside safe_out(...).write_text trips test_exploratory_isolation) -> routed the path through safe_out in part_a.py; generated NFL_SEAT.md regenerated via scripts/render_seat.py; PIT test dates collided with game day -> fixed in the test
surface_delta: 0 (one default-off candidate key nfl_playlevel, no cron or service)
directive_conflicts: none
-->
# W128.3 handoff - NFL play-level personnel and coverage crosses

**Result.** Part A aggregated FTN charting and participation per team-game, point-in-time (trailing 17 games, min 6, strictly before game day).
PREREG committed (7e4ceee) before any outcome join. Three crosses: X1 personnel x shell, X2 motion x man, X3 EPA-vs-two-high x shell,
as 2x2 leaves on team totals, alternate spreads, alternate totals. Fit 2020-2024 (X2 2023-2024), judged on 2025 REG, 2026 descriptive.
118 rows, 74 judged, 44 not judged (n below 40), 0 fit-routed, BH q 0.10 family 0, **0 arms earned**. Raw net above zero in 14 of 74, none with an interval above zero.
Best raw row: X1 team total hi_lo wing FADE +0.075, interval -0.013 to +0.162, n 67. Routed to ride / no bet in every judged leaf.
Hypothesis closed (EXP-NFLPLAYLEVEL-001, parked for R&D). Registry row added in HYPOTHESIS_DOCTRINE.md.

**MEASURE MOVED.** D5(b) NFL: seat stages before 15 applied / 5 interpreted / 2 aggregated / 1 none; after 18 / 5 / 2 / 1
(N24 X1, N25 X2, N26 X3 added as applied: tested splits scored per leaf, null). Source: SEATS/nfl.toml, NFL_SEAT.md.

**Built.** `filters/nfl_playlevel.py` (leaf rules, PITViolation guard), candidate `nfl_playlevel` in `shadow_route.CANDIDATES`
behind `PM_CANDIDATE_ARMS` plus `PM_NFL_PLAYLEVEL` (default off). Tag only: orders follow v1, `kelly_fraction` untouched.
Tests: `tests/test_w128_3_nfl_playlevel.py`; precheck and isolation tests green.

**Caveats.**
- Prices are board_v2 proxies anchored to closing lines, not tradable quotes. Reopen on real Kalshi ladder quotes.
- 2026 personnel and coverage are `carried` from earlier seasons (participation is not served for 2026). 48 rows reach n >= 40 in 2026; descriptive only.
- X2 has a two-season fit (FTN from 2022) and is thin.
- No caller supplies leaves to the NFL candidates yet, so shadow rows carry no playlevel leaves (same as nfl_splits).
- Existing defect, not fixed (Hard Rule 11): `12_EXPLORATORY/nfl_splits/run_splits.py` has `_fence` imports before `from __future__`, a SyntaxError on import. Needs a GG/T number from the gap window.

**operator decisions.** Optional: approve `PM_NFL_PLAYLEVEL=on` on the box so shadow rows tag the leaves. Nothing was run on the box.
No real-capital, pre-registration, or install decision is open from this block.
