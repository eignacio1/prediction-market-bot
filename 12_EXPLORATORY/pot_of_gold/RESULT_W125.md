# W125.3 Part C: pot-of-gold branches scored per leaf on 2026-27 shadow rows

Last reviewed: 2026-11-24. Code `score_w125.py` (44 s). Inputs read-only. Nothing here changes a leaf map; `longshot_cells.toml` is untouched.

## Method (as run)
- Rows: first two-sided pre-start snapshot per (ticker, tier) at or after 2026-11-05, from the newest price archive (main checkout, through
  2026-11-24), joined to the W122.2 settlement fetch (`settle_w122`, 2026-11-20). **Games settled after 11-20 are not joined**; the next
  re-score picks them up. 10,430 settled forward rows, 25 families, NBA / NFL / NHL (MLB is idle until 2027).
- Leaf = family x tier x FLB bucket of the mid (the H-EDGE-5 set) x side. Both sides are scored per bucket: YES is TAKE_FAVOURITE above 0.50 and
  BUY_LONGSHOT below; NO is FADE_LONGSHOT below and fade-the-favourite above. 288 leaves.
- Net per contract at the quote with the exact taker fee (`longshot_bias.net_per_contract`); game-clustered CR1 90% interval per leaf.
- Partial pooling (`variance.partial_pool`, DerSimonian-Laird) across the leaves of one (family, side, favourite|longshot half); 80 pools.
  The shrunk mean and its interval are the leaf's score. Tiers of one game share games, so tau is a lower bound (variance.py caveat).
- Judged n is the 11-05 rule: >= 150 contracts, >= 30 games, minority >= 5. Below it the leaf is IN_SAMPLE and no score is read.
  EARNED = judged n AND shrunk 90% lower bound > 0 AND BH q 0.10 across judged leaves.

## Result: 0 of 18 judged leaves EARNED; 273 of 288 leaves below judged n
All 18 judged leaves are NBA / NHL totals, spreads and team totals at D1. 15 of the 18 have a shrunk net at or below zero and are routed
away ("hypothesis closed, EXP-POT-W125, parked for R&D" for those leaves only). Three NBA leaves sit near zero and continue.

| Family | Leaf (tier D1, FLB bucket, side) | n / games | Shrunk net [90%] | Routing |
|---|---|---|---|---|
| KXNBASPREAD | [.02,.10) NO | 579 / 89 | -0.071 [-0.099, -0.043] | routed away |
| KXNBASPREAD | [.02,.10) YES | 579 / 89 | -0.060 [-0.088, -0.032] | routed away |
| KXNBASPREAD | [.10,.25) NO / YES | 634 / 94 | -0.086 / -0.067 | routed away |
| KXNBATEAMTOTAL | [.10,.25) NO / YES | 585 / 82 | -0.092 / -0.106 | routed away |
| KXNBATEAMTOTAL | [.75,.90) NO | 298 / 63 | -0.144 [-0.180, -0.108] | routed away |
| KXNBATEAMTOTAL | [.75,.90) YES | 298 / 63 | 0.000 [-0.026, +0.027] | continue (ride favourite, no edge shown) |
| KXNBATOTAL | [.10,.25) NO / YES | 355 / 91 | -0.054 / -0.091 | routed away |
| KXNBATOTAL | [.75,.90) NO | 343 / 90 | -0.134 [-0.167, -0.101] | routed away |
| KXNBATOTAL | [.75,.90) YES | 343 / 90 | +0.016 [-0.009, +0.041] | continue |
| KXNBATOTAL | [.90,.98) NO | 182 / 67 | -0.087 [-0.123, -0.052] | routed away |
| KXNBATOTAL | [.90,.98) YES | 182 / 67 | +0.016 [-0.009, +0.041] | continue |
| KXNHLTEAMTOTAL | [.10,.25) NO / YES | 164 / 95 | -0.064 / -0.112 | routed away |
| KXNHLTOTAL | [.90,.98) NO / YES | 158 / 79 | -0.038 / -0.024 | routed away |

Reading: the pot-of-gold side (buying or fading longshots) loses 5-14c per contract after cost in every judged NBA / NHL leaf. The only
non-negative leaves are the favourite YES side at [.75,.98): ride, not pot of gold, and their intervals contain zero. H-EDGE-5 (2025-26 close, `edge_location/h5_flb/RESULT.md`) found the favourite side also fails to clear cost net, so the two reads
agree that no longshot or favourite leaf is earned yet.
The 17 pre-registered MLB / NFL cells: 15 MLB cells have 0 forward rows (idle); KXNFLSPREAD D1 1-5c has 31 contracts / 13 games and KXNFLTOTAL D1 95-99c
25 / 23, both below judged n, so IN_SAMPLE (`out/w125/named_17.json`, from `rescore_w122.py` re-run on the same archive).
Unjudged leaves with the highest shrunk lower bounds (NFL pass-completion NO leaves, n 8-22, NBA rebounds n 18-21) are thin and are NOT scores;
they are listed in `out/w125/leaves_w125.json` and read nothing until judged n.

## FLB bucket as a split
The FLB bucket is now a field on every leaf (`flb`), so a router v2 split can use it. No FLB bucket reaches EARNED on the pot-of-gold side.

## Next look
Judged leaves grow with every in-season week; re-run `score_w125.py` after the settlement fetch refreshes. NFL props and NBA props reach judged n on the
power ledger's dates (`power_ledger.json`), not before.

## Pre-check: Kalshi sports parlay / combo markets (B-024)
Public, unauthenticated `GET https://api.elections.kalshi.com/trade-api/v2/multivariate_event_collections?limit=200` on 2026-11-23 returned 200
collections (more behind the cursor): KXMVENBASINGLEGAME 196, KXMVENFLSINGLEGAME 1, KXMVESPORTSMULTIGAMEEXTENDED 1, KXMVECROSSCATEGORY 1,
KXMVECROSSCATEGORY-SHARD1 1. Each lists `associated_event_tickers` (e.g. KXNFLGAME-26NOV23CINWAS plus its spread, total, team total, props).
So combo markets EXIST. Registered as NOT_IMPLEMENTED cells (T1/T2/T3) in `market_type_registry.py`: NBA_SAME_GAME_COMBO, NFL_SAME_GAME_COMBO,
MULTIGAME_COMBO, CROSS_CATEGORY_COMBO; seat cells in `SEATS/nba.toml` and `nfl.toml`. REGISTERED, NOT BUILT: no engine prices them.
