# W115.1 / W116.1 (B-094) — evidence design: result (DRAFT, not merged)

Corpus: exact W110.5 snapshot, 106,430 rows. Fit 73,233 rows / 375 games (earliest 70%); held out 33,197 rows / 161 games
(NBA, NFL, NHL only). Intervals are 95% game-clustered bootstrap. Numbers from `results.json`, written by `run.py` on 2026-11-17.

## Plainly
- **v2 (pooled + sequential) does not win on evidence. It abstains.** After the validity fix below, it arms 0 of 356 leaves on
  the fit window and 0 of 365 on the full corpus. Its held-out net per row is 0 because it places no bets.
- **v1 (per-leaf, today's map) loses money held out**: −0.0064 net per row [−0.0138, +0.0009] over 17,164 bets. NFL is
  **−0.0201 [−0.0369, −0.0054]**, the interval wholly below 0. Of 105 v1-armed leaves with ≥10 held-out games, 41 are
  net-positive and 1 has its interval above 0. NFL per-leaf arms: hypothesis closed (EXP-W110.5 NFL per-leaf, parked for R&D).
- **Ride every favourite loses held out**: −0.0256 [−0.0394, −0.0129]; NBA −0.0422 [−0.0621, −0.0217].
- **v2 − v1** (paired, per row): ALL +0.0064 [−0.0009, +0.0138]; NFL +0.0201 [+0.0054, +0.0370]. This is the value of
  routing to no bet, not of a found arm.
- The v1 BH-survivor row (70 NHL bets, +0.268 per bet) is **not a clean held-out result**: W110.5 applied BH on the same
  test window.

## Validity defect found and fixed (W116.1)
Fable's e-process used the plug-in game-clustered variance. On binary Kalshi payoffs a short run of favourites that all won
has a variance near 0, so the e-value explodes. Leaf MLB|TEAM_TOTAL|T3|4|up reached log E = 32.9 on 15 games, with
P(net>0) 0.90.
- Synthetic binary null (favourite at 0.85, 10 weekly looks, n=300): false claims **275/300 (92%) before**, **2/300 (0.7%)
  after**.
- Planted +0.10 effect found: 99/100 before, **79/100 after**.

The fix floors the increment variance at the net=0 binary variance c(1−c), with c read off the net and rows within a game
summed as fully correlated (`pipeline.null_row_sd`, `Config.null_var="binary"`). Tests:
`test_binary_null_false_claims_bounded_across_looks`, `test_binary_planted_edge_is_found` and
`test_binary_null_floor_stops_the_all_favourites_won_blowup`. 14/14 pass.

## Power calendar (as of 2026-11-11, 104-week horizon)
- **At today's posterior means:** no leaf can earn an arm under v2 or v1 BH in any sport.
- **At a fixed true net of +0.02 per contract:** v2 (leaf-only upper bound) 12 leaves, first 2027-07-21 (NHL), median
  2028-05-10. v1 BH 0.
- **At +0.05 per contract:** v2 84 leaves, first 2027-01-20, median 2027-11-17. v1 BH 46 leaves, first 2027-02-17, median
  2028-03-15.
- **Per sport:**

  | Sport | v2 at +0.02 | v2 at +0.05 | v1 at +0.05 |
  |---|---|---|---|
  | NBA | 4 | 27 | 18 |
  | NFL | 2 | 30 | 11 |
  | NHL | 6 | 27 | 17 |

  MLB is 0, being off-season in the rate window.

So v2 earns arms sooner and on more leaves than v1 at the same true effect. On the data in hand, though, no leaf shows an
effect it can prove.

## Wiring and registration (done in W116.1)
- `leaf_map.py`: the `PM_LEAF_MAP_VERSION` switch (default v1; v2 = `leaf_maps/leaf_map_v2.json`, sha256 pinned by a test).
  `LeafDecision` carries `posterior` and `source`.
- Frozen pre-registration: `ROUTER_V2_PREREGISTRATION_2026-11-17.md`.
- Gaps: GG-1936 (no free NBA / NHL line history), GG-1937 (Kalshi history unparsed), GG-1938 (no filter column on
  settled rows), GG-1954 (the e-process validity defect, fixed here).
- Turning v2 on for logging is the operator's decision (ACTIVE_QUEUE "Needs your decision"). Today it would log NO_BET
  on every row.
