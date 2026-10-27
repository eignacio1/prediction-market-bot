# W89.3 — Which factors does the line not price? (Part A, NFL) — EXPLORATORY

Purpose (Hard Rule 12): DEPTH, D5(b). Close is the target, never an input. No outcome used to set any weight or threshold.
Method: W77.2 regression close = a + b0·engine + b·term (terms are the W77.2 rolling-origin out-of-sample per-game terms, test seasons 2020–2025, N=1,612 games, F8 populated on 1,436), game-clustered bootstrap B=2000 (seed 20261027), moneyline share = b/b0 on the logit scale. Unpriced size = (1 − b_hi)·SD(term)·slope at 1 SD of the term (b_hi = upper CI, i.e. the most generous bound for "priced"). Fee = 0.07·0.25 = 0.0175/contract (upper schedule bound). BH q=0.05 across 6 tests, unidentified terms (CI wider than 1.0) get p=1.
Known-answer check: simulated true share 0.60 → recovered 0.61 [0.57, 0.65] (tests/test_unpriced_screen.py).
Data: `screen_nfl.json`.

| Factor (seat) | Family | share priced b [95% CI] | unpriced prob @1 SD (point / b_hi) | identified | BH q.05 | clears fee |
|---|---|---|---|---|---|---|
| F8 availability (N10) | total | 0.33 [0.15, 0.51] | 0.018 / 0.013 | yes | yes | **no** (0.013 < 0.0175) |
| F8 availability (N10) | spread | 0.67 [0.46, 0.87] | 0.009 / 0.004 | yes | yes | no |
| F5/F6 coverage×personnel (N7/N8) | spread | −0.24 [−1.17, 0.69] | 0.006 / 0.002 | **no** | no | no |
| F5/F6 | moneyline | −0.16 [−1.28, 0.95] | 0.006 / 0.0003 | **no** | no | no |
| F8 | moneyline | 0.84 [0.58, 1.10] | 0.004 / 0.000 | yes | no (CI spans 1) | no |
| F5/F6 | total | 0.25 [−0.55, 1.05] | 0.004 / 0.000 | **no** | no | no |

Reading:
- **Share priced measured for 2 of the 21 NFL factors (F8, F5/F6) in 6 cells; F8 is identified in all three families, F5/F6 in none.** (D5(b) measured-share count 1 → 2 factor classes; N7/N8 move from "unidentified, stated" to a screened row.)
- **Zero factors clear fee + measured error.** The most unpriced cell, F8 on the total, leaves ≈1.3 points of probability at one SD of the term against a 1.75-point fee. This reproduces W85.1 (EXP-041: 0 of 18,479 strikes clear) from an independent code path, so Part B for F8 would repeat a result already on file; it is not rerun.
- Per-season b for F8 swings (spread 0.22–1.19, total −0.22–0.71): the "partly unpriced" reading is not stable season to season. Rolling single-season intervals were not computed.
- Moneyline F8 is ~fully priced (0.84, CI spans 1).

## Not done (named, with reason)
- **N13 venue / N14 weather (interpreted):** the totals study (`20261011_nfl_totals_venue_weather`) exists but has no per-game points term out of sample; deriving one is the next undone part (Part B candidate #1, free data: schedule roof/surface/temp/wind already in the schedule parquet).
- **NBA (B1–B11, P1–P4):** no stored game-level price history. The W88.3 pull of 1,228 NBA games was not saved, only aggregates. Rebuild with `12_EXPLORATORY/market_history/fetch_game_hourly.py` (public GETs) plus rebuilding pace/availability/lineup terms point-in-time: > the remaining time budget. Registered as a gap.
- **Part B (anchor + adjustment OOS for top 1–3):** not started. For NFL the top candidate (F8) is already settled by EXP-041, so the next undone part is weather/venue then NBA.
- Granularity-index five parts: the split, rank-vs-history, matchup cross and market map exist for F8 and F5/F6 only through the terms used; application is the price-anchored test above. Not extended to other factors.

Stage per factor (ADR-0075): N7/N8/N10 applied (now with share priced measured); N13/N14 interpreted; all other factors unchanged (no term to screen).

Operator line: **pre-register one of these, or keep building** — recommendation: keep building. Nothing here clears the fee; the next lever is a point-in-time weather/venue term and an NBA price history, not a pre-registration.
