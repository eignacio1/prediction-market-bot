# H-MEAS-1 RESULT (W124.2): is the closing price a calibrated estimate of settlement, per family?

Pre-registered in `PREREG.md` (812143c, A1 addendum 1fa410e) before any settlement was joined to a close. Code: `run_meas1.py`, `fetch_starts.py`;
known-answer tests `tests/test_meas1.py`. Numbers: `results.json`, `tables.md`. Verdict population = W123's never-judged fit window + forward data after
2026-11-20T20:00Z; W123's held-out third is in `results.json` as DESCRIPTIVE only (no-re-read rule).

## Verdict
**Families LICENSED for CLV: 0 -> 1** of 50 family cells (sport x family). **30 UNDERPOWERED, 19 NOT LICENSED** (10 miscalibrated, 9 noise-limited).
- **LICENSED: MLB period F3 (first-3-innings) only**, and it is a thin license: 270 markets, 90 games, slope 0.90 [0.21, 1.67] (interval too wide to tell 1 from
  0.5), mean |gap| 0.002 on two merged buckets (n 50 and 220). No early/late stability read (fewer than 30 forward games). W123 held-out (descriptive) slope 1.35 [0.07, 2.42].
  MLB is idle until 2027, so this changes no live scoring. Read it as "passes the frozen rule", not as strong evidence.
- **NOT LICENSED, miscalibrated** (slope interval excludes 1, or gaps above the noise floor too): MLB|total_alt, NBA|moneyline, NBA|team_total, NBA|total_alt, NFL|team_total, NFL|total_alt, NHL|moneyline, NHL|spread_alt, NHL|team_total, NHL|total_alt.
- **NOT LICENSED, noise-limited** (slope interval holds 1, bucket gaps no larger than sampling noise would give, but not under half a round cost): MLB|period_f5, MLB|period_f5spread, MLB|period_f5total, MLB|period_f7, MLB|prop_hit, MLB|spread_alt, MLB|team_total, NBA|spread_alt, NFL|spread_alt. These
  are not shown to be miscalibrated; they need more games (see `games_needed_for_floor` in results.json).
- **UNDERPOWERED** (30): every `*_main` line (one market per game: 46-126 markets, below 200), every NBA / NHL / NFL prop family (26-27 games for NBA/NHL props, 11 for NFL), and MLB/NFL moneyline.
  Games needed per family are in `results.json` (`games_needed`).
- NHL moneyline (1.72 [1.21, 2.21]), NBA moneyline (1.26 [1.03, 1.47]) and NHL team total (1.10 [1.04, 1.16]) have slope intervals wholly above 1 (favourites win more than the
  close says, longshots less): the favourite-longshot signature, not a calibrated close. FLB column in the table is gap(low buckets) - gap(high buckets).
- Wording: NOT LICENSED means that family is scored on settlement for now; it is retested as games accrue. Nothing is closed.

## Variance ratio (settlement sd^2 / CLV sd^2 per contract = the effective-sample multiplier, if the family were licensed)
Computed on markets with a 6 h (or 24 h) snapshot; CLV here = close - snapshot. Median over families: 6 h 410x, 24 h 444x (range 6 h 102-2710).
Per family in the table. The multiplier is real arithmetic but only usable where the family is LICENSED: today that is MLB F3 (24 h ratio 613x; no 6 h snapshots in MLB).

## Second claim: our own orders (arm_order log on the Mac, ends 2026-11-18T20:23Z, A1)
1335 orders, 58 games. Settled gross per contract on CLV: slope 0.52 [-1.27, 2.11], intercept -0.006.
By the frozen rule the interval contains 1, so **PASS**, but it also contains 0 and is 3.4 wide: this is **uninformative**, not support. Mean CLV +0.0114
(sd 0.036) vs mean settled gross +0.0002 (sd 0.395); mean(settled - CLV) -0.0112 [-0.046, +0.024] contains 0 (descriptive).
Arms (n / games / mean CLV / mean settled): FADE 359/36/+0.008/+0.038; MODEL_FADE 213/23/+0.004/-0.125; MOMENTUM 340/35/+0.013/-0.009; RIDE 423/38/+0.016/+0.039.
Limit: no fill status in this log copy (filled-only line not run); orders are placed orders, not fills, so this is not demo-fill P&L. Data epoch: the log starts 2026-11-12, all post-epoch, all sides (0 rows excluded by the 11-06 rule).

## Table (verdict population)
| family | markets | games | slope [90%] | intercept | mean abs gap | half cost | noise floor | FLB | verdict | var ratio 6h | var ratio 24h |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MLB|moneyline | 190 | 95 | 0.67 [-0.12, 1.45] | +0.163 | 0.025 | 0.011 | 0.041 | +0.049 | UNDERPOWERED, needs +5 games | - | 312 |
| MLB|period_f3 | 270 | 90 | 0.90 [0.21, 1.67] | +0.031 | 0.002 | 0.013 | 0.017 | -0.008 | LICENSED | - | 613 |
| MLB|period_f5 | 285 | 95 | 0.89 [0.52, 1.25] | +0.036 | 0.018 | 0.010 | 0.030 | +0.026 | NOT LICENSED (noise_limited) | - | 424 |
| MLB|period_f5spread | 380 | 95 | 0.97 [0.49, 1.45] | -0.002 | 0.010 | 0.009 | 0.023 | +0.023 | NOT LICENSED (noise_limited) | - | 505 |
| MLB|period_f5total | 662 | 95 | 0.98 [0.86, 1.09] | +0.041 | 0.029 | 0.009 | 0.034 | +0.041 | NOT LICENSED (noise_limited) | - | 226 |
| MLB|period_f7 | 285 | 95 | 0.90 [0.63, 1.17] | +0.035 | 0.029 | 0.012 | 0.029 | +0.089 | NOT LICENSED (noise_limited) | - | 647 |
| MLB|prop_hit | 4648 | 95 | 0.98 [0.94, 1.01] | +0.020 | 0.013 | 0.011 | 0.010 | +0.019 | NOT LICENSED (noise_limited) | - | - |
| MLB|spread_alt | 475 | 95 | 1.04 [0.49, 1.53] | +0.009 | 0.020 | 0.009 | 0.024 | +0.017 | NOT LICENSED (noise_limited) | - | 444 |
| MLB|spread_main | 95 | 95 | 0.97 [-0.46, 2.28] | -0.008 | 0.021 | 0.011 | 0.040 | +0.000 | UNDERPOWERED, needs +105 games | - | 477 |
| MLB|team_total | 1330 | 95 | 1.03 [0.94, 1.11] | -0.007 | 0.016 | 0.009 | 0.024 | -0.039 | NOT LICENSED (noise_limited) | - | 243 |
| MLB|total_alt | 940 | 95 | 1.10 [1.00, 1.20] | -0.054 | 0.030 | 0.008 | 0.030 | -0.063 | NOT LICENSED (miscalibrated) | - | 233 |
| MLB|total_main | 95 | 95 | 1.67 [-1.02, 4.53] | -0.316 | 0.018 | 0.011 | 0.057 | -0.022 | UNDERPOWERED, needs +105 games | - | 216 |
| NBA|moneyline | 252 | 126 | 1.26 [1.03, 1.47] | -0.129 | 0.031 | 0.010 | 0.038 | -0.207 | NOT LICENSED (miscalibrated) | 317 | 86 |
| NBA|prop_2d | 271 | 26 | 0.98 [0.76, 1.18] | +0.001 | 0.003 | 0.010 | 0.024 | +0.012 | UNDERPOWERED, needs +4 games | 131 | - |
| NBA|prop_3d | 32 | 23 | 1.49 [-0.10, 2.49] | -0.016 | 0.020 | 0.007 | 0.041 | +0.000 | UNDERPOWERED, needs +121 games | 643 | - |
| NBA|prop_3pt | 1444 | 27 | 0.97 [0.92, 1.03] | +0.011 | 0.018 | 0.011 | 0.018 | +0.028 | UNDERPOWERED, needs +3 games | 487 | - |
| NBA|prop_ast | 1082 | 26 | 1.00 [0.95, 1.05] | +0.009 | 0.035 | 0.011 | 0.019 | +0.014 | UNDERPOWERED, needs +4 games | 222 | - |
| NBA|prop_pra | 962 | 26 | 0.90 [0.82, 0.98] | +0.016 | 0.030 | 0.014 | 0.022 | +0.097 | UNDERPOWERED, needs +4 games | 102 | - |
| NBA|prop_pts | 1297 | 26 | 0.93 [0.88, 0.98] | +0.013 | 0.030 | 0.011 | 0.019 | -0.007 | UNDERPOWERED, needs +4 games | 151 | - |
| NBA|prop_reb | 1417 | 26 | 1.03 [0.98, 1.08] | -0.004 | 0.019 | 0.011 | 0.020 | -0.047 | UNDERPOWERED, needs +4 games | 159 | - |
| NBA|prop_stl | 529 | 26 | 0.94 [0.83, 1.06] | -0.023 | 0.044 | 0.017 | 0.027 | +0.021 | UNDERPOWERED, needs +4 games | 360 | - |
| NBA|spread_alt | 4010 | 126 | 1.07 [0.96, 1.19] | -0.003 | 0.016 | 0.009 | 0.018 | -0.097 | NOT LICENSED (noise_limited) | 424 | 103 |
| NBA|spread_main | 126 | 126 | -2.34 [-7.93, 3.19] | +1.710 | 0.036 | 0.012 | 0.049 | +0.088 | UNDERPOWERED, needs +74 games | 286 | 116 |
| NBA|team_total | 4785 | 126 | 0.97 [0.91, 1.03] | -0.021 | 0.036 | 0.013 | 0.020 | +0.020 | NOT LICENSED (miscalibrated) | 350 | 124 |
| NBA|total_alt | 3528 | 126 | 0.96 [0.88, 1.03] | -0.027 | 0.049 | 0.009 | 0.026 | +0.034 | NOT LICENSED (miscalibrated) | 395 | 111 |
| NBA|total_main | 126 | 126 | 2.32 [-2.23, 6.70] | -0.730 | 0.066 | 0.012 | 0.050 | -0.124 | UNDERPOWERED, needs +74 games | 261 | 94 |
| NFL|moneyline | 92 | 46 | 0.83 [0.34, 1.27] | +0.086 | 0.065 | 0.010 | 0.053 | +0.130 | UNDERPOWERED, needs +54 games | - | 995 |
| NFL|prop_passatt | 66 | 11 | 0.92 [0.59, 1.27] | +0.115 | 0.077 | 0.011 | 0.074 | +0.073 | UNDERPOWERED, needs +23 games | - | 289 |
| NFL|prop_passcomp | 65 | 11 | 1.00 [0.70, 1.30] | +0.056 | 0.056 | 0.010 | 0.063 | -0.004 | UNDERPOWERED, needs +23 games | - | 699 |
| NFL|prop_passtds | 89 | 11 | 1.18 [1.01, 1.32] | -0.021 | 0.046 | 0.008 | 0.052 | -0.057 | UNDERPOWERED, needs +19 games | - | 668 |
| NFL|prop_passyds | 201 | 11 | 1.21 [1.07, 1.34] | -0.064 | 0.059 | 0.009 | 0.041 | -0.156 | UNDERPOWERED, needs +19 games | - | 553 |
| NFL|prop_rec | 909 | 11 | 0.97 [0.86, 1.07] | -0.005 | 0.017 | 0.009 | 0.021 | +0.054 | UNDERPOWERED, needs +19 games | - | 456 |
| NFL|prop_recyds | 1400 | 11 | 1.00 [0.86, 1.13] | -0.016 | 0.016 | 0.009 | 0.027 | -0.000 | UNDERPOWERED, needs +19 games | - | 424 |
| NFL|prop_rryds | 99 | 11 | 1.21 [0.82, 1.52] | -0.081 | 0.020 | 0.011 | 0.059 | -0.018 | UNDERPOWERED, needs +19 games | - | 246 |
| NFL|prop_rshatt | 105 | 11 | 1.18 [0.98, 1.38] | -0.115 | 0.033 | 0.010 | 0.055 | -0.065 | UNDERPOWERED, needs +19 games | - | 93 |
| NFL|prop_rshyds | 559 | 11 | 1.00 [0.82, 1.16] | -0.007 | 0.019 | 0.009 | 0.039 | +0.043 | UNDERPOWERED, needs +19 games | - | 168 |
| NFL|prop_td | 365 | 11 | 1.21 [0.97, 1.41] | -0.026 | 0.022 | 0.007 | 0.025 | -0.079 | UNDERPOWERED, needs +19 games | - | 779 |
| NFL|spread_alt | 1135 | 46 | 1.05 [0.77, 1.29] | -0.026 | 0.016 | 0.008 | 0.033 | -0.026 | NOT LICENSED (noise_limited) | - | 892 |
| NFL|spread_main | 46 | 46 | 3.74 [-1.53, 8.56] | -1.453 | 0.086 | 0.011 | 0.083 | +0.045 | UNDERPOWERED, needs +154 games | - | 555 |
| NFL|team_total | 1172 | 46 | 1.04 [0.99, 1.08] | +0.017 | 0.045 | 0.008 | 0.026 | -0.032 | NOT LICENSED (miscalibrated) | - | 718 |
| NFL|total_alt | 828 | 46 | 0.99 [0.89, 1.09] | +0.057 | 0.054 | 0.008 | 0.043 | -0.015 | NOT LICENSED (miscalibrated) | - | 662 |
| NFL|total_main | 46 | 46 | 0.00 [-9.78, 9.68] | +0.565 | 0.063 | 0.011 | 0.059 | +0.000 | UNDERPOWERED, needs +154 games | - | 406 |
| NHL|moneyline | 238 | 119 | 1.71 [1.21, 2.21] | -0.357 | 0.059 | 0.011 | 0.035 | -0.117 | NOT LICENSED (miscalibrated) | 1509 | 436 |
| NHL|prop_ast | 872 | 27 | 1.12 [0.96, 1.26] | -0.003 | 0.028 | 0.012 | 0.022 | -0.024 | UNDERPOWERED, needs +3 games | 1570 | - |
| NHL|prop_goal | 1194 | 27 | 0.98 [0.81, 1.16] | +0.027 | 0.024 | 0.008 | 0.015 | +0.005 | UNDERPOWERED, needs +3 games | 758 | - |
| NHL|spread_alt | 357 | 119 | 1.36 [0.91, 1.68] | -0.108 | 0.034 | 0.008 | 0.023 | -0.063 | NOT LICENSED (miscalibrated) | 2650 | 730 |
| NHL|spread_main | 119 | 119 | 2.15 [0.91, 3.44] | -0.423 | 0.001 | 0.011 | 0.034 | +0.000 | UNDERPOWERED, needs +81 games | 2710 | 742 |
| NHL|team_total | 1190 | 119 | 1.10 [1.04, 1.16] | -0.013 | 0.037 | 0.010 | 0.020 | -0.058 | NOT LICENSED (miscalibrated) | 1585 | 563 |
| NHL|total_alt | 882 | 119 | 1.02 [0.95, 1.08] | +0.024 | 0.037 | 0.008 | 0.024 | -0.024 | NOT LICENSED (miscalibrated) | 1909 | 773 |
| NHL|total_main | 119 | 119 | -0.27 [-2.29, 1.69] | +0.708 | 0.064 | 0.011 | 0.052 | +0.134 | UNDERPOWERED, needs +81 games | 1237 | 674 |

## What this changes
- CLV may be the primary outcome **only for LICENSED families** (MLB F3 now); everything else keeps settlement as the score. No test that waits on a CLV-primary design for NBA/NFL/NHL can start on this result.
- Noise-limited families (NBA alt spreads, team totals, MLB F5/F7 and team totals) are the cheapest to license next: they need more games, not a better model.
- Favourite-longshot bias is visible in NHL and NBA moneyline (slope > 1), which is what H-EDGE-1 also pointed at; it is a lead for the pot-of-gold and RIDE routing, not a finding about edge.
- Re-run (same code, same rule) at the next weekly look as forward games accrue; PREREG rule unchanged.

## Deviations and notes
- Start time = Kalshi milestone `start_date` (not `occurrence_datetime`, which is the expected end). First run dropped every NHL row because the milestone type is `hockey_match`;
  caught on reading the family list (no NHL rows), fixed the type filter and re-fetched before any verdict was read. Nothing else changed after the first pass.
- Bootstrap helper is local to `run_meas1.py` (124.1's `quant/inference.py` additions are not on main); swap when they land.
