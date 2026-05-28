# Research Questions — Prediction Market Trading Bot

**Purpose:** Define the specific, answerable questions that the research phase must resolve before the project can advance to paper trading. Research without explicit questions produces data, not evidence.  
**Owner (role):** Research Lead (RL)  
**Last reviewed:** 2026-05-22  
**Next review:** G1 Spec Gate (freeze initial set); update after each experiment resolves or raises questions  
**Staleness triggers:** Question resolved; new question identified from experiment results; G4 evidence review  
**Upstream links:** HYPOTHESES.md, ADR-0002, ASSUMPTIONS_REGISTER.md  
**Downstream links:** EXPERIMENT_LOG/, VALIDATION_PLAN.md  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 5/10 — Initial question set; will be refined at G1 after Player_Attribute_Matrix provenance and market category are confirmed

---

## Research Question Taxonomy

| Type | Code | Meaning |
|------|------|---------|
| Signal | SQ | Does the data contain predictive information? |
| Calibration | CQ | Are probability estimates well-calibrated? |
| Edge | EQ | Is the model's edge sufficient to overcome vig and transaction costs? |
| Robustness | RQ | Does the result hold across time, market categories, and data regimes? |
| Risk | RSQ | What is the worst-case outcome under the position sizing regime? |

---

## Primary Research Questions

### SQ-001 — Does the Player_Attribute_Matrix Contain Signal?

**Question:** Do features derived from the Player_Attribute_Matrix produce probability estimates that are more accurate than the market-implied probability (null model) on a held-out test set?

**Why it matters:** This is the foundational validity question. If the answer is no, ADR-0002 must be revisited and the strategy class may need to change.

**Measurement:** Brier score of model vs Brier score of null model on held-out test set. Positive result: model Brier score < null model Brier score with statistical significance.

**Falsification condition:** If model Brier score ≥ null model Brier score across ≥3 independent experiments, ASM-001 is falsified.

**Status:** UNRESOLVED — Phase 3

---

### CQ-001 — Are the Model's Probability Estimates Calibrated?

**Question:** When the model says an event has probability P, does that event occur approximately P fraction of the time?

**Why it matters:** Calibration is required for Kelly criterion to work correctly. An overconfident model will overbet and amplify drawdown.

**Measurement:** Calibration curve (reliability diagram) on held-out test set; expected calibration error (ECE).

**Falsification condition:** Calibration curve systematically above or below the diagonal; overconfidence detected.

**Status:** UNRESOLVED — Phase 3

---

### EQ-001 — Is the Edge After Vig Positive?

**Question:** Is `edge = p_estimate - market_implied_prob - vig > 0` on a sufficient fraction of opportunities to generate positive expected value after accounting for all costs?

**Why it matters:** A well-calibrated model can still generate negative EV if the edge is smaller than the vig.

**Measurement:** Distribution of edge values across held-out events; fraction with positive edge; expected value calculation.

**Falsification condition:** Average edge ≤ 0 after vig across the held-out test set.

**Status:** UNRESOLVED — Phase 3 (requires venue vig data — OQ-006)

---

### RQ-001 — Does Signal Persist Across Time?

**Question:** Is the signal in the Player_Attribute_Matrix stable across different time periods, or does it decay as market participants adapt?

**Why it matters:** A signal that is present in 2022 data but absent in 2024 data will fail in live deployment.

**Measurement:** Compare Brier scores across chronological time windows of equal size.

**Falsification condition:** Systematic degradation of model accuracy in more recent time windows vs older windows.

**Status:** UNRESOLVED — Phase 3

---

### RSQ-001 — What Is the Maximum Drawdown Under the Proposed Risk Regime?

**Question:** Under fractional Kelly sizing (at a fraction TBD at G4) with hard limits from RISK_APPETITE_CONSTRAINTS.md, what is the maximum simulated drawdown on the historical test set?

**Why it matters:** Risk limits must be calibrated to evidence. If simulated drawdown already exceeds limits, the limits are inconsistent.

**Measurement:** Simulate the full decision cycle (forecast → sizing → P&L) on historical held-out test set. Compute maximum drawdown.

**Falsification condition:** Simulated drawdown exceeds hard limits under any reasonable Kelly fraction — indicates limits are too aggressive or model edge is insufficient.

**Status:** UNRESOLVED — Phase 3/4

---

## Secondary Research Questions (Phase 4+)

| ID | Question | Phase | Priority |
|----|----------|-------|----------|
| SQ-002 | Which features from Player_Attribute_Matrix contribute most to signal? | Phase 3 | HIGH |
| SQ-003 | Is there signal in market price momentum (volume, order flow)? | Phase 3+ | MEDIUM |
| CQ-002 | Does temperature scaling or Platt scaling improve calibration? | Phase 3 | MEDIUM |
| EQ-002 | What is the minimum edge threshold for a bet to have positive EV? | Phase 3 | HIGH |
| RQ-002 | Does signal persist across different market categories (sports vs politics)? | Phase 4+ | LOW |

---

## Questions Out of Scope

*These questions are explicitly deferred to prevent scope creep during Phases 0–4.*

| Question | Reason Deferred |
|----------|----------------|
| Does the arb/ strategy generate positive EV? | arb/ folder reference-only; APR-0010 required |
| How does the bot perform on Polymarket vs Kalshi? | Multi-venue is out of scope (SCOPE_IN_OUT.md) |
| Can the model be improved with NLP on news data? | Novel data source; adds complexity before base signal validated |
