# Test Strategy — Prediction Market Trading Bot

**Purpose:** Define what is tested, how it is tested, and what evidence is required for each gate. Testing is the mechanism by which assumptions become verified claims.  
**Owner (role):** Evidence Owner (EO)  
**Last reviewed:** 2026-05-22  
**Next review:** G4 Evidence Gate; update when test approach changes  
**Staleness triggers:** New component added; acceptance criteria change; new failure mode identified  
**Upstream links:** ACCEPTANCE_CRITERIA.md, REQUIREMENTS.md, RESILIENCE_FAILURE_MODES.md  
**Downstream links:** VALIDATION_PLAN.md, 07_TEST_VALIDATION_EVIDENCE/EVIDENCE/, TEST_CASES/  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 6/10 — Strategy is defined; test cases written at Phase 3+

---

## Test Levels

### L1 — Unit Tests
Individual functions and components in isolation. Confirms that a function produces correct output given specified input.

**Scope:** All C1–C7 functions; feature derivation logic; Kelly sizing calculations; temporal integrity checks.

**Standard:** 100% coverage of critical paths (kill switch, risk limit checks, temporal cutoff enforcement). Minimum 80% coverage overall.

### L2 — Integration Tests
Interactions between components. Confirms that the output of one component is correctly consumed by the next.

**Scope:** C1→C2 (schema conformance); C2→C3 (feature vector shape); C3→C5 (forecast field completeness); C5→C4 (approval signal); IF-ALL-C6 (audit log format).

**Standard:** Each interface (per INTERFACES_CONTRACTS.md) must have at least one passing integration test before G4.

### L3 — System Tests (End-to-End)
Full pipeline from data ingestion to forecast/order output. Confirms the system behaves correctly as a whole.

**Scope:** Research backtest pipeline (PIPE-01); paper trading pipeline (PIPE-03, Phase 6+).

**Standard:** Full pipeline must complete without error on a pinned snapshot before any paper/live activation.

### L4 — Kill Switch Drill
Manual test of the kill switch mechanism. **Required at G5 before any live inference or capital use.**

**Scope:** Trigger kill switch while pipeline is running; confirm all components halt within ≤60 seconds; confirm C6 logs the halt event.

**Standard:** All components halted; kill switch event in C6 audit log; component restart requires operator confirmation.

---

## Test Types by Component

| Component | L1 Unit | L2 Integration | L3 System | L4 Kill Switch | Gate Required |
|-----------|---------|---------------|-----------|---------------|--------------|
| C1 Signal Ingestion | Phase 3 | Phase 3 | Phase 3 | N/A | Phase 3 |
| C2 Feature Store | Phase 3 | Phase 3 | Phase 3 | N/A | Phase 3 |
| C3 Forecasting Engine | Phase 3 | Phase 3 | Phase 3 | N/A | Phase 3 |
| C4 Execution Engine | Phase 6 | Phase 6 | Phase 6 | Phase 6 | ADR-0004 |
| C5 Risk Engine | Phase 6 | Phase 6 | Phase 6 | Phase 6 | ADR-0004 |
| C6 Audit Logger | Phase 3 | Phase 3 | Phase 3 | Phase 5 | Phase 3 |
| C7 Kill Switch | Phase 5 | Phase 5 | Phase 5 | G5 DRILL | G5 |

---

## Critical Test Cases (Must Pass Before Gate)

| Test ID | Description | Component | Gate |
|---------|-------------|-----------|------|
| TC-001 | Temporal overlap check rejects any feature with temporal_cutoff > event_date | C2 | Phase 3 |
| TC-002 | Outcome data field rejected from feature store | C1/C2 | Phase 3 |
| TC-003 | Snapshot ID required on all ingested records | C1 | Phase 3 |
| TC-004 | Invalid schema record is rejected with ERROR log; pipeline does not ingest | C1 | Phase 3 |
| TC-005 | Brier score correctly computed vs null model baseline | C3 | G4 |
| TC-006 | Risk limit check rejects order when daily_loss > hard limit | C5 | ADR-0004 |
| TC-007 | Kill switch halts all active components within ≤60 seconds | C7 | G5 |
| TC-008 | idempotency_key prevents duplicate order submission | C4 | ADR-0004 |
| TC-009 | Audit log is append-only; write confirmation before acknowledgement | C6 | Phase 3 |
| TC-010 | No real order submitted without ADR-0005 + G6 gate flag | C4 | G6 |

---

## Evidence Requirements by Gate

| Gate | Required Evidence |
|------|------------------|
| Phase 3 (research build) | TC-001 through TC-004 passing; TC-009 passing |
| G4 Evidence | ≥3 experiments with Brier score vs null model; TC-005 passing; calibration curve |
| G5 Operational | TC-007 (kill switch drill); all L1/L2/L3 tests passing; TC-009 passing |
| G6 Release | TC-010 confirmed; all tests passing; paper trading P&L evidence |
