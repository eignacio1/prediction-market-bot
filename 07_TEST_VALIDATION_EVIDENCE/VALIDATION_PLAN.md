# Validation Plan — Prediction Market Trading Bot

**Purpose:** Map every requirement (FR and NFR) to its validation method, evidence location, and gate. This is the definitive answer to "how do we know the system works?"  
**Owner (role):** Evidence Owner (EO) + Methodology Validator (MV)  
**Last reviewed:** 2026-05-22  
**Next review:** G4 Evidence Gate; update when requirements or acceptance criteria change  
**Staleness triggers:** Requirements change; acceptance criteria updated; new component added; gate passed  
**Upstream links:** ACCEPTANCE_CRITERIA.md, REQUIREMENTS.md, TEST_STRATEGY.md  
**Downstream links:** 07_TEST_VALIDATION_EVIDENCE/EVIDENCE/  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 6/10 — Plan is defined; evidence collection begins Phase 3

---

## Validation Mapping — Functional Requirements

| FR ID | Requirement | Validation Method | Evidence Location | Gate | Status |
|-------|------------|------------------|------------------|------|--------|
| FR-01 | Signal Ingestion (schema validation, snapshot assignment) | TC-003, TC-004; integration test C1→C2 | EVIDENCE/FR-01/ | Phase 3 | 🔴 Pending |
| FR-02 | Forecast Generation (p_estimate + CI + snapshot_id + model_version) | Integration test; inspect C3 output fields against IF-C2-C3 | EVIDENCE/FR-02/ | Phase 3 | 🔴 Pending |
| FR-03 | Calibration Evaluation (Brier + log loss vs null model) | ≥3 experiments in EXPERIMENT_LOG; TC-005 | EVIDENCE/FR-03/ | G4 | 🔴 Pending |
| FR-04 | Decision Recording (append-only log) | TC-009; audit log hash verification | EVIDENCE/FR-04/ | Phase 3 | 🔴 Pending |
| FR-05 | Kill Switch (≤60 seconds, all components) | TC-007 kill switch drill | EVIDENCE/FR-05/ | G5 | 🔴 Pending |
| FR-06 | Backtesting Framework (pinned snapshots, look-ahead detection) | TC-001, TC-002; experiment reproducibility test | EVIDENCE/FR-06/ | Phase 3 | 🔴 Pending |
| FR-07 | Simulated Order Placement | Paper trading system test (PIPE-03) | EVIDENCE/FR-07/ | ADR-0004 | 🔴 Pending |
| FR-08 | Live Order Execution | Live system test (PIPE-04); TC-010 | EVIDENCE/FR-08/ | G6 | 🔴 Pending |
| FR-09 | Risk Limit Enforcement | TC-006; risk limit breach test | EVIDENCE/FR-09/ | ADR-0004 | 🔴 Pending |

---

## Validation Mapping — Non-Functional Requirements

| NFR ID | Requirement | Validation Method | Evidence Location | Gate | Status |
|--------|------------|------------------|------------------|------|--------|
| NFR-01 | Reproducibility (100% pinned artifacts) | Reproduce EXP-001 from scratch on clean env; results match within tolerance | EVIDENCE/NFR-01/ | G4 | 🔴 Pending |
| NFR-02 | Auditability (append-only structured logs) | TC-009; log format inspection; hash mismatch test | EVIDENCE/NFR-02/ | Phase 3 | 🔴 Pending |
| NFR-03 | Safety/Kill Switch (≤60s auto-trigger) | TC-007 timed drill | EVIDENCE/NFR-03/ | G5 | 🔴 Pending |
| NFR-04 | Data Integrity (no leakage, chronological splits) | TC-001, TC-002; temporal overlap check in all experiments | EVIDENCE/NFR-04/ | Phase 3 | 🔴 Pending |
| NFR-05 | Secrets Management (zero hardcoded secrets) | bandit scan; manual code review; no credentials in VCS | EVIDENCE/NFR-05/ | Phase 3 | 🔴 Pending |
| NFR-06 | Observability (structured JSON logs) | Log format inspection; required fields check | EVIDENCE/NFR-06/ | Phase 3 | 🔴 Pending |
| NFR-07 | Portability (dev env no live dependencies) | Run PIPE-01 without any live API credentials; confirm no network calls to venue | EVIDENCE/NFR-07/ | Phase 3 | 🔴 Pending |
| NFR-08 | Change Control (ADR for major changes) | ADR count matches major changes in CHANGELOG; no undocumented major decisions | EVIDENCE/NFR-08/ | G2 | 🔴 Pending |

---

## G4 Evidence Checklist

Before G4 Exit Gate:

### Research Evidence
- [ ] EXP-001 complete with Brier score vs null model (EVIDENCE/FR-03/)
- [ ] EXP-002 complete (or BLOCKED with documented reason)
- [ ] EXP-003 complete (temporal stability check)
- [ ] Calibration curve produced for at least one model
- [ ] Model Brier score < null model Brier score on at least 2 of 3 experiments
- [ ] Hold-out test set accessed only at G4 (not during development)

### Technical Evidence
- [ ] TC-001 through TC-004 passing (temporal integrity, snapshot discipline)
- [ ] TC-005 passing (Brier score computation correct)
- [ ] NFR-01: reproducibility demonstrated
- [ ] NFR-04: no temporal overlap detected in any experiment
- [ ] NFR-05: no secrets in codebase (bandit scan passed)

### Risk Evidence
- [ ] Risk limit thresholds proposed with Brier score justification
- [ ] Fractional Kelly fraction selected with evidence basis
- [ ] Simulated drawdown analysis on historical test set

---

## Evidence Directory Structure

```
07_TEST_VALIDATION_EVIDENCE/EVIDENCE/
  FR-01/   — Ingestion test results
  FR-02/   — Forecast output samples
  FR-03/   — Experiment Brier scores (minimum 3)
  FR-04/   — Audit log samples
  FR-05/   — Kill switch drill record
  FR-06/   — Backtesting framework test results
  FR-07/   — Paper trading system test
  FR-08/   — Live system test (post-G6)
  FR-09/   — Risk limit breach test
  NFR-01/  — Reproducibility demonstration
  NFR-02/  — Audit log format verification
  NFR-03/  — Kill switch timing record
  NFR-04/  — Temporal integrity checks
  NFR-05/  — bandit scan output
  NFR-06/  — Log format sample
  NFR-07/  — Portability test record
  NFR-08/  — ADR completeness review
```
