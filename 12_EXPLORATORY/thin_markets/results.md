# W80.1 — Where the retail flow is: efficiency + fillability table (2025-and-earlier only)

Tool: `efficiency.py` (rules fixed in its docstring, unchanged this block except a timestamp-parse fix for 5-digit fractions). Source: the W78.2/W79.2 sampled store (markets closed before 2026-08-01 only; 2026-season rows untouched). Bootstrap over events, B=1000, seed 20261016. Run 2026-10-20. Depth columns join the live capture (Part A) and are **in-game**, not pre-kickoff: see limits.

## Table (ranked thinnest first; full CIs in `results_table.md`, raw numbers in `results.json`)
| Family | mkts / events | spread ¢ [CI] | fillable-hour share [CI] | OI at ko (median) | late move vs placebo | Part A in-game P(side ≥10 @2¢), n snaps |
|---|---|---|---|---|---|---|
| KXNFL1HSPREAD | 5 / 2 | 25.0 [18.5, 25.0] | 0.26 [0.15, 0.33] | 562 | 0.005 vs 0.000 | 75%, 195 |
| KXNFLTEAMTOTAL | 24 / 19 | 9.5 [6.5, 12.0] | 0.24 [0.14, 0.36] | 2,885 | 0.005 vs 0.000 | 58%, 139 |
| KXNFL1HTOTAL | 2 / 1 | 8.5 [8.5, 8.5] | 0.20 (n=1 event) | 2,541 | 0.000 vs 0.000 | 84%, 130 |
| KXNFLRECYDS | 47 / 41 | 6.5 [6.0, 7.0] | 0.11 [0.06, 0.15] | 165 | 0.005 vs 0.000 | 53%, 1,210 |
| KXNFLRSHYDS | 51 / 49 | 6.0 [5.5, 8.0] | 0.19 [0.13, 0.26] | 840 | 0.000 vs 0.000 | 42%, 626 |
| KXNBAREB | 86 / 84 | 6.0 [4.0, 7.0] | 0.08 [0.06, 0.10] | 87 | 0.005 vs 0.000 | 60% (pre-game), 53 |
| KXNFLPASSYDS | 57 / 47 | 5.0 [5.0, 6.0] | 0.15 [0.09, 0.22] | 340 | 0.000 vs 0.000 | 71%, 238 |
| KXNBAPTS | 87 / 81 | 5.0 [4.0, 7.0] | 0.26 [0.21, 0.32] | 1,396 | **0.030 [0.015, 0.045] vs 0.000** | 86% (pre-game), 63 |
| KXNFLFIRSTTD | 35 / 31 | 5.0 [3.5, 6.0] | 0.17 [0.10, 0.25] | 774 | 0.000 vs 0.000 | 64%, 33 |
| KXNFLANYTD | 87 / 83 | 4.0 [4.0, 5.0] | 0.27 [0.22, 0.33] | 2,566 | 0.000 vs 0.000 | not captured |
| KXNBASPREAD | 90 / 83 | 3.0 [3.0, 4.0] | 0.33 [0.27, 0.38] | 3,145 | 0.015 vs 0.005 | 100% (pre-game), 37 |
| KXNBATOTAL | 87 / 84 | 3.0 [2.0, 4.0] | 0.30 [0.25, 0.35] | 2,558 | 0.020 vs 0.005 | 100% (pre-game), 29 |
| KXNFLTOTAL | 135 / 103 | 3.0 [2.0, 3.0] | 0.24 [0.19, 0.28] | 3,462 | 0.000 vs 0.000 | 75%, 118 |
| KXNFLSPREAD | 128 / 99 | 2.0 [2.0, 3.0] | 0.32 [0.26, 0.38] | 5,538 | 0.000 vs 0.000 | 85%, 156 |
| **KXNBAGAME (ML)** | 99 / 95 | **1.0 [1.0, 1.0]** | **0.96 [0.94, 0.98]** | 426,418 | 0.010 vs 0.000 | 100% (pre-game), 4 |
| KXNFLGAME (ML) | not in the 2025 sample | — | — | — | — | 96%, 26 (in-game) |

## What can and cannot be ranked
- **Clear:** game ML is in a different class from everything else. Spread 1¢ with a zero-width CI, 96% of hours fillable for a $1 flat stake, OI ~4e5. Every thinner family has spread ≥2¢, median hourly volume 0 (CI [0,0]), and fillable share 0.08–0.33.
- **Clear (within NFL props):** RECYDS (0.11), PASSYDS (0.15), RSHYDS (0.19) are the least fillable pre-game hours and have the widest spreads among families with real n (≥47 events). ANYTD and the game-level spread/total are the most fillable thin cells.
- **Cannot rank yet:** KXNFL1HSPREAD (2 events), KXNFL1HTOTAL (1 event), KXNFLTEAMTOTAL's report move ([0.000, 0.145], wide). KXNFLGAME is absent from the 2025 sample, so game ML for NFL is not compared; the NBA game ML stands in.
- **Price responsiveness:** only NBA families show late (lineup-window) moves separable from placebo (PTS 0.030 [0.015, 0.045]; spread/total 0.015–0.020 vs 0.005). NFL families show ~0 within 25 minutes of inactives and after the Friday report. Reading: either those books are very slow to update or are too illiquid to print a candle change. The data cannot tell the two apart.
- Ranking between mid-ranked families (ranks 4–10) overlaps in CI; treat 4–10 as one thin tier.

## F8 (non-QB starters out) pricing share per family
**Not computable.** The store has price history only; there is no injury/inactives feed joined to it, so the share of moves attributable to F8 events cannot be formed. The "late move vs placebo" column is the closest proxy (a lineup-window move). Registered as a data gap, not guessed.

## Part A depth join: limits (stated plainly)
- Depth is measured only by the live order-book capture (Kalshi keeps no historical book). The weekend books (n above) are **in-game** snapshots, not pre-kickoff, because the old capture windowed on `close_time`, which trails the game by ~45h (the `listed=0` defect fixed in PR #288). Pre-kickoff depth at 6h/2h/30min exists only as forward capture from 2026-10-20 00:51Z on, hourly, with n so far: NBA `>6h` only (GAME 4, SPREAD 37, TOTAL 29, PTS 63, REB 53, TEAMTOTAL 38). NFL pre-kickoff depth: n=0. The Part A questions on 6h/2h/30min movement are therefore **unanswered**, not estimated.
- Hourly cadence is too coarse for the 30-minute question; a separate cron line would be needed (not added this block).
- Capture caps 500 books/run; 743 were due at 00:51Z, a 243 backlog per run. Watch for it starving.
- In-game depth is a worst-or-different case for fillability than pre-game depth; use it only as an ordering of families, not as the pre-game floor.
