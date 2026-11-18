# W116.3 Part A - D6 trace tables (NBA, NFL, NHL) and the coverage-rule findings

**Last reviewed:** 2026-11-18 (W116.3, B-091 + B-092). Sources, all box reads on box HEAD 53c83e86 (contains #503, deployed 2026-11-18T00:54:51Z):
`04_EXECUTION/BOX_TASKS/results/20261118T010409Z_d6_trace_read.md` (3-day window, 35,171 arm-order rows; the NBA game block is cut
mid-output by the bridge, so its NBA game name is unreadable), `20261118T010409Z_d6_read.md`, and `20261118T010409Z_deploy_truth_read.md`. The traced games
started before #503 deployed, so every row in them was logged by the pre-fix code. The row-level layer 6 (`size_for` on the row) cannot show
on them yet. It shows on rows logged after 00:54:51Z, and PR #507's `error_after` field reads exactly that.

Layers (`coverage.d6_layers`): 1 model p · 2 market state · 3 factor filters · 4 tree arm · 5 held-out net · 6 sizing · 7 post-epoch fills.

## NBA (D6 wired 3: NBA_GAME_TOTAL T3, NBA_SPREAD T2, NBA_SPREAD T3)

| Layer | File / log | What was there | The break |
|---|---|---|---|
| 1 | `logs/shadow/NBA_*.jsonl` (`nba_pregame_v1`) | p on every game-family row; props rows carry p too | Props cells (16) fail layer 1 in d6_read: no arm-path rows for them |
| 2 | same rows, `router.move_source` | mid, horizon, move source on every routed row (`ledger_tail` or `na:unavailable`) | none |
| 3 | `router.filters_n`, `filter_data/nba_team_percentiles.json`, `filter_splits.json` | filters on 533-1,992 rows per game cell; **rows with a kept split: 0 in every traced cell** | Rule credits layer 3 from the split file, rows never fired a kept split (GG-1951). NBA_TEAM_TOTAL T1-T3: no kept split in the file at all |
| 4 | `router.branch` / `reason`, `leaf_map.json` | FADE / RIDE / MOMENTUM leaves on GAME_TOTAL T2/T3, SPREAD T2/T3; `leaf_thin` and `leaf_not_in_map` elsewhere | NBA_SPREAD T1: no non-thin arm leaf. Props: `leaf_not_in_map` on every row |
| 5 | `leaf_map.json` `test.test_n_games` | ≥ 10 on the arm leaves of the wired cells | none on wired cells |
| 6 | `size_for` (arm rows; row-level after #503) | size_for on 31-65 arm-path rows per wired cell | NBA_GAME_TOTAL T1: every sizing came back NO_BET |
| 7 | `logs/arm_orders/orders.jsonl` + demo fills | post-epoch fills on the 3 wired cells | NBA_GAME_TOTAL T2: orders, no post-epoch fill yet |

ERROR rows in the window: 3,096 (`KeyError` 2,367 + `KeyError:'market_ticker'` 729), all logged before #503.

## NFL (D6 wired 0; game 26NOV16LACBAL)

| Layer | File / log | What was there | The break |
|---|---|---|---|
| 1 | `logs/shadow/NFL_*.jsonl` | p on all 12 game-family cells (T1-T3) | T4 / T4NFL-* / T5 and the pass-yards prop: no rows |
| 2 | same rows | router block on every row (router = rows in every cell) | none |
| 3 | `filter_data/nfl_*.csv` + `nfl_weather_backfill.csv`, `filter_splits.json` | filters on 20-1,325 rows per cell; 25 rows per cell dropped weather with `pit_violation` (forecast dated after the row, guard working) | **No NFL series has a kept split in filter_splits.json** → layer 3 = 0 on all 9 spread / total / team-total cells |
| 4 | `router.branch` | RIDE / FADE on SPREAD, TOTAL, TEAM_TOTAL; MONEYLINE all NO_BET (`leaf_not_in_map`, `leaf_thin`) | MONEYLINE T1-T3 |
| 5 | `leaf_map.json` | test_n_games ≥ 10 on 9 cells | none past layer 3 |
| 6 | size_for | 11-74 arm-path rows sized per cell | none past layer 3 |
| 7 | arm orders | post-epoch ok orders: SPREAD T3 5, TEAM_TOTAL T3 1; 4 cells pass the fills rule | needs layer 3 first |

ERROR rows in the window: 181 (`KeyError`), all before #503. Re-run of the first one under today's code: routes RIDE (`NFL|NFL_GAME_TOTAL|T2|4|flat`).

## NHL (D6 wired 0; game 26NOV16VANUTA)

| Layer | File / log | What was there | The break |
|---|---|---|---|
| 1 | `logs/shadow/NHL_*.jsonl` | p on all 9 game-family cells | T4 / T4NHL-* / T5: no rows |
| 2 | same rows | router block on 10-693 rows per cell, **absent on rows logged before the W115.3 hook** (the traced game: router 0) | rows before #502 (GG-1940) |
| 3 | `exp_output/NHL_EVENTS/*.parquet` | **store directory does not exist on the box**; every row `filters_unavailable:nhl_game_not_in_store` | the store (GG-1953); PR #507 makes it fit, the install waits on approval |
| 4 | router.branch | RIDE on GAME_TOTAL T2/T3, MONEYLINE T2, PUCK_LINE T2/T3 | T1 cells: `leaf_not_in_map` |
| 5 | leaf_map.json | test_n_games ≥ 10 on 7 cells | - |
| 6 | size_for | sizing passes on 5 cells | - |
| 7 | arm orders | post-epoch fills on 2 cells | - |

ERROR rows in the window: 97 (`KeyError:'market_ticker'`), all before #503. Re-run under today's code: NO_BET `leaf_not_in_map`, no raise.

## Coverage rules the box cannot satisfy (findings)

1. **Layer 3 is credited from `filter_splits.json`, not from rows** (GG-1951). Every traced row, wired NBA cells included, has
   `split_kept` empty. Either the router's split lookup never matches the file's keys, or the rule over-credits. Until that is settled,
   the 3 wired NBA cells pass layer 3 on paper only. PR #507 adds the window-wide `split_kept` count per cell so the next read shows it.
2. **NFL layer 3 cannot pass on any NFL cell**: the box has NFL filter data, but `filter_splits.json` keeps no NFL split. Six NFL cells
   miss D6 by this one layer (NFL_GAME_TOTAL T3, SPREAD T1/T3, TEAM_TOTAL T3 miss exactly one).
3. **NHL layer 3 needs a store the box does not have** (GG-1953). The store's build did not fit the 961 MB box (2,049 MB compile,
   913 MB filter state). PR #507 brings that down to 270 / 318 MB; `nhl_event_store_install` is in "Needs your decision".
4. **Layer 6 at row level is unreadable on pre-#503 games**: the traced games' rows have `row_size_for` 0 because they predate #503.
   This is not a break. The next trace after #507 deploys reads it on new rows.
5. **Layer 5 needs `test_n_games ≥ 10`**. That holds on every arm leaf of a cell past layer 4. Not a break today.
