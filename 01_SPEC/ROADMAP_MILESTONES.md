# Roadmap and Milestones — Prediction Market Trading Bot

**Purpose:** Map the phase gate sequence to calendar targets and artifact deliverables. Living document — updated at each gate.  
**Owner (role):** Execution Lead (EL)  
**Last reviewed:** 2026-05-28 (G4 Evidence Gate CLOSED; Phase 4 complete; Phase 5 active)  
**Next review:** G5 gate passage; monthly review  
**Staleness triggers:** Phase gate passed; milestone slipped >1 week; major dependency change; scope change  
**Upstream links:** PROJECT_CHARTER.md, SCOPE_IN_OUT.md, REQUIREMENTS.md  
**Downstream links:** 04_EXECUTION/PLAN.md, 04_EXECUTION/TODO_NEXT.md  
**Decision references:** ADR-0001, ADR-0002, ADR-0003, ADR-0004 (ACCEPTED — APR-0012)  
**Confidence:** 9/10 — Phases 0–4 complete; Phase 5 entry; Phases 6+ are design targets

---

## Phase Map

| Phase | Name | Gate | Target Completion | Status |
|-------|------|------|------------------|--------|
| 0 | Directory Scaffolding + Governance Spine | G0 Intent | 2026-05-22 | ✅ COMPLETE — APR-0002 signed |
| 1 | Spec + Research Framing | G1 Spec | 2026-05-22 | ✅ COMPLETE — APR-0003 signed |
| 2 | Architecture + Infrastructure Design | G2 Architecture | 2026-05-22 | ✅ COMPLETE — APR-0004 signed |
| 3 | Execution + Environment Build | G3 Execution | 2026-05-22 | ✅ COMPLETE — APR-0005 signed |
| 4 | Research Build + Evidence Capture | G4 Evidence | 2026-05-28 | ✅ COMPLETE — APR-0006 + APR-0012 signed; TEST Brier +0.0084/ECE 0.0247 |
| 5 | Operational Readiness | G5 Operational | TBD (Phase 5) | 🔴 Not Started |
| 6 | Paper Trading | — | TBD (Phase 6) | 🔴 Not Started |
| 7 | Promotion Gate | G6 Release | TBD (Phase 7) | 🔴 Not Started |
| 8 | Live Capital Operations | — | Post-G6 | 🔴 Not Started |
| 9 | Self-Service Governance | — | Ongoing from Phase 8 | 🔴 Not Started |

---

## Phase 0 — Directory Scaffolding + Governance Spine
**Gate: G0 Intent | Status: ✅ COMPLETE (APR-0002 signed 2026-05-22)**

| Milestone | Owner | Status |
|-----------|-------|--------|
| Full directory skeleton instantiated | DS | ✅ Done 2026-05-21 |
| 00_ADMIN complete (Charter, RACI, Glossary, Approvals, Access) | DS/PO | ✅ Done 2026-05-22 |
| ADR-0001 and ADR-0002 accepted | DS | ✅ Done 2026-05-21 |
| MEMORY_BANK.md initialized with all canonical links | DS | ✅ Done 2026-05-22 |
| Baseline Context Pack produced | DS | ✅ Done 2026-05-22 (CP-2026-05-22_baseline-handoff.md) |
| G0 exit: Charter frozen; RACI published; Memory Bank initialized | DS/PO | ✅ COMPLETE — APR-0002 signed 2026-05-22 |

---

## Phase 1 — Spec + Research Framing
**Gate: G1 Spec | Status: ✅ COMPLETE (APR-0003 signed 2026-05-22)**

| Milestone | Owner | Status |
|-----------|-------|--------|
| REQUIREMENTS.md frozen (all FR/NFR complete) | PO | ✅ Done 2026-05-22 (T-010) |
| ACCEPTANCE_CRITERIA.md frozen | EO | ✅ Done 2026-05-22 (T-011) |
| RESEARCH_QUESTIONS.md initial set | RL | ✅ Done 2026-05-22 |
| HYPOTHESES.md initial set | RL | ✅ Done 2026-05-22 |
| Player_Attribute_Matrix staged as DS-01 with header | RL | ✅ Done 2026-05-22 (SNAP-001) |
| ADR-0002 confirmed (strategy class: forecast-only) | DS | ✅ Done 2026-05-21 |
| ASSUMPTIONS_REGISTER.md populated | RL/AO | ✅ Done 2026-05-22 |
| G1 exit: Requirements testable; priorities explicit; assumptions logged | PO/DS | ✅ COMPLETE — APR-0003 signed 2026-05-22 |

---

## Phase 2 — Architecture + Infrastructure Design
**Gate: G2 Architecture | Status: ✅ COMPLETE (APR-0004 signed 2026-05-22)**

| Milestone | Owner | Status |
|-----------|-------|--------|
| ARCHITECTURE_OVERVIEW.md canonical | AO | ✅ Done 2026-05-22 |
| INTERFACES_CONTRACTS.md with downstream acknowledgement | AO | ✅ Done 2026-05-22 |
| DATA_FLOWS_LINEAGE.md complete | AO | ✅ Done 2026-05-22 |
| RESILIENCE_FAILURE_MODES.md (all components) | AO | ✅ Done 2026-05-22 |
| THREAT_MODEL.md drafted | AO/RCO | ✅ Done 2026-05-22 |
| DEPENDENCY_LOCKS/ initialized | EL | ✅ Done 2026-05-22 |
| G2 exit: Interfaces stable; failure modes mapped; architecture canonical | AO/EL/DS | ✅ COMPLETE — APR-0004 signed 2026-05-22 |

---

## Phase 3 — Execution + Environment Build
**Gate: G3 Execution | Status: ✅ COMPLETE (APR-0005 signed 2026-05-22)**

| Milestone | Owner | Status |
|-----------|-------|--------|
| RUN_INSTRUCTIONS.md + ENVIRONMENTS.md canonical | EL | ✅ Done 2026-05-22 |
| PLAN.md + RID_LOG.md baselined | EL | ✅ Done 2026-05-22 |
| ADR-0003 accepted (Kalshi primary venue) | AO | ✅ Done 2026-05-23 (APR-0011) |
| C1 NBAIngestionClient implemented | EL | ✅ Done 2026-05-26 (T-032) |
| C2 FeatureStore implemented (v1.2.0, 31 features) | EL | ✅ Done 2026-05-28 (T-033/T-046) |
| C3 ModelForecaster + C4 RiskEngine + C6 AuditLogger implemented | EL | ✅ Done 2026-05-26–28 (T-034/T-039/T-039b) |
| 179/179 tests passing | EL | ✅ Done 2026-05-28 |
| G3 exit: Delivery path credible; owners assigned; constraints acknowledged | EL/DS | ✅ COMPLETE — APR-0005 signed 2026-05-22 |

---

## Phase 4 — Research Build + Evidence Capture
**Gate: G4 Evidence | Status: ✅ COMPLETE — G4 CLOSED 2026-05-28 (APR-0006 + APR-0012)**

| Milestone | Owner | Status |
|-----------|-------|--------|
| TEST_STRATEGY.md complete | EO | ✅ Done 2026-05-22 |
| VALIDATION_PLAN.md complete (req mapping table) | EO/MV | ✅ Done 2026-05-22 |
| EXP-001/002/003 complete (50-player cohort, SNAP-2026-05-28-001) | RL | ✅ Done 2026-05-28 (T-043) |
| G4 evidence criteria met (3/3 beat null; ECE<0.05 all) | RL | ✅ Done 2026-05-28 |
| HYP-001/002/004 confirmed; HYP-005 falsified | RL | ✅ Done 2026-05-28 (T-044) |
| FEATURE_VERSION 1.2.0 (prune F-032–F-038) | EL | ✅ Done 2026-05-28 (T-046) |
| ADR-0004 ACCEPTED via APR-0012 (LR+Platt model class, v1-9939a6a5) | AO | ✅ Done 2026-05-28 (T-047/048) |
| PERFORMANCE_METRICS.md populated (validation + TEST set) | MV | ✅ Done 2026-05-28 |
| VALIDATION_SIGNOFF.md — all 4 roles signed | MV/EO | ✅ Done 2026-05-28 |
| ASSUMPTIONS_LIMITATIONS.md populated | MV | ✅ Done 2026-05-28 |
| G4_VALIDATION_REPORT.md complete (TEST results populated) | EO | ✅ Done 2026-05-28 |
| G4 Context Pack produced (CP-2026-05-28) | DS | ✅ Done 2026-05-28 |
| TEST set evaluation — Brier +0.0084 / ECE 0.0247 / AUC 0.6062 | RL | ✅ Done 2026-05-28 (T-048) |
| Risk limit thresholds confirmed with evidence basis | RCO/MV | 🔲 DEFERRED — Phase 5 (live-data signal context required) |
| G4 exit: Evidence collected; model validated; TEST set assessed; sign-off path executed | EO/MV/DS | 🔲 PENDING |

---

## Phase 5 — Operational Readiness
**Gate: G5 Operational | Status: 🔴 Not Started**

| Milestone | Owner | Due |
|-----------|-------|-----|
| C7 Monitoring + Kill Switch implemented and tested | EL | Phase 5 |
| C8 Visual Dashboard — Phase 5 panels (health + forecast performance + calibration trend + alert feed) | EL | Phase 5 |
| Kill switch drill timed and verified ≤60 seconds (TC-007, NFR-03) | EL/EO | Phase 5 |
| SLA_SLO_SLI.md thresholds populated with evidence | OO | Phase 5 |
| OBSERVABILITY.md wired (C7 metrics emitting) | OO | Phase 5 |
| Live credentials provisioned (ACC-0002) | EL | Phase 5 (before G5) |
| Venue API integration smoke test (no orders) | EL | Phase 5 |
| SENSITIVITY_STRESS_TESTS.md populated | MV | Phase 5 |
| CAPACITY_PLANNING.md created | OO | Phase 5 |
| G5 exit: Operable by someone other than builder; kill switch tested | OO/DS | G5 |

---

## Phase 6 — Paper Trading
**Gate: — | Status: 🔴 Not Started**

| Milestone | Owner | Due |
|-----------|-------|-----|
| ADR-0004 formally accepted (APR-0012) | AO | G4 gate |
| C5 Execution Engine implemented (simulated) | EL | Phase 6 |
| C8 Visual Dashboard — paper trading panels (P&L, fill rates, position history) | EL | Phase 6 |
| Live inference pipeline running (no orders) | EL | Phase 6 |
| Paper trading position sizing and order simulation | EL | Phase 6 |
| HYP-003 tested (EXP-004 — edge vs vig) | RL | Phase 6 |

---

## Phase 7 — Promotion Gate
**Gate: G6 Release | Status: 🔴 Not Started**

| Milestone | Owner | Due |
|-----------|-------|-----|
| ADR-0005 drafted (live capital authorization) | AO | Phase 7 |
| Final validation report (TEST set + live paper results) | MV/EO | Phase 7 |
| Live credentials (ACC-0002 confirmed) | EL | Phase 7 |
| G6 exit: All release gate criteria; ADR-0005 accepted; APR-0009 signed | DS/RCO | G6 |

---

## Phase 8+ — Live Capital + Self-Service Governance

| Phase | Description | Gate |
|-------|-------------|------|
| 8 | Live capital operations; full C1–C8 active | Post-G6 |
| 9 | Self-service governance; quarterly retrieval drills; meta-ADR reviews | Ongoing |

---

## Planned Artifacts (Phase 5+ — not yet created)

| Artifact | Phase | Module | Owner |
|---------|-------|--------|-------|
| SENSITIVITY_STRESS_TESTS.md | 5 | 08_MODEL_RISK_GOVERNANCE/ | MV |
| CAPACITY_PLANNING.md | 5 | 10_INFRA_OPERATIONS/ | OO |
| MIGRATION_PLAN.md | 6+ | 02_ARCHITECTURE_DESIGN/ | AO |
| FAIRNESS_BIAS_ASSESSMENT.md | 6+ | 08_MODEL_RISK_GOVERNANCE/ | MV |
| RELEASE_CHANGE_NOTES/Phase6.md | 6 | 10_INFRA_OPERATIONS/ | EL |
