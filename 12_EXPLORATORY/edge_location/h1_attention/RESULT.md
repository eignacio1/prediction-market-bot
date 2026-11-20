# H1 Attention: RESULT (W123.1, 2026-11-20)
Pre-registration: `../HYPOTHESIS.md` section 3 + Addendum A1 (written before any outcome was joined). Code: `run_h1.py`, `fetch_settled.py`.
Data: `exp_output/PRICE_ARCHIVE` snapshots (2026-08-01 to 2026-11-20) joined to Kalshi public settled results (231,739 settled tickers fetched).

## Verdict: NOT SUPPORTED (on the 18 non-headline families that could be judged); 18 prop families UNDERPOWERED
- Clause 1 fails: of 18 judged non-headline families, none has a held-out net gap above zero with its 90% interval wholly above zero.
  The highest non-headline point estimate is MLB period_f7, +0.0031 [-0.0339, +0.0375].
  Nine non-headline intervals exclude zero, all on the negative side (a loss after costs). BH at q 0.10 over 30 judged families keeps one, MLB team_total, and it is negative.
- Clause 2, as A1 fixed it (signed, market-weighted): non-headline -0.0423 vs headline -0.0439. The difference is 0.0015, far inside the intervals. The literal absolute reading: non-headline 0.0424 vs headline 0.0613, so headline is larger.
- Pooled held-out net: headline -0.0227 [-0.0498, +0.0041] (266 games); non-headline -0.0361 [-0.0442, -0.0276] (257 games).
- Words: hypothesis closed for these 18 families (EXP H1, parked for R&D). It is a routing result: in these families, at a 10:00 ET snapshot, the taker's cost exceeds any settled-rate-minus-price gap the fit window found. No market or arm closes.

## What could not be judged (the least-watched markets, the core of H1)
- 18 player-prop families (NBA 8, NFL 10) are UNDERPOWERED: props are only in the archive for the last third of each season window (NBA 10-14 games, NFL 15 games), so the fit window is empty and A1's direction rule has nothing to fix. Not judged, no number read.
- NHL goal / assist props (4,533 and 2,552 settled markets) have no snapshot before 15:00Z on the game date at all (listed later), so they are outside A1's price rule. Same for most NBA prop markets (e.g. PTS 516 of 3,939 have a pre-start snapshot).
- n needed: at least 30 held-out games per family plus a fit window of comparable size. MLB hit (the one judged prop, 57 held-out games) needed about 77 games at one round cost of sd. The archive adds roughly one game-night of props per game date, so the date by which 30 held-out games exist is a forecast, not a measure; re-run H1 for props when 30 held-out games per family exist (a dated addendum, not a new test).
- B2 (Kalshi minus consensus): not testable; the NHL 2025-26 consensus file does not overlap the archive. NHL 2026-27 closes arrive from Monday; the only figure remains the W117.2 NHL moneyline gap of +0.16c (n 1,312).

## Part A / B table (primary; price = last snapshot at or before 15:00Z game date; held-out = last 1/3 by date per sport)
Net = directional (direction fixed on fit window), mean per contract after taker ask and fee 0.07 P (1-P). H headline, N non-headline. Cost = mean round cost (spread half + fee) on judged rows.
| sport | family | H/N | markets | games | judged n | judged games | held-out net | 90% CI | raw gap | cost | BH |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MLB | moneyline | H | 484 | 242 | 161 | 81 | +0.0336 | [-0.0533, +0.1189] | +0.0011 | 0.0226 | n |
| MLB | period_f3 | N | 648 | 218 | 209 | 71 | -0.0282 | [-0.0569, -0.0001] | -0.0043 | 0.0480 | n |
| MLB | period_f5 | N | 657 | 219 | 216 | 72 | -0.0403 | [-0.0886, +0.0115] | -0.0111 | 0.0464 | n |
| MLB | period_f5spread | N | 872 | 218 | 284 | 71 | -0.0372 | [-0.0819, +0.0089] | +0.0093 | 0.0495 | n |
| MLB | period_f5total | N | 1443 | 218 | 464 | 71 | -0.0633 | [-0.1248, -0.0033] | +0.0364 | 0.0413 | n |
| MLB | period_f7 | N | 635 | 213 | 207 | 69 | +0.0031 | [-0.0339, +0.0375] | +0.0001 | 0.0456 | n |
| MLB | prop_hit | N | 2303 | 168 | 897 | 57 | -0.0328 | [-0.0590, -0.0082] | -0.0027 | 0.0322 | n |
| MLB | spread_alt | N | 1095 | 219 | 355 | 71 | -0.0220 | [-0.0501, +0.0073] | -0.0013 | 0.0198 | n |
| MLB | spread_main | H | 219 | 219 | 71 | 71 | -0.0121 | [-0.1094, +0.0834] | +0.0107 | 0.0228 | n |
| MLB | team_total | N | 3050 | 219 | 987 | 71 | -0.0461 | [-0.0642, -0.0281] | +0.0288 | 0.0340 | Y |
| MLB | total_alt | N | 2173 | 219 | 697 | 71 | -0.0439 | [-0.0756, -0.0140] | +0.0447 | 0.0210 | n |
| MLB | total_main | H | 219 | 219 | 71 | 71 | +0.0030 | [-0.0971, +0.1043] | +0.0264 | 0.0234 | n |
| NBA | moneyline | H | 340 | 170 | 132 | 66 | -0.0468 | [-0.1389, +0.0462] | -0.0004 | 0.0197 | n |
| NBA | prop_2d | N | 94 | 10 | 0 | 0 | not judged | - | - | - | - |
| NBA | prop_3d | N | 19 | 9 | 0 | 0 | not judged | - | - | - | - |
| NBA | prop_3pt | N | 618 | 14 | 0 | 0 | not judged | - | - | - | - |
| NBA | prop_ast | N | 444 | 14 | 0 | 0 | not judged | - | - | - | - |
| NBA | prop_pra | N | 353 | 13 | 0 | 0 | not judged | - | - | - | - |
| NBA | prop_pts | N | 516 | 14 | 0 | 0 | not judged | - | - | - | - |
| NBA | prop_reb | N | 589 | 14 | 0 | 0 | not judged | - | - | - | - |
| NBA | prop_stl | N | 17 | 2 | 0 | 0 | not judged | - | - | - | - |
| NBA | spread_alt | N | 5261 | 169 | 2053 | 65 | -0.0241 | [-0.0603, +0.0137] | -0.0030 | 0.0212 | n |
| NBA | spread_main | H | 169 | 169 | 65 | 65 | -0.1261 | [-0.2297, -0.0315] | -0.1021 | 0.0240 | n |
| NBA | team_total | N | 6409 | 169 | 2470 | 65 | -0.0599 | [-0.1003, -0.0187] | +0.0318 | 0.0282 | n |
| NBA | total_alt | N | 4732 | 169 | 1820 | 65 | -0.0656 | [-0.1211, -0.0101] | +0.0426 | 0.0230 | n |
| NBA | total_main | H | 169 | 169 | 65 | 65 | -0.1061 | [-0.2129, -0.0118] | +0.0824 | 0.0237 | n |
| NFL | moneyline | H | 296 | 148 | 114 | 57 | -0.1052 | [-0.1915, -0.0126] | +0.0004 | 0.0200 | n |
| NFL | prop_passatt | N | 90 | 15 | 0 | 0 | not judged | - | - | - | - |
| NFL | prop_passcomp | N | 90 | 15 | 0 | 0 | not judged | - | - | - | - |
| NFL | prop_passtds | N | 125 | 15 | 0 | 0 | not judged | - | - | - | - |
| NFL | prop_passyds | N | 282 | 15 | 0 | 0 | not judged | - | - | - | - |
| NFL | prop_rec | N | 1162 | 15 | 0 | 0 | not judged | - | - | - | - |
| NFL | prop_recyds | N | 1807 | 15 | 0 | 0 | not judged | - | - | - | - |
| NFL | prop_rryds | N | 125 | 15 | 0 | 0 | not judged | - | - | - | - |
| NFL | prop_rshatt | N | 158 | 15 | 0 | 0 | not judged | - | - | - | - |
| NFL | prop_rshyds | N | 756 | 15 | 0 | 0 | not judged | - | - | - | - |
| NFL | prop_td | N | 482 | 15 | 0 | 0 | not judged | - | - | - | - |
| NFL | spread_alt | N | 3648 | 149 | 1389 | 57 | -0.0584 | [-0.0971, -0.0194] | +0.0411 | 0.0177 | n |
| NFL | spread_main | H | 149 | 149 | 57 | 57 | -0.0305 | [-0.1366, +0.0767] | +0.1166 | 0.0225 | n |
| NFL | team_total | N | 3819 | 149 | 1482 | 57 | -0.0194 | [-0.0489, +0.0092] | +0.0021 | 0.0223 | n |
| NFL | total_alt | N | 2682 | 149 | 1026 | 57 | -0.0279 | [-0.0838, +0.0311] | -0.0051 | 0.0182 | n |
| NFL | total_main | H | 149 | 149 | 57 | 57 | -0.1141 | [-0.2203, -0.0089] | +0.0442 | 0.0226 | n |
| NHL | moneyline | H | 320 | 160 | 120 | 60 | -0.0966 | [-0.2025, +0.0099] | +0.0000 | 0.0219 | n |
| NHL | spread_alt | N | 480 | 160 | 180 | 60 | -0.0667 | [-0.1220, -0.0122] | +0.0477 | 0.0175 | n |
| NHL | spread_main | H | 160 | 160 | 60 | 60 | +0.0562 | [-0.0460, +0.1584] | +0.0588 | 0.0214 | n |
| NHL | team_total | N | 1600 | 160 | 600 | 60 | -0.0308 | [-0.0612, +0.0029] | +0.0038 | 0.0220 | n |
| NHL | total_alt | N | 1194 | 160 | 461 | 60 | -0.0336 | [-0.0783, +0.0099] | -0.0067 | 0.0168 | n |
| NHL | total_main | H | 160 | 160 | 60 | 60 | -0.0056 | [-0.1180, +0.0949] | +0.0335 | 0.0227 | n |

Rows dropped: no settled result 40,530 (future games and unsettled), unusable quote 1,648. Split dates (first held-out day): {'NHL': '2026-11-12', 'NBA': '2026-11-11', 'MLB': '2026-09-25', 'NFL': '2026-10-25'}.
Sensitivity (snapshot nearest 24 h before the cut, never the verdict): coverage is NBA / NFL / NHL only (MLB has none), 13 families judged; none has a positive interval, every judged interval that excludes zero is negative, so it agrees with the primary.

## Which families lead
Closest to zero after cost: MLB period_f7 (+0.0031), MLB headline lines and NHL spread_main (+0.056, interval [-0.046, +0.158]); none excludes zero. Raw gaps are positive on alternate totals and team totals (MLB +0.045 / +0.029, NBA +0.043 / +0.032, NFL spread_alt +0.041, NHL spread_alt +0.048): the favorite-longshot shape exists in the settled rate, and the taker spread plus fee is larger than it. That is the lead for routing: those families are where a resting (maker) test, not a taker test, would be pointed, which is H4's question, not this one's.
