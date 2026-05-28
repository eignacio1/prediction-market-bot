# Experiment Record — [EXP-NNN: Title]

*Copy this template; rename to EXP-NNN_short-title.md; fill all fields before running.*

**Status:** PLANNED / RUNNING / COMPLETE / ABANDONED  
**Experiment ID:** EXP-NNN  
**Owner:** RL  
**Hypothesis tested:** HYP-XXX  
**Research question:** SQ/CQ/EQ/RQ/RSQ-XXX  
**Started:** YYYY-MM-DD  
**Completed:** YYYY-MM-DD  

---

## Objective

*One paragraph: what question does this experiment answer and why does it matter?*

---

## Snapshot IDs Used

| Snapshot ID | Dataset | Description | Ingested |
|-------------|---------|-------------|----------|
| SNAP-YYYY-MM-DD-001 | DS-01 | Player_Attribute_Matrix v4 | YYYY-MM-DD |

*All datasets must be registered in DATA_SNAPSHOTS_INDEX.md before experiment runs.*

---

## Code Reference

| Item | Detail |
|------|--------|
| Commit hash | [git hash of code used to run this experiment] |
| Script / notebook | [path to entry point] |
| Dependency lock | DEPENDENCY_LOCKS/requirements-YYYY-MM-DD.txt |

---

## Experimental Design

**Train window:** YYYY-MM-DD to YYYY-MM-DD  
**Validation window:** YYYY-MM-DD to YYYY-MM-DD  
**Test window:** YYYY-MM-DD to YYYY-MM-DD (held out; accessed only at G4)  
**Split method:** Chronological (no random shuffling)  

**Features used:**

| Feature ID | Feature Name | Source | Temporal Safety |
|-----------|-------------|--------|----------------|
| F-001 | ... | DS-01 | VERIFIED |

**Model class:** [e.g., Logistic Regression / XGBoost]  
**Hyperparameters:** [list]  
**Null model:** market_implied_prob baseline  

---

## Temporal Integrity Check

- [ ] All feature temporal_cutoff values precede event_date
- [ ] No outcome data appears in the feature set
- [ ] Train/validation/test splits are strictly chronological with no overlap
- [ ] Snapshot IDs are registered and immutable

---

## Results

| Metric | Train | Validation | Null Model (Val) | Notes |
|--------|-------|-----------|-----------------|-------|
| Brier Score | | | | Lower is better |
| Log Loss | | | | Lower is better |
| ECE (Calibration) | | | | Lower is better |
| AUC-ROC | | | | Higher is better |

**Calibration curve:** [attach or describe]  
**Edge distribution:** [describe distribution of p_estimate - market_implied_prob]

---

## Look-Ahead Audit

- [ ] Automated temporal overlap check passed
- [ ] Manual review of temporal_cutoff for all features confirmed
- [ ] Lineage register entries confirmed for all features used

---

## Interpretation

**Does this experiment confirm or falsify the hypothesis?**

*Interpretation goes here.*

**Key findings:**
- Finding 1
- Finding 2

**Unexpected results:**
- ...

---

## Confidence

**Confidence in this result:** X/10  
**Reason:** *Why this confidence level?*

---

## Follow-Up

| Action | Owner | Due |
|--------|-------|-----|
| ... | RL | ... |

---

## Links

- Research question: RESEARCH_QUESTIONS.md#SQ-XXX
- Hypothesis: HYPOTHESES.md#HYP-XXX
- Snapshots: DATA_SNAPSHOTS_INDEX.md
- Results summary: RESULTS_SUMMARIES/EXP-NNN-summary.md
