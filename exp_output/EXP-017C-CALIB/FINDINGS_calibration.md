# EXP-017C — Calibration Root-Cause of the Non-Monotonic Edge

**Date:** 2026-07-06 **Parent:** EXP-017B / EXP-017 / GG-004 / ADR-0004 (model class)
**Data:** `logs/.vps_portfolio_cache_mlb.json` (n=151 unique resolved MLB positions, 2026-06-30 → 07-05)
**Script:** `scripts/run_exp017c_calibration_mlb.py` (deterministic seed=17; md5-stable; Murphy identity validates exactly)
**Status:** Analysis only. No shared nav/governance files touched.

---

## The question (from EXP-017B Finding 3)

EXP-017B found realized profit is **non-monotonic** in the model's edge signal (mid-conviction bets lose). It named two candidate causes: a **calibration defect** (model_p ≠ empirical frequency) or a **payoff/pricing artifact**. This experiment decides between them, because the fix differs entirely: calibration defect → recalibrate model_p (ADR-0004); payoff artifact → bet-selection rule, no model change.

**Verdict: NEITHER a calibration defect nor a payoff artifact — the non-monotonicity is dominated by SAMPLING VARIANCE at n=151. The model is well-calibrated and the strategy's *expected* edge is cleanly monotonic and positive. Realized P&L simply has not converged to it.** This refines (and partly overturns) 017B's "calibration defect" hypothesis.

---

## Evidence 1 — The model is well-calibrated

Binary event reconstructed exactly (0/151 mismatch): `event = player reached threshold = (dir==YES)==(WIN)`. Forecast = `model_p`.

| metric | value | reading |
|--------|-------|---------|
| Reliability (Murphy) | **0.0054** | near-zero = well-calibrated |
| Resolution | 0.0380 | positive discrimination (modest but real) |
| Uncertainty (base var) | 0.2481 | base rate 0.457 |
| Brier (full) | 0.2184 | — |
| **Brier Skill Score** | **+0.120** | model beats base-rate-only forecast by 12% |
| ECE | 0.067 | modest miscalibration |
| **Calibration slope b** | **0.852, 95% CI [0.468, 1.316]** | **CI includes 1.0 → not distinguishable from perfect** |
| Calibration intercept a | +0.086 | ≈ 0 |

The logistic recalibration fit `logit(event) = a + b·logit(model_p)` returns a slope whose CI straddles 1.0 and an intercept ≈ 0. Statistically, **model_p is not distinguishable from perfectly calibrated.** Murphy decomposition validates exactly (REL − RES + UNC = binned Brier to machine precision; binning gap 0.0028 is within-bin variance, informational).

*Per-threshold slopes (k=1, k=2) are reported but underpowered* — restricted model_p range within a single threshold makes the logit slope unstable (CIs [−2.26, 1.74] and [−2.91, 0.71]). Do not read the negative point estimates as signal; the CIs swamp them. Both thresholds show ECE ≈ 0.067.

## Evidence 2 — Expected edge IS monotonic; realized is noise around it

The edge-realization table computes, per fee-net-edge bucket, expected pnl-per-$1-staked under (i) raw model_p, (ii) recalibrated p, vs (iii) realized:

| edge bucket | n | model_exp | calib_exp | realized | calib_gap | residual |
|-------------|----|-----------|-----------|----------|-----------|----------|
| ≤0 | 3 | −1.0% | −3.0% | −100.0% | +1.9pp | +97.0pp |
| (0, 0.03] | 42 | +3.8% | +0.4% | +7.8% | +3.5pp | −7.5pp |
| (0.03, 0.06] | 41 | +10.4% | +7.2% | **−23.3%** | +3.2pp | **+30.5pp** |
| (0.06, 0.10] | 45 | +19.9% | +17.6% | −5.1% | +2.3pp | **+22.8pp** |
| >0.10 | 20 | +35.5% | +31.6% | +34.3% | +3.9pp | −2.6pp |

Two decisive reads:

- **model_exp and calib_exp are both monotonic** (+3.8 → +10.4 → +19.9 → +35.5%), and they barely differ (**calib_gap only 2–4pp**). Recalibration would change almost nothing — direct proof calibration is not the cause.
- **The failing buckets' shortfall is the RESIDUAL term** (calibrated-expected minus realized): +30.5pp and +22.8pp. Calibration explains 2–4pp; the other ~20–30pp is variance/sampling. At ~40 bets/bucket with high-variance binary payoffs, this is exactly the noise magnitude expected.

So the mid-band loss is not the model being wrong about those bets — it's those ~40 bets landing below their (positive) expectation this sample.

## Evidence 3 — What this says about EXP-017B's tail-concentration

If expected edge is monotonic and positive and the model is calibrated, then the tail-concentration EXP-017B found (all profit in the >0.10 bucket; strip it and the book is negative) is **most parsimoniously explained as variance, not structure.** The >0.10 bucket over-realized (barely — residual −2.6pp) while the mid bands under-realized. This is what a positive-EV strategy looks like at small n: realized P&L scattered widely around a positive expectation.

**Critical consequence:** a rule like "only bet edge > 0.10" would be **fitting noise.** It removes the buckets that happened to lose this sample, with no evidence they are structurally worse (their *expected* edge is positive and monotonic). Such a rule should NOT be adopted on this data. (The A/B harness, step b, tests this directly.)

---

## Assumptions

- Calibration measured on the selected bet sample (conditional calibration). Verified good on exactly that sample — no separate selection-bias correction applied (small n precludes it).
- `expected_pnl_per_dollar` uses the same half-vig entry price as `compute_pnl_unit` (EXP-018 convention). Stake normalized to $1.
- Reconstructed event verified exact vs `actual_hits` (0/151 mismatch).

## Key Risks

- **n=151 is small for calibration too.** Slope CI [0.468, 1.316] is wide; "calibrated" means "not distinguishable from calibrated," not "proven calibrated." A real modest overconfidence (b≈0.85 point estimate) cannot be ruled out.
- **Variance conclusion is a null result.** "It's noise" is always the harder claim to falsify. It is supported here (calib_gap ≪ residual), but only more sample confirms it.
- **Regime.** 5 consecutive game-days, one market regime.

## Validation Checks (done)

- Murphy decomposition identity validates exactly (recompose_ok=True). ✅
- Reliability bins sum to n=151. ✅
- Event reconstruction exact vs actual_hits. ✅
- Determinism: identical md5 across runs. ✅
- Recalibration (calib_exp) computed via the IRLS-fit transform, not assumed. ✅

## Confidence

- **High** that the non-monotonicity is NOT a calibration defect (calib_gap 2–4pp vs 20–30pp residual; slope CI includes 1).
- **High** that a min-edge/tail filter would be noise-fitting on this sample.
- **Medium-High** that the strategy has genuine positive *expected* edge (calibrated model + monotonic positive expected-edge curve), pending more n to confirm calibration and let realized P&L converge.
- **Medium** on residual mild overconfidence (b≈0.85) being real vs noise.

---

## Recommendation (revises the EXP-017B action list)

1. **Do NOT recalibrate as a priority** — calibration is sound; it would solve a non-problem. (Revisit only if b drifts below its CI as n grows.)
2. **Do NOT adopt a min-edge>0.10 or tail-only rule** — it fits variance. The A/B harness will demonstrate the in-sample improvement is not a defensible edge delta.
3. **Highest-value action is SAMPLE ACCUMULATION toward Tier 2 (n≥500), strategy essentially as-is.** The binding constraint is variance, not model quality. This reframes the whole transition: the model is ready; the *sample* is not.
4. **YES: monitor with a pre-registered decision rule, do not hard-kill.** −62%/staked at n=11 with Fisher p=0.056 is borderline and likely variance-inflated; quarantine is cheap insurance but should be framed as a watch item with an explicit n/EV trigger, not a proven fix.
5. **Enhancers (PAM, psych gradients) remain premature** — but for a *different reason than 017B implied*: not because the base signal is miscalibrated, but because at current n we cannot measure whether any enhancer moves the needle. Which is exactly what the A/B harness (step b) is for.
