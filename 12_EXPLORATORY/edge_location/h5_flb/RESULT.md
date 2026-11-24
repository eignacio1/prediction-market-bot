# H-EDGE-5 RESULT: favourite-longshot bias at the close, per family x price bucket (2025-26 regular season)

Last reviewed: 2026-11-24. Pre-registration `PREREG.md` (commits 42e706b, e7c0278) was committed before any 2025-26 settlement was joined to a price.
Code `fetch_h5.py`, `run_h5.py`; raw output `results.json`, `tables.md` (every row, with and without backfilled quotes).

## Verdict: NOT SUPPORTED. 0 of 7 testable family x bucket cells have a net interval above zero; BH q 0.10 rejects none (all q = 1.000)
Net after costs is negative or indistinguishable from zero in every testable cell. Gross is often positive in the favourite buckets
(favourites do settle slightly above price, the H-MEAS-1 direction); the round cost (half spread + taker fee, 1.0-5.4c) takes all of it.

| Family | Bucket (arm) | n / games | Gross | Cost | Net, 90% game-clustered interval | Verdict | Routing consequence |
|---|---|---|---|---|---|---|---|
| NHL moneyline (previously read by W117.2, not by bucket) | [.50,.75) ride fav | 1,296 / 1,296 | -0.0207 | 0.0225 | -0.0432 [-0.0658, -0.0205] | NOT SUPPORTED | hypothesis closed (EXP-H-EDGE-5, parked for R&D) |
| NHL moneyline | [.75,.90) ride fav | 13 / 13 | +0.0669 | 0.0179 | +0.0490 [-0.1219, +0.2199] | UNDERPOWERED | none; 13 games in the bucket |
| NBA moneyline | [.50,.75) ride fav | 762 / 762 | -0.0064 | 0.0215 | -0.0279 [-0.0564, +0.0006] | NOT SUPPORTED | hypothesis closed (EXP-H-EDGE-5, parked for R&D) |
| NBA moneyline | [.75,.90) ride fav | 350 / 350 | -0.0126 | 0.0152 | -0.0279 [-0.0624, +0.0067] | NOT SUPPORTED | hypothesis closed (EXP-H-EDGE-5, parked for R&D) |
| NBA moneyline | [.90,.98) ride fav | 63 / 63 | +0.0592 | 0.0096 | +0.0496 [+0.0237, +0.0755] | UNDERPOWERED (< 100 contracts) | LEAD, not routed: interval above 0 but below the pre-registered n; judged on 2026-27 rows (see below) |
| NBA team total | [.02,.10) NO | 2 / 2 | +0.0900 | 0.0480 | +0.0420 | UNDERPOWERED | none |
| NBA team total | [.10,.25) NO | 467 / 277 | -0.0376 | 0.0516 | -0.0892 [-0.1247, -0.0536] | NOT SUPPORTED | hypothesis closed (EXP-H-EDGE-5, parked for R&D) |
| NBA team total | [.25,.50) NO | 1,429 / 379 | -0.0332 | 0.0528 | -0.0860 [-0.1191, -0.0530] | NOT SUPPORTED | hypothesis closed (EXP-H-EDGE-5, parked for R&D) |
| NBA team total | [.50,.75) ride fav | 1,474 / 386 | +0.0410 | 0.0535 | -0.0126 [-0.0439, +0.0188] | NOT SUPPORTED | hypothesis closed (EXP-H-EDGE-5, parked for R&D) |
| NBA team total | [.75,.90) ride fav | 378 / 239 | +0.0111 | 0.0528 | -0.0418 [-0.0779, -0.0056] | NOT SUPPORTED | hypothesis closed (EXP-H-EDGE-5, parked for R&D) |
| NFL team total | all six buckets | 9-46 / 6-14 each | -0.17 .. +0.11 | 0.034-0.044 | every interval wide; widest bucket [.25,.50) -0.2141 [-0.4001, -0.0281] | UNDERPOWERED (< 30 games each) | none; the regular-season history on disk is the last 5 weeks |
| NHL team total | none | none | | | | NO POPULATION | Kalshi history does not list it; reopen when it does |

Mirror (NO-longshot) rows are the same bets as the favourite rows seen from the other listing, descriptive only, not in the BH count (`tables.md`).
Early/late stability and the no-backfill variant are in `tables.md`; the no-backfill variant moves no net by more than 0.9c and flips no verdict.

## What the verdict is and is not
- It is a read of the close, 0-60 min stale (hourly candles), at today's fee schedule, on 2025-26 history. It is not a read of earlier horizons, other families, or 2026-27.
- It does not say favourites are priced correctly: gross is positive in five favourite buckets with n >= 30. It says the gap is smaller than one
  round cost here, which is the pre-registered claim. The modal outcome stated in advance (about 65%: no cell SUPPORTED) held.
- NBA team total: 2,949 of 7,674 rows were dropped for a spread above 10c (the pre-registered cap) and 681 for no candle in the last 3 hours; only Feb-Jun 2026 is listed
  (disclosed in PREREG). Sample is the lower-spread, later-season part of the market.
- NBA moneyline [.90,.98): the one interval above zero. n 63 is below the pre-registered 100 contracts, so it is a LEAD, nothing is routed, and with 63 games a
  season it cannot reach the n that resolves a 1c interval in one season (games_needed_1c about 965). It stays a named 2026-27 forward look, not a leaf.
- Early partial-data runs peeked at NBA moneyline, NBA team total and NFL team total while the candle fetch was incomplete; no verdict was taken from them and the numbers above are the complete-data run.

## Routing consequence and reopen
No leaf-map change in this block. Hypothesis closed (EXP-H-EDGE-5, parked for R&D) for the NOT SUPPORTED cells above.
Reopen trigger: the same gap appears in 2026-27 rows (H-MEAS-1 slope intervals with a net-of-cost read at a finer close than hourly), or Kalshi history lists NHL team totals or more NBA / NFL team-total seasons.
