# Control Mapping — Prediction Market Trading Bot

**Purpose:** Map security and compliance controls to NFRs, threat model entries, and governance requirements. Provides a single view of what controls exist, where they're implemented, and their current status.  
**Owner (role):** Risk and Compliance Owner (RCO)  
**Last reviewed:** 2026-05-22  
**Next review:** G2 (architecture confirmed); G5 (pre-live audit); update when new threat identified  
**Staleness triggers:** New threat added to THREAT_MODEL.md; NFR changed; control implementation completed or failed; new phase gate cleared  
**Upstream links:** THREAT_MODEL.md, NON_FUNCTIONAL_REQUIREMENTS.md, RISK_APPETITE_CONSTRAINTS.md  
**Downstream links:** ACCESS_CONTROL_MATRIX.md, POLICY_REQUIREMENTS.md, VALIDATION_PLAN.md  
**Decision references:** ADR-0001  
**Confidence:** 6/10 — Control design complete; implementation status pending Phase 3+

---

## Control Taxonomy

Controls are classified by type:

| Type | Code | Description |
|------|------|-------------|
| Preventive | PRE | Stop a threat from occurring |
| Detective | DET | Identify when a threat has occurred |
| Corrective | COR | Recover from or limit damage after a threat |
| Compensating | COM | Alternative control when primary is not feasible |

---

## Control Register

### C-001 — Secret Isolation (NFR-05)

| Field | Detail |
|-------|--------|
| Control ID | C-001 |
| Type | Preventive |
| Threat addressed | TH-02 (Credential Exposure) |
| NFR addressed | NFR-05 (Zero Hardcoded Secrets) |
| Description | No API keys, passwords, or tokens stored in code files, VCS, or logs |
| Implementation | .gitignore, pre-commit hook (bandit), vault/env-var protocol (SECRETS_HANDLING.md) |
| Implementation phase | Phase 1 (pre-commit) / Phase 5 (vault) |
| Validation method | bandit static scan; manual pre-commit hook audit; git grep for known secret patterns |
| Current status | DESIGN — pre-commit hook specified; vault TBD at G5 |
| Evidence location | VALIDATION_PLAN.md NFR-05 row |

---

### C-002 — Temporal Integrity Enforcement (NFR research)

| Field | Detail |
|-------|--------|
| Control ID | C-002 |
| Type | Preventive |
| Threat addressed | TH-01 (Data Contamination / Look-ahead Bias) |
| NFR addressed | FR-04 (Temporal Integrity) |
| Description | Mandatory `temporal_cutoff` field on all features; outcome data on separate ingestion path; chronological splits only |
| Implementation | TC-001 (overlap check), TC-002 (shuffle prohibition), DATA_FLOWS_LINEAGE.md TI-01 through TI-04 |
| Implementation phase | Phase 3 |
| Validation method | Automated temporal overlap test (TC-001); code review |
| Current status | DESIGN |
| Evidence location | TEST_STRATEGY.md TC-001, TC-002 |

---

### C-003 — Kill Switch (NFR-03)

| Field | Detail |
|-------|--------|
| Control ID | C-003 |
| Type | Corrective |
| Threat addressed | TH-05 (Kill Switch Failure), TH-04 (Order Duplication) |
| NFR addressed | NFR-03 (Kill Switch ≤60s halt) |
| Description | C7 monitors all limits; auto-triggers kill switch on breach; must halt all components within 60 seconds |
| Implementation | C7 (Monitoring); RUNBOOKS/RUNBOOK_kill-switch.md; TC-009, TC-010 |
| Implementation phase | Phase 5 (paper trading); tested before G5 |
| Validation method | Kill switch drill (TC-009, TC-010); timed halt measurement |
| Current status | DESIGN |
| Evidence location | TEST_STRATEGY.md TC-009, TC-010; RUNBOOKS/RUNBOOK_kill-switch.md |

---

### C-004 — Immutable Audit Log (NFR-06)

| Field | Detail |
|-------|--------|
| Control ID | C-004 |
| Type | Detective |
| Threat addressed | TH-09 (Audit Log Loss), TH-03 (Shadow Docs) |
| NFR addressed | NFR-06 (Audit Completeness) |
| Description | C6 logs all forecast decisions, position sizing, execution events, and risk limit evaluations with timestamps |
| Implementation | C6 (Audit Logger); append-only log; structured JSON format |
| Implementation phase | Phase 3+ |
| Validation method | TC-007 (audit completeness); log integrity check |
| Current status | DESIGN |
| Evidence location | TEST_STRATEGY.md TC-007 |

---

### C-005 — Gate Enforcement (Governance)

| Field | Detail |
|-------|--------|
| Control ID | C-005 |
| Type | Preventive |
| Threat addressed | TH-07 (Unauthorized Capital Deployment) |
| NFR addressed | NFR-02 (Phase Gate Compliance) |
| Description | No component activated before its phase gate is cleared; gate exit criteria documented and signed in APPROVALS_REGISTER.md |
| Implementation | APPROVALS_REGISTER.md; ROADMAP_MILESTONES.md gate criteria; CHANGE_CONTROL.md Class A enforcement |
| Implementation phase | All phases |
| Validation method | APPROVALS_REGISTER sign-off audit; ADR chain review |
| Current status | ACTIVE — G0 in progress |
| Evidence location | APPROVALS_REGISTER.md |

---

### C-006 — ADR Immutability (Governance)

| Field | Detail |
|-------|--------|
| Control ID | C-006 |
| Type | Preventive |
| Threat addressed | TH-03 (Shadow Docs / Governance Drift) |
| NFR addressed | NFR-08 (Governance Completeness) |
| Description | Accepted ADRs are immutable; any change requires a superseding ADR; no silent changes to model, risk limits, or strategy |
| Implementation | CHANGE_CONTROL.md Class A enforcement; ADR naming convention; DECISION_LOG.md index |
| Implementation phase | All phases |
| Validation method | Manual ADR audit; DECISION_LOG.md currency check |
| Current status | ACTIVE |
| Evidence location | 03_DECISIONS/ADR-0001 |

---

### C-007 — Drift Monitoring (Operational)

| Field | Detail |
|-------|--------|
| Control ID | C-007 |
| Type | Detective |
| Threat addressed | TH-08 (Stale Model / Undetected Drift) |
| NFR addressed | FR-08 (Drift Monitoring) |
| Description | C7 computes rolling Brier score and ECE; auto-alerts on threshold breach; auto-halts on kill threshold |
| Implementation | C7; MONITORING_DRIFT_PLAN.md; RUNBOOKS/RUNBOOK_model-drift.md |
| Implementation phase | Phase 5+ |
| Validation method | TC-008 (monitoring alert); drift simulation test |
| Current status | DESIGN |
| Evidence location | MONITORING_DRIFT_PLAN.md |

---

### C-008 — Data Snapshot Immutability (Research Integrity)

| Field | Detail |
|-------|--------|
| Control ID | C-008 |
| Type | Preventive |
| Threat addressed | TH-01 (Data Contamination), TH-06 (Overfitting via Data Leakage) |
| NFR addressed | FR-04 (Temporal Integrity) |
| Description | Every data snapshot is registered with hash and schema version; immutable after registration; all experiments cite Snapshot IDs |
| Implementation | DATA_SNAPSHOTS_INDEX.md; snapshot naming convention (SNAP-YYYY-MM-DD-NNN) |
| Implementation phase | Phase 3+ |
| Validation method | Hash verification; experiment log citation audit |
| Current status | DESIGN |
| Evidence location | DATA_SNAPSHOTS_INDEX.md |

---

### C-009 — Dependency Lock (Supply Chain)

| Field | Detail |
|-------|--------|
| Control ID | C-009 |
| Type | Preventive |
| Threat addressed | TH-01 (Indirect data contamination via dependency mutation) |
| NFR addressed | NFR-07 (Reproducibility) |
| Description | All dependencies pinned to exact versions; requirements-lock.txt maintained; bandit scans all imports |
| Implementation | DEPENDENCIES.md; requirements-lock.txt (Phase 1); DEPENDENCY_LOCKS/ |
| Implementation phase | Phase 1 |
| Validation method | Dependency diff check; bandit scan |
| Current status | DESIGN |
| Evidence location | DEPENDENCIES.md |

---

### C-010 — Frozen Model Policy (Model Risk)

| Field | Detail |
|-------|--------|
| Control ID | C-010 |
| Type | Preventive |
| Threat addressed | TH-08 (Stale Model), TH-06 (Silent Overfitting via Retraining) |
| NFR addressed | FR-07 (Frozen Model) |
| Description | Retraining in production is prohibited; model promoted via ARTIFACT_REGISTRY.md with ADR approval |
| Implementation | ARTIFACT_REGISTRY.md; CHANGE_CONTROL.md (Class A); REJECTED_OPTIONS.md RO-007 |
| Implementation phase | Phase 5+ |
| Validation method | Artifact registry audit; production environment check |
| Current status | POLICY ACTIVE — implementation phase 5 |
| Evidence location | ARTIFACT_REGISTRY.md; MODEL_CARD.md Governance section |

---

## Control-to-Threat Mapping Summary

| Threat ID | Threat Name | Primary Control | Secondary Controls |
|-----------|-------------|-----------------|-------------------|
| TH-01 | Data Contamination | C-002 (Temporal Integrity) | C-008 (Snapshots), C-009 (Dependencies) |
| TH-02 | Credential Exposure | C-001 (Secret Isolation) | — |
| TH-03 | Shadow Docs | C-006 (ADR Immutability) | C-004 (Audit Log) |
| TH-04 | Order Duplication | C-003 (Kill Switch) | C-004 (Audit Log) |
| TH-05 | Kill Switch Failure | C-003 (Kill Switch) | C-007 (Drift Monitoring) |
| TH-06 | Overfitting | C-002 (Temporal Integrity) | C-008 (Snapshots), C-010 (Frozen Model) |
| TH-07 | Unauthorized Capital | C-005 (Gate Enforcement) | C-006 (ADR Immutability) |
| TH-08 | Stale Model | C-007 (Drift Monitoring) | C-010 (Frozen Model) |
| TH-09 | Audit Log Loss | C-004 (Audit Log) | — |

---

## Control Status Summary

| Control | Type | Status | Phase Active |
|---------|------|--------|-------------|
| C-001 Secret Isolation | PRE | DESIGN / partial | Phase 1 |
| C-002 Temporal Integrity | PRE | DESIGN | Phase 3 |
| C-003 Kill Switch | COR | DESIGN | Phase 5 |
| C-004 Audit Log | DET | DESIGN | Phase 3 |
| C-005 Gate Enforcement | PRE | **ACTIVE** | All |
| C-006 ADR Immutability | PRE | **ACTIVE** | All |
| C-007 Drift Monitoring | DET | DESIGN | Phase 5 |
| C-008 Snapshot Immutability | PRE | DESIGN | Phase 3 |
| C-009 Dependency Lock | PRE | DESIGN | Phase 1 |
| C-010 Frozen Model Policy | PRE | POLICY ACTIVE | Phase 5 |
