# ADR-0042 — MLB T1 YES Direction: REJECT Quarantine, Monitor Instead + A/B Edge-Delta Harness as the Enhancer Activation Gate (PROPOSED)

> **Numbering note (2026-07-07):** originally drafted as ADR-0041; renumbered to ADR-0042 after a concurrent session took ADR-0041 / GG-097 / T-247 (see SESSION_CLAIMS). This ADR uses GG-098 and T-250. Re-verify at push time — origin may hold numbers not visible locally (no network in the authoring session).

> **CORRECTION (2026-07-07, operator review — supersedes the original D1).** The first draft of D1 proposed *adopting* a YES-direction quarantine. The operator rejected this as over-calibration on n≈11, and he is correct. D1 below is now **REJECT the quarantine — monitor instead.** The harness has been fixed accordingly (a `MIN_REMOVED_N`=30 guard; quarantine_YES now returns `UNDERPOWERED_REMOVAL`, not DEFENSIBLE). The rest of this ADR (D2, and the calibration/variance findings) is unchanged and stands. Principle applied: **realign components if the data demands it; do not destroy built capability on a tiny sample.**

**Status:** PROPOSED — awaiting operator (and DS) sign-off on D2. (D1 is a decision to NOT change live selection — no capital action; nothing goes dark.) Two decisions: (D1) do **not** quarantine YES — monitor it and keep collecting; (D2) adopt the A/B edge-delta harness holdout-gate as the mandatory prerequisite for activating any future strategy enhancer (PAM, psychological gradients, multi-factor formulas).
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

Cross-experiment conclusion: **the model is calibrated and has genuine positive *expected* edge; realized P&L is variance-dominated at this sample size.** The binding constraint is sample size, not model quality.

**Operator-review update (2026-07-07).** Two facts confirm the variance read and defeat the original quarantine proposal: (1) the live book has since grown to **n=169**, and the aggregate has swung from +$15.23 (n=151) to **−$44.76** — an ~$60 move in 18 bets, i.e. no directional verdict is stable yet. (2) The YES losses are concentrated in k=2 (2+ hits): YES k=2 went 0/7, but P(≤0 | Binomial, p≈0.31) = **0.073** — variance-consistent — and at threshold level the model actually *under*-predicts k=2 (0.226 vs 0.273 actual), so there is not even a clean k=2 over-prediction mechanism. Quarantining YES would discard the fine k=1 YES bets and stop the very data collection needed to ever judge YES. The removed-set is n≈11 — far below any bar for concluding a category is structurally negative-EV.

## Decision

**D1 — Do NOT quarantine YES; monitor instead.** The YES sub-book (n≈11–12) is NOT quarantined. Keep taking YES bets under the existing model/selection so the sample can accumulate to a size that can actually be judged. Rationale: at n≈11 the underperformance is variance-consistent (Binomial P=0.073), the model is calibrated per threshold, and the aggregate book is itself unstable (sign-flipped n=151→169). Quarantine would be over-calibration and would destroy built capability (YES-direction betting) plus the data needed to evaluate it. **Pre-registered monitor (not an auto-action):** track the YES sub-book; only if, at **n_YES ≥ 40**, YES EV is still negative with Fisher p<0.05 AND a *mechanism* is identified (e.g. a persistent threshold- or player-specific over-prediction, not a bare win-rate gap) does a targeted realignment get proposed — and even then the realignment adjusts the offending mechanism, it does not blanket-drop the direction. This is a monitoring decision, so there is no live/dark state change and no capital action.

**D2 — A/B harness holdout-gate (PROPOSED).** No future strategy enhancer (PAM/MLB, psychological gradients, multi-factor formula composition, new features) is activated in the live paper book until it clears `DEFENSIBLE_IMPROVEMENT` in the A/B harness (`scripts/ab_harness.py`) **holdout mode** — hypothesis pre-registered, rule fit/selected on train days and scored on unseen test days, bootstrap Δ CI excluding 0 at n_B ≥ MIN_N. This operationalizes the Principal-Vision line "the methodology is the asset" and prevents the enhancer phase from becoming in-sample noise-fitting (which EXP-017C/D showed is trivially easy at current n).

## Consequences

- **Positive:** preserves built YES-direction capability and its data stream; installs a rigorous, reusable gate (D2) for all future edge work with an over-calibration guard (`MIN_REMOVED_N`); avoids three tempting mistakes — recalibrating a calibrated model, adopting a noise-fit tail filter, and quarantining a category on ~11 observations.
- **Negative / cost:** the YES sub-book continues to carry small negative realized P&L while the sample accumulates (accepted — it is the price of the data needed to judge it; the amounts are paper and small). D2 adds a required step before any enhancer activation (intended friction).
- **Explicitly rejected this session (do not re-propose without new evidence):** (a) **YES quarantine** — over-calibration on n≈11; (b) min-edge/tail filtering (`edge>0.10`) and edge-band filtering (`edge>0.03`) — fail holdout / underpowered; (c) Platt/logistic recalibration of `model_p` — unnecessary (model is calibrated, EXP-017C) and null→harmful in holdout (EXP-017D).

## Evidence / reproducibility

- Scripts: `scripts/run_exp017b_decomp_mlb.py`, `run_exp017c_calibration_mlb.py`, `ab_harness.py`, `run_ab_experiment.py` (all deterministic, seed=17, md5-stable; reuse audited fee/edge helpers with GG-077 direction-aware recomputation).
- Findings: `exp_output/EXP-017B-DECOMP/FINDINGS.md`, `exp_output/EXP-017C-CALIB/FINDINGS_calibration.md`, `exp_output/EXP-017D-ABHARNESS/FINDINGS_ab.md`; harness spec `scripts/README_ab_harness.md`.
- Data: `logs/.vps_portfolio_cache_mlb.json` (n=151 closed; headline reproduces EXP-017 to 4 dp). Base commit e250a29.

## Open items

- D2 requires operator (and DS per ADR-0005) sign-off before it is binding. D1 is a monitor decision — no sign-off gate, no live change.
- GG-004 remains OPEN (Tier 2 n≥500 not met). This ADR does not close it. Note the aggregate has already sign-flipped (n=151 +$15.23 → n=169 −$44.76), reinforcing that no directional verdict is stable yet.
- **T-250 (reframed):** no quarantine to wire. Instead, monitor the YES sub-book and re-run EXP-017B/C/D as the book grows; investigate a mechanism only if YES stays negative with p<0.05 at n_YES ≥ 40.
