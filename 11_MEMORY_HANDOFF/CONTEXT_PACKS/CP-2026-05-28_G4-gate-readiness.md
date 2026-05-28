# Context Pack — G4 Gate CLOSED / Phase 5 Entry
**Trigger:** G4 Evidence Gate closure; Phase 5 Operational Readiness entry  
**Date:** 2026-05-28  
**Produced by:** DS (Earl Ignacio)  
**G4 status:** ✅ CLOSED — TEST Brier +0.0084 / ECE 0.0247 / AUC 0.6062; ADR-0004 ACCEPTED (APR-0012); all sign-offs

---

## 1. Project Summary

A solo-operator NBA prediction market trading bot built on the Compass OS governance framework. The bot generates calibrated probability estimates for player prop markets (points over/under vs L10 rolling mean), using a LogisticRegression + PlattScaling model trained on historical nba_api data. Phase 3/4 (Research Build) is complete. The system has demonstrated consistent predictive signal across 3 independent chronological backtest experiments. G4 evidence criteria are met; formal gate requires TEST set evaluation and ADR-0004 acceptance.

---

## 2. Current State (2026-05-28 — Post G4 Closure)

| Area | Status |
|------|--------|
| Directory | 11 modules; all required artifacts present or registered as Phase 5+ planned |
| Phases 0–4 | ✅ COMPLETE — G0–G4 gates cleared (APR-0002 through APR-0006 + APR-0012) |
| Phase 5 | 🔴 ACTIVE — C7 (Monitoring + Kill Switch) + C8 (Visual Dashboard) primary targets |
| G4 evidence | ✅ CLOSED — 3/3 VAL + TEST all pass; TEST Brier +0.0084 / ECE 0.0247 / AUC 0.6062 |
| Components | C1 ✅ C2 ✅ (v1.2.0, 31 feat) C3 ✅ C4 ✅ C6 ✅; C5/C7/C8 Phase 5+ |
| Tests | 179/179 passing |
| ADR-0004 | ✅ ACCEPTED (APR-0012 2026-05-28) — LR+Platt (`v1-9939a6a5`) confirmed |
| Visual Dashboard | C8 registered (Architecture, Scope, Interfaces); Phase 5 implementation next |

**Key results:**
- VALIDATION: EXP-001 +0.0056/ECE 0.0345; EXP-002 +0.0049/ECE 0.0289; EXP-003 +0.0026/ECE 0.0369
- **TEST (EXP-001, 2023-24, 3,254 rows): Brier +0.0084 / ECE 0.0247 / AUC 0.6062 — stronger than VAL average**
- HYP-001/002/004 ✅ CONFIRMED; HYP-005 ✗ FALSIFIED; HYP-003 BLOCKED (Phase 5+ — DS-02 required)

---

## 3. Top 10 Canonical Links

| Purpose | Location |
|---------|----------|
| Project index + state | 11_MEMORY_HANDOFF/MEMORY_BANK.md |
| Requirements (frozen) | 01_SPEC/REQUIREMENTS.md |
| Architecture (canonical) | 02_ARCHITECTURE_DESIGN/ARCHITECTURE_OVERVIEW.md |
| ADR index | 03_DECISIONS/DECISION_LOG/DECISION_LOG.md |
| Run instructions | 06_CODE_EXECUTION_REPRODUCIBILITY/RUN_INSTRUCTIONS.md |
| Experiment results | 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/RESULTS_INDEX.md |
| G4 validation report | 07_TEST_VALIDATION_EVIDENCE/VALIDATION_REPORTS/G4_VALIDATION_REPORT.md |
| Validation sign-off | 08_MODEL_RISK_GOVERNANCE/VALIDATION_SIGNOFF.md |
| Performance metrics | 08_MODEL_RISK_GOVERNANCE/PERFORMANCE_METRICS.md |
| Kill switch runbook | 10_INFRA_OPERATIONS/RUNBOOKS/RUNBOOK_kill-switch.md |

---

## 4. Top 5 Current Risks / Issues

| # | Risk / Issue | Severity | Mitigation |
|---|-------------|---------|-----------|
| 1 | Signal magnitude (+0.0084 TEST Brier) may not survive venue vig (HYP-003 untested) | HIGH | EXP-004 at Phase 5 with live DS-02 prices; gate blocker before paper trading |
| 2 | C7 + C8 (monitoring + dashboard) not yet implemented — required before G5 paper trading gate | HIGH | Phase 5 primary focus (T-049 + T-050) |
| 3 | Kill switch drill (TC-007) not yet executed — NFR-03 ≤60s requirement unverified | HIGH | T-051 kill switch drill required before G5 |
| 4 | No live venue prices (DS-02 deferred) — real edge vs vig unknown | MEDIUM | HYP-003 / EXP-004; blocked on DS-02 integration |
| 5 | PRF taxonomy not operationalized as numeric features (OQ-017) | LOW | Phase 5+ research item |

---

## 5. Next 4 Milestones

| # | Milestone | Owner | When |
|---|-----------|-------|------|
| 1 | Phase 5: C7 Monitoring + Kill Switch implementation (T-049) | EL | Phase 5 — immediate |
| 2 | Phase 5: Kill switch drill (TC-007, NFR-03 ≤60s) — G5 gate blocker (T-051) | EL/DS | Phase 5 |
| 3 | Phase 5: C8 Visual Dashboard — Phase 5 panels: health + forecasts + calibration (T-050) | EL | Phase 5 |
| 4 | Phase 5: HYP-003 (EXP-004 — edge vs Kalshi vig; requires DS-02 live prices) | RL | Phase 5 |

---

## 6. "Do Not Break" Invariants

1. **arb/ folder = REFERENCE ONLY.** No incorporation until APR-0010. No exceptions.
2. **ADRs are immutable once accepted.** Changes require a superseding ADR.
3. **No real capital until G6 Release Gate.** DS sign-off + ADR-0005 required.
4. **No automated retraining.** Frozen model policy. New ADR + new model version required.
5. **Zero hardcoded secrets.** NFR-05. Vault/env-var protocol only.
6. **Kill switch must halt all components ≤60 seconds.** NFR-03. Tested before G5.
7. **BOT_C4_ACTIVE must NEVER be set in ENV-01 or ENV-02.**
8. **AuditLogger write failure (returns False) must trigger kill switch in all callers.**
9. **venue_id hardcoding is PROHIBITED.** Always a parameter.
10. **TEST set accessed only at formal G4 gate.** No preview.

---

## 7. Open Questions + Decision Deadlines

| OQ | Question | Owner | Deadline |
|----|---------|-------|---------|
| OQ-017 | PRF taxonomy encoding — which archetypes add signal? | RL | Phase 5+ |
| HYP-003 / EXP-004 | Does model edge survive venue vig? (G5 gate blocker) | RL | Phase 5 (DS-02 required) |
| TC-007 | Does kill switch halt all components in ≤60s? (NFR-03 — G5 gate blocker) | EL/DS | Phase 5 |
| DS-02 | When is live venue price feed available? | RL | Phase 5 |

---

## 8. Contact + Escalation

| Role | Person | Scope |
|------|--------|-------|
| All roles | Earl Ignacio (solo operator) | All decisions; no external escalation in Phase 3/4 |
