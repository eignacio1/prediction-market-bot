# H-EDGE-5 pre-registration: favourite-longshot bias at the close, per family x price bucket

Last reviewed: 2026-11-24. **Written:** 2026-11-24 (W125.3), BEFORE any 2025-26 settlement result is joined to any price.
Program EDGE. Binds with HYPOTHESIS_DOCTRINE Part I and COMMON_RULES_W125. Code `run_h5.py` is not written when this is committed.

## Claim
At the close, a contract's settled rate departs from its price in the favourite-longshot direction (favourites settle ABOVE their
price, longshots BELOW) by more than one round cost (taker fee at the entry price + half the spread at the close), in at least one
price bucket, in a family. Equivalent test: mean NET per contract of the bucket's arm > 0.

## What has and has not been seen (disclosure)
- Seen as counts only in this block: market rows per series by close month in the on-disk Kalshi stores (no `result` read, no price joined).
- Seen before this block, outcome-bearing, on this population: **W117.2 read NHL moneyline 2025-26 regular season (1,312 games, last
  hourly candle >= 1 h before start): Kalshi-vs-books gap +0.0016 and "riding consensus at ask" -0.055.** That is not a bucketed
  favourite-longshot read, but it is an outcome read on the same games and prices; any NHL moneyline verdict below is therefore
  labelled "population previously read by W117.2 (not by bucket)". No other family below was read at 2025-26 by any earlier test.
- Seen, other populations (not judged here): H-MEAS-1 (#558) close slopes on 2026-27 rows (NHL ML 1.71, NBA ML 1.26, NHL TT 1.10);
  W89.2 / W122.2 pot-of-gold cells on the 2026 price archive. Those are the reason this hypothesis exists; they are not in this
  population (2025-26 only) and nothing from them is reused as a threshold.

## Population (fixed now)
2025-26 REGULAR SEASON games, by game start. Cut-offs: NHL start 2025-10-07 .. 2026-04-16; NBA 2025-10-21 .. 2026-04-12 (NBA Cup
games included, play-in and playoffs excluded); NFL 2025-09-04 .. 2026-01-04. Playoffs and preseason excluded and counted. Never
judged by H-MEAS-1 (it read 2026-27 and later). Start time = Kalshi public milestone `start_date` whose `related_event_tickers`
contains the market's event ticker (the H-MEAS-1 rule; `occurrence_datetime` is the expected END, not used). No milestone -> dropped,
counted; a family with < 50% start coverage is reported UNMEASURABLE.

## Families (fixed now; any addition is made BEFORE the join, never after)
| Family | Series | 2025-26 history on disk (counts of market rows, by close month; no outcomes read) | Status |
|---|---|---|---|
| NHL moneyline | KXNHLGAME | 3,330 markets with hourly candles (w84-3 store, 2025-09 on) | in |
| NBA moneyline | KXNBAGAME | 2,958 markets listed 2025-10..2026-06; candles NOT stored for 2025-26, fetched read-only by this block | in |
| NBA team total | KXNBATEAMTOTAL | 9,486 markets, listed 2026-02..2026-06 ONLY (Oct-Jan 2025-26 not listed in any store); candles fetched | in, partial season |
| NFL team total | KXNFLTEAMTOTAL | 791 markets 2025-12..2026-02; regular season = Dec 2025 - 4 Jan 2026 only; candles fetched | in, last weeks only |
| NHL team total | KXNHLTEAMTOTAL | **none**: the only rows on disk close 2026-09 or later (README: live endpoint only, no history) | NO POPULATION; written as such, reopen trigger = Kalshi history lists it |
No other family is added. Spread, total and alt lines are not part of this hypothesis.

## Price (the close) and the row
- Close = the last hourly candle of the market with `end_period_ts` <= start and >= start - 3 h, with a two-sided close
  (`yes_bid` > 0, `yes_ask` > `yes_bid`), full spread <= 0.10, mid in [0.02, 0.98]. Mid = (bid + ask)/2 of that candle's close. The close is
  therefore 0-60 min stale (hourly candles; no finer 2025-26 price exists); stated, not corrected.
- Backfill (flagged): if the last candle lacks a bid or an ask but the preceding candle (<= 2 h earlier) has it, that side is carried
  forward and the row is flagged `backfilled`; results are shown with and without flagged rows. A row with no usable quote is dropped, counted.
- Unit = one contract on one ticker. **Moneyline: one row per game, the favourite's listing (mid >= 0.5)**; the longshot-NO bucket is the
  same economic bet from the other listing, so it is shown as a mirror, descriptive only, not tested, not in the BH count.
  Team totals: every strike's ticker is a row (YES listing); rows of one game are dependent, so clusters are GAMES.
- Void / non-yes-no results dropped, counted.

## Arm per bucket, buckets, net
Buckets (fixed now, the H-MEAS-1 set): mid in [.02,.10) [.10,.25) [.25,.50) [.50,.75) [.75,.90) [.90,.98].
Arm: mid >= 0.5 -> buy YES at the ask (favourite); mid < 0.5 -> buy NO at 1 - bid (longshot).
Per contract: gross = payoff - mid-of-the-side; cost = half spread + taker fee at the entry price (`quant/costs.py` `taker_entry_cost`,
series fee schedule, "prelive"; if the series is absent from the schedule, `quant/money.py` fee_k007); net = gross - cost
(= `quant/money.py` `fill_pnl`). The fee schedule is today's, applied to 2025-26 history (flagged). Gross, cost and net are always shown together.

## Test, interval, multiplicity
- Per family x bucket: n contracts, n games, mean gross, mean cost, mean net, 90% interval = game-clustered CR1
  (`quant/variance.py` `clustered_mean`, level 0.90). Testable only with >= 30 games AND >= 100 contracts; otherwise UNDERPOWERED
  (games needed stated via `quant/variance.py` `games_needed`).
- BH at q = 0.10 across ALL testable family x bucket cells (`quant/multiplicity.py` `benjamini_hochberg` on one-sided p from z = mean/se,
  direction net > 0). At most 3 (NHL ML) + 3 (NBA ML) + 6 (NBA TT) + 6 (NFL TT) = 18 cells.
- **SUPPORTED** = 90% net interval wholly above zero AND BH-rejected. **LEAD** = interval wholly above zero, not BH-rejected (reported, never routed).
  **NOT SUPPORTED** = anything else testable. Family verdict = SUPPORTED if any of its cells is SUPPORTED.
- Early/late stability (by start date halves) is descriptive.

## Routing consequence, in advance
SUPPORTED cell -> "a RIDE-favourite / NO-longshot leaf proposed for router v2 at that family x bucket, forward-judged on 2026-27 rows
after this commit"; no leaf map changes in this block. NOT SUPPORTED -> "hypothesis closed (EXP-H-EDGE-5, parked for R&D)" with reopen trigger = the
family's 2025-26 gap, if any, appears in 2026-27 rows (H-MEAS-1 slope intervals) or more history lists. UNDERPOWERED -> stated n needed.

## Modal outcome (stated before the join)
Most likely (about 65%): NO cell SUPPORTED. The close slope of H-MEAS-1 says favourites win more than the close, but the gap is a
few cents per contract against a round cost of about 2-3 cents in these buckets, and hourly closes add noise. If any cell is
SUPPORTED, the most likely are the favourite buckets of NHL moneyline ([.50,.75) / [.75,.90)) or NBA moneyline. NBA team total and
NFL team total are expected thin (NFL TT: about 3 weeks of games, probably UNDERPOWERED in most buckets). A tighter interval is not an edge:
gross, cost and net are read side by side.

## Deviations log
(none yet; every change after this commit is dated and listed here)
