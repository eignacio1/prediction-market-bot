# W118.1 MLB 2026 look-back through router v2 — RESULT
Last reviewed: 2026-11-18. Spec frozen before results: SPEC.md (commit "W118.1: MLB look-back frozen spec"). Reproduce: `PYTHONPATH=src python3 12_EXPLORATORY/mlb_lookback/run.py <scratch>`; numbers in `results.json`.

## Corpus (Part A, as run)
Premise correction: the game-market shadow ledger holds the **postseason only** (2026-10-05..10-29), not the regular season. Operator chose the
postseason-only look-back on 2026-11-18 ("Proceed with recommendation"). 2,153 settled rows -> 2,087 after dedupe; 12 cells
(MONEYLINE / RUN_LINE / GAME_TOTAL / TEAM_TOTAL x T1-T3), 22 games per cell. SPEC said "22 games"; the game-id split sees **25 ids**
(3 games carry a different id in at least one family — a join caveat, logged as a gap, not corrected here). Split (2/3 by start time):
16 fit games / 1,302 rows, 9 held-out games / 785 rows. Held-out games per cell are **8-9, under the 10-game minimum: nothing here is judged.**

## Routers (Part B)
| Router | fit-window leaves armed | held-out net / row (90% game-clustered) |
|---|---|---|
| v2 pooled + e-process (no prior) | 0 of 80 | 0.0000 (no bets) |
| v1 per leaf | 0 of 80 (all thin) | 0.0000 (no bets) |
| ride every favourite | n/a | +0.0366 [-0.0241, +0.0896], 9 games |
| always FADE | n/a | -0.0782 [-0.1239, -0.0272] |
| always MOMENTUM (where a move exists) | n/a | +0.0415 [-0.0175, +0.1052], 8 games |
Full-corpus v2 (frozen map): 81 leaves, 0 armed. Per cell held-out net by arm: `results.json` -> `heldout_unrouted_arm_by_cell`.
What the held-out rows show (description, not verdict): RIDE is positive in 11 of 12 cells but every interval spans 0 except
TEAM_TOTAL T2/T3 (+0.058 [+0.015, +0.101], +0.058 [+0.020, +0.098]); FADE is negative everywhere and its intervals exclude 0 in 6 cells; MODEL_FADE is negative on MONEYLINE.

## Routing per cell (Part B.3)
All 12 cells: **NO BET provisional** (v2 arms nothing on 25 games). Hypothesis closed (EXP-W118.1-MLB-<cell>, parked for R&D); logs continue in 2027.
RIDE is the baseline the 2027 test measures against. This is a routing result, not "MLB failed": 0 cells have an earned arm, 12 have a recorded routing.

## MLB layers 1-5 (d6 shape, `results.json` -> `d6_mlb_lookback`)
12 registered game cells: layer 1 (logged model p) 12, layer 2 (market-state leaves) 12, layer 3 (factor filters as splits) 0,
layer 4 (non-thin armed leaf) 0, layer 5 (leaf with 10+ held-out games) 0. Wired 0. d6_read itself is unchanged.
Out of scope: the 6 other MLB game cells and the player-hit / T4M cells are not in this ledger.

## Measure moved
MLB cells routed 0 -> 12 recorded (all NO BET provisional; **earned arms 0**). P1: 0 of 12 at a scored look (below judged n). P2: 0 verdicts issued.
