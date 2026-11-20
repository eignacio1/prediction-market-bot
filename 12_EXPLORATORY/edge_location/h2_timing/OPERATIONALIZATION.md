# H2 timing — operationalization, frozen before any result is read

**Written:** 2026-11-20 (W123.2), before any CLV or drift number was computed. HYPOTHESIS.md section 3 H2 is the pre-registration;
this file only fixes the words it leaves open ("about 24 h", "close", "round cost"). It changes no rule, claim or threshold.

## Data
- Arm orders: box `logs/arm_orders/orders.jsonl`, `event == "arm_order"` (all rows are post-epoch; the log starts 2026-11-12). Pulled read-only.
- Shadow rows (model p): box `exp_output/PREGAME_SHADOW/{NBA,NFL}_*.jsonl`, rows from 2026-11-05. NHL has no shadow ledger there, so NHL
  enters Part A only (orders carry their own start time) and not Part B.
- Prices: `exp_output/PRICE_ARCHIVE/prices_*.jsonl` (about 3-minute cycles; each cycle covers a subset of series).
- Start time: the order's `start_time_utc`, else the shadow row's `start_time_utc` for the same event. No start time = excluded, counted.
- Game = sport + the date-team segment of the event ticker; every interval clusters by game.

## Definitions (fixed now)
- Price = yes mid (bid+ask)/2 from an archive snapshot; a snapshot counts only if bid > 0, ask > bid and spread <= 0.10.
- Close = the last qualifying snapshot at or before start and no more than 2 h before it. No such snapshot = excluded, counted.
- Part A CLV (per contract, in the order's own side): close price of that side minus entry price. Positive = the price moved our way.
  Games not yet started at read time are excluded. Buckets by `hours_to_start`: <1, 1-6, 6-24, 24-48, 48+. Reported over ALL orders
  (the pre-registration says every arm order), not only filled ones.
- Part B early points: the qualifying snapshot nearest to 24 h before start (window 22-26 h) and to 6 h (window 5-7 h). Drift = close mid - early mid.
- Signal = shadow `p_yes` minus the early mid, from the shadow row of the same market nearest the early snapshot in time (within 1 h).
  Consensus move: no free consensus exists at early horizons for NBA / NFL (closes only), so it is reported as not available, not as zero.
- Model: drift = a + b * signal [+ arm dummies in the second model]; fit on the first 2/3 of games by start date, b judged on the last 1/3
  (OLS slope on the held-out third, game-clustered bootstrap, 2,000 resamples, 90% interval).
- Round cost = full spread at the early snapshot + Kalshi taker fee 0.07 * p * (1 - p) (doctrine I.6). Also shown with the half-spread entry cost.
- Implied CLV (held-out) = mean of sign(signal) * drift per contract, minus the round cost. H2 is SUPPORTED only if the pre-registered rule
  holds at 24 h or 6 h (b > 0, interval excludes zero, implied CLV after cost > 0). UNDERPOWERED when the interval is wider than the
  effect that would matter; the n needed is stated from the observed variance at 80% power.
