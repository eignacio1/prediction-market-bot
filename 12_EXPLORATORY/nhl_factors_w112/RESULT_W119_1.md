# W119.1 NHL goalie + special-teams splits, and NHL through router v2 (2026-11-19)

**Sources:** `leaf_scores.json` (score_leaves.py, 53,088 shadow rows, 324 games, 226 fit / 98 held out, 2026-10-03 to 11-19);
`12_EXPLORATORY/nhl_router_v2/results.json`. Pre-registration: `PREREG_W119_1_GOALIE_ST.md` (committed before scoring).

## Part B: layer-3 classes
- Tested 2 classes x 2 views (side, total) = 4 splits, 42 leaves. **Kept (reportable, held-out mean net > 0): 8 of 42** (goalie 2, special teams 6).
  23 leaves were reportable (not thin); **0 pass BH q=0.10**, so 0 DRAFT. Modal outcome in the PREREG held.
- Special teams has full coverage (324 games). Goalie has 178 of 324: a goalie needs 100 season shots and the 2026 box has 343 games.
  There is no pre-game lineup feed, so "last completed starter" is the proxy (registered gap). Goalie leaves are routed on thin evidence.
- **Defect found and fixed in this block:** the goalie shrinkage target (league save rate) was the whole-season total, which leaks later games
  into earlier rows. It is now an expanding rate; `test_goalie_no_leak_from_later_games` pins it. Numbers above are from after the fix.
- Reading: with 98 held-out games, a routed positive here is a lead for the next look, not a verdict.

## Part C: NHL through router v2 (pooled + sequential, W117.2 consensus prior, transfer sd 0.03)
- 99 seen NHL leaves across 9 cells (3 markets x T1-T3). **Every leaf routes to NO_BET; 0 armed.** Held-out (98 games): no bets placed, net 0.0,
  with or without the prior. Routed to no bet in these leaves; logs continue. Hypothesis closed (EXP-W119.1-NHL-V2, parked for R&D).
- Consistent with the box D6 read: no arm clears zero after costs yet. The sequential e-process needs more games than 324 to arm a leaf.
- `leaf_maps/nhl_v2.json` = `leaf_map_v2.json` with the seen NHL leaves replaced; other sports unchanged. Selected only by
  `PM_LEAF_MAP_VERSION=nhl_v2`; the default stays v1. Nothing flipped.
