# W103.2 (B-045) — overreaction and regimes in Kalshi prices

Status: pre-registration pushed (commit 2218a77, 2026-11-06 00:56Z) BEFORE any forward price was looked at; results below. Descriptive and gross of spread/fees. No cell opened, no order, no claim of trading edge.

## Pre-registration (frozen when this commit is pushed)

Data: `yes_mid` snapshots from `exp_output/PRICE_ARCHIVE` (see INVENTORY.md). Family = `series_ticker` (23). Cluster = `event_ticker` (one game).

1. **Step move** = change in `yes_mid` of one market between consecutive snapshots, kept only when the gap is <= 30 minutes (cadence is 20; a longer gap is an outage).
2. **sigma_f** = root-mean-square of ALL step moves of the family (pooled, mean not removed). **Big move = |step move| > k * sigma_f with k = 3.** k is fixed here, before outcomes; no other k is tried or reported as a result. (A k = 2 and k = 4 sensitivity may be shown afterwards labelled "sensitivity, not the finding".)
3. A move counts only if the market's price BEFORE the move was in [0.05, 0.95] (a market near its bounds cannot revert by construction).
4. **Refractory:** after an accepted event on a market, further big moves on that market within the next 60 minutes are skipped (overlapping windows would count one episode twice).
5. **Reversion at horizon h** = -sign(move) * (price at h - price after the move). **Family statistic R_h = sum(reversion) / sum(|move|)** (ratio of sums; 0.4 = 40% of the big moves was given back; negative = the price kept going). Horizons: **next snapshot (20 min +/- 5), 60 min (+/- 10), and the settlement proxy** (last snapshot, only if <=0.03 or >=0.97). No interpolation; an event without a snapshot at the horizon drops out of that horizon only.
6. **Interval and p:** game-clustered bootstrap (whole games resampled, 2,000 draws, seed 20261105), 95% percentile interval, two-sided bootstrap p. **n_events and n_games stated for every cell; a cell with < 15 games is FLAGGED "interval undercovers", not read.**
7. **PRIMARY test = R at 60 minutes, per family, with Holm (family-wise 0.05) and Benjamini-Hochberg (q = 0.10) over all families with >= 15 games** using `quant/multiplicity.py` (the MULTIPLICITY_LEDGER method). The 20-minute and settlement-proxy horizons, the pre-game (prior days) vs game-day split, and the tight-book split are SECONDARY and reported without adjustment, labelled as such.
8. **Pre-game vs in-play:** calendar proxy only (ticker date vs snapshot date; prior days vs game day) — see INVENTORY.md for why. "Game day" is NOT called in-play.
9. **Tight-book robustness:** repeat the primary with events whose `half_spread` <= 0.01 at the event snapshot, to see whether reversion is bid-ask bounce.
10. **Regime:** per market-hour, label **jumpy** if the hour holds >= 1 big move (same k, sigma_f), **calm** otherwise; hours with < 2 step moves are unlabelled. Stability = P(jumpy next hour | jumpy now) vs P(jumpy next hour | calm now). Reversion by regime uses the label of the hour BEFORE the event's hour (known at the time; the event's own hour is jumpy by construction).
11. **Fade/follow wording:** an R whose 95% interval excludes 0 on the correct side AND survives the primary Holm/BH is a "measured overshoot (fade)" or "measured drift (follow)"; anything else is "no distinguishable effect at this n". All results are gross of fees and spread; none is a trading edge claim, no cell is opened.
12. **MEASURE:** families with a measured overshoot / reversion ESTIMATE (R_60 with interval) X of N (N = 23). Estimate availability is separate from significance.

## Results (run 2026-11-06 on the compact extract of 3,375,442 snapshots; code: `analyze.py`, raw numbers: `results.json`)

**Deviations, stated honestly.** (1) The pre-registration says 23 series; the archive has **22** (I miscounted; no number depends on it — Holm/BH run over 22). (2) The 5/15-minute horizons are not measurable (20-min cadence); ~20 and ~60 min used as registered. (3) The price-in-[0.05,0.95] filter was applied after the refractory step, so an excluded move can still block the next 60 minutes on that market (slightly fewer events, no direction of bias). (4) "Game day" = snapshot UTC date equals the ticker date or the day after (evening games spill past UTC midnight); it is NOT in-play.

## Headline

- **Measured estimate of reversion at 60 min: 22 of 22 series** (every one has >= 27 games).
- **Holm-significant fades (3):** KXMLBHIT, KXNFLTEAMTOTAL, KXNHLTOTAL. **BH-only (2):** KXMLBF5SPREAD, KXNHLTEAMTOTAL. **No series shows a significant follow (drift).** The other 17 are indistinguishable from 0.
- **The sizes are not equal in meaning.** KXMLBHIT's R_60 = +0.08 shrinks to **+0.008** in the tight-book subset — most of it is bid-ask bounce in the mid, not a capturable overshoot. KXNFLTEAMTOTAL (+0.29; tight book +0.27) and KXNHLTOTAL (+0.51; tight +0.87, n = 65 events) survive that check and also show up on **prior days** (certainly pre-game: +0.50 and +0.50), so they are not an in-play artifact. They are the two candidates worth a pre-registered follow-up; neither is an edge claim (gross of cost; NHL has only 10 days).
- **Regime label available: yes** — calm/jumpy per market-hour, built and tested. It is persistent (P(jumpy next hour | jumpy now) 0.15–0.72 against 0.01–0.10 after a calm hour in every series) but, honestly, a jumpy hour mostly means "the game is on" — it separates live hours from idle hours more than it finds a subtle volatility state. Reversion differs by regime in the series that have enough jumpy events (KXNFLTEAMTOTAL +0.22 calm vs +0.69 jumpy; KXMLBHIT +0.07 vs +0.41; KXNFLGAME +0.14 vs −0.49), but most jumpy cells are thin or overlap zero, and these are unadjusted.
- **Settlement proxy (secondary):** many series show negative R to settle (KXNFLGAME −0.42, KXNBATOTAL −0.23, KXMLBGAME −0.20, KXMLBTOTAL −0.12). Read with care: only markets that had already resolved at their last snapshot qualify, which selects on outcome. It hints that prices underreact to the final outcome after a big move; it is not a finding.


### B1 — PRIMARY: R at 60 min, per series (22 series, all with >= 15 games)

R = share of the big move given back after ~60 min (+ = fade, - = follow). Gross of spread and fees. 95% game-clustered interval. † = fewer than 15 games, not read.

| Series | sigma (1-step) | R_60 [95% CI] (events / games) | p | Holm adj | BH q | verdict |
|---|---|---|---|---|---|---|
| KXMLBF3 | 0.070 | +0.06 [-0.07, +0.19] (104 ev / 77 g) | 0.360 | 1.000 | 0.793 | no distinguishable effect |
| KXMLBF5 | 0.073 | +0.07 [-0.03, +0.17] (378 ev / 241 g) | 0.199 | 1.000 | 0.547 | no distinguishable effect |
| KXMLBF5SPREAD | 0.074 | +0.09 [+0.02, +0.17] (664 ev / 327 g) | 0.020 | 0.380 | 0.088 | BH-only fade (q<=0.10) |
| KXMLBF5TOTAL | 0.073 | -0.01 [-0.06, +0.04] (1174 ev / 420 g) | 0.663 | 1.000 | 0.858 | no distinguishable effect |
| KXMLBF7 | 0.073 | +0.05 [-0.01, +0.11] (546 ev / 366 g) | 0.125 | 1.000 | 0.393 | no distinguishable effect |
| KXMLBGAME | 0.045 | +0.01 [-0.12, +0.14] (715 ev / 317 g) | 0.892 | 1.000 | 0.934 | no distinguishable effect |
| KXMLBHIT | 0.125 | +0.08 [+0.07, +0.09] (4171 ev / 554 g) | 0.001 | 0.022 | 0.007 | Holm-significant fade |
| KXMLBSPREAD | 0.075 | +0.01 [-0.09, +0.10] (912 ev / 286 g) | 0.869 | 1.000 | 0.934 | no distinguishable effect |
| KXMLBTEAMTOTAL | 0.070 | +0.02 [-0.02, +0.06] (2356 ev / 463 g) | 0.376 | 1.000 | 0.793 | no distinguishable effect |
| KXMLBTOTAL | 0.065 | +0.11 [+0.01, +0.21] (957 ev / 280 g) | 0.046 | 0.782 | 0.169 | no distinguishable effect |
| KXNBAGAME | 0.034 | +0.12 [-0.18, +0.47] (67 ev / 35 g) | 0.455 | 1.000 | 0.793 | no distinguishable effect |
| KXNBASPREAD | 0.050 | -0.04 [-0.40, +0.30] (369 ev / 27 g) | 0.767 | 1.000 | 0.934 | no distinguishable effect |
| KXNBATEAMTOTAL | 0.059 | +0.04 [-0.10, +0.18] (666 ev / 48 g) | 0.577 | 1.000 | 0.793 | no distinguishable effect |
| KXNBATOTAL | 0.057 | -0.04 [-0.18, +0.09] (617 ev / 44 g) | 0.559 | 1.000 | 0.793 | no distinguishable effect |
| KXNFLGAME | 0.029 | -0.12 [-0.42, +0.17] (195 ev / 80 g) | 0.424 | 1.000 | 0.793 | no distinguishable effect |
| KXNFLSPREAD | 0.038 | +0.02 [-0.17, +0.19] (1581 ev / 109 g) | 0.887 | 1.000 | 0.934 | no distinguishable effect |
| KXNFLTEAMTOTAL | 0.038 | +0.29 [+0.16, +0.41] (1429 ev / 120 g) | 0.001 | 0.022 | 0.007 | Holm-significant fade |
| KXNFLTOTAL | 0.041 | +0.03 [-0.08, +0.15] (1736 ev / 122 g) | 0.568 | 1.000 | 0.793 | no distinguishable effect |
| KXNHLGAME | 0.025 | +0.02 [-0.51, +0.50] (69 ev / 30 g) | 0.942 | 1.000 | 0.942 | no distinguishable effect |
| KXNHLSPREAD | 0.039 | +0.11 [-0.20, +0.42] (117 ev / 43 g) | 0.528 | 1.000 | 0.793 | no distinguishable effect |
| KXNHLTEAMTOTAL | 0.056 | +0.10 [+0.02, +0.19] (460 ev / 63 g) | 0.020 | 0.380 | 0.088 | BH-only fade (q<=0.10) |
| KXNHLTOTAL | 0.047 | +0.51 [+0.41, +0.59] (634 ev / 73 g) | 0.001 | 0.022 | 0.007 | Holm-significant fade |

### B2 — SECONDARY (unadjusted, read as hints): other horizons

| Series | R_20min | R_to_settle_proxy |
|---|---|---|
| KXMLBF3 | +0.04 [-0.04, +0.13] (392 ev / 247 g) | -0.03 [-0.09, +0.03] (701 ev / 346 g) |
| KXMLBF5 | +0.02 [-0.03, +0.08] (580 ev / 337 g) | -0.01 [-0.07, +0.06] (881 ev / 413 g) |
| KXMLBF5SPREAD | +0.06 [+0.01, +0.10] (813 ev / 399 g) | +0.03 [-0.03, +0.10] (1091 ev / 438 g) |
| KXMLBF5TOTAL | +0.02 [-0.01, +0.06] (1643 ev / 534 g) | -0.05 [-0.09, -0.02] (2426 ev / 538 g) |
| KXMLBF7 | +0.08 [+0.04, +0.13] (729 ev / 454 g) | -0.05 [-0.11, +0.01] (956 ev / 409 g) |
| KXMLBGAME | -0.01 [-0.08, +0.07] (806 ev / 341 g) | -0.20 [-0.32, -0.07] (890 ev / 330 g) |
| KXMLBHIT | +0.08 [+0.07, +0.10] (5602 ev / 610 g) | -0.02 [-0.02, -0.01] (7922 ev / 631 g) |
| KXMLBSPREAD | +0.02 [-0.02, +0.06] (1299 ev / 404 g) | -0.00 [-0.06, +0.06] (1588 ev / 442 g) |
| KXMLBTEAMTOTAL | +0.06 [+0.04, +0.08] (2950 ev / 566 g) | -0.07 [-0.10, -0.04] (4333 ev / 607 g) |
| KXMLBTOTAL | +0.03 [-0.02, +0.08] (1810 ev / 458 g) | -0.12 [-0.17, -0.08] (2595 ev / 535 g) |
| KXNBAGAME | -0.05 [-0.22, +0.11] (118 ev / 52 g) | +0.14 [-0.23, +0.54] (147 ev / 43 g) |
| KXNBASPREAD | -0.14 [-0.27, -0.02] (715 ev / 51 g) | -0.03 [-0.30, +0.28] (915 ev / 66 g) |
| KXNBATEAMTOTAL | -0.02 [-0.10, +0.08] (965 ev / 64 g) | -0.07 [-0.23, +0.08] (1093 ev / 59 g) |
| KXNBATOTAL | -0.04 [-0.15, +0.07] (789 ev / 60 g) | -0.22 [-0.39, -0.06] (1072 ev / 60 g) |
| KXNFLGAME | +0.03 [-0.13, +0.19] (271 ev / 95 g) | -0.42 [-0.78, -0.05] (247 ev / 64 g) |
| KXNFLSPREAD | +0.06 [-0.04, +0.16] (2289 ev / 121 g) | -0.04 [-0.24, +0.16] (2685 ev / 119 g) |
| KXNFLTEAMTOTAL | +0.12 [+0.06, +0.19] (2103 ev / 128 g) | +0.07 [-0.06, +0.20] (1888 ev / 128 g) |
| KXNFLTOTAL | +0.10 [+0.00, +0.19] (1946 ev / 130 g) | -0.09 [-0.22, +0.05] (2176 ev / 120 g) |
| KXNHLGAME | +0.03 [-0.17, +0.24] (127 ev / 55 g) | -0.30 [-0.82, +0.09] (82 ev / 26 g) |
| KXNHLSPREAD | +0.01 [-0.13, +0.16] (184 ev / 55 g) | +0.01 [-0.35, +0.31] (141 ev / 39 g) |
| KXNHLTEAMTOTAL | +0.18 [+0.11, +0.26] (446 ev / 65 g) | +0.06 [-0.05, +0.16] (537 ev / 58 g) |
| KXNHLTOTAL | +0.21 [+0.15, +0.27] (769 ev / 79 g) | +0.16 [-0.01, +0.31] (691 ev / 58 g) |

### B3 — SECONDARY: prior days (certainly pre-game) vs game day (pre-game + in-play mixed) vs tight book (half-spread <= 1c), R_60

| Series | prior days | game day | tight book |
|---|---|---|---|
| KXMLBF3 | +0.12 [+0.02, +0.22] (34 ev / 25 g) | +0.03 [-0.16, +0.20] (70 ev / 53 g) | -0.04 [-0.14, +0.03] (11 ev / 10 g) † |
| KXMLBF5 | +0.00 [-0.02, +0.03] (67 ev / 57 g) | +0.08 [-0.05, +0.21] (311 ev / 195 g) | +0.05 [-0.09, +0.19] (210 ev / 135 g) |
| KXMLBF5SPREAD | +0.15 [+0.11, +0.19] (219 ev / 120 g) | +0.07 [-0.03, +0.18] (445 ev / 222 g) | +0.08 [-0.08, +0.24] (198 ev / 126 g) |
| KXMLBF5TOTAL | -0.01 [-0.03, +0.01] (365 ev / 170 g) | -0.01 [-0.08, +0.06] (809 ev / 306 g) | +0.02 [-0.08, +0.12] (443 ev / 194 g) |
| KXMLBF7 | +0.04 [-0.02, +0.10] (106 ev / 101 g) | +0.06 [-0.02, +0.13] (438 ev / 306 g) | +0.09 [-0.05, +0.24] (99 ev / 81 g) |
| KXMLBGAME | +0.16 [-0.15, +0.54] (7 ev / 6 g) † | +0.01 [-0.11, +0.14] (706 ev / 314 g) | +0.03 [-0.10, +0.14] (680 ev / 305 g) |
| KXMLBHIT | -0.00 [-0.01, +0.00] (22 ev / 4 g) † | +0.08 [+0.07, +0.09] (4141 ev / 551 g) | +0.01 [+0.00, +0.01] (2899 ev / 544 g) |
| KXMLBSPREAD | -0.03 [-0.03, -0.02] (3 ev / 2 g) † | +0.01 [-0.09, +0.11] (906 ev / 283 g) | -0.03 [-0.14, +0.07] (687 ev / 252 g) |
| KXMLBTEAMTOTAL | +0.10 [+0.03, +0.17] (185 ev / 64 g) | +0.02 [-0.03, +0.06] (2166 ev / 435 g) | -0.03 [-0.07, +0.02] (1235 ev / 351 g) |
| KXMLBTOTAL | +0.01 [-0.00, +0.03] (35 ev / 22 g) | +0.11 [+0.00, +0.22] (922 ev / 265 g) | +0.06 [-0.06, +0.18] (758 ev / 232 g) |
| KXNBAGAME | -0.06 [-0.12, +0.01] (27 ev / 15 g) | +0.23 [-0.24, +0.78] (40 ev / 21 g) | +0.23 [-0.24, +0.75] (41 ev / 22 g) |
| KXNBASPREAD | +0.87 [+0.87, +0.87] (2 ev / 1 g) † | -0.04 [-0.39, +0.29] (367 ev / 26 g) | -0.08 [-0.61, +0.52] (237 ev / 20 g) |
| KXNBATEAMTOTAL | +0.15 [-0.09, +0.46] (115 ev / 9 g) † | +0.02 [-0.13, +0.17] (551 ev / 45 g) | -0.02 [-0.46, +0.42] (93 ev / 24 g) |
| KXNBATOTAL | -0.02 [-0.14, +0.18] (116 ev / 11 g) † | -0.04 [-0.22, +0.11] (501 ev / 36 g) | -0.05 [-0.40, +0.23] (253 ev / 24 g) |
| KXNFLGAME | -0.01 [-0.11, +0.11] (11 ev / 7 g) † | -0.13 [-0.44, +0.18] (184 ev / 76 g) | -0.12 [-0.44, +0.18] (187 ev / 79 g) |
| KXNFLSPREAD | +0.04 [-0.08, +0.20] (96 ev / 17 g) | +0.02 [-0.19, +0.21] (1485 ev / 99 g) | -0.00 [-0.23, +0.22] (1187 ev / 98 g) |
| KXNFLTEAMTOTAL | +0.50 [+0.33, +0.70] (285 ev / 54 g) | +0.23 [+0.08, +0.38] (1144 ev / 109 g) | +0.27 [+0.07, +0.48] (472 ev / 92 g) |
| KXNFLTOTAL | +0.01 [-0.06, +0.08] (710 ev / 77 g) | +0.05 [-0.15, +0.24] (1026 ev / 97 g) | +0.03 [-0.18, +0.24] (861 ev / 98 g) |
| KXNHLGAME | +0.38 [+0.07, +0.51] (7 ev / 4 g) † | -0.00 [-0.58, +0.50] (62 ev / 26 g) | +0.20 [-0.37, +0.73] (51 ev / 23 g) |
| KXNHLSPREAD | +0.05 [+0.00, +0.23] (22 ev / 7 g) † | +0.13 [-0.30, +0.56] (95 ev / 38 g) | +0.10 [-0.36, +0.60] (73 ev / 31 g) |
| KXNHLTEAMTOTAL | +0.08 [+0.03, +0.15] (352 ev / 55 g) | +0.17 [-0.12, +0.46] (108 ev / 38 g) | -0.43 [-1.37, -0.04] (5 ev / 4 g) † |
| KXNHLTOTAL | +0.50 [+0.44, +0.55] (537 ev / 66 g) | +0.56 [+0.12, +1.08] (97 ev / 23 g) | +0.87 [+0.23, +1.49] (65 ev / 22 g) |

### C1 — Regime label: stability and reversion by (lagged) regime

P(jumpy next hour | jumpy now) vs P(jumpy next hour | calm now); R_60 by the regime of the hour BEFORE the event.

| Series | P(j|j) | P(j|c) | R_60 after calm hour | R_60 after jumpy hour |
|---|---|---|---|---|
| KXMLBF3 | 0.17 | 0.05 | -0.04 [-0.26, +0.18] (55 ev / 44 g) | n/a |
| KXMLBF5 | 0.25 | 0.06 | +0.07 [-0.05, +0.20] (322 ev / 199 g) | +0.97 [+0.97, +0.97] (1 ev / 1 g) † |
| KXMLBF5SPREAD | 0.22 | 0.05 | +0.09 [-0.01, +0.19] (477 ev / 259 g) | +0.01 [-0.09, +0.08] (7 ev / 4 g) † |
| KXMLBF5TOTAL | 0.15 | 0.06 | -0.02 [-0.09, +0.05] (813 ev / 308 g) | +1.17 [+1.17, +1.17] (1 ev / 1 g) † |
| KXMLBF7 | 0.23 | 0.06 | +0.04 [-0.04, +0.12] (421 ev / 298 g) | +0.43 [+0.23, +0.65] (21 ev / 18 g) |
| KXMLBGAME | 0.48 | 0.03 | +0.01 [-0.10, +0.14] (608 ev / 303 g) | -0.05 [-0.49, +0.38] (84 ev / 41 g) |
| KXMLBHIT | 0.22 | 0.10 | +0.07 [+0.05, +0.08] (3875 ev / 537 g) | +0.41 [+0.31, +0.51] (115 ev / 76 g) |
| KXMLBSPREAD | 0.33 | 0.04 | +0.02 [-0.08, +0.13] (716 ev / 263 g) | +0.03 [-0.38, +0.44] (53 ev / 28 g) |
| KXMLBTEAMTOTAL | 0.25 | 0.05 | +0.01 [-0.04, +0.06] (1897 ev / 405 g) | +0.20 [+0.02, +0.44] (78 ev / 51 g) |
| KXMLBTOTAL | 0.48 | 0.04 | +0.10 [-0.02, +0.21] (797 ev / 239 g) | +0.23 [-0.44, +1.23] (25 ev / 14 g) † |
| KXNBAGAME | 0.56 | 0.03 | +0.17 [-0.20, +0.58] (51 ev / 27 g) | n/a |
| KXNBASPREAD | 0.52 | 0.04 | -0.06 [-0.59, +0.48] (263 ev / 21 g) | n/a |
| KXNBATEAMTOTAL | 0.33 | 0.05 | +0.13 [-0.08, +0.34] (356 ev / 35 g) | -0.41 [-0.44, -0.24] (5 ev / 2 g) † |
| KXNBATOTAL | 0.29 | 0.04 | -0.01 [-0.30, +0.25] (295 ev / 23 g) | n/a |
| KXNFLGAME | 0.72 | 0.01 | +0.14 [-0.27, +0.56] (87 ev / 47 g) | -0.49 [-0.98, +0.04] (56 ev / 29 g) |
| KXNFLSPREAD | 0.63 | 0.02 | +0.24 [-0.04, +0.54] (746 ev / 79 g) | -0.29 [-0.70, +0.11] (362 ev / 45 g) |
| KXNFLTEAMTOTAL | 0.63 | 0.02 | +0.22 [+0.05, +0.37] (687 ev / 102 g) | +0.69 [+0.40, +1.01] (236 ev / 79 g) |
| KXNFLTOTAL | 0.56 | 0.02 | +0.15 [-0.07, +0.38] (679 ev / 94 g) | +0.05 [-0.38, +0.51] (198 ev / 51 g) |
| KXNHLGAME | 0.58 | 0.01 | +0.12 [-0.52, +0.80] (50 ev / 26 g) | -0.43 [-1.21, -0.04] (13 ev / 7 g) † |
| KXNHLSPREAD | 0.47 | 0.02 | +0.22 [-0.14, +0.60] (75 ev / 37 g) | -0.44 [-1.95, +1.50] (8 ev / 6 g) † |
| KXNHLTEAMTOTAL | 0.32 | 0.05 | +0.08 [+0.00, +0.17] (352 ev / 61 g) | +0.22 [-0.23, +0.66] (31 ev / 21 g) |
| KXNHLTOTAL | 0.45 | 0.05 | +0.48 [+0.35, +0.61] (398 ev / 71 g) | +0.63 [+0.52, +0.75] (146 ev / 44 g) |

## When the line jumps, it usually ... (one paragraph per sport)

**MLB.** Across the ten MLB families, a big step in the line is, on average, mostly kept, not given back: at 60 minutes −1% to +11% of the move reverts and 8 of 10 families are indistinguishable from none. The one significant fade, player hits (KXMLBHIT, +8% over 4,171 moves in 554 games), is almost entirely bid-ask bounce (+0.8% on tight books), so it does not look capturable. After a hot hour, reversion is larger (+41% after a jumpy hour), but the thin-book caveat applies there too.

**NFL.** Team totals (KXNFLTEAMTOTAL) are the clearest overreacting line on the board: after a jump about 29% comes back within an hour (95% interval 16–41%, 120 games), 50% on prior days when no game is on, and it holds on tight books. Spreads, totals and moneylines show no distinguishable effect; the moneyline leans toward following (−12%, interval wide). Nothing here is net of cost.

**NBA.** Ten days and 27–52 games per family: every NBA family is indistinguishable from zero at 60 minutes (−4% to +12%, intervals wide). The one 20-minute reading that excludes zero (spread, −14%, a follow) is unadjusted and thin. Nothing to say yet beyond "lines neither clearly fade nor follow".

**NHL.** Also 10 days. Totals (KXNHLTOTAL) fade strongly: about half of a big jump returns within the hour (+51%, interval 41–59%, 73 games), also pre-game (+50%) and on tight books. Team totals (+10%), spreads (+11%) and moneylines (+2%) are weaker, the last two with intervals spanning zero. The strength and the short window say this must be re-measured as the season fills before anything is built on it.

## Limits (plain)

- Mid-quote reversion is not tradeable reversion; the tight-book column shows how much survives, none of it is net of fees.
- Pre-game vs in-play is not observable (no game-start time, status always `active`); "prior days" is the only certainly-pre-game slice and it is small for several MLB families.
- 20-minute cadence; one-step moves are 20-minute moves, so "big" is relative to a 20-minute scale.
- Cluster = game; the 10-day NBA/NHL samples span few distinct days, so game-level independence is optimistic.
- 22 families x several slices: only the 60-minute row is multiplicity-controlled.

## ADR-0075 stage
Aggregated (inventory) and interpreted (the fade/follow measurement, regime label). Not applied: no price, order or model reads these yet.
