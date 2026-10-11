# NFL QB-shrunk challenger — pre-registration (EXPLORATORY draft)

**Status:** ACCEPTED (operator, 2026-10-10 19:13 PT)
**Arm:** nfl_pregame (team -> team+personnel)
**Label:** EXPLORATORY. Stays PROPOSED until the operator accepts it. No sizing change, no order, no live ledger touched.
**Source study:** `12_EXPLORATORY/20261009_nfl_qb_challenger/` (plan frozen before fitting), results in `W64_1_nfl_qb_challenger_results.md`.

## Challenger
Frozen EXP-037 recipe (ridge lambda=100 on home margin, probit-Platt on margin/sigma) with 13 features: the 11 frozen features EB-shrunk (K=2) plus `qb_epa_h/a`
(projected starter = prior game's starter, last 16 starts, k=6, shrunk to league mean). Refit rolling-origin only; the frozen model artifact stays untouched.

## Cells (shadow only, logged beside the frozen NFL pregame rows)
| Cell | Market | Band | Compared against |
|---|---|---|---|
| C1 | KXNFLGAME home-win moneyline | T1 pre-game (12-48h) | frozen EXP-037 probability, same game |
| C2 | KXNFLGAME home-win moneyline | T1 pre-game | Kalshi mid at kickoff-30min (descriptive only) |

## Judged n
- Primary (C1, challenger minus frozen, paired Brier): backtest mean delta -0.0027, per-game SD 0.0342 -> one-sided alpha 0.05, power 0.80 needs
  n = 6.19 x 0.0342^2 / 0.0027^2 ~ **984 games** (~3.6 NFL regular seasons). Looks before n=984 are "keep accruing", not verdicts.
- C2 (vs market), sized with W62.2's per-game SD ~0.106: MDE 0.038 at n=60, 0.024 at n=150. The backtest gap to the mid (+0.004 worse than frozen, CI spans 0)
  is far below that MDE; C2 cannot be judged at any feasible n and is reported, not decided.

## Verdict rule (fixed)
At n >= 984 resolved shadow games: challenger beats frozen iff the 99.375% (m=8) game-bootstrap CI upper limit of (challenger - frozen) Brier is < 0
AND the challenger is better in >= 5 of the seasons observed (or in every season if fewer than 5). Otherwise: no improvement. Seed 20261009, B=2000.

## Thinner edge expected
The backtest gain is calibration versus the frozen model, not edge versus the market: in 2025 the challenger was worse than frozen (+0.0038 Brier) and
worse versus the mid. Expect the market comparison to show nothing; a win here would mean a better model, not a trade.

## Multiplicity
m = 8 (recal, lam30, lam300, dome, + full, qb_only, eb_only, full_oracle) on 2019-2025; any later NFL challenger on these seasons raises m.
