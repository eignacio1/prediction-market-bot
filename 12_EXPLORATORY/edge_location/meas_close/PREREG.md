# H-MEAS-1 pre-registration: is the closing price a calibrated estimate of settlement, per family?

**Written:** 2026-11-24 (W124.2), BEFORE any settlement result is joined to any close. Program EDGE, measurement branch.
Binds with HYPOTHESIS_DOCTRINE Part I and COMMON_RULES_W124. Code: `run_meas1.py` (not yet written when this is committed).

## What has and has not been seen (disclosure)
- Seen: W123 H1 RESULT (aggregate gaps at the 15:00Z game-date snapshot, held-out thirds, per family) and H2 Part A (CLV of arm orders,
  gross, no settlement). Not seen: any settled result at a CLOSE price; no close has been computed by this block.
- Seen as a design fact, no outcomes: Kalshi `occurrence_datetime` is the EXPECTED END of a game (NBA IND-CHI: 04:00Z; the milestone
  start_date for the same game is 01:00Z), so it is not used as a start. Start comes from the public milestone `start_date` (below).

## Claim
Within a family, P(settles YES | closing yes-mid = c) = c: calibration slope 1, intercept 0. "Close" = the last QUALIFYING archive snapshot
at or before game start and no more than 2 h before it. Qualifying = yes_bid > 0, yes_ask > yes_bid, full spread <= 0.10, mid in [0.02, 0.98]
(H2 OPERATIONALIZATION definition, unchanged). No qualifying snapshot -> dropped, counted per family.
- Start = `start_date` of the Kalshi public milestone (types basketball / football / hockey / baseball game) whose `related_event_tickers`
  contains the market's event ticker. No milestone -> dropped, counted. Families with < 50% start coverage are reported UNMEASURABLE (no verdict).
- Results = Kalshi public settled `result` (yes / no), fetched read-only. Void / other results dropped, counted.
- Family = H1's taxonomy (`run_h1.py`: sport x moneyline / spread_main / spread_alt / total_main / total_alt / team_total / period_* / prop_*),
  with the main line chosen as the market whose CLOSE mid is nearest 0.5 in the event. Both tickers of a two-sided market are rows.

## Populations (the no-re-read rule)
- VERDICT population = markets whose start is before each sport's W123 split date (W123's FIT window, never judged by W123) UNION markets with
  start after 2026-11-20T20:00Z (forward). W123 split dates, frozen from H1: NHL 2026-11-12, NBA 2026-11-11, MLB 2026-09-25, NFL 2026-10-25.
  Disclosure: W123 computed raw gaps in the fit window at the 15:00Z snapshot to fix directions; here the price is the close, the claim is
  calibration and nothing in the fit window is fitted or selected, so it is a population W123 did not judge.
- EXCLUDED from any verdict: W123's held-out third (start between each split date and 2026-11-20T20:00Z). Shown only as a labelled DESCRIPTIVE table.
- Fit / judge split (item 4): nothing is fitted (the claim is the identity line), so the split is used for STABILITY and for the no-re-read rule.
  Early = W123 fit window; late = forward (after 2026-11-20T20:00Z). Reported per family where each has >= 30 games; a sign flip of the
  slope-minus-1 between early and late with both intervals excluding 0 downgrades LICENSED to NOT LICENSED (unstable). The pooled verdict
  population carries the verdict.

## Rule per family (>= 30 games AND >= 200 markets in the verdict population; fewer -> UNDERPOWERED, n needed stated)
1. Slope: OLS of y (1 if YES) on c over verdict rows; 90% percentile interval from a game-clustered bootstrap (2,000 resamples, seed 20261124).
   Condition S: the interval contains 1.
2. Bucket gap: price buckets [.02,.10) [.10,.25) [.25,.50) [.50,.75) [.75,.90) [.90,.98]. Condition B: the market-weighted mean over buckets
   of |settled rate - mean c| is below HALF one round cost, round cost = mean over verdict rows of (yes_ask - mid) + 0.07 * ask * (1 - ask)
   at the close (the H1 definition). Buckets with < 20 markets are pooled into the neighbour toward 0.5.
3. LICENSED = S and B and stable. NOT LICENSED otherwise, with a tag: `miscalibrated` (the debiased gap fails too) or `noise_limited`
   (the observed gap fails only because small buckets inflate |gap|: debiased mean |gap| = observed - 0.798 * mean bucket bootstrap SE is
   below half cost). The tag changes no verdict; it says whether more data could license. `noise_limited` families state n needed.
4. LICENSED means closing-line value MAY be the primary outcome for that family; settlement stays the confirmation. Nothing else changes.

## Favourite-longshot bias (how it is shown)
Per family: the bucket table (settled rate, mean c, gap, bootstrap interval), the fitted slope and intercept, and FLB = gap in the
two lowest buckets minus gap in the two highest (longshots over- vs under-priced). Shown, not a verdict input.

## Variance ratio (the effective-sample multiplier)
Per family, per contract, YES side: early = the qualifying snapshot nearest 6 h before start (window 5-7 h). settlement outcome = y - early mid;
CLV = close mid - early mid. Ratio = var(settlement outcome) / var(CLV), sd^2 both over the same rows (24 h secondary, window 22-26 h).
The ratio is the number of settlement-measured contracts one CLV-measured contract is worth, valid only where the family is LICENSED
and only for effects that move the price before the close. Reported for every family; used only for licensed ones.

## Second claim: our own orders
Orders: `logs/arm_orders/orders.jsonl`, event arm_order, post-epoch (Mac evidence copy, ends 2026-11-18T20:23Z; newer box rows are not read,
stated as a data limit). Own side, per contract: CLV = close of that side - entry price (limit); settled gross = y_side - entry. Regress
settled gross on CLV over orders whose game has settled (all orders; filled orders as a second line); game-clustered bootstrap, 90%.
Pass: the slope interval contains 1 and >= 30 games; < 30 games = UNDERPOWERED with n needed. Fee and spread are a constant cost, shown
beside, not in the slope. Start time = the order's own start_time_utc (H2 rule).

## Output and consequence
RESULT.md + results.json (per family: n markets / games, slope, intercept, intervals, bucket table, S, B, tag, verdict, variance ratio at
6 h and 24 h, drop counts), the W123 held-out DESCRIPTIVE table, the orders claim. Registry row H-MEAS-1 in HYPOTHESIS_DOCTRINE II.1.
LICENSED families may use CLV as a primary outcome in later pre-registrations; NOT LICENSED stay settlement-only. A null here is a
measurement routing result (hypothesis closed for that family, EXP H-MEAS-1, parked for R&D); no market, arm or cell closes.
