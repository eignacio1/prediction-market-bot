# Approvals Register — Prediction Market Trading Bot

**Purpose:** Track all formal approvals required for phase gate passages, capital deployment, and major changes. Every approval must link to evidence artifacts.  
**Owner (role):** Risk/Control Owner (RCO)  
**Last reviewed:** 2026-05-28 (APR-0007 ACCEPTED — G5 gate CLOSED; EXP-004 Part B complete on mobile hotspot; HYP-003 🟢 CONFIRMED)  
**Next review:** G6 Release Gate (APR-0008/0009) — after model data refresh (2024-26 seasons) and VPS provisioning  
**Staleness triggers:** Gate passed; approval expired; approver role changed; new approval category required  
**Upstream links:** PROJECT_CHARTER.md, 03_DECISIONS/DECISION_LOG/  
**Downstream links:** 09_SECURITY_PRIVACY_COMPLIANCE/CONTROL_MAPPING.md  
**Decision references:** ADR-0001  
**Confidence:** 9/10 — Structure is complete; cells populate as gates are cleared  

---

## Register

| Approval ID | What Is Approved | Approver Role | Date | Evidence Link | Expiry / Review Trigger |
|------------|-----------------|---------------|------|---------------|------------------------|
| APR-0001 | Adopt Compass OS and PDTP governance framework | DS | 2026-05-21 | ADR-0001_adopt-compass-os.md | Superseded by Meta-ADR only |
| APR-0002 | G0 Intent Gate passage | DS / PO | 2026-05-22 | Charter + RACI + SCOPE_IN_OUT (frozen); 74 artifacts; 22/22 cross-refs verified; MEMORY_BANK.md populated; all 7 invariants encoded | Gate G1 passage |
| APR-0003 | G1 Spec Gate passage | PO | 2026-05-22 | REQUIREMENTS.md + ACCEPTANCE_CRITERIA.md (FROZEN 2026-05-22); all 5 G1 exit criteria met; ENV-01 scaffold verified; OQ-001 ✅ OQ-003 ✅ resolved | Gate G2 passage |
| APR-0004 | G2 Architecture Gate passage | AO | 2026-05-22 | ARCHITECTURE_OVERVIEW.md + INTERFACES_CONTRACTS.md + RESILIENCE_FAILURE_MODES.md + THREAT_MODEL.md (all CANONICAL 2026-05-22); C4/C5 naming corrected across all 4 artifacts; tech stack confirmed; interface contracts versioned | Gate G3 passage |
| APR-0005 | G3 Execution Gate passage | EL / DS | 2026-05-22 | RUN_INSTRUCTIONS.md + ENVIRONMENTS.md (T-026, CANONICAL G3 2026-05-22); RID_LOG.md (T-027, CANONICAL G3 2026-05-22); PLAN.md baselined; RID-D002/D003 archived; ADR-0003 skeleton CANONICAL PENDING — OQ-006 excepted (CA-legal venue enumeration; operator-only action; does not block gate per standing authorization) | Gate G4 passage |
| APR-0011 | ADR-0003 formal acceptance — Venue Selection (Kalshi Primary; CA-Legal Multi-Venue) | AO / DS | 2026-05-23 | ADR-0003_venue-selection.md (ACCEPTED); OQ-006 resolved; Kalshi confirmed CFTC-DCM, all 50 states, NBA markets; Polymarket US noted as Phase 6+ secondary | Superseded by new venue ADR only |
| APR-0012 | ADR-0004 formal acceptance — Model Class: LR+Platt (Phase 3 baseline) | AO / DS | 2026-05-28 | ADR-0004_model-class-selection.md (ACCEPTED); TEST Brier +0.0084 / ECE 0.0247 / AUC 0.6062; G4_VALIDATION_REPORT.md; exp_output/EXP-001/EXP-001_test_evaluation.json | Superseded by model class change ADR only |
| APR-0006 | G4 Evidence Gate passage | EO / MV / AO / DS | 2026-05-28 | G4_VALIDATION_REPORT.md; PERFORMANCE_METRICS.md (TEST set populated); VALIDATION_SIGNOFF.md (all roles); APR-0012 (ADR-0004 accepted); 3/3 VAL + TEST all pass Brier + ECE criteria | Gate G5 passage |
| APR-0013 | TC-007 Kill Switch Drill — NFR-03 pass | DS | 2026-05-28 | `KS-C8D7D90AF942`; halt 0.340ms; SLA 60,000ms; VALIDATION_SIGNOFF.md TC-007 row signed; `logs/drill_audit.jsonl` (3 entries: CRITICAL/INFO/WARNING) | G5 kill switch gate cleared |
| APR-0007 | G5 Operational Gate passage | OO / AO | **2026-05-28** | Kill-switch drill ✅ APR-0013 (0.340ms); ST-001–004 ✅; EXP-004 Part A ✅ HYP-003 SUPPORTED (+$0.0855 EV/bet, 2,481 bets); **EXP-004 Part B ✅** (37 live KXNBAPTS markets; session EXP-004-FE3E2169; Fox Edge +0.405 YES; SGA Edge −0.116 NO); DS-02-B-001 RESOLVED; HYP-003 🟢 CONFIRMED; T-049–T-055 ✅; 267/267 tests; H-001/H-002/H-003 hygiene fixes applied | Gate G6 passage |
| APR-0008 | G6 Release Gate — LIVE CAPITAL AUTHORIZATION | PO / RCO | PENDING | Final validation report + compliance spine + rollback test | Annual re-approval or material change |
| APR-0009 | Promote paper trading → live capital (ADR-0005) | PO / RCO | PENDING | ADR-0005 evidence; approvals APR-0006, 0007, 0008 | Per-venue re-approval |
| APR-0010 | arb/ folder incorporation into active development | PO / AO | PENDING | ADR granting incorporation | Per-incorporation |

---

## Approval Classification

| Classification | Examples | Approval Required From |
|---------------|----------|----------------------|
| Phase gate | G0–G6 passage | Relevant role owners per gate |
| Capital deployment | Any real money → live venue | PO + RCO (minimum) |
| Major scope change | New venue; new strategy class; arb/ incorporation | PO + AO + DS |
| Data access | New external data source; new API key | RCO + AO |
| Model promotion | Research → paper trading → live | MO/V + RCO + PO |
