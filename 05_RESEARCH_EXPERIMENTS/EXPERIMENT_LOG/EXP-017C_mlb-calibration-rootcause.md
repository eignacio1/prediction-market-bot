# Experiment Record — EXP-017C: MLB T1 Calibration Root-Cause

**Status:** COMPLETE
**Experiment ID:** EXP-017C (child of EXP-017B)
**Owner:** RL
**Hypothesis tested:** Is EXP-017B's non-monotonic edge a CALIBRATION defect (model_p ≠ empirical freq) or a PAYOFF/variance artifact?
**Research question:** routes the fix — recalibrate model (ADR-0004) vs bet-selection rule vs neither
**Started / Completed:** 2026-07-06

---

## Objective

Decide the cause of EXP-017B Finding 3 (non-monotonic realized profit). A calibrated probability model should be monotonic; determine whether model_p is miscalibrated (region-specific) or whether the non-monotonicity is payoff/variance.

## Data / Code Reference

| Item | Detail |
|------|--------|
| Portfolio | `logs/.vps_portfolio_cache_mlb.json` (n=151) |
| Script | `scripts/run_exp017c_calibration_mlb.py` (deterministic seed=17; md5-stable; Murphy identity validates exactly) |
| Base commit | e250a29 |
| Binary event | reconstructed as (dir==YES)==(WIN); verified 0/151 mismatch vs actual_hits≥threshold |
| Methods | reliability diagram, Brier + Murphy decomposition, ECE, IRLS logistic calibration slope+CI, per-threshold split, edge-realization (model-exp vs calibrated-exp vs realized) |

## Results

| Metric | Value | Reading |
|--------|-------|---------|
| Reliability (Murphy) | 0.0054 | well-calibrated |
| Brier Skill Score | +0.120 | beats base-rate forecast |
| ECE | 0.067 | modest |
| Calibration slope b | 0.852, 95% CI [0.468, 1.316] | includes 1.0 — not distinguishable from perfect |

Edge-realization: model-expected and calibrated-expected edge are both monotonic and nearly equal (calib_gap 2–4pp); the failing mid-buckets' shortfall is the residual/variance term (+30.5pp, +22.8pp). Per-threshold slopes underpowered (restricted range) — not read as signal.

## Interpretation

The non-monotonicity is NOT a calibration defect and NOT a payoff artifact — it is sampling variance at n=151. Model is calibrated; expected edge monotonic and positive; realized P&L simply has not converged. **Refines (partly overturns) EXP-017B's calibration-defect hypothesis.** Consequences: recalibration would fix a non-problem; a tail/min-edge filter would fit noise; the dominant lever is sample accumulation.

## Confidence

High that it's not calibration (calib_gap ≪ residual; slope CI includes 1). Medium on residual mild overconfidence (b≈0.85) being real vs noise.

## Verification

Murphy decomposition identity validates exactly (recompose_ok=True); reliability bins sum to n; event reconstruction exact; determinism confirmed.

## Links

- Findings: `exp_output/EXP-017C-CALIB/FINDINGS_calibration.md` · JSON: `exp_output/EXP-017C-CALIB/exp017c_calibration_results.json`
- Parent: EXP-017B · Downstream: EXP-017D · Governance: ADR-0004 (model class — confirmed sound), ADR-0027 (calibration temp — no change), ADR-0042
