# W60.1 — Is the only ACTIVE cohort real? (GG-300) + Monday overwrite guard (GG-228)

Run 2026-10-08 on the VPS, demo venue, read-only GETs. Script: `scripts/w60_1_cohort_fill_truth.py`. Per-row output: `W60_1_cohort_fill_truth_rows.json`.

## Part A — fill truth for the T4M-PROJ epoch-12 clean cohort

**Verdict:** Of 1,952 epoch-12 closed rows, only 107 (5.5%) correspond to a real demo fill. 1,845 (94.5%) have no fill in the venue's complete fill history. Those 1,845 are paper P&L for orders the demo venue never filled. The cohort can claim "the model and its paper-settlement arithmetic produced these results". It cannot claim that these were executed trades. On the 107 real fills P&L is -$0.403/bet, and the CI excludes zero.

### 1. NOT_RETRIEVABLE sample
30 of the 731 (seeded, seed 60) were re-queried: **30/30 return HTTP 404 `not_found`**, the same as at T-571. No 410s and no other codes. A 404 on single-order lookup means the order object is gone. It does not mean "filled but purged": 730 of the 731 have no fill in the fills history either (see 3).

### 2. Venue history and retention
| Endpoint | Rows | Pages | Earliest | Latest | Pagination |
|---|---|---|---|---|---|
| GET /portfolio/fills | 2,572 (2,572 unique fill_ids) | 3 | 2026-05-19T01:09Z | 2026-10-08T00:23Z | ran to end (no cursor left) |
| GET /portfolio/settlements | 90 | 1 | 2026-07-21T04:50Z | 2026-10-08T01:56Z | ran to end |

Fills retention reaches back past the cohort start (2026-07-31), so no cohort row is outside the horizon. Fills exist in every month May–Oct, so there is no coverage hole. Settlements are aggregated per ticker, so they were used only as corroboration (0 UNVERIFIABLE rows needed it). Of the 2,572 fills, 332 are KXMLBHIT. The rest are NBA tickers from the earlier book.

Joins: 103 by `kalshi_order_id`, **4 by the fallback** (ticker + side + ±180 s of `entered_at`). 0 rows lack an order id.

### 3. Classification (cohort n=1,952; 770 WIN / 1,182 LOSS)
| Label | n | Basis |
|---|---|---|
| CONFIRMED_FILLED | 107 | 103 order-id match + 4 fallback |
| CONFIRMED_NOT_FILLED | 1,845 | 139 order lookup said CANCELED (T-571), 1,706 no fill in a complete fills history that covers the row's date |
| UNVERIFIABLE | 0 | — |

The 731 T-571 NOT_RETRIEVABLE rows resolve as 730 NOT_FILLED + 1 FILLED. The T-571 "34 confirmed" grew to 107 only because newer rows and the full fills list were checked. The cohort has also grown from 1,898 to 1,952 since W59.1.

### P&L per bet, game-clustered (176 games total; t-critical on G-1 df)
| Set | n | games | mean P&L/bet | 95% CI | total |
|---|---|---|---|---|---|
| All rows | 1,952 | 176 | -0.0526 | [-0.148, +0.043] | -$102.72 |
| CONFIRMED_FILLED | 107 | 41 | **-0.4026** | [-0.650, -0.156] | -$43.08 |
| CONFIRMED_NOT_FILLED (paper-only) | 1,845 | 174 | -0.0323 | [-0.133, +0.068] | -$59.64 |

Caveats. The fills-absence inference assumes the fills endpoint is complete for this account. The evidence is full pagination, unique ids, 103/107 order-id agreement and continuous monthly coverage. It is not proof. Filled rows are not a random subset: fills may depend on price or liquidity, so -0.40/bet on n=107 may not describe what the paper rows would have earned. P&L here is the ledger's recorded `pnl`; I did not recompute it from fill prices.

## Part B — GG-228 guard
(pending)
