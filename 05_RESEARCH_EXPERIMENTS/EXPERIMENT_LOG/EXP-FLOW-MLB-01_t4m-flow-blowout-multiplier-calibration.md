# Experiment Record — EXP-FLOW-MLB-01: T4M-FLOW/FLOW-BLOWOUT Multiplier Calibration

**Status:** PLANNED  
**Experiment ID:** EXP-FLOW-MLB-01  
**Owner:** EL  
**Hypothesis tested:** T4M-FLOW alpha hypothesis (ADR-0039) — see Objective  
**Research question:** Does a sustained run-differential blowout systematically shift a batter's true hit probability (up for the trailing team facing tiring/mop-up relief, down for the leading team pulled early / facing fresh relief) by an amount the market fails to price in, beyond what T4M-PROJ's flat model already captures?  
**Started:** (not started)  
**Completed:** (not started)

**Governance note — read before acting on this document:** T4M-FLOW is registered `status="BLOCKED"` in `T4_MLB_SUBBAND_REGISTRY` (`execution_bands.py`), gated on this exact experiment ID (`exp_gate=("EXP-FLOW-MLB-01",)`) per ADR-0039/T-219. **This document defines methodology only. It does not authorize running this experiment, registering data snapshots, or any Phase 8 activation.** T4M-FLOW cannot fire a paper or live bet until this experiment runs, is interpreted, and clears its own Phase 8 Activation Gate + APR, independent of T4M-PROJ's existing ADR-0023 approval.

---

## Objective

`T4MlbFlowEvaluator` (`t4_mlb_execution_engine.py`), tree `FLOW-BLOWOUT`, tracks per-`game_id` whether `|score_diff| >= _BLOWOUT_RUN_THRESHOLD` (currently 6 runs) has held for at least `_BLOWOUT_SUSTAIN_INNINGS` (currently 2 innings). Once sustained, it applies an asymmetric multiplier to the batter's effective `ba_l10` before the Binomial update — `_BLOWOUT_TRAILING_MULT` (currently 1.15, an uplift) for a batter on the trailing team, `_BLOWOUT_LEADING_MULT` (currently 0.80, a discount) for a batter on the leading team — on the thesis that blowout innings systematically change the quality of pitching faced (tiring starters / mop-up relief against the trailing team's lineup) and roster usage (leading-team regulars pulled early, backups entering). Both multiplier values were borrowed from NBA T4-FLOW's order of magnitude as a starting placeholder; ADR-0039 is explicit that **no MLB-specific derivation exists for either constant, or for the 6-run/2-inning thresholds that define "sustained blowout" in the first place.**

This experiment answers three things: (1) whether the sustained-blowout condition itself correlates with a real shift in batting outcomes for MLB specifically (not assumed from the NBA analogy), (2) if so, what the trailing/leading multipliers should actually be, and (3) whether the market's price already reflects this shift by the time the sustain threshold is crossed — the T4 latency thesis (CLAUDE.md's T4 alpha) applied to this specific in-game pattern, as distinct from T4M-PROJ's pregame-only baseline.

---

## Snapshot IDs Used

*Not yet registered — no experiment has run. To be filled per `DATA_SNAPSHOTS_INDEX.md` protocol at Phase 8 Activation, using resolved MLB game logs with per-inning score state plus T4M-PROJ's live cycle/price audit trail.*

| Snapshot ID | Dataset | Description | Ingested |
|-------------|---------|-------------|----------|
| (TBD) | ESPN MLB boxscore / play-by-play, resolved games | Per-inning score_diff, batting team, to reconstruct blowout onset/duration retrospectively | (TBD) |
| (TBD) | T4M-PROJ live cycle log | Per-cycle `MLBLiveBatterState` snapshots for at-bats occurring during reconstructed blowout windows | (TBD) |
| (TBD) | Kalshi KXMLBHIT resolved market prices | Same-cycle `CachedPrice` (mid/vig) during blowout windows, from the existing T4M-PROJ price cache audit log | (TBD) |

---

## Code Reference

| Item | Detail |
|------|--------|
| Commit hash | (TBD — pin to the commit at experiment run time) |
| Script / notebook | `t4_mlb_execution_engine.py::T4MlbFlowEvaluator` (evaluator under test); a dedicated offline backtest runner, and the score_diff reconstruction/labeling script it depends on, do not yet exist and must be written before this experiment can move to RUNNING |
| Dependency lock | (TBD) |

---

## Experimental Design

**Train window:** (TBD — must postdate T4M-PROJ's live-paper-trading start so enough resolved games with genuine blowout innings exist)  
**Validation window:** (TBD)  
**Test window:** (TBD; held out per standard protocol)  
**Split method:** Chronological (no random shuffling) — consistent with project-wide temporal integrity policy

**Approach:** Two layers, since this experiment must validate a condition NBA's analogous experiment (also not yet run, per repo search — no `EXP-FLOW-01` precedent exists to borrow calibrated values from) has not itself established:

1. **Effect existence/direction:** For all resolved plate appearances occurring while a reconstructed blowout condition (candidate thresholds swept, not fixed at 6 runs / 2 innings) is active, compare trailing-batter and leading-batter empirical hit rates against each batter's own `ba_l10` baseline from the same period. This tests whether a real shift exists at all, in either direction, before any multiplier value is fit.
2. **Multiplier + threshold calibration:** If step 1 shows a real, directionally-consistent effect, grid-sweep `_BLOWOUT_RUN_THRESHOLD` (candidates: 4, 5, 6, 7, 8), `_BLOWOUT_SUSTAIN_INNINGS` (candidates: 1, 2, 3), and the trailing/leading multipliers (fit via observed hit-rate ratios rather than assumed from the NBA analogy) against realized outcomes and resolved Kalshi prices, to find the combination that maximizes calibrated edge over the market_implied_prob null.

**Features used:**

| Feature ID | Feature Name | Source | Temporal Safety |
|-----------|-------------|--------|----------------|
| F-FLOW-01 | score_diff, is_batting_team_leading, inning | ESPN live MLB boxscore poll — **not currently parsed into T4M-PROJ's live loop; must be added to the C1 extraction layer before live evaluation, though this experiment can use post-hoc reconstruction from resolved boxscores without touching the live pipeline** | NOT YET WIRED (flagged in `t4_mlb_execution_engine.py`'s module docstring as Phase-8-adjacent follow-up; retrospective reconstruction for this experiment does not require the live wiring to exist first) |
| F-FLOW-02 | h_so_far, ab_so_far, batting_slot, ba_l10 | Same as T4M-PROJ/T4M-ARITH — existing C1/C2 layers | VERIFIED (already governs live T4M-PROJ) |
| F-FLOW-03 | mip, vig at evaluation cycle | Kalshi KXMLBHIT price cache | VERIFIED (already governs live T4M-PROJ) |

**Model class:** Binomial threshold-probability (frozen, ADR-0004/ADR-0023) with a multiplicative adjustment to `ba_l10` — same base model class as T4M-PROJ/T4M-ARITH; the multiplier itself is the new parameter under calibration, not a new model class.  
**Hyperparameters:** `_BLOWOUT_RUN_THRESHOLD`, `_BLOWOUT_SUSTAIN_INNINGS`, `_BLOWOUT_TRAILING_MULT`, `_BLOWOUT_LEADING_MULT` — all four currently hardcoded provisional constants in `t4_mlb_execution_engine.py`, explicitly marked non-calibrated and borrowed from an NBA order-of-magnitude guess pending this experiment.  
**Null model:** market_implied_prob baseline (mip + vig at the qualifying cycle) — same standard as EXP-ARITH-MLB-01 and the project-wide T1 precedent (GG-004).

---

## Temporal Integrity Check

- [ ] All feature temporal_cutoff values precede event_date (score_diff and inning state used to detect blowout onset must reflect only information available at that cycle's timestamp — no using the final score to retroactively label "this was a blowout" earlier than it actually became one)
- [ ] No outcome data appears in the feature set (the plate appearance's own outcome must not influence the score_diff/blowout labeling used to select it into the sample)
- [ ] Train/validation/test splits are strictly chronological with no overlap
- [ ] Snapshot IDs are registered and immutable

*(Unchecked — experiment has not run. These are the checks that must pass before this document can move to RUNNING.)*

---

## Results

*(Not yet run.)*

| Metric | Train | Validation | Null Model (Val) | Notes |
|--------|-------|-----------|-----------------|-------|
| Brier Score | | | | Lower is better |
| Log Loss | | | | Lower is better |
| ECE (Calibration) | | | | Lower is better |
| AUC-ROC | | | | Higher is better |

**Calibration curve:** (TBD)  
**Edge distribution:** (TBD — distribution of `p_flow - (mip + vig)` across all qualifying sustained-blowout cycles is the primary object of interest; separately reported for trailing vs. leading batters, since the hypothesis predicts opposite-signed effects)

---

## Look-Ahead Audit

- [ ] Automated temporal overlap check passed
- [ ] Manual review of temporal_cutoff for all features confirmed
- [ ] Lineage register entries confirmed for all features used

*(Unchecked — pending experiment run.)*

---

## Interpretation

*(Not yet run — no interpretation exists.)*

**Does this experiment confirm or falsify the hypothesis?**

*(TBD)*

**Key findings:**
- *(TBD)*

**Unexpected results:**
- *(TBD)*

---

## Confidence

**Confidence in this result:** N/A — not yet run  
**Reason:** This document exists to define methodology ahead of execution, per T-219's follow-up scope. No result exists to have confidence in. Note also that step 1 (effect existence) genuinely could falsify the premise entirely — unlike EXP-ARITH-MLB-01, which tests a threshold/gate calibration on an effect that plausibly exists by construction (thin-AB Binomial variance contraction is a mathematical fact), T4M-FLOW's underlying behavioral premise (blowout innings change batter outcomes in this specific direction) is an empirical claim borrowed wholesale from an untested NBA analogy and could simply be wrong for MLB.

---

## Follow-Up

| Action | Owner | Due |
|--------|-------|-----|
| Build a score_diff/inning reconstruction script from resolved ESPN boxscores (retrospective; does not require live C1 wiring) | EL | Before Phase 8 Activation Gate request |
| Build an offline backtest runner joining reconstructed blowout windows to T4M-PROJ's resolved cycle log and Kalshi price cache | EL | Same as above |
| Register data snapshots per `DATA_SNAPSHOTS_INDEX.md` protocol once inputs are finalized | EL | Same as above |
| Run step 1 (effect existence/direction test) before investing in step 2's grid sweep | EL | Same as above |
| If step 1 falsifies the premise: document the null result here and in `GOVERNANCE_GAP_LOG.md`; leave T4M-FLOW `status="BLOCKED"` indefinitely; do not proceed to step 2 | EL | After step 1 |
| If step 1 confirms a real effect: run step 2's grid sweep, populate Results, and draft a Phase 8 Activation Gate request + APR for T4M-FLOW per ADR-0039's Governance Impact section | EL | After step 1 |
| Separately: live ESPN score_diff extraction must be added to `run_t4_mlb_live.py`'s C1 layer before T4M-FLOW can ever evaluate live/paper cycles, regardless of this experiment's outcome — currently `T4MlbGameContext.score_diff` defaults to `0.0` and is never populated from a live poll | EL | Before any Phase 8 live wiring, independent of this experiment's timeline |

---

## Links

- Governing ADR: `03_DECISIONS/ADR-0039_mlb-native-t4-subband-architecture-scoping.md`
- Registry entry: `execution_bands.py::T4_MLB_SUBBAND_REGISTRY[ExecutionBand.T4M_FLOW]`
- Evaluator under test: `src/prediction_market_bot/t4_mlb_execution_engine.py::T4MlbFlowEvaluator`
- Test coverage (construction/logic, not backtest): `tests/test_t4_mlb_engine.py`
- Task registration: `04_EXECUTION/TODO_NEXT.md` — T-219
- NBA precedent (structurally analogous, not a substitute — no NBA `EXP-FLOW-01` result exists to borrow calibrated values from as of this writing): `t4_execution_engine.py`'s T4-FLOW sub-band, itself still Phase-8-blocked
