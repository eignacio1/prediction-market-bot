# ADR-0042 — YES-Direction Quarantine (MLB T1) + A/B Edge-Delta Harness as the Enhancer Activation Gate (PROPOSED)

> **Numbering note (2026-07-07):** originally drafted as ADR-0041; renumbered to ADR-0042 per the SESSION_CLAIMS reconciliation note after a concurrent session took ADR-0041 / GG-098 / T-250. GG-098→GG-098, T-250→T-250 throughout. Re-verify at push time — origin may hold numbers not visible locally (no network in the authoring session).

**Status:** PROPOSED — awaiting operator (and DS) sign-off. Two coupled decisions: (D1) adopt a reversible YES-direction quarantine on the MLB T1 book; (D2) adopt the A/B edge-delta harness holdout-gate as the mandatory prerequisite for activating any future strategy enhancer (PAM, psychological gradients, multi-factor formulas). D1 changes live paper selection and is therefore capital-adjacent — it does not go live until signed off.
**Date:** 2026-07-07
**Session:** Edge-Strategy Decomposition (2026-07-07T04:30Z) — canonical session number to be assigned by operator (concurrent with SESSION 122–124).
**Operator:** Earl Ignacio
**Scope:** MLB T1 bet selection (direction filter); project-wide experiment governance (enhancer activation prerequisite). No change to `risk.py` `_HARD_LIMITS`, no change to model class (ADR-0004), no NBA impact.
**Supersedes / relates:** builds on EXP-017 (GG-004 Tier-1 verdict); does not supersede any ADR. Relates to ADR-0004 (model class — confirmed sound here), ADR-0024 (stop/pivot tiers), ADR-0027 (calibration temperature — no change warranted), GG-004 (commercial validation, OPEN), GG-094 (MLB has no qualitative layer), GG-098 (YES sub-book, registered this session).

---

## Context

EXP-017 reached ADR-0024 Tier 1 for MLB T1 on 2026-07-06 (n=151, EV=+$0.1009/bet, WR 49.7%, PnL +$15.23, DIRECTIONAL_POSITIVE against live Kalshi prices). Before shifting project focus to edge/enhancer work, three follow-on experiments decomposed that result to test whether the edge is broad or subset-driven:

- **EXP-017B (decomposition):** the +$0.10/bet aggregate is not distinguishable from zero (bootstrap 95% CI [−$1.86, +$2.13], P(EV>0)=53%). All positive edge is on the NO side (+8.7%/staked, +$125.50); the 11 YES bets are −62%/staked (−$110.27), erasing ~88% of NO profit. Realized profit is non-monotonic in the edge signal and concentrated in ~20 high-conviction bets.
- **EXP-017C (calibration root-cause):** the non-monotonicity is NOT a calibration defect. `model_p` is well-calibrated (reliability 0.005; Brier skill +0.12; logistic calibration slope 0.85 with 95% CI [0.47, 1.32] — includes 1.0). Expected edge is monotonic; the mid-band shortfall is the residual/variance term (20–30pp) not the calibration gap (2–4pp). Recalibration would fix a non-problem.
- **EXP-017D (A/B harness):** of the candidate fixes, only YES-quarantine clears a DEFENSIBLE_IMPROVEMENT bar (Δ$/staked CI excludes 0 in BOTH in-sample and holdout; P(Δ>0)=99.6%; P(kept>removed)=99.7–99.8%). min-edge/tail filtering is UNDERPOWERED and collapses out-of-sample; recalibration is null→harmful; an edge-band filter adds nothing over the direction cut.

Cross-experiment conclusion: **the model is calibrated and has genuine positive *expected* edge; realized P&L at n=151 is variance-dominated.** The binding constraint is sample size, not model quality. The one robust, holdout-surviving selection improvement is removing the YES direction.

## Decision

**D1 — YES-direction quarantine (PROPOSED).** Add a reversible configuration flag (not a code fork) that excludes YES-direction bets from the MLB T1 book. Justification: YES is anti-predictive on all evidence to date — Fisher YES-vs-NO p=0.056 (EXP-017B), removed-vs-kept P=99.7% (EXP-017D), dual-mode DEFENSIBLE Δ. Implemented as config so it is trivially reversible and auditable. **Mandatory pre-registered re-review trigger:** re-evaluate at n_YES ≥ 30 resolved YES observations; if the YES sub-book's EV recovers above 0 with p>0.05 the quarantine is lifted. Rationale for caution: the adopt decision rests on only 11 removed bets — defensible on data-to-date, not proven across regimes.

**D2 — A/B harness holdout-gate (PROPOSED).** No future strategy enhancer (PAM/MLB, psychological gradients, multi-factor formula composition, new features) is activated in the live paper book until it clears `DEFENSIBLE_IMPROVEMENT` in the A/B harness (`scripts/ab_harness.py`) **holdout mode** — hypothesis pre-registered, rule fit/selected on train days and scored on unseen test days, bootstrap Δ CI excluding 0 at n_B ≥ MIN_N. This operationalizes the Principal-Vision line "the methodology is the asset" and prevents the enhancer phase from becoming in-sample noise-fitting (which EXP-017C/D showed is trivially easy at current n).

## Consequences

- **Positive:** removes a demonstrably losing sub-book; installs a rigorous, reusable gate for all future edge work; avoids two tempting mistakes (recalibrating a calibrated model; adopting a noise-fit tail filter).
- **Negative / cost:** D1 reduces bet volume (~7% of positions) — mild headwind to Tier-2 sample accumulation, which is the dominant lever (accepted trade-off given YES is negative-EV). D2 adds a required step before any enhancer activation (intended friction).
- **Explicitly rejected this session (do not re-propose without new evidence):** min-edge/tail filtering (`edge>0.10`), edge-band filtering (`edge>0.03`), Platt/logistic recalibration of `model_p`. All failed holdout in EXP-017D / were shown unnecessary in EXP-017C.

## Evidence / reproducibility

- Scripts: `scripts/run_exp017b_decomp_mlb.py`, `run_exp017c_calibration_mlb.py`, `ab_harness.py`, `run_ab_experiment.py` (all deterministic, seed=17, md5-stable; reuse audited fee/edge helpers with GG-077 direction-aware recomputation).
- Findings: `exp_output/EXP-017B-DECOMP/FINDINGS.md`, `exp_output/EXP-017C-CALIB/FINDINGS_calibration.md`, `exp_output/EXP-017D-ABHARNESS/FINDINGS_ab.md`; harness spec `scripts/README_ab_harness.md`.
- Data: `logs/.vps_portfolio_cache_mlb.json` (n=151 closed; headline reproduces EXP-017 to 4 dp). Base commit e250a29.

## Open items

- D1/D2 require operator (and DS per ADR-0005) sign-off before this ADR moves to ACCEPTED and the flag goes live.
- GG-004 remains OPEN (Tier 2 n≥500 not met). This ADR does not close it.
- Wiring the quarantine flag into the live selection path (`paper_trader.py` / band selection) is a separate implementation task (T-250) gated on sign-off.
