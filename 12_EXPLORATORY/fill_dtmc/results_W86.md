# W86.3 (Quant A3): size and fills. Pillar EXECUTION. Date 2026-10-23.

Code: `dtmc.py` (estimator, hitting times, game-clustered bootstrap), `part_a_size.py`, `part_b_fills.py`, `part_b_mlb.py`;
test `tests/test_fill_dtmc.py`. Raw numbers: `results_part_a.json`, `results_part_b.json`, `results_mlb_e3.json`.

## Premise corrections (verify-before-trust)
1. The E3 numbers (25.4% / 28.9% fills vs 48.3% / 52.1% non-fills) are MLB **paper-book** positions
   (`paper_portfolio_mlb_t4.json`, `paper_portfolio_mlb.json` + fill-status sidecars). They are NOT the demo-fill-policy
   control/treatment arms. I reproduced all four numbers exactly (`results_mlb_e3.json`).
2. Depth rows come from PRODUCTION public order books (`archive_market_prices.py`), not demo books. Demo-order fill
   timing (Part B) is from the demo exchange. Findings that mix them: none; each part says which it uses.
3. Only the top level and cumulative-within-5c size are archived, never a ladder. "Size that moves the price 1 tier"
   is exact (top level of the opposite side). "Size that moves it 2 cents" is only bracketed [top, within-5c].
4. Queue position and the book path while resting are logged nowhere. "Behind others" and "book moved away" cannot
   be states. The chain is over elapsed-time bins. Registered as a gap (queue-position logging).
5. NBA and NHL are not depth-sampled; NFL depth exists for Oct only. Markouts exist only since 2026-10-21T04:30Z and
   include no MLB; fill time is derivable only for those orders.

## Part A: resting size (contracts, opposite-side top level; each row gives a YES-buy and a NO-buy observation)
Median (p10 / p90) of top-of-book size, by family and time to start. Median CI is clustered by game; "-" = under 5 games.
| Family | 0-60m | 60-180m | 180-720m | >720m | started |
|---|---|---|---|---|---|
| Moneyline (GAME_WINNER) | 239k (317 / 1.9M) | 340k (6.5k / 3.8M) | 1.4M (1 game) | 726 (5 / 2.2k) | 7.4k (129 / 235k) |
| Run line / spread | 8.4k (1.1k / 83k) | 6.8k (695 / 73k) | 1.1k (76 / 8.1k) | 280 (22 / 5.0k) | 675 (2 / 6.9k) |
| Total | 6.6k (1.1k / 133k) | 6.9k (1.2k / 135k) | 675 (8 / 12k) | 500 (23 / 7.8k) | 750 (3 / 8.2k) |
| Team total | 3.1k (781 / 8.5k) | 2.8k (889 / 7.7k) | 2.0k (100 / 4.7k) | 112 (8 / 1.1k) | 859 (22 / 5.5k) |
| Player prop | 1.4k (25 / 10k) | 1.0k (25 / 8.6k) | 349 (17 / 3.2k) | 234 (16 / 1.7k) | 250 (2 / 10.7k) |
| Partial game (F3/F5/F7) | 1.7k (13 / 21k) | 1.9k (17 / 17k) | 439 (7 / 4.6k) | 39 (4 / 1.2k) | 433 (1 / 27k) |
- Reading: inside 3h of start, one tier is thousands of contracts for every game family, far above a $1 stake
  (about 1/p contracts). Medians hide a heavy low tail: 20-55% of far-from-start observations show under 100
  contracts at the top (player props 18-38%, partial games up to 55%). Time-to-start bucket matters by 1-3 orders
  of magnitude for moneyline and run line, because depth builds toward game time.
- Within-5c size is the 2-cent bracket's upper end; its medians are in `results_part_a.json`.
- Refill: between consecutive snapshots of one ticker, the top level is within 10% of its prior size or larger in
  82% of 37,210 pairs under 30 min apart (ratio p10 / p50 / p90 = 0.4 / 1.0 / 3.7). Consumption and cancellation
  cannot be separated at this cadence, so this is persistence, not a refill rate.
- Max contracts before an order moves the price one tier: a distribution, per cell above, never one number. At a
  $1-$5 stake the answer is "never, except in the low tail".
- Caveat: strikes far from the money (tail prices) dominate the >720m rows; the table is not conditioned on price.

## Part B: fills (Markov chain over elapsed-time bins; demo exchange, orders from 2026-10-21T04:30Z)
Estimator test: `test_recovers_known_matrix`, `test_recovers_hitting_probability_and_time`, `test_censoring_*`,
`test_cluster_bootstrap_interval_covers_truth` pass: a chain with known transition probabilities is recovered to
within 0.01-0.02 from 60k simulated lives, with censoring.

**When it applies:** exit type and exit time are both logged, the horizon can be cut into a few bins, and censoring is
independent of the exit. **When it does not:** it sees no book, so it cannot attribute a fill to queue position
versus price movement; exit times that are missing for one outcome (here, cancels) bias P(fill) up unless imputed.

Measured (one result per arm x sport, `results_part_b.json`; intervals clustered by game, n_games small):
- Treatment arms cancel at 5 s. P(fill): NBA 0.097 [0.077, 0.121] (n=6,247, 23 games); NFL 0.317 (n=145, 1 game); NHL
  0.018 [0, 0.027] (n=171, 12 games). Every treatment fill occurs at t < 2 s (immediately marketable).
- Control arms rest until sweep. NBA P(fill) 0.573 [0.525, 0.635] (n=6,220, 25 games) with 2,375 cancelled orders that
  have no logged cancel time imputed as exits after 2 h (sensitivity: lower bound uses them as cancels, as done here).
  Fill time p10 / p50 / p90 = 0 s / 6.7k s / 32k s: fills are bimodal, immediate crosses and long rests.
- Control NHL P(fill) 0.584 (n=164, 12 games; CI [0, 0.72] is too wide to read). Control NFL: 1 game, no interval.

Win rate of fills by time to fill (control NBA, 11 games): fill under 2 s 0.503 [0.340, 0.706] (n=866); 30-120 min
0.434 [0.33, 0.53] (n=753); over 2 h 0.413 [0.33, 0.51] (n=1,576). The ordering fits adverse selection growing with rest
time but the intervals overlap: not a finding. "Price moved through us vs hit while the price stood still" is not
separable without the book path (see premise 4); elapsed time is the only path proxy.

## E3 explained (MLB paper books; `results_mlb_e3.json`; cluster = game)
| | fills win | non-fills win | gap | adverse selection | price chosen | non-fill edge |
|---|---|---|---|---|---|---|
| T4 MLB | 25.4% [16.3, 36.9] n=177, 69 games | 48.3% [45.5, 51.0] n=4,139, 392 games | -22.9pp | -29.6pp | +16.3pp | -9.6pp |
| T1 MLB | 28.9% [20.2, 37.9] n=83, 57 games | 52.1% [46.8, 56.9] n=386, 159 games | -23.2pp | -39.2pp | +21.5pp | -5.5pp |
Identity: gap = (win_fill - mid_fill) + (mid_fill - mid_nonfill) + (mid_nonfill - win_nonfill), mid = price of the side
taken. Fills sit at higher prices (0.55 vs 0.39 T4; 0.68 vs 0.47 T1), so the price we chose RAISES the fill win rate
by 16-21pp and explains none of the shortfall. The whole gap is adverse selection: fills win 30-39pp below their own
price, against 5-10pp for non-fills. **Queue position and time resting cannot be measured: neither is logged for these
books. The data says "who fills is who wins less than priced"; it does not say whether that is queue priority or
price movement through the order.** Resolving that needs queue-position logging (registered).

## Granularity index (five parts)
Split: arm x sport x time-to-fill bin. Rank vs history: none (epoch only 2 days old). Matchup cross: none. Market map:
Part A table (family x time-to-start). Application: not applied; stage = aggregated/interpreted.

## For the quant core next wave
`dtmc.estimate`/`summarise` (absorbing-chain hitting times with censoring), `dtmc.cluster_bootstrap` (game-clustered
resampling over a statistic), `part_b_mlb`'s three-term gap identity, `part_a_size.parse_ts` (tolerant ISO parse).
