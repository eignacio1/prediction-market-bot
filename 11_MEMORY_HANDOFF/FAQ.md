# FAQ — Prediction Market Trading Bot

**Purpose:** Answer common questions about this project with authoritative, defensible answers. Prevents re-derivation of settled questions across context windows. Questions here are closed — they have canonical answers backed by artifacts.  
**Owner (role):** Director/Sponsor (DS)  
**Last reviewed:** 2026-05-22  
**Next review:** Weekly; add new question whenever one is asked for the second time  
**Staleness triggers:** Answer becomes outdated; referenced artifact changes; new canonical answer established  
**Upstream links:** MEMORY_BANK.md (index), all referenced artifacts  
**Downstream links:** None  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 9/10 — All answers backed by canonical artifacts

---

## Governance Questions

**Q: Can we start using the arb/ folder now?**  
A: No. arb/ is reference-only for holistic future planning. Incorporating it requires a new ADR (APR-0010 placeholder). See REJECTED_OPTIONS.md RO-001 and ADR-0002. This is invariant #1 in MEMORY_BANK.md.

**Q: Can we change the risk limits without an ADR?**  
A: No. Any change to a hard limit in RISK_APPETITE_CONSTRAINTS.md requires an ADR + RCO sign-off. Temporary overrides are prohibited. The kill switch is the emergency response — not a limit override. See CHANGE_CONTROL.md Class A and "Risk Limit Change Governance."

**Q: Can we retrain the model in production?**  
A: No. Retraining in production is explicitly prohibited (REJECTED_OPTIONS.md RO-007; MODEL_CARD.md Governance). Any model update requires a new model version with a new ADR + G4-equivalent evidence. See CHANGE_CONTROL.md Class A.

**Q: Is an accepted ADR reversible?**  
A: No. Accepted ADRs are immutable. They can be superseded by a new ADR that explicitly references and supersedes the prior one, but the original ADR remains in the record unchanged. See ADR-0001 and CHANGE_CONTROL.md.

**Q: What is the "anti-shadow-doc rule"?**  
A: Any document, analysis, or data used to make a decision must enter the project directory within 72 hours of being used. If it influenced a decision but isn't in the directory, it's a shadow document — a governance violation. See CHANGE_CONTROL.md and COMMUNICATIONS_PLAN.md.

---

## Data Questions

**Q: Can we use Player_Attribute_Matrix_v4.docx in an experiment right now?**  
A: No. DS-01 provenance is unknown (OQ-001). Before any experiment, the operator must: (1) document source, creator, creation date, (2) inspect and document schema, (3) validate against DATA_REQUIREMENTS.md, (4) register as a snapshot. See DATA_PROVENANCE.md action list and KNOWN_ISSUES.md KI-001.

**Q: What is "temporal integrity" and why does it matter?**  
A: Temporal integrity means no feature used to train the model can contain information that would not have been available before the event outcome was known. Violating this is "look-ahead bias" — the model learns to use future information, producing inflated backtesting metrics that collapse in live deployment. Rules TI-01 through TI-04 in DATA_FLOWS_LINEAGE.md; automated check in TC-001. Violating this is a CRITICAL failure.

**Q: What is a "snapshot" and why are they immutable?**  
A: A snapshot is a point-in-time, hash-verified, registered copy of a dataset used in an experiment. Immutability ensures that any experiment can be reproduced exactly — the data is frozen at the state it was in when the experiment was run. See DATA_SNAPSHOTS_INDEX.md.

**Q: Can outcome data go into the feature store?**  
A: No. Outcome/resolution data (DS-03) is ingested on a completely separate path and never enters the feature store. This prevents data leakage from resolution into training. See DATA_FLOWS_LINEAGE.md TI-03.

---

## Model and Research Questions

**Q: What is the null model?**  
A: The null model is the market-implied probability: `mid_price = (bid + ask) / 2`. It is the minimum bar. Any forecasting model that does not produce a better Brier score than the market's own implied probability has no edge and should not be deployed. See METHODOLOGY.md.

**Q: What is the "edge"?**  
A: `edge = p_estimate - market_implied_prob - vig`. If edge > threshold (threshold TBD at G4), a position is considered. If edge ≤ 0, no position is placed. See METHODOLOGY.md and HYPOTHESES.md HYP-003.

**Q: What model class are we using?**  
A: TBD — selected at ADR-0003 during Phase 3. Candidates: logistic regression (calibrated, simple), XGBoost with Platt scaling, isotonic regression wrapper. See METHODOLOGY.md Model Selection Criteria.

**Q: What is "calibration" and why is it required?**  
A: Calibration means a model's predicted probability matches the empirical frequency of outcomes. A model that says "70% probability" should be right approximately 70% of the time. Without calibration, position sizing (Kelly) is unreliable. ECE < 0.05 is the requirement. See METHODOLOGY.md Calibration Approach.

**Q: How many experiments are needed before G4?**  
A: Minimum 3 independent experiments to avoid cherry-picking. All experiments must use the same methodology, chronological splits, and held-out test set. See RESULTS_SUMMARIES/RESULTS_INDEX.md G4 evidence requirements and TEST_STRATEGY.md.

---

## Risk and Safety Questions

**Q: What is the kill switch?**  
A: The kill switch is C7's mechanism to halt all pipeline components within ≤60 seconds of a trigger (NFR-03). It is the ONLY emergency response — there is no override path, no bypass, and no partial halt mode. It is triggered automatically by hard limit breaches and manually by the operator. See EXECUTION_ARCHITECTURE.md and RUNBOOKS/RUNBOOK_kill-switch.md.

**Q: What triggers the kill switch automatically?**  
A: Hard limit breaches (daily loss, session loss, maximum position size, simultaneous position count — all in RISK_APPETITE_CONSTRAINTS.md); drift kill threshold (Brier > baseline + 0.10); C4 Risk Engine unavailable with open position; C6 Audit Logger write failure. See SLA_SLO_SLI.md and RUNBOOK_kill-switch.md.

**Q: What happens if the kill switch triggers while the venue API is unreachable?**  
A: The pipeline halts locally. Orders already submitted to the venue that were not yet confirmed cancelled are logged as "unconfirmed." The operator must manually verify position state at the venue before any restart. See RUNBOOK_kill-switch.md Step 4.

**Q: Can we go live with real capital before G6?**  
A: No. Live capital deployment is gated behind G6 Release Gate, which requires: ADR-0005 accepted, kill switch tested and confirmed ≤60s, paper trading performance documented, all compliance gaps resolved, DS + RCO sign-off. See ROADMAP_MILESTONES.md and APPROVALS_REGISTER.md. This is invariant #4 in MEMORY_BANK.md.

---

## Technical Questions

**Q: Where should secrets (API keys, passwords) be stored?**  
A: Never in code, VCS, or logs. During Phase 1-4: .env file (gitignored) with python-dotenv. From Phase 5+: vault solution (TBD at G5, OQ-009). See SECRETS_HANDLING.md and CONTROL_MAPPING.md C-001.

**Q: What Python version is this project using?**  
A: Python 3.11+ (stable, LTS equivalent, walrus operator and match-case available). See DEPENDENCIES.md.

**Q: How do I reproduce a specific experiment?**  
A: (1) Check the EXPERIMENT_LOG entry for the experiment — it contains the Snapshot IDs, code commit hash, and run command. (2) Restore the snapshot data. (3) Check out the exact code commit. (4) Run the command in RUN_INSTRUCTIONS.md. See RUN_INSTRUCTIONS.md for the full procedure.

**Q: What is ENV-01 / ENV-02 / ENV-03?**  
A: Three strictly separated environments: ENV-01 (Research — no live credentials, snapshots only), ENV-02 (Paper Trading — live market data read-only, simulated execution), ENV-03 (Live Capital — full API access). No credential sharing between environments. See ENVIRONMENTS.md.

---

## Process Questions

**Q: How do I make a change to the system?**  
A: Check CHANGE_CONTROL.md. Is it Class A (requires ADR before implementation)? Class B (requires CHANGELOG entry)? Class C (artifact update only)? Do not implement a Class A change without a completed, accepted ADR. See CHANGE_CONTROL.md.

**Q: What is the weekly cadence?**  
A: Every week: review all artifacts with staleness triggers; update OPEN_QUESTIONS.md; update RID_LOG.md; post STATUS_REPORT. See COMMUNICATIONS_PLAN.md.

**Q: What is a "Context Pack" (CP)?**  
A: A snapshot document issued at each gate that captures the full project state at that point in time. The baseline CP is CP-2026-05-22_baseline-handoff.md. Future CPs are issued at G1, G2, etc. They are frozen once issued. See MEMORY_BANK.md and 11_MEMORY_HANDOFF/.

**Q: How do I know if an artifact is current?**  
A: Check the "Last reviewed" and "Staleness triggers" fields in the universal header. If the last review date is older than the staleness trigger warrants, the artifact may be stale. M1 health metric tracks freshness. See MEMORY_BANK.md Compass OS Health section.
