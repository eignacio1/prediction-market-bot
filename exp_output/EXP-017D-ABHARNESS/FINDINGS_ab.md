# EXP-017D — A/B Edge-Delta Harness: Candidate-Fix Evaluation

> **CORRECTION (2026-07-07, operator review).** The original recommendation below to *adopt* YES-quarantine was over-calibration on n≈11 and is **REJECTED** (see ADR-0042 as corrected). Dropping ~11 known-losing bets tautologically improves the book but cannot establish that the YES *category* is negative-EV — at fuller data (book has since grown to n=169) the YES k=2 0/7 run is variance-consistent (Binomial P(≤0)=0.073) and the overall book has swung to −$44.76, confirming the variance regime. The harness has been fixed with a `MIN_REMOVED_N`=30 guard: category-removal filters now return **`UNDERPOWERED_REMOVAL`**, not DEFENSIBLE, when the removed set is small — which is exactly what quarantine_YES now returns in both modes. Correct action: **keep taking YES bets, monitor, do not quarantine.** Read the table below with that correction in mind.

**Date:** 2026-07-06 **Parent:** EXP-017C / 017B / GG-004
**Data:** `logs/.vps_portfolio_cache_mlb.json` (n=151; holdout cutoff 2026-07-03 → train 50 / test 101)
**Code:** `scripts/ab_harness.py` (framework) + `scripts/run_ab_experiment.py` (driver). Deterministic seed=17; md5-stable.
**Primary metric:** pnl-per-$1-staked (sizing-neutral). **Status:** analysis only; no shared nav/governance files touched.

---

## Purpose

Two jobs at once: (1) evaluate the candidate fixes suggested by 017B/017C, and (2) stand up the reusable gate every future change — including PAM / psych-gradient enhancers — must pass. A change is adopt-worthy only if it produces a **defensible edge delta** (bootstrap Δ CI excludes 0) that **survives holdout** (rule fit/selected on train days, scored on test days). In-sample gains alone are presumed noise-fitting until holdout confirms.

## Method note that matters

Every variant here is a **subset** of baseline (filters/quarantines). For nested comparisons the harness uses a **paired bootstrap** (one common resample; the filter applied within it), which preserves shared-bet covariance. A naive independent bootstrap overstates Δ variance for nested strategies — it wrongly called YES-quarantine INCONCLUSIVE. The paired result is the correct one and is used throughout. (Both are implemented; `boot_method` is recorded per comparison.)

## Verdict tiers

`DEFENSIBLE_IMPROVEMENT` (Δ CI excludes 0, Δ>0, n_B≥30) · `HARMFUL` (CI excludes 0, Δ<0) · `INCONCLUSIVE` (CI includes 0) · `UNDERPOWERED` (n_B<30).

---

## Results

| variant | mode | n_B | B $/staked | Δ (pp) | Δ 95% CI | P(Δ>0) | verdict |
|---------|------|-----|-----------|--------|----------|--------|---------|
| **quarantine_YES** | in-sample | 140 | +8.71% | **+7.77** | **[+1.7, +15.0]** | 99.6% | **DEFENSIBLE** |
| **quarantine_YES** | holdout | 92 | +3.35% | **+11.27** | **[+2.4, +22.0]** | 99.6% | **DEFENSIBLE** |
| min_edge_0.10 | in-sample | 20 | +34.3% | +33.3 | [−10.1, +79.5] | 93.3% | UNDERPOWERED |
| min_edge_0.10 | holdout | 11 | +22.5% | +30.4 | [−35.3, +96.3] | 83.0% | UNDERPOWERED |
| YESquar+min_edge_0.03 | in-sample | 95 | +9.25% | +8.31 | [−0.5, +18.3] | 96.6% | INCONCLUSIVE |
| YESquar+min_edge_0.03 | holdout | 58 | +1.84% | +9.76 | [−3.2, +24.5] | 92.8% | INCONCLUSIVE |
| platt_recal_edge>0 | in-sample | 108 | +2.62% | +1.68 | [−6.2, +10.2] | 65.1% | INCONCLUSIVE |
| platt_recal_edge>0 | holdout | 61 | −14.42% | −6.50 | [−29.0, +15.7] | 27.0% | INCONCLUSIVE |

Baseline: in-sample +0.94%/staked (+$15.23); holdout-test −7.93%/staked (−$79.76 — the late period is negative, consistent with 017B's time-window flag).

## Reading

1. **YES-quarantine is the only defensible fix — and it holds out-of-sample.** Paired Δ CI excludes 0 in both modes; P(kept > removed) = 99.7% / 99.8%. The 11 YES bets are distinguishably worse than the NO book, not a lucky-draw artifact. This is adopt-worthy as a reversible config change. Caveat: the evidence still rests on ~11 removed bets; it is "defensible on the data to date," not "proven for all regimes."

2. **The min-edge / tail filter is NOT defensible — exactly as 017C predicted.** Despite the largest in-sample point gain (+33pp), its CI includes 0 and it collapses to n=11 with a ±100pp CI in holdout. Adopting it would be textbook noise-fitting. This is the harness doing its job: killing the seductive in-sample winner.

3. **The edge-band filter adds nothing over the direction filter.** `YESquar+min_edge_0.03` is INCONCLUSIVE and *weaker* than pure `quarantine_YES` (which is DEFENSIBLE). Stacking the mid-band filter injects noise. Keep the direction cut; drop the edge-band cut.

4. **Recalibration is null-to-harmful.** +1.7pp in-sample (near-zero, as 017C's calib_gap implied), −6.5pp in holdout. Fitting a Platt correction on 50 obs to a model that is already calibrated (017C) adds variance and hurts out-of-sample. Do not recalibrate.

---

## Assumptions

- pnl/size are realized ground truth; rescoring only changes selection + calibration metrics, never a bet's pnl. Verified in code.
- Holdout split is temporal (train < 2026-07-03 ≤ test). Only 50/101 — low power, especially for tail/rescore variants; treat holdout as directional corroboration, not proof.
- Paired bootstrap is correct for nested (subset) strategies; independent is used only if a variant ever adds bets outside baseline (none here do).

## Key Risks

- **Small-n throughout.** Even the DEFENSIBLE YES-quarantine rests on 11 removed bets; holdout test n=101. Re-run as sample grows.
- **Regime confinement.** 5 game-days, one regime. A "defensible" delta here is defensible *on this regime*.
- **Multiple comparisons.** Four variants × two modes = 8 tests; no multiplicity correction applied. YES-quarantine's dual-mode 99.6% survives casual Bonferroni (0.05/8), but treat single-mode 95%-ish results as weak.

## Validation Checks (done)

- Invariants: baseline n=151; train+test = 50+101 = 151. ✅
- Determinism: identical md5 across runs. ✅
- Paired vs independent bootstrap both implemented; nesting auto-detected; method recorded. ✅
- Filter diagnostic (removed vs kept) computed independently of the Δ test. ✅

## Confidence

- **High** that min-edge/tail filtering and recalibration are non-defensible on current data (both fail holdout).
- **Medium-High** that YES-quarantine is a real, adopt-worthy improvement (dual-mode defensible), tempered by n=11.
- **High** in the harness itself as the reusable gate for future changes.

---

## Recommendations

1. **Adopt YES-quarantine as a reversible config flag** (not a code fork), with a pre-registered re-review trigger (e.g., re-evaluate at n_YES≥30). It is the single defensible fix found. — *For Earl to approve; would warrant a DECISION_LOG entry + possibly a small ADR since it changes live selection.*
2. **Do NOT adopt min-edge filtering or recalibration.** Document them as tested-and-rejected so they aren't re-proposed. — *suggested GG/DECISION_LOG note.*
3. **Route every future enhancer (PAM, psych gradients, multi-factor) through this harness in holdout mode before activation.** This operationalizes "the methodology is the asset" and prevents the enhancer phase from becoming noise-fitting.
4. **The dominant lever remains sample accumulation toward Tier 2** (017C): most variants are UNDERPOWERED/INCONCLUSIVE purely because n is small. The harness will discriminate far better at n≥500.
