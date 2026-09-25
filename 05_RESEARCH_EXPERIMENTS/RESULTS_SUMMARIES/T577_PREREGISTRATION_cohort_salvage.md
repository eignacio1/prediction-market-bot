# T-577 Pre-Registration — Cohort Salvage or Declare

**Pushed BEFORE any new statistic is computed on raw ledger rows.** Immutable from this point; any deviation found necessary later is logged as a deviation in the results summary, not edited in here.

**Inherited, verified, not re-derived:** GG-300/301/303 findings (35 FILLED / 139 CANCELED / 731 NOT_RETRIEVABLE across 905 T4M-PROJ epoch-12 clean rows; 395/731 NR rows in the GG-303 duplicate/fabricated-order-id population; the 34/35 confirmed-FILLED rows are non-random on `mid_price_at_entry`, `gross_edge`, `size_usd` and cluster on one `game_date`). Cross-checked directly against `paper_portfolio_mlb_t4.LIVE.20260922.json` + `t571_kalshi_verification_results.json` (same snapshot T-571/T-573 used): 905/905 match, verdict counts identical.

## Tiers (fixed partition, applied mechanically in Deliverable 2)

1. **CONFIRMED-REAL** — verdict=FILLED (n=35 expected)
2. **CONFIRMED-CANCELED** — verdict=CANCELED (n=139 expected)
3. **DUPLICATE-SUSPECT** — verdict=NOT_RETRIEVABLE and in GG-303's A∪B∪C buckets (n=395 expected)
4. **UNCONFIRMED-CLEAN** — verdict=NOT_RETRIEVABLE and in GG-303's bucket D only (n=336 expected)

## Salvage criteria (what makes a tier or tier-combination usable)

- **Minimum n:** 30 resolved bets, matching the G6 floor already in force (`CLAUDE.md` Gate structure) — this project does not get to apply a laxer bar to a salvage analysis than it applies to its own live-capital gate.
- **Maximum allowable selection bias:** identical test and threshold T-573 already established — two-sided Mann-Whitney U, Bonferroni α=0.05/5=0.01, on the 5 continuous observables (`mid_price_at_entry`, `gross_edge`, `h_so_far_at_entry`, `ab_remaining_at_entry`, `size_usd`), comparing the candidate tier-combination against CONFIRMED-REAL. **Zero of the 5 may survive Bonferroni** for a combination to be called unbiased. `kalshi_threshold` and `game_date` are reported descriptively (as T-573 did); a >2x share ratio on any single `game_date` between groups is treated as disqualifying concentration even without a formal categorical test, since that is the exact failure mode that invalidated the 34-row subset.
- **Required game-date spread:** ≥5 distinct `game_date` values, no single date accounting for >30% of the tier's rows.
- **Bias-correction method: scenario bounds, not a fitted reweighting model.** With only 35 confirmed-real points to anchor any propensity model, and 3 of 5 covariates already shown non-random, a fitted IPW/propensity correction would be estimated from too few events to trust its own weights — that just relocates the fragility into a black box instead of removing it. Instead: compute the calibration statistic (Brier skill vs. climatology, model-vs-market paired difference, win_rate, P&L, via the existing `t565_calibration_model_vs_market.py` machinery, unmodified) separately for (S1) CONFIRMED-REAL alone, (S2) CONFIRMED-REAL + UNCONFIRMED-CLEAN combined, and (S3) UNCONFIRMED-CLEAN alone — then report the S1–S2 (or S1–S3) spread as the honest interval, rather than a single reweighted point. This is a bracket, not a point estimate.
- **DUPLICATE-SUSPECT is not eligible for inclusion in any combination**, regardless of n or bias test outcome — its rows carry a demonstrated fabricated-order-id defect (GG-303) that is a data-integrity failure, not a statistical-power problem; no reweighting scheme corrects for fabricated identity fields.

## UNRECOVERABLE trigger (stated in advance)

Declare UNRECOVERABLE if **either**:
(a) no tier combination other than CONFIRMED-REAL alone passes both the bias screen and the n≥30/date-spread screen (i.e., the only usable-by-the-bias-test population is the same 35 rows GG-301 already showed produce a negative, non-generalizable headline), **or**
(b) the S1–S2 bracket spans both a positive and negative calibration skill (model-beats-market and market-beats-model both consistent with the data).

Either condition alone is sufficient. Both compounding is a stronger UNRECOVERABLE, not a different verdict.

— T-577, 2026-09-25, pushed prior to Deliverable 2/3 computation.
