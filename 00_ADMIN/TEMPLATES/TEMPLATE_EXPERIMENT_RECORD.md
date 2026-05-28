# Experiment Record — EXP-YYYY-MM-DD_[short-title]

**Purpose:** Document a single research experiment with full provenance for reproducibility and traceability.  
**Owner (role):** Research Lead (RL)  
**Last reviewed:** YYYY-MM-DD  
**Next review:** YYYY-MM-DD  
**Staleness triggers:** Data snapshot retired; code reference invalidated; result superseded by follow-up experiment  
**Upstream links:** RESEARCH_QUESTIONS.md, HYPOTHESES.md, DATA_SNAPSHOTS_INDEX.md  
**Downstream links:** RESULTS_SUMMARIES/, VALIDATION_PLAN.md, MODEL_CARD.md  
**Decision references:** ADR-0002 (strategy class)  
**Confidence:** X/10 — [Why]  

---

## Experiment ID

`EXP-YYYY-MM-DD_[short-title]`

## Question

[Which research question from RESEARCH_QUESTIONS.md does this address?]

## Hypothesis

[Specific, falsifiable hypothesis. Cite from HYPOTHESES.md where applicable.]

## Method

[Step-by-step description of the experimental procedure. Precise enough to replicate without additional context.]

## Data

| Field | Value |
|-------|-------|
| Snapshot ID(s) | [Link to DATA_SNAPSHOTS_INDEX.md entry] |
| Time window | YYYY-MM-DD to YYYY-MM-DD |
| Sample size | [N events/markets] |
| Train/test split | [e.g., 70/30 chronological split] |
| Look-ahead bias check | [Confirmed clean / Issues noted] |

## Code Reference

| Field | Value |
|-------|-------|
| Repository / location | [Path or repo] |
| Commit / tag | [Pinned commit hash or tag] |
| Entry point | [Script or notebook name] |
| Environment | [Link to ENVIRONMENTS.md entry] |

## Metrics and Results

| Metric | Value | Null Model Baseline | vs. Baseline |
|--------|-------|--------------------|-----------  |
| Brier Score | | | |
| Log Loss | | | |
| Calibration (visual) | | | |
| [Other metric] | | | |

## Interpretation

[What do the results mean? Does the hypothesis hold? What's the effect size?]

## Limitations / Threats to Validity

- [e.g., Small sample; single time window; feature leakage risk; ...]

## Next Experiment

[What does this result suggest as the logical next experiment? Link to a new HYPOTHESES.md entry if created.]

## Confidence

**Result confidence:** X/10  
**Reason:** [Explain. Consider: sample size, look-ahead risk, model complexity, out-of-sample gap]
