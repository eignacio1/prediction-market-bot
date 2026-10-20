# W81.2 NBA lineup cross - final results (EXPLORATORY, not a verdict)

Part A (index parts 1-3): see `results_partA.md` (stage reached: interpreted). Part B (parts 4-5) below.

## Part B step 1 - what can be joined to the KXNBAPTS price history (`price_join.py` -> `price_join_markets.csv`)
Rules are Part A's, unchanged, applied to the 2025-26 season (store label 2026, the only season with KXNBAPTS candles; regular season only).
- Candle-bearing KXNBAPTS markets in the archive: **100** (93 events), closing 2025-11-27 to 2026-06-14. 24,431 market records listed in total (1,183 events, 5,805 player-games, median 4 strikes per player-game; 828 records carry no floor strike).
- Of the 100: **57** absorber games had no qualifying teammate absence (clean controls), **22** matched no regular-season game (playoff or date mismatch), **9** absorber not analysable (no trailing history), **12** markets (**10 distinct game-absorber pairs**, 9 games) have a single injury-or-illness absence of a rotation player. By role of the absent player: creator 0, starter 4, rotation 8.
- **Point-in-time join of the absence to the price history.** Injury-report snapshots (2-hourly ET grid, `20261012_nba_points_minutes/inj`, `20261013_nba_games_availability/inj2026`) observe the absent player in only **2 of the 12** (both games where the player is Out): Porzingis (Out from 2025-12-18 15:30 ET; the market was created 2025-12-21 03:01Z) and Clingan (Out from 2025-12-10 19:30 ET; market created 2025-12-11 08:01Z). **Both reports precede the market's creation.** For the other 10 the absent player appears in no snapshot of the game day or the three days before (not listed, or listed under a name the normaliser misses), so no announcement time exists.
- Every market opens hours before tip (created 1 to 20 hours before close), mostly before the day's first report slot (11:30 ET). The absence was therefore either already public when the market opened or has no observable time. **No market has a "before news" price and an "after news" price inside its own history.**

## Part B step 2 - the test (part 5) was NOT run
The pre-registered test needs the market's price change across the bracket between "not yet reported" and "reported". That bracket does not exist in the price history for any of the 12, and the rule forbids approximating the time. A level test on the opening price would need a counterfactual no-absence price and has n = 10 pairs. Stage stays **interpreted**; no verdict word is issued (REAL-NOT-PRICED / REAL-AND-PRICED / INVISIBLE / NOT REAL all withheld). Gap registered as GG-985.

Part A's own finding stands for what it is: the role-level uplift is real (creator out +1.75 pts [1.46, 2.06], starter +1.00, rotation +0.34, 2016-2025) and the player-level redistribution is mostly noise at this sample.
