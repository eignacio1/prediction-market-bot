# W129.3 Part C — 2026-08-15 slate, 12 MLB game cells, seven D6 layers, dry mode
**Last reviewed:** 2026-11-25. Script `dry_run_w129_3.py`; data `RESULT_W129_3_C.json`. No outcome column read (home_runs / away_runs untouched). No order, ledger write or network call. Kelly 0.
**Slate:** 15 games in the store, all 15 priced by the engine (2,000 draws), rows from `prices_2026-08-14/15.jsonl` for games starting 2026-08-15 ET.

| Cell | rows | games | L1 model p | L2 market state | L3 filters | L4 arm | L5 forward net | L6 sizing | L7 fills |
|---|---|---|---|---|---|---|---|---|---|
| MONEYLINE T1 | 1,236 | 15 | 1,236 | yes | 0 | NO_BET 1,236 (26 thin) | 0 | yes | 0 |
| MONEYLINE T2 | 0 | 0 | - | - | - | - | - | - | - |
| MONEYLINE T3 | 28 | 7 | 28 | yes | 0 | NO_BET 28 (all thin) | 0 | yes | 0 |
| RUN_LINE T1 | 1,728 | 14 | 1,728 | yes | 0 | RIDE 50, NO_BET 1,678 | 0 | yes | 0 |
| RUN_LINE T2 | 0 | 0 | - | - | - | - | - | - | - |
| RUN_LINE T3 | 84 | 7 | 84 | yes | 0 | NO_BET 84 (all thin) | 0 | yes | 0 |
| GAME_TOTAL T1 | 3,168 | 14 | 3,139 | yes | 0 | FADE 57, RIDE 97, NO_BET 3,014 | 0 | yes | 0 |
| GAME_TOTAL T2 | 0 | 0 | - | - | - | - | - | - | - |
| GAME_TOTAL T3 | 154 | 7 | 152 | yes | 0 | NO_BET 154 (all thin) | 0 | yes | 0 |
| TEAM_TOTAL T1 | 4,032 | 14 | 4,032 | yes | 0 | RIDE 181, NO_BET 3,851 | 0 | yes | 0 |
| TEAM_TOTAL T2 | 0 | 0 | - | - | - | - | - | - | - |
| TEAM_TOTAL T3 | 196 | 7 | 196 | yes | 0 | NO_BET 196 (all thin) | 0 | yes | 0 |

**Layers present end to end: 4 of 7 (L1, L2, L4, L6) on 8 of 12 cells; 0 of 12 reach all seven.** Missing, not imputed:
- **T2 (all four cells): no rows.** The price archive logs 22:00–05:59Z only, so a 4–8h-before-start row exists only for games starting after about 02Z; this slate has none. A T2 gap in the archive, not in the router.
- **L1 gaps:** 29 GAME_TOTAL T1 and 2 T3 rows sit on a rung off the priced ladder; logged `engine_gap = null` by rule, never imputed.
- **L1 is an as-played-lineup price, not a pre-game one:** the posted-lineup feed does not exist (Dependency of the PREREG). The prices here show the pipeline is wired, not that a 2027 price would be available at T1.
- **L3 (factor filters as splits): absent on every cell.** No MLB per-row filter supply exists; filters were passed as None.
- **L4 arms are the v1 look-back map** (market-state leaves, no engine tercile). T3 rows are all thin leaves. The engine tercile split is the 2027 test, not yet in the map.
- **L5: absent.** v1 nets are 2026 look-back only; no forward held-out net per arm exists before 2027.
- **L7: absent.** No MLB order or fill exists (MLB idle; the ADR-0072 arm-order demo book has no MLB arm).

**Defect found and fixed in this block:** Part B wrote the board file as `"HOME|AWAY|DATE"` keys, but `MLBEngineForecaster` looks up `(home, away, date)` tuples, and no loader existed, so no engine price would have reached any row (L1 = 0 on every cell until fixed). Fixed with `mlb_board_daily.load_board` and a test.
