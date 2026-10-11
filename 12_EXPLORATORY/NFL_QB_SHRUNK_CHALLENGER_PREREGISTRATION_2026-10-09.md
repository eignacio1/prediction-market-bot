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

## Addendum 2026-10-10 (operator + strategic window, 19:27 PT; written before any challenger row exists)
The original text above is untouched. This addendum supersedes the "Judged n" and "Verdict rule" sections above for gating purposes.

1. **The ~984-game gate is withdrawn.** Its arithmetic was off (6.18 x 0.0342^2 / 0.0027^2 = ~992, not 984), and the verdict rule above (99.375% CI, m=8) would need ~1,790 games at 80% power, so the section contradicted itself.
   More basically it asked the wrong question: challenger vs frozen at -0.0027 Brier was already answered out-of-sample on 1,852 rolling-origin games (2019-2025). Re-proving it live over ~3.6 seasons would answer nothing that makes money.
2. **The backtest is the model-selection evidence for the QB term.** C1 (challenger vs frozen, same game, paired) is reported descriptively at each NFL look. It is never gated.
3. **The judged comparison is C2: challenger vs the Kalshi mid** (KXNFLGAME home-win moneyline, mid at kickoff-30min), on the same cells, with the same n, looks and verdict rule as EXP-037's market comparison (NFL looks at judged n=60 and 150; first look with EXP-037, ~2026-11-02). The calibration engine lists the challenger under that rule.
4. **Expected result, stated before any row:** on 2025's 182 priced games the challenger was worse than both frozen (Brier 0.2221 vs 0.2182) and the mid (0.2115). "Keep accruing" or "no edge versus the market" is the modal outcome. A win here would mean a better model than the market mid, which the backtest gives no reason to expect.
