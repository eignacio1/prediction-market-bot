# EXP-042 — Ride cells: out-of-sample pre-registration (W91.1)

**Status:** FROZEN at commit (hash recorded in the commit message and in `results_W91_1.md`). Written 2026-10-28 ~01:00Z, **before any new row was read.** Nothing below may be edited after the freeze; a change is a new EXP with a superseding note.
**Pillar:** PROOF. **Measure:** ride cells pre-registered 0 -> 11 (forward look dates join P3); 89.2's cells tested out of sample 0 -> n of 11.
**Scope guard:** research only. No order, stake, kelly_fraction, gate, model, runner, registry cell or ledger is touched. Entry prices below are *hypothetical taker prices*, not orders.

## 1. The 11 cells (exactly as W89.2 defined them; `12_EXPLORATORY/longshot_bias/results_W89.md`)

Entry is a taker at the quote: YES at ask, NO at 1-bid. Fee = `fee_k007`. Depth at the quote is recorded, not filtered on. **No re-selection, no new buckets, side fixed.**

| # | Family | Tier | Bucket (p = mid) | Book | Side | W89.2 n / games | W89.2 net, 95% lo |
|---|---|---|---|---|---|---|---|
| 1 | KXMLBHIT | T0-2h | 20-25c | all | YES | 1892 / 368 | +.027, +.0065 |
| 2 | KXMLBHIT | T0-2h | 20-25c | tight | YES | 1151 / 339 | +.044, +.017 |
| 3 | KXMLBF5TOTAL | T6-24h | 90-95c | all | YES | 143 / 138 | +.038, +.022 |
| 4 | KXMLBF5TOTAL | T6-24h | 90-95c | wide | YES | 111 / 107 | +.033, +.011 |
| 5 | KXMLBF5TOTAL | T2-6h | 90-95c | tight | YES | 85 / 83 | +.043, +.017 |
| 6 | KXNFLTOTAL | D1 | 5-10c | all | NO | 154 / 92 | +.038, +.0065 |
| 7 | KXMLBSPREAD | T>24h | 20-25c | tight | NO | 186 / 147 | +.052, +.0026 |
| 8 | KXMLBTEAMTOTAL | T6-24h | 15-20c | tight | NO | 49 / 40 | +.095, +.0085 |
| 9 | KXMLBF5 | T2-6h | 10-15c | all | NO | 44 / 44 | +.078, +.0087 |
| 10 | KXMLBTOTAL | T0-2h | 85-90c | wide | YES | 52 / 52 | +.089, +.047 |
| 11 | KXMLBF7 | T0-2h | 40-45c | wide | YES | 121 / 88 | +.065, +.0006 |

Definitions inherited unchanged from `calib.py`: tight = half-spread <= 0.01, wide = otherwise, all = both; MLB tiers by hours to first pitch (T>24h, T6-24h, T2-6h, T0-2h); NFL tiers by ET calendar day before kickoff (D0 excluded, GG-1252); p = mid of the first two-sided pre-start observation per (ticker, tier); `side_pnl` YES = y - ask - fee(ask), NO = (1-y) - (1-bid) - fee(1-bid). Game-clustered bootstrap (1000 resamples, seed 20261027) and `benjamini_hochberg` from `prediction_market_bot.quant.inference`.

## 2. Backward test (Part B of W91.1)

**Window = every date before 2026-08-01 that Kalshi lists** for the family (determined by the listing inventory taken *before* this file; metadata only, no prices or outcomes):

| Family | Listed from | Backward window |
|---|---|---|
| KXMLBHIT, KXMLBF5TOTAL, KXMLBF5 | 2026-03-26 | 2026-03-26 .. 2026-07-31 |
| KXMLBTEAMTOTAL | 2026-04-01 | 2026-04-01 .. 2026-07-31 |
| KXMLBSPREAD, KXMLBTOTAL | 2025-10-01 (2025 postseason, ~220 markets) + 2026-03 | 2025-10-01 .. 2026-07-31 |
| KXMLBF7 | 2026-07-01 | 2026-07-01 .. 2026-07-31 only |
| KXNFLTOTAL | 2025-08-21 | 2025-08-21 .. 2026-01-31 (2025 season, D1 only) |

MLB 2025 regular season is not listed for any of these families. Cell 11's backward window is one month; its expected outcome is UNTESTED and it then rests on the forward test alone. A family not listed for a date contributes NONE for that date; it is never imputed.

**Method.** Hourly candles. For each (ticker, tier) the first two-sided hourly candle (bid and ask both present) whose end falls inside the tier gives bid/ask at the candle close; tier = hours from candle end to true first pitch/kickoff. True start times from MLB StatsAPI / ESPN schedule, joined by date + teams (not by the ticker's HHMM, which is assumed ET, GG-1253; the check of that assumption is a Part B deliverable). W89.2 used the first ~20-minute archive snapshot. **Method difference, stated:** an hourly candle close is a coarser, later-in-the-hour observation than a 20-min snapshot, so entry prices differ by up to an hour of drift and a ticker can fall in a different tier or bucket. This is why the overlap check comes first.

**Overlap check (before any pre-August date is read).** Run the candle method on 2026-08-01 .. 2026-10-27 for the same cells, on every game for which the archive and the candles both exist. Pass iff all of: (a) >= 85% of matched (ticker, tier) observations land in the same 5c bucket; (b) |mean entry-price difference| <= 0.01; (c) for every cell with >= 30 overlap games, the candle-method net/contract lies inside W89.2's 95% interval for that cell. **If any condition fails, the backward test is VOID and `results_W91_1.md` says so; no earlier date is then scored.** The overlap sample is also fetch-budgeted by the rule below, so a cell with < 30 overlap games is judged on (a) and (b) alone.

**Fetch rule (outcome-independent).** One sport at a time, phases separate (list -> schedule -> candles), so a later phase cannot overwrite an earlier phase's output (89.7 lesson). Every strike of every event in the window, no sampling. Order: smaller families first (F5TOTAL, F5, TOTAL, TEAMTOTAL, SPREAD, F7, KXNFLTOTAL), KXMLBHIT last; within a family newest event first. Fetching stops at a hard wall-clock cap per part, **not** on any observed price or outcome. Coverage (fraction of listed events/strikes fetched) is reported per cell; a cell whose fetched coverage leaves < 30 games is UNTESTED, not FAIL.

**Per-cell status.**
- `n_games < 30` in the backward window -> **UNTESTED** (a thin cell proves nothing either way; the GG-1292 lesson).
- Otherwise score net/contract per cell with the game-clustered 95% interval, one-sided p for BH.
- **HELD_OUT** iff: BH-flagged at q = 0.10 across the cells that were testable, AND clustered 95% lower bound > 0, AND the sign agrees with the fixed side. Else **FAILED**.

## 3. Forward test

Archive rows (`exp_output/PRICE_ARCHIVE/prices_*.jsonl`) with timestamp after the freeze commit time, same method as W89.2 (first two-sided snapshot per ticker per tier). Scored once per cell at its look, not before ("no score read below judged n").

**Judged n.** Judged games = ((z_a + z_b) * sigma_c / delta)^2, one-sided alpha = 0.05 (z = 1.645), power 0.80 (z = 0.842), delta = W89.2's measured net, sigma_c = cluster SD implied by W89.2's interval (SE = (net - lo)/1.96, sigma_c = SE * sqrt(games)). Because W89.2 picked these cells for being the best of many, the measured effect is a winner's-curse upper bound; the *half-effect* column is the honest planning number and is the judged n used for a PASS call. Reaching the full-effect n earlier gives a "look" but only reports; it cannot pass.

| Cell | Judged games (full effect) | Judged games (half effect = judged n) |
|---|---|---|
| 1 | 342 | 1367 |
| 2 | 206 | 823 |
| 3 | 40 | 158 |
| 4 | 77 | 307 |
| 5 | 49 | 196 |
| 6 | 102 | 408 |
| 7 | 214 | 855 |
| 8 | 54 | 214 |
| 9 | 56 | 224 |
| 10 | 19 | 75 |
| 11 | 140 | 557 |

**When each look falls.** MLB accrues nothing between the World Series (ends by ~2026-11-01) and opening day (~2027-03-25). Games/day per cell from W89.2 (n_games / 58 archive days). Earliest *full-effect* look date (opening day + judged/rate): cell 1 ~2027-05-18, 2 ~04-29, 3 ~04-11, 4 ~05-06, 5 ~04-28, 7 ~06-17, 8 ~06-11, 9 ~06-07, 10 ~04-15, 11 ~06-25. The half-effect looks (the ones that can pass) need ~4x the games: for the fast cells that is after the 2027 All-Star break, and for cells 7, 8, 9, 11 it is **at or after the end of the 2027 regular season**, i.e. they may need two seasons; each such cell is reported with its realised accrual at 2027-10-01 and does not pass early. Cell 6 (KXNFLTOTAL D1, ~12 games/week archive): full-effect look ~2026-12-21, half-effect (408 games) is **not reachable in one NFL season** (~270 games) and needs 2027's season; it rests on the backward test + pooled 2025+2026 reading. These dates are a clock for *when to look*; a look happens when judged games are reached, not on the date.

## 4. Pass rule and pre-registered modal outcomes

A cell is **PASS** (HELD_OUT in backward; FORWARD_PASSED in forward) iff net lower bound (game-clustered 95%) > 0 AND BH q = 0.10 across the 11 (separately for backward and forward) AND side/sign as fixed. A cell failing either is not promoted; one backward FAIL does not kill a cell that is UNTESTED forward, and one forward PASS needs no backward pass but the table records both.

**Modal outcome (stated before the data).** Most cells regress to zero, as selected-from-many cells do. Backward: 2-4 of 11 testable, <= 2 HELD_OUT; cells 8, 9, 10 and 11 most likely UNTESTED (n_games < 30 after the window and coverage). Cell 1 and 2 (the largest-n cells) are the most likely to hold if any do. If 0 of 11 hold, that is a result: the W89.2 ride set is a data-snooping artifact and RIDE stays empty. Forward: modal outcome = zero PASS before 2027-06; cell 3 and 10 are the first judged looks (2027-04).

## 5. Statuses (ride-table contract with 91.2)

`ride.py` reads `ride_cells.toml` with statuses IN_SAMPLE / HELD_OUT / FORWARD_PASSED / FAILED / UNTESTED. This file fixes: all 11 start IN_SAMPLE; the window (not this block) writes the moves. RIDE only for HELD_OUT or FORWARD_PASSED.

## 6. Out of scope / gaps

New cells, buckets or sides (any) -> a new EXP. Depth, fill and slippage are recorded, not tested. Anything unfetchable in budget -> a GG, with the coverage stated.
