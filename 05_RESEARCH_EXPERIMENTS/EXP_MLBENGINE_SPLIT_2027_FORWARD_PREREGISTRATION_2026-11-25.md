# EXP-MLBENGINE-SPLIT-2027 — MLB engine price as a router input, 12 game cells, 2027 forward test (pre-registration)

**Frozen:** 2027-03-01T00:00:00Z (rows scored are those with `run_ts` at or after this instant). **Committed 2026-11-25, before any 2027 row exists.**
**Pillar / measure:** PROOF P3 (MLB next look dated, 0 → 12 cells) and DEPTH D6 MLB. Standing authorization 2026-10-08 (new pre-registration); named in `RESULT_W127_2_C.md` and the W127.2 handoff.
**Status:** frozen; nothing here is wired to an order, gate, runner or ledger. Shadow only, Kelly 0, no stake. It sits beside `12_EXPLORATORY/mlb_lookback/PREREG_2027.md` (the look-back routing test, MLB-2027) and does not replace it.

## Question
Does adding the MLB engine's price as a layer-1 input (`engine_gap = engine p_yes − market mid`, terciles) to each existing leaf let router v2 earn an arm that clears zero **after the exact Kalshi fee**, on 2027 rows only? The engine price is one input to the tree, never the bet (ADR-0077). "Raw sim beats the market mid" is already closed as a hypothesis (EXP-MLBSIM-001, parked for R&D) and is not what is tested here.

## Pinned inputs
| Input | Pin |
|---|---|
| Engine | `src/prediction_market_bot/mlb_engine/` (`forecaster.MLBEngineForecaster`, `joint_board`, `sim`, `pit`), merge state of origin/main `023c680`; no refit in season (Hard Rule 4) |
| Cells | 12: `MLB_MONEYLINE`, `MLB_RUN_LINE`, `MLB_GAME_TOTAL`, `MLB_TEAM_TOTAL` × T1, T2, T3. Rung units: KXMLBTOTAL k = total ≥ k; KXMLBSPREAD k = win by ≥ k; KXMLBTEAMTOTAL k = team runs ≥ k |
| Leaf map prior | none. Every leaf starts NO BET; the 2026 look-back map and the 2026 postseason are a prior for nothing and are not pooled in as evidence |
| Router | v2 (pooled posterior + e-process), arms per leaf: RIDE, FADE, MOMENTUM, MODEL_FADE (`model_p > market + vig`, the fade arm's entry rule), POT_OF_GOLD where a leaf has longshot / parlay rows, NO_BET |
| Fee | `quant/money.py::fee`, exact, taker, rounded up to a centicent; spread at the quote; both reported |
| Variance | the 2026 per-cell game variance in `mlb_lookback/results.json` → `power_calendar_2027.var_game` |
| Data epoch | NO-side demo fills before 2026-11-06T01:03:42Z were mirror-priced; not used. All scored rows are 2027 |

## Rule (frozen)
1. Every shadow row at each band logs `engine_p`, `engine_gap = engine_p − mid`, the market state fields, and the engine input stamp (lineup source, Savant store date). A row with no engine price is logged with `engine_gap = null`, falls in its own "no engine" tercile, and is counted in a skip-reason number; it is never imputed.
2. `engine_gap` terciles (cut points fit on 2027 rows to date, refit weekly at each look using rows before that look) are added as a leaf-key field under each existing leaf.
3. The arm per leaf is chosen by router v2 on 2027 rows only: a leaf arms only when P(net>0) ≥ 0.90 and the path-averaged e-value ≥ 10 (alpha 0.10), at 10+ settled games in the leaf.
4. Scored unit: the **game**. Net per row = payout − entry (at the ask, the arm's own side) − exact fee, held to settlement. **Gross, round cost (spread + fee) and net are reported side by side** per cell and per arm; settlement is the final score from the public scoreboard. Regular season only; the postseason is excluded.
5. Intervals are game-clustered (bootstrap, 2,000 resamples, seed 20270301). **Benjamini–Hochberg at q = 0.10 across the 12 cells.**
6. A cell PASSES iff it is BH-rejected and its net lower bound is > 0 at or after its judged n. A pass is a finding that licenses a separate pre-registered order arm, not an activation. A non-pass is routed (ride / no bet in those leaves), never "no edge", and closes only this test ("hypothesis closed (EXP-MLBENGINE-SPLIT-2027, parked for R&D)"); no cell, market or arm closes.

## Judged n (from the 2026 variance, `quant.variance.games_needed`)
One-sided, α = 0.05, power 0.80, game as the unit (rows_per_game 1, icc 0), minimum effect **+0.02 net per contract**; the +0.04 column is the larger effect. Games to settle, at an assumed 90 games/week (the same assumption as the look-back calendar).

| Cell | var_game | n at +0.02 (T1 / T2 / T3) | n at +0.04 (T1 / T2 / T3) |
|---|---|---|---|
| GAME_TOTAL | .01792 / .01842 / .01785 | 277 / 285 / 276 | 70 / 72 / 69 |
| MONEYLINE | .24504 / .25239 / .25171 | 3,788 / 3,902 / 3,891 | 947 / 976 / 973 |
| RUN_LINE | .04184 / .03772 / .03785 | 647 / 584 / 586 | 162 / 146 / 147 |
| TEAM_TOTAL | .01688 / .00988 / .00881 | 261 / 153 / 137 | 66 / 39 / 35 |

These are the whole cell's settled games and are a **floor**: a leaf sees fewer games than its cell, so a leaf can reach its 10-game minimum long before the cell reaches judged n, and an arm may be earned (router v2) before the cell is scored.
**Stated plainly: MONEYLINE cannot reach judged n at +0.02 inside the 2027 season** (≈ 2,430 games; MDE at 2,430 games ≈ 0.025). It is read at the season-end look, labelled UNDERPOWERED.

## Look dates (calendar 2027; Tuesdays 10:00 UTC, the weekly router look)
Assumption, stated: opening day **2027-03-25**, regular season ends **2027-10-03**; both are **expected dates to confirm against the MLB schedule** (the arm-date alarm in `mlb_board_install.py` reads the real first game from the schedule cache). The dates below move with the real opening day by the same number of days.
- **Weekly router looks:** every Tuesday from 2027-03-30. Router v2 only; descriptive counts otherwise; no score is read below a cell's judged n.
- **Scored looks (cell reaches n at +0.02):** TEAM_TOTAL T2 and T3 **2027-04-13**; TEAM_TOTAL T1 **2027-04-20**; GAME_TOTAL T1–T3 **2027-04-27**; RUN_LINE T2 and T3 **2027-05-18**; RUN_LINE T1 **2027-05-25**.
- **MONEYLINE T1–T3:** first read at the n for +0.04 on **2027-06-15** (labelled: powered only for ≥ +0.04), final read at the season-end look.
- **Season-end look: 2027-10-05.** Every cell not yet at its judged n is read here and labelled UNDERPOWERED with its achieved MDE.
- A fresh 2028 continuation, if any, is a new dated pre-registration.

## Modal outcome (stated before any 2027 row)
- **Game total, team total, run line (9 cells): NOT DISTINGUISHABLE at the scored look, ~80%; router v2 arms RIDE on some team-total T2/T3 and total leaves by midseason ~30%** (the look-back lead: RIDE on TEAM_TOTAL T2/T3). A cell BH-rejected with lower bound > 0: ~10%. A cell significantly negative net of fee (fee drag): ~10%.
- **Moneyline (3 cells): NOT DISTINGUISHABLE and UNDERPOWERED at 2027-10-05, ~90%.** Router v2 arms no moneyline leaf: ~90%. Close prices are efficient and the 2026 moneyline model-vs-market gain was −0.0037.
- **Across the 12 cells:** the engine tercile earns an arm on at least one leaf (any arm, not NO BET): ~35%. All 12 cells end the season with every leaf RIDE or NO BET: ~45%.

## How this differs from the look-back test and from EXP-029 / EXP-MLBSIM-001
The look-back test (PREREG_2027) asks whether the 2026 leaf routing holds, on market-state leaves only. This test adds the engine tercile as one more split under those leaves. EXP-MLBSIM-001 compared the raw sim to the market mid by Brier, which is not the verdict here; a result in one says nothing about the other.

## Dependencies (named, not assumed)
- Engine prices exist on a row only if the daily board runs (`scripts/mlb_board_install.py`, a named `*_install` the operator approves) and the Savant store is current through the prior day. The Stats API 406s the box and the store is built off-box, so the board job reads a synced store and schedule cache; a stale input logs `engine_gap = null` and an alarm. Without the install this test scores the market-state leaves only, and says so in its result.
- Savant returned header-only files for every October 2026 day; the in-season feed must be confirmed in April.

## Not done by this pre-registration
No order, position, stake, `kelly_fraction`, runner, cron line, registry cell, leaf map, `PM_LEAF_MAP_VERSION` or gate is created or changed.
