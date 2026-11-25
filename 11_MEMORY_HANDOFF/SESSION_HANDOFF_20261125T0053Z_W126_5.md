# Session handoff W126.5 — NFL factors as tree splits on team totals and alternate lines (B-013)
**Last reviewed:** 2026-11-24 · branch session/20261125T002552Z-w126-5-nfl-splits

Rules read: first line of COMMON_RULES_W126.md = "# Wave 126 common rules".

## Result
- EXP-NFLSPLITS-001 (PREREG committed 1222250 before any outcome join; section 8 operational definitions 0a7e3b4, also before the join).
- Fit 2019-2024, judged 2025 REG, nflverse. 1,871 games, 37,420 bets. **Proxy prices** (board_v2 anchored to consensus, earlier seasons only); there is no Kalshi history for these series before 2026.
- 156 split x leaf x arm rows; 94 judged (n >= 40 games); 62 not judged for n. BH family 0: no leaf had a fit-shrunk 90% lower bound above 0, so every leaf routed to ride / no bet at fit.
- Arms earned 0. Raw 2025 net > 0 in 14 of 94 judged rows; none with an interval above 0. Best: officials AS ref_mid wing FADE +0.041 (lo -0.071, n 45).
- Verdict: ride / no bet in every judged leaf. Hypothesis closed (EXP-NFLSPLITS-001, parked for R&D). No cell, market or arm closes.
- 2026 archive look NOT produced (scan returned no usable settled ladder rows). No 2026 number is claimed.
- **2026 shadow rows "from this commit forward" do not exist yet.** The forward look in PREREG s3 is unread.

## Built (Part B)
- `decision_trees/filters/nfl_splits.py` (leaf rules, point-in-time asserts); `shadow_route.py` candidate `nfl_splits`, behind `PM_NFL_SPLITS` (default off), tags rows `split_leaves`, `split_applied=False`. The arm is still router v2's.
- `tests/test_w126_5_nfl_splits.py` (5 tests). Isolation and shadow_route tests pass.

## MEASURE MOVED (D5(b) NFL, source RESULT.md)
- Splits tested to a verdict (applied, routed to ride / no bet): qb, rest, officials, weather, matchup (5 of 5 judged >= 1 leaf).
- Seat file: only N12 (officials) moved aggregated -> applied. N3, N4, N14 / N22, N23 were already applied; unchanged. N15, N16 untouched.
- Registry: EXP-NFLSPLITS-001 row added to HYPOTHESIS_DOCTRINE.md.

## Activation proposal (dated 2026-11-24, needs operator approval, nothing run)
Set `PM_NFL_SPLITS=on` on the box so NFL shadow rows carry the leaves for the forward look; read the forward look only after games_needed is met.
Hard Rule 14 surface check: adds zero crons / services / RUNTIME_REGISTRY entries; one default-off env flag; health signals not touched by this block.

directive_conflicts: none found in OPERATOR_DIRECTIVES.md for this block.
pattern_sweep: exploratory writes go through `safe_out` (isolation test caught two files; swept src/ scripts/ tests/ 12_EXPLORATORY/nfl_splits; no other unrouted writes). Proxy-price caveat restated in PREREG, RESULT and registry.
surface_delta: +0 cron, +0 service, +1 default-off candidate key (`nfl_splits`).
Not touched: ROLLING_BACKLOG.json; no installs.
