# Session Handoff — Edge-Strategy Decomposition (2026-07-07)

**UTC:** 2026-07-07 ~04:30Z · **Canonical session #:** TBD (concurrent with SESSION 122–124; assign at reconciliation)
**Operator:** Earl Ignacio · **Focus:** internal-validity decomposition of the MLB T1 Tier-1 edge; build the reusable enhancer-activation gate.
**Network:** none in this session — nothing pushed to origin or deployed to VPS. All work is LOCAL and awaits operator push/deploy.

---

## What was done

Advisory turn ("are we ready to pivot to edge/P&L focus?") converted into three chained experiments plus full documentation.

**EXP-017B — Edge decomposition** (`scripts/run_exp017b_decomp_mlb.py`, `exp_output/EXP-017B-DECOMP/FINDINGS.md`)
Headline reproduced exactly (n=151, EV +$0.1009/bet, WR 49.7%, PnL +$15.23). Decomposition: aggregate is bootstrap-insignificant (95% CI [−$1.86,+$2.13], P(EV>0)=53%); all edge is NO-side (n=140, +8.71%/staked, +$125.50); YES sub-book is anti-predictive (n=11, −62%/staked, −$110.27); realized profit non-monotonic in edge and concentrated in ~20 bets (>100% of net). T2/T3 overlays contributed nothing (all NEUTRAL / injury False).

**EXP-017C — Calibration root-cause** (`scripts/run_exp017c_calibration_mlb.py`, `exp_output/EXP-017C-CALIB/FINDINGS_calibration.md`)
Binary event reconstructed exactly (0/151 mismatch). Model is well-calibrated: reliability 0.005, Brier skill +0.12, logistic slope 0.852 CI [0.468,1.316] (includes 1.0). Edge-realization: expected edge monotonic; mid-band shortfall is the residual/variance term (20–30pp) not the calibration gap (2–4pp). **Refines/overturns 017B's calibration-defect hypothesis: the non-monotonicity is variance, not miscalibration.** Murphy decomposition validates exactly (recompose_ok=True).

**EXP-017D — A/B edge-delta harness** (`scripts/ab_harness.py`, `run_ab_experiment.py`, `README_ab_harness.md`, `exp_output/EXP-017D-ABHARNESS/FINDINGS_ab.md`)
Reusable gate: bootstrap Δ CI must exclude 0, n_B≥30, survive holdout (train<cutoff, test≥cutoff). Paired bootstrap for nested filters. Results: **quarantine_YES DEFENSIBLE in both modes** (P=99.6%); min_edge_0.10 UNDERPOWERED and collapses OOS; edge-band filter INCONCLUSIVE; recalibration null→harmful. Demonstrated the harness killing the seductive in-sample winner.

All scripts deterministic (seed=17), md5-stable, invariants pass, reuse audited fee/edge helpers with GG-077 direction-aware recomputation.

## Strategic Decisions This Session

1. **ADR-0042 (PROPOSED)** — adopt reversible YES-quarantine (D1) + A/B harness holdout-gate as enhancer prerequisite (D2). Awaits operator/DS sign-off (D1 is capital-adjacent).
2. **GG-098 registered (OPEN)** — MLB T1 positive aggregate carried by a NO subset; YES sub-book anti-predictive. Re-review trigger n_YES≥30.
3. **Rejected (do not re-propose):** min-edge/tail filtering, edge-band filtering, model recalibration — all fail holdout / unnecessary (model is calibrated).
4. **Standing conclusion:** the dominant lever is sample accumulation toward Tier 2, not model surgery. Model class (ADR-0004) confirmed sound; ADR-0027 calibration temperature unchanged.

## Files touched (all local, uncommitted at handoff)

- New: `scripts/run_exp017b_decomp_mlb.py`, `run_exp017c_calibration_mlb.py`, `ab_harness.py`, `run_ab_experiment.py`, `README_ab_harness.md`; `exp_output/EXP-017{B,C,D}-*/`; `03_DECISIONS/ADR-0042_*.md`; `05_RESEARCH_EXPERIMENTS/EXPERIMENT_LOG/EXP-017{B,C,D}_*.md`; this handoff.
- Appended (section-anchored): `04_EXECUTION/SESSION_CLAIMS.md`, `03_DECISIONS/GOVERNANCE_GAP_LOG.md` (GG-098), `03_DECISIONS/DECISION_LOG/DECISION_LOG.md` (ADR-0042 index + 3 judgment calls), `04_EXECUTION/TODO_NEXT.md` (T-250/251/252), `11_MEMORY_HANDOFF/MEMORY_BANK.md` (delta pointer).
- NOT touched: another session's uncommitted `src/.../c7_monitoring/monitor.py`, `tests/test_c7_monitor.py`.

## Numbering / concurrency note

Originally reserved ADR-0041/GG-097/T-247; a concurrent session (GG-095) had taken those, flagged via SESSION_CLAIMS. Renumbered to **ADR-0042 / GG-098 / T-250-252** (verified free locally). Re-verify at push time — origin may hold numbers not visible locally (no network here).

## Next actions (in TODO_NEXT)

- **T-250** — on ADR-0042 sign-off, wire the YES-quarantine flag into MLB T1 selection.
- **T-251** — re-run EXP-017B/C/D as n grows toward Tier 2 (n≥500).
- **T-252** — route all future enhancers (MLB PAM/GG-094, psych gradients, multi-factor) through the harness holdout gate. PAM is a multi-session build, deferred per operator.

## Operator to-do (outside this session's reach)

Push local commits to origin and deploy if desired; assign canonical session number; give ADR-0042 D1/D2 sign-off decision.
