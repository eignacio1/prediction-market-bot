# W121.3 / B-097 — Capacity and dollar ceiling per arm per sport

**Source:** box `capacity_read` 2026-11-20 ~15:20 UTC over `logs/arm_orders/orders.jsonl` (89,885 rows, post-epoch 2026-11-06T01:03:42Z only, GG-1771); net per contract from W117.1 (game-clustered, real spread, after fees, cross). Tables: `capacity_table.csv` / `capacity_table.json` / `ceiling.json` (dashboards read these); raw box output `capacity_read_20261120.json`.

**THIS IS A CEILING, NOT A SIZING RULE.** Kelly stays 0, no real capital moves, no arm is armed by this ranking. It only orders future wiring.

## What was measured, and what was not
- **Depth is measured live, per order, at decision time** (`book_at_submit` logged on every arm order). No depth constant is used anywhere.
- **Part A ticks 1 / 2 / 3: NOT MEASURABLE today.** Orders log the touch size only. The ladder archive (`DEPTH_ARCHIVE`, MLB/NFL series only) returned **0 files / 0 rows on the box** (MLB is idle; NFL ladder not captured). So within-1/2/3-tick depth is null for every sport. **NBA and NHL have no ladder captured at all.** Closing this needs a new capture series, which is a new live component (Hard Rule 14) — named for the window, not done here.
- What is reported instead: **touch size** both sides — *cross-touch* (what a taker crossing meets; this is what the ceiling uses, because the net estimates are for crossing) and *own-touch* (queue ahead of a resting order). Distribution = p25 / median / p75, by hours to start (0-2h, 2-6h, 6-24h, 24h+) in the JSON (`by_hours_to_start`).
- **NFL: 0 depth samples.** NFL arm orders carry no `book_at_submit` size, so NFL has fillable-size n = 0 and **no ceiling** (opportunities/day are counted: see table).
- Time bucket = hours to start as logged on the order (not hours-to-close).

## Net per contract (W117.1 cross, post-epoch) — every interval spans 0
| Arm | Net/contract | 95% interval | n |
|---|---|---|---|
| FADE | +0.166 | [-0.016, +0.348] | 105 orders / 20 games |
| RIDE | +0.016 | [-0.057, +0.089] | 253 / 22 |
| MOMENTUM | +0.052 | [-0.087, +0.191] | 96 / 21 |
| MODEL_FADE | no estimate (2 settled fills) | — | no ceiling stated |

Net is pooled per arm, not per cell, so the same number multiplies every cell of an arm. Because every interval spans 0, **every ceiling below has a lower bound under $0**; the point estimate is a ceiling-if-the-point-is-true, not a forecast.

## Method
$/day = opportunities/day × contracts × net/contract. Contracts = min(bankroll × 1% / entry, $25 event cap / entry, cross-touch depth). The 1% is a **scenario knob** (the demo book uses flat stakes; nothing here is bankroll sizing). Demo caps: event $25, arm/day $1,500, book/day $2,500, applied pro rata (the book/day cap binds: scale 0.556). Opportunity = distinct (day, ticker, side) among placed orders, routed skips and would-orders, per day the sport logged (NBA 9 days, NFL 6, NHL 4 — **short windows; per-day rates are noisy**). Low/high use depth p25/p75 with the net interval ends.

## $/day ceiling by arm and sport (point [low, high])
| Arm · sport | $1k | $10k | $100k |
|---|---|---|---|
| FADE · NBA | 1,116 [-106, 2,348] | 1,107 [-106, 2,325] | 1,107 [-106, 2,325] |
| FADE · NHL | 63 [-1, 131] | 64 [-1, 133] | 64 [-1, 133] |
| MOMENTUM · NBA | 86 [-145, 317] | 86 [-131, 316] | 86 [-131, 316] |
| MOMENTUM · NHL | 7 [-11, 25] | 7 [-11, 25] | 7 [-11, 25] |
| RIDE · NBA | 10 [-26, 54] | 10 [-21, 54] | 10 [-21, 54] |
| RIDE · NHL | 7 [-25, 40] | 7 [-26, 40] | 7 [-26, 40] |

$10k and $100k are identical: the $25 event cap binds before bankroll does; $1k is marginally different because at $10 per opportunity the 1% scenario stake, not the cap, sets the contract count. **The bankroll is not the limiting factor — the demo caps and touch depth are.** MODEL_FADE and NFL: no ceiling (no net estimate / no depth). The ceilings after the book cap are bounded by $2,500/day staked.

## Top 10 cells by ceiling ($10k bankroll; not a sizing rule)
| # | Cell | n orders | cross-touch median [p25, p75] | opps/day | $/day [low, high] | spans 0 |
|---|---|---|---|---|---|---|
| 1 | NBA · NBA_SPREAD · T3 · FADE | 159 | 1,695 [656, 2,123] | 60.9 | 830.6 [-80.1, 1,741.2] | yes |
| 2 | NBA · NBA_SPREAD · T2 · FADE | 126 | 608 [242, 1,896] | 50.2 | 138.3 [-13.3, 290.0] | yes |
| 3 | NBA · NBA_GAME_TOTAL · T2 · FADE | 38 | 218 [113, 1,176] | 27.2 | 100.9 [-9.7, 211.5] | yes |
| 4 | NHL · NHL_GAME_TOTAL · T2 · FADE | 21 | 910 [2, 3,550] | 15.0 | 51.2 [-0.1, 107.2] | yes |
| 5 | NBA · NBA_SPREAD · T2 · MOMENTUM | 105 | 1,086 [426, 2,375] | 64.2 | 32.8 [-54.9, 120.5] | yes |
| 6 | NBA · NBA_GAME_TOTAL · T3 · FADE | 14 | 244 [133, 585] | 9.6 | 28.8 [-2.8, 60.4] | yes |
| 7 | NBA · NBA_TEAM_TOTAL · T2 · MOMENTUM | 58 | 250 [25, 549] | 59.3 | 18.2 [-16.9, 66.8] | yes |
| 8 | NBA · NBA_TEAM_TOTAL · T3 · MOMENTUM | 77 | 250 [100, 2,000] | 39.3 | 13.7 [-22.9, 50.2] | yes |
| 9 | NBA · NBA_GAME_TOTAL · T2 · MOMENTUM | 66 | 727 [182, 3,732] | 29.1 | 9.3 [-15.6, 34.2] | yes |
| 10 | NBA · NBA_TEAM_TOTAL · T2 · FADE | 87 | 5 [1, 7] | 52.7 | 8.6 [-0.2, 21.7] | yes |

The ranking is FADE-heavy because FADE has the largest net point (+0.166) and NBA spreads have the most opportunities and deepest touch. That is the pooled estimate talking, not a per-cell finding.

## Fillable contracts, median cross-touch, by cell
All 51 cells with n, p25 / median / p75, own-touch median, opportunities/day and $/day at three bankrolls are in `capacity_table.csv`. Highlights: 
33 of 51 cells have n < 30 orders (read as indicative only); 3 cells have a median cross touch under 20 contracts (e.g. NBA|NBA_TEAM_TOTAL|T2|FADE, NHL|NHL_GAME_TOTAL|T1|MODEL_FADE, NHL|NHL_PUCK_LINE|T1|MODEL_FADE) — thin books, so size binds there. Large medians (NHL moneyline/puck line, NBA spread T3 MODEL_FADE in the thousands) are near-settled or far-from-touch quotes; treat them as 'not depth-limited', not as real capacity.

## Findings and caveats
1. Fillable depth is **not** the binding constraint in most NBA/NHL cells at demo stake sizes; the $25 event cap and the lack of a proven net are. Thin cells: NBA team-total T2 FADE (median 5), NHL game-total T2 FADE in the 2-6h bucket (median 1.5).
2. No cell's ceiling is distinguishable from zero. The largest, NBA spread T3 FADE, is +$831/day at the point and −$80 to +$1,741 across the interval.
3. Cross vs rest: resting orders fill 39/428 (RIDE), 57/340 (MOMENTUM), 22/342 (FADE touch) per W119.3 and are adversely selected, so the own-touch (queue) numbers are in the table but no ceiling is built on resting fills.
4. Opportunity counts include would-orders and routed skips; placed-order depth is applied to all of them (assumption: unplaced opportunities see similar depth).
5. Data windows are 4–9 days; per-day rates will move.

## Gaps registered for the window
- Ladder capture for NBA/NHL (and a working NFL/MLB archive on the box) to measure ticks 1–3 — new live component, needs the install gate.
- Per-cell net estimates (not pooled) once n permits.
- NFL arm orders log no depth at submit.
