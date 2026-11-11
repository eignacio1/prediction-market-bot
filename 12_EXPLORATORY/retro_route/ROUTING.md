# W110.5 retro-route: where each leaf goes (ride / fade / momentum / no bet)

Built 2026-11-11 from every settled shadow row on the box (paper rows, not fills; the GG-1771 fill epoch does not apply). Spec frozen before results: `SPEC.md`. All numbers are net per contract after the exact Kalshi taker fee, the taker price (ask, or 1 minus bid) already paying the spread.

## In plain English

- 365 leaves (cell x band x favoured-side price bin x last move). 189 are thin (under 60 fit rows or 20 fit games) and default to **no bet**. 113 leaves chose an arm on the earlier 70% of games, and 105 of those have enough held-out games (10+) to report.
- On the held-out 30% of games, **1 leaf** survives Benjamini-Hochberg q=0.10, and **0 leaves** meet the draft bar (BH, lower 90% bound above 0, 15+ held-out games). So there are **no pre-registration drafts** from this pass; the one BH leaf has only 11 held-out games and is listed below as a lead for the window, not a result.
- Every other routed leaf's held-out interval includes zero or sits below it: those leaves are **routed away from the arm they picked on the fit window** and default to no bet until a forward test says otherwise. That is a routing result, not a verdict on the market.
- The cleaner signal is at family level (table below, unrouted, every row of the held-out games): riding the market's favoured side beats fading it in nearly every family, and the model-disagreement fade holds up on NHL puck line (and, with a wide interval, NHL moneyline). Those are leads for the forward test, not drafts.

## Inventory (Part A): settled shadow rows after dedupe

Raw settled rows 110,470; after dedupe (one per market ticker and run; one moneyline ticker per game and run) 106,430.

| Sport | Family | Rows | Games | First | Last |
|---|---|---|---|---|---|
| MLB | MLB_GAME_TOTAL | 701 | 24 | 2026-10-05 | 2026-10-29 |
| MLB | MLB_MONEYLINE | 66 | 24 | 2026-10-05 | 2026-10-29 |
| MLB | MLB_RUN_LINE | 396 | 24 | 2026-10-05 | 2026-10-29 |
| MLB | MLB_TEAM_TOTAL | 924 | 24 | 2026-10-05 | 2026-10-29 |
| NBA | NBA_GAME_TOTAL | 11,939 | 154 | 2026-10-20 | 2026-11-10 |
| NBA | NBA_MONEYLINE | 456 | 154 | 2026-10-20 | 2026-11-10 |
| NBA | NBA_SPREAD | 14,304 | 154 | 2026-10-20 | 2026-11-10 |
| NBA | NBA_TEAM_TOTAL | 14,544 | 154 | 2026-10-20 | 2026-11-10 |
| NFL | NFL_GAME_TOTAL | 4,786 | 87 | 2026-10-04 | 2026-11-10 |
| NFL | NFL_MONEYLINE | 261 | 87 | 2026-10-04 | 2026-11-10 |
| NFL | NFL_SPREAD | 6,582 | 87 | 2026-10-04 | 2026-11-10 |
| NFL | NFL_TEAM_TOTAL | 6,688 | 87 | 2026-10-04 | 2026-11-10 |
| NHL | NHL_GAME_TOTAL | 28,595 | 270 | 2026-10-03 | 2026-11-11 |
| NHL | NHL_MONEYLINE | 3,267 | 270 | 2026-10-03 | 2026-11-11 |
| NHL | NHL_PUCK_LINE | 12,921 | 270 | 2026-10-03 | 2026-11-11 |

## Arms, family level, held-out games only, every row (not routed)

Mean net per contract, 90% game-clustered interval, rows / games. The unrouted reference; leaves below refine it.

| Family | Ride | Fade | Follow move | Model fade |
|---|---|---|---|---|
| NBA NBA_GAME_TOTAL | -0.034 [-0.065, -0.003] 4807/67 | -0.059 [-0.090, -0.028] 4807/67 | -0.045 [-0.091, +0.002] 2482/60 | -0.043 [-0.108, +0.022] 3439/66 |
| NBA NBA_MONEYLINE | +0.043 [-0.037, +0.120] 195/67 | -0.088 [-0.166, -0.007] 195/67 | -0.001 [-0.068, +0.067] 102/65 | -0.027 [-0.113, +0.062] 168/64 |
| NBA NBA_SPREAD | -0.031 [-0.060, -0.001] 5884/67 | -0.038 [-0.068, -0.008] 5884/67 | -0.022 [-0.060, +0.018] 3003/66 | -0.032 [-0.099, +0.034] 4180/67 |
| NBA NBA_TEAM_TOTAL | -0.064 [-0.089, -0.038] 5801/67 | -0.072 [-0.099, -0.044] 5801/67 | -0.044 [-0.084, -0.006] 2751/50 | -0.046 [-0.100, +0.012] 3382/64 |
| NFL NFL_GAME_TOTAL | -0.014 [-0.069, +0.039] 1423/28 | -0.024 [-0.076, +0.032] 1423/28 | -0.025 [-0.085, +0.039] 590/28 | -0.032 [-0.122, +0.058] 1211/28 |
| NFL NFL_MONEYLINE | +0.134 [+0.017, +0.236] 84/28 | -0.173 [-0.275, -0.056] 84/28 | -0.070 [-0.214, +0.065] 28/19 | -0.005 [-0.129, +0.128] 78/27 |
| NFL NFL_SPREAD | -0.007 [-0.053, +0.037] 2091/28 | -0.028 [-0.072, +0.018] 2091/28 | -0.094 [-0.147, -0.035] 790/28 | +0.002 [-0.081, +0.098] 1578/28 |
| NFL NFL_TEAM_TOTAL | -0.011 [-0.044, +0.021] 1985/28 | -0.030 [-0.062, +0.003] 1985/28 | -0.030 [-0.058, -0.000] 812/28 | -0.014 [-0.067, +0.045] 1263/28 |
| NHL NHL_GAME_TOTAL | -0.023 [-0.045, +0.001] 6964/66 | -0.059 [-0.084, -0.037] 6964/66 | -0.015 [-0.044, +0.012] 1432/66 | -0.023 [-0.080, +0.036] 4653/66 |
| NHL NHL_MONEYLINE | +0.010 [-0.081, +0.106] 804/66 | -0.053 [-0.149, +0.038] 804/66 | +0.074 [+0.015, +0.133] 116/59 | +0.062 [-0.059, +0.170] 541/49 |
| NHL NHL_PUCK_LINE | +0.015 [-0.028, +0.055] 3159/66 | -0.057 [-0.097, -0.015] 3159/66 | +0.007 [-0.019, +0.034] 540/66 | +0.088 [+0.037, +0.136] 2443/66 |

## Routing by family (Part C)

### MLB MLB_GAME_TOTAL

Leaves 24; thin 21; routed to fade the market 1, no bet 21, ride the market 2; reportable held-out 0; BH 0.

### MLB MLB_MONEYLINE

Leaves 9; thin 9; routed to no bet 9; reportable held-out 0; BH 0.

### MLB MLB_RUN_LINE

Leaves 24; thin 23; routed to no bet 23, ride the market 1; reportable held-out 0; BH 0.

### MLB MLB_TEAM_TOTAL

Leaves 24; thin 21; routed to no bet 22, ride the market 2; reportable held-out 0; BH 0.

### NBA NBA_GAME_TOTAL

Leaves 27; thin 8; routed to fade the market 3, model-disagreement fade 4, follow the move 5, no bet 12, ride the market 3; reportable held-out 15; BH 0.

Reportable leaves, best held-out first (band, favoured-price bin 0=<.35 ... 4=>=.8, move):

| Leaf | Arm | Held-out net | 90% interval | Rows / games | BH |
|---|---|---|---|---|---|
| T2, 2, down | follow the move | +0.090 | [-0.049, +0.216] | 184/37 |  |
| T3, 4, flat | model-disagreement fade | +0.046 | [-0.022, +0.122] | 113/26 |  |
| T3, 2, flat | ride the market | +0.039 | [-0.103, +0.191] | 36/17 |  |
| T3, 3, up | fade the market | +0.029 | [-0.057, +0.104] | 119/26 |  |
| T2, 3, down | follow the move | +0.008 | [-0.110, +0.126] | 188/37 |  |
| T3, 2, down | follow the move | +0.006 | [-0.136, +0.143] | 173/36 |  |

### NBA NBA_MONEYLINE

Leaves 24; thin 24; routed to no bet 24; reportable held-out 0; BH 0.

### NBA NBA_SPREAD

Leaves 25; thin 4; routed to fade the market 5, model-disagreement fade 1, follow the move 4, no bet 15; reportable held-out 10; BH 0.

Reportable leaves, best held-out first (band, favoured-price bin 0=<.35 ... 4=>=.8, move):

| Leaf | Arm | Held-out net | 90% interval | Rows / games | BH |
|---|---|---|---|---|---|
| T2, 2, flat | fade the market | +0.091 | [-0.046, +0.233] | 35/23 |  |
| T3, 3, down | fade the market | +0.059 | [-0.063, +0.188] | 120/43 |  |
| T2, 3, down | fade the market | +0.051 | [-0.046, +0.146] | 181/49 |  |
| T2, 2, up | follow the move | +0.045 | [-0.051, +0.136] | 344/59 |  |
| T3, 2, flat | model-disagreement fade | +0.042 | [-0.150, +0.218] | 46/23 |  |
| T3, 3, up | follow the move | +0.005 | [-0.081, +0.091] | 199/52 |  |

### NBA NBA_TEAM_TOTAL

Leaves 27; thin 7; routed to fade the market 1, model-disagreement fade 1, follow the move 4, no bet 19, ride the market 2; reportable held-out 8; BH 0.

Reportable leaves, best held-out first (band, favoured-price bin 0=<.35 ... 4=>=.8, move):

| Leaf | Arm | Held-out net | 90% interval | Rows / games | BH |
|---|---|---|---|---|---|
| T3, 2, up | follow the move | +0.038 | [-0.071, +0.151] | 156/35 |  |
| T3, 3, flat | model-disagreement fade | -0.004 | [-0.130, +0.139] | 61/26 |  |
| T2, 3, down | follow the move | -0.008 | [-0.109, +0.087] | 192/34 |  |
| T2, 4, down | ride the market | -0.059 | [-0.117, +0.003] | 299/40 |  |
| T3, 2, down | follow the move | -0.064 | [-0.191, +0.062] | 183/38 |  |
| T2, 2, down | follow the move | -0.072 | [-0.193, +0.046] | 166/30 |  |

### NFL NFL_GAME_TOTAL

Leaves 21; thin 0; routed to fade the market 6, model-disagreement fade 2, follow the move 2, no bet 6, ride the market 5; reportable held-out 14; BH 0.

Reportable leaves, best held-out first (band, favoured-price bin 0=<.35 ... 4=>=.8, move):

| Leaf | Arm | Held-out net | 90% interval | Rows / games | BH |
|---|---|---|---|---|---|
| T2, 2, down | ride the market | +0.012 | [-0.084, +0.092] | 70/23 |  |
| T2, 2, flat | fade the market | +0.003 | [-0.087, +0.085] | 59/20 |  |
| T3, 4, down | follow the move | -0.007 | [-0.090, +0.094] | 47/15 |  |
| T3, 2, up | follow the move | -0.035 | [-0.246, +0.184] | 42/13 |  |
| T3, 4, up | ride the market | -0.039 | [-0.145, +0.051] | 60/17 |  |
| T3, 2, flat | ride the market | -0.043 | [-0.180, +0.101] | 40/14 |  |

### NFL NFL_MONEYLINE

Leaves 22; thin 22; routed to no bet 22; reportable held-out 0; BH 0.

### NFL NFL_SPREAD

Leaves 21; thin 0; routed to fade the market 3, model-disagreement fade 1, no bet 8, ride the market 9; reportable held-out 13; BH 0.

Reportable leaves, best held-out first (band, favoured-price bin 0=<.35 ... 4=>=.8, move):

| Leaf | Arm | Held-out net | 90% interval | Rows / games | BH |
|---|---|---|---|---|---|
| T2, 3, down | fade the market | +0.037 | [-0.082, +0.153] | 65/26 |  |
| T3, 3, down | ride the market | +0.033 | [-0.092, +0.150] | 45/17 |  |
| T3, 4, down | ride the market | +0.030 | [-0.078, +0.106] | 69/24 |  |
| T3, 4, flat | ride the market | +0.001 | [-0.064, +0.055] | 157/26 |  |
| T1, 4, na | ride the market | -0.004 | [-0.055, +0.042] | 314/28 |  |
| T2, 3, flat | ride the market | -0.012 | [-0.095, +0.079] | 71/25 |  |

### NFL NFL_TEAM_TOTAL

Leaves 23; thin 2; routed to fade the market 2, model-disagreement fade 2, follow the move 3, no bet 7, ride the market 9; reportable held-out 16; BH 0.

Reportable leaves, best held-out first (band, favoured-price bin 0=<.35 ... 4=>=.8, move):

| Leaf | Arm | Held-out net | 90% interval | Rows / games | BH |
|---|---|---|---|---|---|
| T2, 2, up | follow the move | +0.048 | [-0.110, +0.187] | 54/20 |  |
| T3, 2, down | ride the market | +0.036 | [-0.131, +0.180] | 32/12 |  |
| T2, 3, down | follow the move | +0.034 | [-0.088, +0.172] | 68/24 |  |
| T3, 4, down | ride the market | +0.012 | [-0.057, +0.066] | 80/19 |  |
| T2, 4, down | ride the market | -0.007 | [-0.052, +0.030] | 139/27 |  |
| T2, 2, flat | ride the market | -0.012 | [-0.160, +0.115] | 32/20 |  |

### NHL NHL_GAME_TOTAL

Leaves 35; thin 14; routed to fade the market 2, model-disagreement fade 2, follow the move 3, no bet 21, ride the market 7; reportable held-out 13; BH 0.

Reportable leaves, best held-out first (band, favoured-price bin 0=<.35 ... 4=>=.8, move):

| Leaf | Arm | Held-out net | 90% interval | Rows / games | BH |
|---|---|---|---|---|---|
| T3, 4, up | model-disagreement fade | +0.056 | [-0.017, +0.142] | 113/54 |  |
| T3, 3, up | follow the move | +0.032 | [-0.091, +0.153] | 62/42 |  |
| T3, 4, flat | ride the market | +0.021 | [-0.004, +0.041] | 971/64 |  |
| T3, 4, down | ride the market | +0.015 | [-0.028, +0.052] | 84/47 |  |
| T2, 3, up | ride the market | +0.012 | [-0.068, +0.085] | 130/58 |  |
| T2, 4, flat | ride the market | +0.010 | [-0.014, +0.034] | 1899/62 |  |

### NHL NHL_MONEYLINE

Leaves 26; thin 19; routed to model-disagreement fade 4, no bet 20, ride the market 2; reportable held-out 6; BH 1.

Reportable leaves, best held-out first (band, favoured-price bin 0=<.35 ... 4=>=.8, move):

| Leaf | Arm | Held-out net | 90% interval | Rows / games | BH |
|---|---|---|---|---|---|
| T2, 3, flat | ride the market | +0.268 | [+0.246, +0.289] | 70/11 | yes |
| T2, 2, up | model-disagreement fade | +0.172 | [-0.018, +0.341] | 17/15 |  |
| T3, 3, flat | model-disagreement fade | +0.050 | [-0.126, +0.193] | 30/10 |  |
| T3, 2, flat | model-disagreement fade | +0.046 | [-0.093, +0.189] | 108/35 |  |
| T2, 2, flat | ride the market | -0.048 | [-0.164, +0.072] | 320/50 |  |
| T2, 2, down | model-disagreement fade | -0.061 | [-0.291, +0.217] | 22/17 |  |

### NHL NHL_PUCK_LINE

Leaves 33; thin 15; routed to fade the market 4, model-disagreement fade 3, follow the move 2, no bet 23, ride the market 1; reportable held-out 10; BH 0.

Reportable leaves, best held-out first (band, favoured-price bin 0=<.35 ... 4=>=.8, move):

| Leaf | Arm | Held-out net | 90% interval | Rows / games | BH |
|---|---|---|---|---|---|
| T2, 3, down | ride the market | +0.076 | [-0.006, +0.143] | 96/47 |  |
| T2, 2, flat | fade the market | +0.058 | [-0.057, +0.182] | 242/35 |  |
| T2, 4, down | model-disagreement fade | +0.028 | [-0.046, +0.093] | 67/42 |  |
| T1, 4, na | model-disagreement fade | +0.010 | [-0.066, +0.074] | 60/45 |  |
| T3, 4, flat | model-disagreement fade | +0.002 | [-0.073, +0.068] | 258/56 |  |
| T3, 2, flat | fade the market | -0.013 | [-0.133, +0.117] | 130/33 |  |

## D6 layers 1-5 per cell (what this pass supplies)

Layer 1 simulated probability: the logged `p_yes`. Layer 2 market state: bid / ask / mid, band, price bin, last move (from the ticker's own earlier shadow rows). Layer 3 factor filters: **price, band and move only**; the 110.1 / 110.2 factor filters are not joined per row (gap below). Layer 4 a tree choosing the arm: this leaf router (fit on 70% of games). Layer 5 per-leaf held-out net after costs per arm: reported where a leaf has 10+ held-out games.

| Cell | Leaves with held-out result | Layers present |
|---|---|---|
| MLB MLB_GAME_TOTAL | 0 | 1, 2, 4 (3 partial; 5 awaits more games) |
| MLB MLB_MONEYLINE | 0 | 1, 2, 4 (3 partial; 5 awaits more games) |
| MLB MLB_RUN_LINE | 0 | 1, 2, 4 (3 partial; 5 awaits more games) |
| MLB MLB_TEAM_TOTAL | 0 | 1, 2, 4 (3 partial; 5 awaits more games) |
| NBA NBA_GAME_TOTAL | 15 | 1, 2, 4, 5 (3 partial) |
| NBA NBA_MONEYLINE | 0 | 1, 2, 4 (3 partial; 5 awaits more games) |
| NBA NBA_SPREAD | 10 | 1, 2, 4, 5 (3 partial) |
| NBA NBA_TEAM_TOTAL | 8 | 1, 2, 4, 5 (3 partial) |
| NFL NFL_GAME_TOTAL | 14 | 1, 2, 4, 5 (3 partial) |
| NFL NFL_MONEYLINE | 0 | 1, 2, 4 (3 partial; 5 awaits more games) |
| NFL NFL_SPREAD | 13 | 1, 2, 4, 5 (3 partial) |
| NFL NFL_TEAM_TOTAL | 16 | 1, 2, 4, 5 (3 partial) |
| NHL NHL_GAME_TOTAL | 13 | 1, 2, 4, 5 (3 partial) |
| NHL NHL_MONEYLINE | 6 | 1, 2, 4, 5 (3 partial) |
| NHL NHL_PUCK_LINE | 10 | 1, 2, 4, 5 (3 partial) |

## Gaps for the window (registered here, not fixed in this block)

- **Archive join not done.** Move since open and last hour come from the ticker's own earlier shadow rows, not `PRICE_ARCHIVE`; the ladder gap is not a column. A streaming archive join (2 GB) plus the MLB / NFL settlement cache would add archive-only rows with no model p (ride / fade / momentum only). NBA / NHL archive tickers have no settlement cache.
- **Factor filters not joined.** 110.1 (NFL weather, matchup) and 110.2 (NBA via the 109.1 tree) are not per-row fields in the shadow ledgers, so leaves split on market state only. Feature rows are hashed (`feature_row_sha256`), not stored.
- **Small windows.** NFL 87 games, MLB postseason 24 games, NBA 154, NHL 270 since early October; the held-out 30% is 161 games across sports. The leaf count is large against that; BH is the guard and it leaves one name.
- Shadow data was pulled read-only from the box into a scratch directory; nothing was written to the box.
