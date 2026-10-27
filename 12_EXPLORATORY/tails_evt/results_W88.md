# W88.1 Part A: tails for the real-money limits (box data 2026-10-27, game-clustered)

Method: peaks-over-threshold GPD on per-game losses (threshold = 75th percentile, min 15 exceedances), 95% intervals from 1,000 game-resampled refits. Known-answer tests: `tests/test_tails_evt.py` (6). Applies to: roughly independent per-game losses with at least ~15 exceedances. Does not apply to: per-$-staked loss on binary contracts (capped at 1.0, so the return level sits in the censored body), or extrapolation past ~3x the sample size.

A bug found and fixed mid-block: the first sampler double-counted tail mass and overstated drawdowns about 2x. The test `test_sample_tail_model_keeps_tail_probability` now guards it. All numbers below are post-fix.

## Per-game loss (USD at ledger measurement stakes)
| Cohort | Games | Bets | P&L | Fit | 1-in-100 (GPD, 95% CI) | 1-in-1000 (GPD, 95% CI) | Normal 1/100, 1/1000 |
|---|---|---|---|---|---|---|---|
| T4 MLB filled | 69 | 177 | -37.9 | 17 exc, xi=0.20 | 7.18 [2.98, 12.04] | 14.71 [3.05, 57.06] extrapolated | 5.3, 6.8 |
| T4 MLB paper | 394 | 4316 | -140.9 | 99 exc, xi=0.045 | 13.09 [10.44, 15.94] | 22.29 [14.45, 36.47] | 12.1, 16.0 |
| T1 MLB filled | 57 | 83 | -124.7 | TOO FEW (14 exc) | none | none | 29.9, 39.1 |
| T1 MLB paper | 173 | 469 | -113.2 | 43 exc, xi=-0.16 | 53.57 [40.49, 62.48] | 73.59 [48.61, 103.30] extrapolated | 49.0, 64.9 |

Where n is too small: T1 filled (14 exceedances) has no tail fit. T4 filled's 1-in-1000 interval spans 3 to 57 and is not usable. Both 1-in-1000 paper figures extrapolate beyond the sample (394 and 173 games). Normal understates the T4 filled tail by 26% at 1/100 and 54% at 1/1000, and the fit is heavy-tailed (xi=0.20).

## Max drawdown (USD, $1,000 normalized bankroll, flat measurement stakes), 99th / 99.9th percentile
| Cohort | 30 games as-is | 30 games zero-edge | 90 games as-is | 90 games zero-edge |
|---|---|---|---|---|
| T4 filled | 46.7 / 61.7 | 32.8 / 48.4 | 99.6 / 121.1 | 56.1 / 77.3 |
| T4 paper | 71.2 / 92.3 | 62.5 / 83.0 | 141.5 / 171.2 | 113.1 / 142.7 |
| T1 filled (bootstrap only) | 218.6 / 259.5 | 159.5 / 196.8 | 471.3 / 542.3 | 292.7 / 361.4 |
| T1 paper | 304.8 / 379.5 | 288.2 / 362.4 | 565.8 / 707.7 | 517.8 / 656.0 |

The 20% kill is $200. T4 stays under it at 90 games at flat stakes; T1 does not at either horizon, even at zero edge, which matches the GG-135 ruin geometry.

## Versus `mc_empirical_bootstrap.py`
It resamples Gaussian daily aggregates, so it carries no information beyond the first two moments. T4 (n=4316): P(kill) 0.0 at 30 days, 7.9% at 90, 75.1% at 182, 99.8% at 365. Those are driven by the drift and variance of the stake-scaled book, not by tails.

## Kelly 0 and the smallest positive Kelly
Kelly 0: no stake, no loss, no tail. Any positive Kelly scales per-game loss and drawdown linearly with stake. The ADR-0048 smallest nonzero multiplier (0.10x of the baseline, about 0.01 absolute for T1) scales the figures above by the ratio of that stake to the measurement stake. Not run as a separate simulation.

## Stake concentration
A binary contract loses at most its stake, so a game's worst loss is bounded by the stake deployed on that game. EVT governs dollar loss at the measurement stake; the binding protection is a per-game aggregate exposure cap.

## Gaps
- Shadow books' fill-priced per-game P&L is not available (only order and fill counts), so no tail for them.
- T4 cache shows `cache_bankroll=$1000.0` against realized P&L of -$140.93 (flat-stake book). Registered, not fixed.
- Stage reached (ADR-0075): tails are aggregated and interpreted; not yet applied to any enforced limit.
