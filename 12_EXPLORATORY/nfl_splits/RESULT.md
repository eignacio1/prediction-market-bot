# EXP-NFLSPLITS-001 RESULT (W126.5)

**Last reviewed:** 2026-11-24. Source: `run_splits.py` -> `results.json` (this folder). PREREG.md was committed first (1222250, 0a7e3b4).
Fit 2019-2024, judged on 2025 regular season, **proxy prices** (board_v2 anchored to nflverse closing lines, earlier seasons only; not tradable quotes). 1871 games, 37420 bets. Cost = Kalshi fee + archive-median half-spread (AS 0.005, AT 0.01, TT 0.015). MIN_N = 40 games.

## Headline

- **156 split x leaf x arm rows; 94 judged on 2025; 62 not judged (n below MIN_N).**
- **Fit-routed rows (BH family): 0.** On 2019-2024 no leaf had an arm whose partially-pooled 90% lower bound cleared zero, so every leaf was routed to ride / no bet before 2025 was read.
- **Arms earned: 0.** Raw 2025 net is above zero in 14 of 94 judged rows, and its 90% interval excludes zero in 0.
- Verdict in routing words: these factors, as splits on team totals and alternate ladders at consensus-anchored prices, route to **ride / no bet in every judged leaf**. This closes only EXP-NFLSPLITS-001's hypothesis (parked for R&D); no cell, market or arm closes.

## Stage by split (D5(b) NFL, source: this file)

| Split | Rows | Judged rows (2025, n>=40) | Judged -> stage |
|---|---|---|---|
| qb | 24 | 18 | applied (tested, routed to ride / no bet) |
| rest | 36 | 14 | applied (tested, routed to ride / no bet) |
| officials | 36 | 26 | applied (tested, routed to ride / no bet) |
| weather | 24 | 10 | applied (tested, routed to ride / no bet) |
| matchup | 36 | 26 | applied (tested, routed to ride / no bet) |

Rule from PREREG s7: a split moves to `applied` iff at least one leaf was judged on the held-out set, whatever the sign.

## Every row

`fit_shrunk` = partially-pooled 2019-2024 net per bet (n games in fit). `net` interval = 90% game-clustered (CR1). `net@mean-spread` = net at the archive-mean half-spreads (sensitivity). Bootstrap p only for fit-routed rows (there are none).

| split | market | leaf | band | arm | fit n | fit_shrunk | 2025 games | gross | cost | net | 90% interval | net@mean-spread | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| matchup | AS | mu_high | mid | FADE | 272 | -0.0468 | 97 | +0.0219 | 0.0212 | +0.0006 | [-0.0311, +0.0324] | -0.0100 | routed to ride / no bet in this leaf |
| matchup | AS | mu_high | mid | RIDE | 272 | +0.0051 | 97 | -0.0219 | 0.0211 | -0.0429 | [-0.0746, -0.0112] | -0.0532 | routed to ride / no bet in this leaf |
| matchup | AS | mu_high | wing | FADE | 58 | -0.0468 | 20 | - | - | - | - | - | not judged: n below MIN_N (n=20) |
| matchup | AS | mu_high | wing | RIDE | 58 | +0.0051 | 20 | - | - | - | - | - | not judged: n below MIN_N (n=20) |
| matchup | AS | mu_low | mid | FADE | 272 | -0.0468 | 97 | -0.0077 | 0.0213 | -0.0290 | [-0.0583, +0.0002] | -0.0397 | routed to ride / no bet in this leaf |
| matchup | AS | mu_low | mid | RIDE | 272 | +0.0051 | 97 | +0.0077 | 0.0211 | -0.0134 | [-0.0426, +0.0158] | -0.0237 | routed to ride / no bet in this leaf |
| matchup | AS | mu_low | wing | FADE | 111 | -0.0468 | 50 | +0.0326 | 0.0175 | +0.0151 | [-0.0882, +0.1185] | +0.0042 | routed to ride / no bet in this leaf |
| matchup | AS | mu_low | wing | RIDE | 111 | +0.0051 | 50 | -0.0326 | 0.0171 | -0.0497 | [-0.1530, +0.0537] | -0.0597 | routed to ride / no bet in this leaf |
| matchup | AS | mu_mid | mid | FADE | 271 | -0.0468 | 78 | -0.0059 | 0.0212 | -0.0270 | [-0.0646, +0.0105] | -0.0377 | routed to ride / no bet in this leaf |
| matchup | AS | mu_mid | mid | RIDE | 271 | +0.0051 | 78 | +0.0059 | 0.0210 | -0.0152 | [-0.0527, +0.0224] | -0.0255 | routed to ride / no bet in this leaf |
| matchup | AS | mu_mid | wing | FADE | 128 | -0.0468 | 37 | - | - | - | - | - | not judged: n below MIN_N (n=37) |
| matchup | AS | mu_mid | wing | RIDE | 128 | +0.0051 | 37 | - | - | - | - | - | not judged: n below MIN_N (n=37) |
| matchup | AT | mu_high | mid | FADE | 272 | -0.0397 | 105 | +0.0044 | 0.0264 | -0.0220 | [-0.0508, +0.0069] | -0.0370 | routed to ride / no bet in this leaf |
| matchup | AT | mu_high | mid | RIDE | 272 | -0.0127 | 105 | -0.0044 | 0.0261 | -0.0305 | [-0.0594, -0.0016] | -0.0450 | routed to ride / no bet in this leaf |
| matchup | AT | mu_high | wing | FADE | 0 | - | 1 | - | - | - | - | - | not judged: n below MIN_N (n=1) |
| matchup | AT | mu_high | wing | RIDE | 0 | - | 1 | - | - | - | - | - | not judged: n below MIN_N (n=1) |
| matchup | AT | mu_low | mid | FADE | 272 | -0.0431 | 91 | +0.0033 | 0.0263 | -0.0230 | [-0.0527, +0.0067] | -0.0380 | routed to ride / no bet in this leaf |
| matchup | AT | mu_low | mid | RIDE | 272 | -0.0092 | 91 | -0.0033 | 0.0260 | -0.0293 | [-0.0589, +0.0004] | -0.0438 | routed to ride / no bet in this leaf |
| matchup | AT | mu_low | wing | FADE | 3 | - | 0 | - | - | - | - | - | not judged: n below MIN_N (n=0) |
| matchup | AT | mu_low | wing | RIDE | 3 | - | 0 | - | - | - | - | - | not judged: n below MIN_N (n=0) |
| matchup | AT | mu_mid | mid | FADE | 271 | -0.0323 | 76 | -0.0358 | 0.0263 | -0.0621 | [-0.1008, -0.0235] | -0.0771 | routed to ride / no bet in this leaf |
| matchup | AT | mu_mid | mid | RIDE | 271 | -0.0200 | 76 | +0.0358 | 0.0260 | +0.0098 | [-0.0288, +0.0484] | -0.0047 | routed to ride / no bet in this leaf |
| matchup | AT | mu_mid | wing | FADE | 2 | - | 0 | - | - | - | - | - | not judged: n below MIN_N (n=0) |
| matchup | AT | mu_mid | wing | RIDE | 2 | - | 0 | - | - | - | - | - | not judged: n below MIN_N (n=0) |
| matchup | TT | mu_high | mid | FADE | 485 | -0.0406 | 179 | +0.0038 | 0.0311 | -0.0273 | [-0.0499, -0.0048] | -0.0347 | routed to ride / no bet in this leaf |
| matchup | TT | mu_high | mid | RIDE | 485 | -0.0203 | 179 | -0.0038 | 0.0305 | -0.0343 | [-0.0568, -0.0118] | -0.0414 | routed to ride / no bet in this leaf |
| matchup | TT | mu_high | wing | FADE | 196 | -0.0406 | 82 | +0.0415 | 0.0281 | +0.0134 | [-0.0591, +0.0859] | +0.0060 | routed to ride / no bet in this leaf |
| matchup | TT | mu_high | wing | RIDE | 196 | -0.0203 | 82 | -0.0415 | 0.0270 | -0.0685 | [-0.1410, +0.0039] | -0.0754 | routed to ride / no bet in this leaf |
| matchup | TT | mu_low | mid | FADE | 468 | -0.0406 | 149 | +0.0048 | 0.0312 | -0.0264 | [-0.0515, -0.0012] | -0.0337 | routed to ride / no bet in this leaf |
| matchup | TT | mu_low | mid | RIDE | 468 | -0.0203 | 149 | -0.0048 | 0.0306 | -0.0355 | [-0.0606, -0.0103] | -0.0425 | routed to ride / no bet in this leaf |
| matchup | TT | mu_low | wing | FADE | 352 | -0.0406 | 113 | +0.0043 | 0.0279 | -0.0235 | [-0.0854, +0.0383] | -0.0310 | routed to ride / no bet in this leaf |
| matchup | TT | mu_low | wing | RIDE | 352 | -0.0203 | 113 | -0.0043 | 0.0267 | -0.0310 | [-0.0929, +0.0308] | -0.0379 | routed to ride / no bet in this leaf |
| matchup | TT | mu_mid | mid | FADE | 441 | -0.0406 | 152 | -0.0048 | 0.0311 | -0.0359 | [-0.0598, -0.0120] | -0.0432 | routed to ride / no bet in this leaf |
| matchup | TT | mu_mid | mid | RIDE | 441 | -0.0203 | 152 | +0.0048 | 0.0306 | -0.0258 | [-0.0497, -0.0019] | -0.0328 | routed to ride / no bet in this leaf |
| matchup | TT | mu_mid | wing | FADE | 270 | -0.0406 | 89 | -0.0503 | 0.0281 | -0.0784 | [-0.1429, -0.0139] | -0.0859 | routed to ride / no bet in this leaf |
| matchup | TT | mu_mid | wing | RIDE | 270 | -0.0203 | 89 | +0.0503 | 0.0270 | +0.0234 | [-0.0411, +0.0879] | +0.0165 | routed to ride / no bet in this leaf |
| officials | AS | ref_high | mid | FADE | 530 | -0.0375 | 109 | +0.0347 | 0.0213 | +0.0134 | [-0.0167, +0.0435] | +0.0027 | routed to ride / no bet in this leaf |
| officials | AS | ref_high | mid | RIDE | 530 | -0.0042 | 109 | -0.0347 | 0.0211 | -0.0558 | [-0.0859, -0.0257] | -0.0661 | routed to ride / no bet in this leaf |
| officials | AS | ref_high | wing | FADE | 173 | -0.0375 | 49 | -0.0063 | 0.0176 | -0.0239 | [-0.1234, +0.0755] | -0.0348 | routed to ride / no bet in this leaf |
| officials | AS | ref_high | wing | RIDE | 173 | -0.0042 | 49 | +0.0063 | 0.0172 | -0.0109 | [-0.1103, +0.0886] | -0.0210 | routed to ride / no bet in this leaf |
| officials | AS | ref_low | mid | FADE | 530 | -0.0375 | 42 | -0.0302 | 0.0211 | -0.0513 | [-0.0930, -0.0097] | -0.0620 | routed to ride / no bet in this leaf |
| officials | AS | ref_low | mid | RIDE | 530 | -0.0042 | 42 | +0.0302 | 0.0209 | +0.0093 | [-0.0323, +0.0509] | -0.0010 | routed to ride / no bet in this leaf |
| officials | AS | ref_low | wing | FADE | 178 | -0.0375 | 13 | - | - | - | - | - | not judged: n below MIN_N (n=13) |
| officials | AS | ref_low | wing | RIDE | 178 | -0.0042 | 13 | - | - | - | - | - | not judged: n below MIN_N (n=13) |
| officials | AS | ref_mid | mid | FADE | 530 | -0.0375 | 120 | -0.0121 | 0.0212 | -0.0333 | [-0.0622, -0.0043] | -0.0439 | routed to ride / no bet in this leaf |
| officials | AS | ref_mid | mid | RIDE | 530 | -0.0042 | 120 | +0.0121 | 0.0211 | -0.0090 | [-0.0379, +0.0199] | -0.0193 | routed to ride / no bet in this leaf |
| officials | AS | ref_mid | wing | FADE | 177 | -0.0375 | 45 | +0.0586 | 0.0176 | +0.0410 | [-0.0711, +0.1531] | +0.0301 | routed to ride / no bet in this leaf |
| officials | AS | ref_mid | wing | RIDE | 177 | -0.0042 | 45 | -0.0586 | 0.0172 | -0.0758 | [-0.1879, +0.0364] | -0.0859 | routed to ride / no bet in this leaf |
| officials | AT | ref_high | mid | FADE | 530 | -0.0284 | 109 | -0.0092 | 0.0263 | -0.0356 | [-0.0634, -0.0078] | -0.0506 | routed to ride / no bet in this leaf |
| officials | AT | ref_high | mid | RIDE | 530 | -0.0240 | 109 | +0.0092 | 0.0260 | -0.0168 | [-0.0446, +0.0110] | -0.0313 | routed to ride / no bet in this leaf |
| officials | AT | ref_high | wing | FADE | 4 | - | 0 | - | - | - | - | - | not judged: n below MIN_N (n=0) |
| officials | AT | ref_high | wing | RIDE | 4 | - | 0 | - | - | - | - | - | not judged: n below MIN_N (n=0) |
| officials | AT | ref_low | mid | FADE | 530 | -0.0422 | 42 | -0.0313 | 0.0263 | -0.0576 | [-0.1114, -0.0038] | -0.0726 | routed to ride / no bet in this leaf |
| officials | AT | ref_low | mid | RIDE | 530 | -0.0102 | 42 | +0.0313 | 0.0260 | +0.0053 | [-0.0485, +0.0591] | -0.0093 | routed to ride / no bet in this leaf |
| officials | AT | ref_low | wing | FADE | 6 | - | 0 | - | - | - | - | - | not judged: n below MIN_N (n=0) |
| officials | AT | ref_low | wing | RIDE | 6 | - | 0 | - | - | - | - | - | not judged: n below MIN_N (n=0) |
| officials | AT | ref_mid | mid | FADE | 530 | -0.0289 | 120 | +0.0029 | 0.0264 | -0.0235 | [-0.0511, +0.0042] | -0.0385 | routed to ride / no bet in this leaf |
| officials | AT | ref_mid | mid | RIDE | 530 | -0.0235 | 120 | -0.0029 | 0.0260 | -0.0289 | [-0.0565, -0.0013] | -0.0435 | routed to ride / no bet in this leaf |
| officials | AT | ref_mid | wing | FADE | 6 | - | 1 | - | - | - | - | - | not judged: n below MIN_N (n=1) |
| officials | AT | ref_mid | wing | RIDE | 6 | - | 1 | - | - | - | - | - | not judged: n below MIN_N (n=1) |
| officials | TT | ref_high | mid | FADE | 530 | -0.0370 | 109 | +0.0091 | 0.0311 | -0.0220 | [-0.0426, -0.0015] | -0.0293 | routed to ride / no bet in this leaf |
| officials | TT | ref_high | mid | RIDE | 530 | -0.0240 | 109 | -0.0091 | 0.0306 | -0.0397 | [-0.0602, -0.0192] | -0.0467 | routed to ride / no bet in this leaf |
| officials | TT | ref_high | wing | FADE | 438 | -0.0370 | 96 | -0.0403 | 0.0280 | -0.0684 | [-0.1279, -0.0088] | -0.0758 | routed to ride / no bet in this leaf |
| officials | TT | ref_high | wing | RIDE | 438 | -0.0240 | 96 | +0.0403 | 0.0269 | +0.0134 | [-0.0461, +0.0729] | +0.0065 | routed to ride / no bet in this leaf |
| officials | TT | ref_low | mid | FADE | 530 | -0.0370 | 42 | -0.0156 | 0.0311 | -0.0467 | [-0.0856, -0.0078] | -0.0540 | routed to ride / no bet in this leaf |
| officials | TT | ref_low | mid | RIDE | 530 | -0.0240 | 42 | +0.0156 | 0.0305 | -0.0149 | [-0.0538, +0.0240] | -0.0219 | routed to ride / no bet in this leaf |
| officials | TT | ref_low | wing | FADE | 421 | -0.0370 | 32 | - | - | - | - | - | not judged: n below MIN_N (n=32) |
| officials | TT | ref_low | wing | RIDE | 421 | -0.0240 | 32 | - | - | - | - | - | not judged: n below MIN_N (n=32) |
| officials | TT | ref_mid | mid | FADE | 530 | -0.0370 | 120 | +0.0017 | 0.0312 | -0.0295 | [-0.0509, -0.0080] | -0.0368 | routed to ride / no bet in this leaf |
| officials | TT | ref_mid | mid | RIDE | 530 | -0.0240 | 120 | -0.0017 | 0.0306 | -0.0323 | [-0.0537, -0.0108] | -0.0393 | routed to ride / no bet in this leaf |
| officials | TT | ref_mid | wing | FADE | 445 | -0.0370 | 104 | +0.0053 | 0.0280 | -0.0226 | [-0.0814, +0.0361] | -0.0301 | routed to ride / no bet in this leaf |
| officials | TT | ref_mid | wing | RIDE | 445 | -0.0240 | 104 | -0.0053 | 0.0268 | -0.0322 | [-0.0909, +0.0266] | -0.0391 | routed to ride / no bet in this leaf |
| qb | AS | any_new | mid | FADE | 375 | -0.0372 | 64 | +0.0142 | 0.0213 | -0.0071 | [-0.0493, +0.0350] | -0.0178 | routed to ride / no bet in this leaf |
| qb | AS | any_new | mid | RIDE | 375 | -0.0046 | 64 | -0.0142 | 0.0211 | -0.0353 | [-0.0774, +0.0068] | -0.0456 | routed to ride / no bet in this leaf |
| qb | AS | any_new | wing | FADE | 106 | -0.0372 | 31 | - | - | - | - | - | not judged: n below MIN_N (n=31) |
| qb | AS | any_new | wing | RIDE | 106 | -0.0046 | 31 | - | - | - | - | - | not judged: n below MIN_N (n=31) |
| qb | AS | none | mid | FADE | 1223 | -0.0372 | 208 | +0.0007 | 0.0212 | -0.0206 | [-0.0415, +0.0004] | -0.0312 | routed to ride / no bet in this leaf |
| qb | AS | none | mid | RIDE | 1223 | -0.0046 | 208 | -0.0007 | 0.0210 | -0.0217 | [-0.0427, -0.0008] | -0.0320 | routed to ride / no bet in this leaf |
| qb | AS | none | wing | FADE | 424 | -0.0372 | 76 | +0.0182 | 0.0176 | +0.0005 | [-0.0820, +0.0831] | -0.0103 | routed to ride / no bet in this leaf |
| qb | AS | none | wing | RIDE | 424 | -0.0046 | 76 | -0.0182 | 0.0173 | -0.0355 | [-0.1180, +0.0471] | -0.0455 | routed to ride / no bet in this leaf |
| qb | AT | any_new | mid | FADE | 375 | -0.0344 | 64 | -0.0187 | 0.0263 | -0.0450 | [-0.0832, -0.0068] | -0.0600 | routed to ride / no bet in this leaf |
| qb | AT | any_new | mid | RIDE | 375 | -0.0181 | 64 | +0.0187 | 0.0260 | -0.0072 | [-0.0454, +0.0310] | -0.0218 | routed to ride / no bet in this leaf |
| qb | AT | any_new | wing | FADE | 1 | - | 0 | - | - | - | - | - | not judged: n below MIN_N (n=0) |
| qb | AT | any_new | wing | RIDE | 1 | - | 0 | - | - | - | - | - | not judged: n below MIN_N (n=0) |
| qb | AT | none | mid | FADE | 1223 | -0.0344 | 208 | -0.0036 | 0.0264 | -0.0300 | [-0.0511, -0.0089] | -0.0450 | routed to ride / no bet in this leaf |
| qb | AT | none | mid | RIDE | 1223 | -0.0181 | 208 | +0.0036 | 0.0260 | -0.0224 | [-0.0435, -0.0013] | -0.0369 | routed to ride / no bet in this leaf |
| qb | AT | none | wing | FADE | 15 | - | 1 | - | - | - | - | - | not judged: n below MIN_N (n=1) |
| qb | AT | none | wing | RIDE | 15 | - | 1 | - | - | - | - | - | not judged: n below MIN_N (n=1) |
| qb | TT | qb_new | mid | FADE | 376 | -0.0375 | 64 | +0.0065 | 0.0312 | -0.0247 | [-0.0608, +0.0115] | -0.0320 | routed to ride / no bet in this leaf |
| qb | TT | qb_new | mid | RIDE | 376 | -0.0235 | 64 | -0.0065 | 0.0306 | -0.0372 | [-0.0733, -0.0010] | -0.0442 | routed to ride / no bet in this leaf |
| qb | TT | qb_new | wing | FADE | 265 | -0.0375 | 47 | +0.0338 | 0.0279 | +0.0059 | [-0.0886, +0.1003] | -0.0016 | routed to ride / no bet in this leaf |
| qb | TT | qb_new | wing | RIDE | 265 | -0.0235 | 47 | -0.0338 | 0.0268 | -0.0606 | [-0.1550, +0.0339] | -0.0675 | routed to ride / no bet in this leaf |
| qb | TT | qb_same | mid | FADE | 1547 | -0.0375 | 263 | +0.0005 | 0.0311 | -0.0306 | [-0.0455, -0.0158] | -0.0379 | routed to ride / no bet in this leaf |
| qb | TT | qb_same | mid | RIDE | 1547 | -0.0235 | 263 | -0.0005 | 0.0306 | -0.0311 | [-0.0459, -0.0162] | -0.0381 | routed to ride / no bet in this leaf |
| qb | TT | qb_same | wing | FADE | 1140 | -0.0375 | 200 | -0.0093 | 0.0280 | -0.0373 | [-0.0791, +0.0045] | -0.0448 | routed to ride / no bet in this leaf |
| qb | TT | qb_same | wing | RIDE | 1140 | -0.0235 | 200 | +0.0093 | 0.0269 | -0.0176 | [-0.0594, +0.0242] | -0.0245 | routed to ride / no bet in this leaf |
| rest | AS | away_rest_edge | mid | FADE | 176 | -0.0381 | 31 | - | - | - | - | - | not judged: n below MIN_N (n=31) |
| rest | AS | away_rest_edge | mid | RIDE | 176 | -0.0032 | 31 | - | - | - | - | - | not judged: n below MIN_N (n=31) |
| rest | AS | away_rest_edge | wing | FADE | 64 | -0.0385 | 14 | - | - | - | - | - | not judged: n below MIN_N (n=14) |
| rest | AS | away_rest_edge | wing | RIDE | 64 | -0.0018 | 14 | - | - | - | - | - | not judged: n below MIN_N (n=14) |
| rest | AS | even | mid | FADE | 1253 | -0.0372 | 214 | +0.0095 | 0.0212 | -0.0118 | [-0.0333, +0.0098] | -0.0224 | routed to ride / no bet in this leaf |
| rest | AS | even | mid | RIDE | 1253 | -0.0052 | 214 | -0.0095 | 0.0211 | -0.0305 | [-0.0521, -0.0090] | -0.0408 | routed to ride / no bet in this leaf |
| rest | AS | even | wing | FADE | 412 | -0.0381 | 85 | +0.0038 | 0.0176 | -0.0138 | [-0.0896, +0.0620] | -0.0247 | routed to ride / no bet in this leaf |
| rest | AS | even | wing | RIDE | 412 | -0.0023 | 85 | -0.0038 | 0.0172 | -0.0211 | [-0.0969, +0.0548] | -0.0312 | routed to ride / no bet in this leaf |
| rest | AS | home_rest_edge | mid | FADE | 170 | -0.0395 | 27 | - | - | - | - | - | not judged: n below MIN_N (n=27) |
| rest | AS | home_rest_edge | mid | RIDE | 170 | +0.0001 | 27 | - | - | - | - | - | not judged: n below MIN_N (n=27) |
| rest | AS | home_rest_edge | wing | FADE | 54 | -0.0391 | 8 | - | - | - | - | - | not judged: n below MIN_N (n=8) |
| rest | AS | home_rest_edge | wing | RIDE | 54 | -0.0002 | 8 | - | - | - | - | - | not judged: n below MIN_N (n=8) |
| rest | AT | away_rest_edge | mid | FADE | 176 | -0.0342 | 31 | - | - | - | - | - | not judged: n below MIN_N (n=31) |
| rest | AT | away_rest_edge | mid | RIDE | 176 | -0.0182 | 31 | - | - | - | - | - | not judged: n below MIN_N (n=31) |
| rest | AT | away_rest_edge | wing | FADE | 4 | - | 0 | - | - | - | - | - | not judged: n below MIN_N (n=0) |
| rest | AT | away_rest_edge | wing | RIDE | 4 | - | 0 | - | - | - | - | - | not judged: n below MIN_N (n=0) |
| rest | AT | even | mid | FADE | 1253 | -0.0342 | 214 | +0.0046 | 0.0263 | -0.0218 | [-0.0423, -0.0012] | -0.0368 | routed to ride / no bet in this leaf |
| rest | AT | even | mid | RIDE | 1253 | -0.0182 | 214 | -0.0046 | 0.0260 | -0.0306 | [-0.0511, -0.0101] | -0.0451 | routed to ride / no bet in this leaf |
| rest | AT | even | wing | FADE | 10 | - | 1 | - | - | - | - | - | not judged: n below MIN_N (n=1) |
| rest | AT | even | wing | RIDE | 10 | - | 1 | - | - | - | - | - | not judged: n below MIN_N (n=1) |
| rest | AT | home_rest_edge | mid | FADE | 170 | -0.0342 | 27 | - | - | - | - | - | not judged: n below MIN_N (n=27) |
| rest | AT | home_rest_edge | mid | RIDE | 170 | -0.0182 | 27 | - | - | - | - | - | not judged: n below MIN_N (n=27) |
| rest | AT | home_rest_edge | wing | FADE | 2 | - | 0 | - | - | - | - | - | not judged: n below MIN_N (n=0) |
| rest | AT | home_rest_edge | wing | RIDE | 2 | - | 0 | - | - | - | - | - | not judged: n below MIN_N (n=0) |
| rest | TT | long | mid | FADE | 378 | -0.0372 | 67 | -0.0397 | 0.0312 | -0.0709 | [-0.1088, -0.0330] | -0.0782 | routed to ride / no bet in this leaf |
| rest | TT | long | mid | RIDE | 378 | -0.0238 | 67 | +0.0397 | 0.0306 | +0.0091 | [-0.0287, +0.0470] | +0.0021 | routed to ride / no bet in this leaf |
| rest | TT | long | wing | FADE | 210 | -0.0372 | 41 | -0.0048 | 0.0281 | -0.0329 | [-0.1252, +0.0595] | -0.0403 | routed to ride / no bet in this leaf |
| rest | TT | long | wing | RIDE | 210 | -0.0238 | 41 | +0.0048 | 0.0270 | -0.0222 | [-0.1145, +0.0702] | -0.0291 | routed to ride / no bet in this leaf |
| rest | TT | normal | mid | FADE | 1465 | -0.0372 | 243 | +0.0098 | 0.0311 | -0.0213 | [-0.0366, -0.0061] | -0.0287 | routed to ride / no bet in this leaf |
| rest | TT | normal | mid | RIDE | 1465 | -0.0238 | 243 | -0.0098 | 0.0306 | -0.0404 | [-0.0556, -0.0252] | -0.0474 | routed to ride / no bet in this leaf |
| rest | TT | normal | wing | FADE | 1116 | -0.0372 | 192 | -0.0042 | 0.0280 | -0.0322 | [-0.0763, +0.0119] | -0.0397 | routed to ride / no bet in this leaf |
| rest | TT | normal | wing | RIDE | 1116 | -0.0238 | 192 | +0.0042 | 0.0269 | -0.0227 | [-0.0668, +0.0214] | -0.0296 | routed to ride / no bet in this leaf |
| rest | TT | short | mid | FADE | 103 | -0.0372 | 20 | - | - | - | - | - | not judged: n below MIN_N (n=20) |
| rest | TT | short | mid | RIDE | 103 | -0.0238 | 20 | - | - | - | - | - | not judged: n below MIN_N (n=20) |
| rest | TT | short | wing | FADE | 79 | -0.0372 | 16 | - | - | - | - | - | not judged: n below MIN_N (n=16) |
| rest | TT | short | wing | RIDE | 79 | -0.0238 | 16 | - | - | - | - | - | not judged: n below MIN_N (n=16) |
| weather | AS | adverse | mid | FADE | 22 | - | 37 | - | - | - | - | - | not judged: n below MIN_N (n=37) |
| weather | AS | adverse | mid | RIDE | 22 | - | 37 | - | - | - | - | - | not judged: n below MIN_N (n=37) |
| weather | AS | adverse | wing | FADE | 7 | - | 13 | - | - | - | - | - | not judged: n below MIN_N (n=13) |
| weather | AS | adverse | wing | RIDE | 7 | - | 13 | - | - | - | - | - | not judged: n below MIN_N (n=13) |
| weather | AS | benign | mid | FADE | 156 | -0.0468 | 143 | +0.0093 | 0.0212 | -0.0120 | [-0.0374, +0.0135] | -0.0226 | routed to ride / no bet in this leaf |
| weather | AS | benign | mid | RIDE | 156 | +0.0051 | 143 | -0.0093 | 0.0211 | -0.0303 | [-0.0558, -0.0049] | -0.0406 | routed to ride / no bet in this leaf |
| weather | AS | benign | wing | FADE | 60 | -0.0468 | 52 | +0.0215 | 0.0175 | +0.0040 | [-0.0957, +0.1038] | -0.0069 | routed to ride / no bet in this leaf |
| weather | AS | benign | wing | RIDE | 60 | +0.0051 | 52 | -0.0215 | 0.0171 | -0.0386 | [-0.1384, +0.0611] | -0.0487 | routed to ride / no bet in this leaf |
| weather | AT | adverse | mid | FADE | 22 | - | 37 | - | - | - | - | - | not judged: n below MIN_N (n=37) |
| weather | AT | adverse | mid | RIDE | 22 | - | 37 | - | - | - | - | - | not judged: n below MIN_N (n=37) |
| weather | AT | adverse | wing | FADE | 1 | - | 0 | - | - | - | - | - | not judged: n below MIN_N (n=0) |
| weather | AT | adverse | wing | RIDE | 1 | - | 0 | - | - | - | - | - | not judged: n below MIN_N (n=0) |
| weather | AT | benign | mid | FADE | 156 | - | 143 | +0.0198 | 0.0263 | -0.0066 | [-0.0319, +0.0187] | -0.0216 | routed to ride / no bet in this leaf |
| weather | AT | benign | mid | RIDE | 156 | - | 143 | -0.0198 | 0.0260 | -0.0458 | [-0.0711, -0.0205] | -0.0603 | routed to ride / no bet in this leaf |
| weather | AT | benign | wing | FADE | 1 | - | 1 | - | - | - | - | - | not judged: n below MIN_N (n=1) |
| weather | AT | benign | wing | RIDE | 1 | - | 1 | - | - | - | - | - | not judged: n below MIN_N (n=1) |
| weather | TT | adverse | mid | FADE | 22 | - | 37 | - | - | - | - | - | not judged: n below MIN_N (n=37) |
| weather | TT | adverse | mid | RIDE | 22 | - | 37 | - | - | - | - | - | not judged: n below MIN_N (n=37) |
| weather | TT | adverse | wing | FADE | 19 | - | 33 | - | - | - | - | - | not judged: n below MIN_N (n=33) |
| weather | TT | adverse | wing | RIDE | 19 | - | 33 | - | - | - | - | - | not judged: n below MIN_N (n=33) |
| weather | TT | benign | mid | FADE | 156 | -0.0485 | 143 | +0.0026 | 0.0311 | -0.0285 | [-0.0464, -0.0107] | -0.0359 | routed to ride / no bet in this leaf |
| weather | TT | benign | mid | RIDE | 156 | -0.0124 | 143 | -0.0026 | 0.0306 | -0.0332 | [-0.0511, -0.0153] | -0.0402 | routed to ride / no bet in this leaf |
| weather | TT | benign | wing | FADE | 132 | -0.0485 | 122 | +0.0111 | 0.0280 | -0.0169 | [-0.0703, +0.0365] | -0.0244 | routed to ride / no bet in this leaf |
| weather | TT | benign | wing | RIDE | 132 | -0.0124 | 122 | -0.0111 | 0.0269 | -0.0379 | [-0.0913, +0.0154] | -0.0449 | routed to ride / no bet in this leaf |

## What this does and does not say

- Prices are consensus-anchored proxies. A null here says the consensus line already carries these factors at the rungs tested; it does not say real Kalshi ladders cannot differ.
- Cuts (fit seasons): referee prior [-0.4339448772723464, 0.6679777236338323]; matchup terciles {'TT': [-2.00119029266228, 1.9046143529777941], 'AS': [-3.1179676050625016, 3.123256380524386], 'AT': [-2.147271818800374, 2.5297882178176145]}.
- Weather forecasts exist only from 2024, so S4 has one fit season and no leaf could be fit-routed. Rare leaves (`qb_new`, `short` rest) fall under MIN_N and are listed as not judged.
- No 2026 shadow rows from this commit forward exist yet; the forward look in PREREG s3 is not read.
- Overlap: W110.1 already returned 0 arms on weather / matchup for sides and totals. This result agrees on the new markets.
