# Stakeholders RACI — Prediction Market Trading Bot

**Purpose:** Define role ownership for every major artifact and workstream. No artifact is unowned. No owner lacks a review cadence.  
**Owner (role):** Directory Steward (DS)  
**Last reviewed:** 2026-07-23 — GG-074 monthly staleness review: verified current, no drift found. Artifact-level RACI structure unaffected by phase/venue/ledger changes since 2026-05-21.  
**Next review:** 2026-08-23  
**Staleness triggers:** New team member; ownership transfer; new major workstream added; phase gate passed  
**Upstream links:** PROJECT_CHARTER.md  
**Downstream links:** All artifacts (each references the relevant role from this RACI)  
**Decision references:** ADR-0001  
**Confidence:** 9/10 — Solo build; roles assigned to single operator; structured for future delegation  

---

## Role Definitions

| Role | Abbreviation | Function |
|------|-------------|----------|
| Directory Steward | DS | Owns directory health, structure, link integrity, archiving, health reporting, cadence coordination |
| Product/Problem Owner | PO | Owns intent, scope, requirements, acceptance criteria, success metrics |
| Architecture Owner | AO | Owns architecture, interfaces, NFRs, failure modes, threat model |
| Execution Lead | EL | Owns plan, status reporting, dependency tracking, delivery coordination |
| Evidence Owner | EO | Owns test strategy, validation plan, evidence capture, sign-off readiness |
| Risk/Control Owner | RCO | Owns control mapping, audit evidence spine, approvals register, risk appetite |
| Operations Owner | OO | Owns runbooks, SLOs, observability, incident process, kill switch |
| Research Lead | RL | Owns research questions, experiment logs, research summaries, signal development |
| Model Owner / Validator | MO/V | Owns model documentation, limitations, monitoring/drift plan, validation report |

*Solo build note: All roles currently held by Earl Ignacio. RACI structure preserved for governance integrity and future delegation.*

---

## Artifact-Level RACI

**Key:** R = Responsible (writes/updates) | A = Accountable (approves) | C = Consulted | I = Informed

### 00_ADMIN

| Artifact | R | A | C | I |
|----------|---|---|---|---|
| README.md | DS | DS | All | All |
| PROJECT_CHARTER.md | PO | DS | AO, RCO, EL | All |
| GLOSSARY.md | DS/RL | DS | AO, MO/V | All |
| STAKEHOLDERS_RACI.md | DS | DS | PO | All |
| COMMUNICATIONS_PLAN.md | EL | DS | All | All |
| APPROVALS_REGISTER.md | RCO | DS | PO, EO | All |
| ACCESS_REQUESTS.md | RCO | DS | OO | All |
| CHANGELOG.md | DS | DS | — | All |

### 01_SPEC

| Artifact | R | A | C | I |
|----------|---|---|---|---|
| VISION_OUTCOMES.md | PO | PO | DS, AO | All |
| SCOPE_IN_OUT.md | PO | DS | AO, RCO | All |
| REQUIREMENTS.md | PO | PO | AO, EO, RCO | All |
| ACCEPTANCE_CRITERIA.md | EO | PO | AO, MO/V | All |
| NON_FUNCTIONAL_REQUIREMENTS.md | AO | PO | OO, RCO, EO | All |
| RISK_APPETITE_CONSTRAINTS.md | RCO | PO | AO, OO | All |
| DATA_REQUIREMENTS.md | RL | PO | AO, EO | All |
| ROADMAP_MILESTONES.md | EL | PO | DS, AO | All |

### 02_ARCHITECTURE_DESIGN

| Artifact | R | A | C | I |
|----------|---|---|---|---|
| ARCHITECTURE_OVERVIEW.md | AO | AO | PO, EO, OO | All |
| SYSTEM_CONTEXT.md | AO | AO | PO, RCO | All |
| DATA_FLOWS_LINEAGE.md | AO | AO | RL, EO, RCO | All |
| INTERFACES_CONTRACTS.md | AO | AO | EO, OO, RL | All |
| EXECUTION_ARCHITECTURE.md | AO | AO | OO, RCO | All |
| RESILIENCE_FAILURE_MODES.md | AO | AO | OO, RCO | All |
| THREAT_MODEL.md | AO/RCO | RCO | OO | All |

### 03_DECISIONS

| Artifact | R | A | C | I |
|----------|---|---|---|---|
| DECISION_LOG/ADR-*.md | Varies by decision | DS | Relevant domain owners | All |
| ASSUMPTIONS_REGISTER.md | RL | AO | EO, RCO | All |
| OPEN_QUESTIONS.md | DS | DS | All | All |
| TRADEOFFS.md | AO | AO | PO, RCO | All |
| REJECTED_OPTIONS.md | AO | DS | — | All |

### 04_EXECUTION

| Artifact | R | A | C | I |
|----------|---|---|---|---|
| PLAN.md | EL | PO | AO, DS | All |
| TODO_NEXT.md | EL | EL | DS | All |
| STATUS_REPORTS/*.md | EL | DS | All | All |
| RID_LOG.md | EL | EL | AO, RCO, OO | All |
| RETROS/*.md | DS | DS | All | All |

### 05_RESEARCH_EXPERIMENTS

| Artifact | R | A | C | I |
|----------|---|---|---|---|
| RESEARCH_QUESTIONS.md | RL | PO | MO/V, EO | All |
| HYPOTHESES.md | RL | RL | MO/V | All |
| EXPERIMENT_LOG/*.md | RL | MO/V | EO | All |
| RESULTS_SUMMARIES/*.md | RL | MO/V | PO, EO | All |

### 06_CODE_EXECUTION_REPRODUCIBILITY

| Artifact | R | A | C | I |
|----------|---|---|---|---|
| RUN_INSTRUCTIONS.md | EL | AO | OO, EO | All |
| ENVIRONMENTS.md | AO | AO | OO, RCO | All |
| DATA_SNAPSHOTS_INDEX.md | RL/EO | EO | AO, RCO | All |
| SECRETS_HANDLING.md | RCO | RCO | OO, AO | All |
| PIPELINES_JOBS.md | AO | OO | EL, EO | All |

### 07_TEST_VALIDATION_EVIDENCE

| Artifact | R | A | C | I |
|----------|---|---|---|---|
| TEST_STRATEGY.md | EO | EO | AO, MO/V | All |
| VALIDATION_PLAN.md | EO | MO/V | AO, RCO | All |
| VALIDATION_REPORTS/*.md | EO/MO/V | MO/V | PO, RCO | All |

### 08_MODEL_RISK_GOVERNANCE

| Artifact | R | A | C | I |
|----------|---|---|---|---|
| MODEL_CARD.md | MO/V | MO/V | PO, RCO, EO | All |
| METHODOLOGY.md | MO/V | MO/V | RL, EO | All |
| MONITORING_DRIFT_PLAN.md | MO/V | OO | RCO, EO | All |
| VALIDATION_SIGNOFF.md | MO/V | RCO | PO | All |

### 09_SECURITY_PRIVACY_COMPLIANCE

| Artifact | R | A | C | I |
|----------|---|---|---|---|
| CONTROL_MAPPING.md | RCO | RCO | AO, OO | All |
| ACCESS_CONTROL_MATRIX.md | RCO | RCO | OO, DS | All |
| VENDOR_RISK.md | RCO | RCO | AO | All |

### 10_INFRA_OPERATIONS

| Artifact | R | A | C | I |
|----------|---|---|---|---|
| SLA_SLO_SLI.md | OO | AO | EO, PO | All |
| OBSERVABILITY.md | OO | AO | RCO, MO/V | All |
| RUNBOOKS/*.md | OO | OO | AO, EL | All |
| ONCALL.md | OO | OO | DS | All |

### 11_MEMORY_HANDOFF

| Artifact | R | A | C | I |
|----------|---|---|---|---|
| MEMORY_BANK.md | DS | DS | All | All |
| CONTEXT_PACKS/*.md | DS | DS | EL, AO | All |
| LESSONS_LEARNED.md | DS | DS | All | All |
| FAQ.md | DS | DS | All | All |

---

## Cadence Owners

| Cadence | Facilitator | Participants |
|---------|------------|-------------|
| Daily execution sync | EL | EL, DS |
| Weekly DIR | DS | DS, all artifact owners |
| Weekly C4 Council | AO / RCO | AO, RCO, OO, EO, MO/V |
| Biweekly Integration Review | AO | AO, EO, OO, RL |
| Monthly Gate Readiness Review | EL + DS | EL, DS, PO, AO |
| Quarterly Retrieval Drill | DS | DS + any new participant |
