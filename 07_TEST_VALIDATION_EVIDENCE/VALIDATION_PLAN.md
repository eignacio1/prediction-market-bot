# Validation Plan — Prediction Market Trading Bot

**Purpose:** Map every requirement (FR and NFR) to its validation method, evidence location, and gate. This is the definitive answer to "how do we know the system works?"  
**Owner (role):** Evidence Owner (EO) + Methodology Validator (MV)  
**Last reviewed:** 2026-07-02 (documentation-remediation pass — every row's Status column read "🔴 Pending" despite G4 and G5 both closing months ago and Phase 6/7 running live; corrected below. Same underlying issue as 01_SPEC/ACCEPTANCE_CRITERIA.md — the `EVIDENCE/` subfolders this plan points to are genuinely empty, verified by direct listing, so "operationally demonstrated" is the honest status, not "PENDING" and not "COMPLETE.") Prior substantive review: 2026-05-22  
**Next review:** Update when requirements or acceptance criteria change, or same-session as any gate passage — the G4/G5 closures should have triggered this update and did not for over a month  
**Staleness triggers:** Requirements change; acceptance criteria updated; new component added; gate passed  
**Upstream links:** ACCEPTANCE_CRITERIA.md, REQUIREMENTS.md, TEST_STRATEGY.md  
**Downstream links:** 07_TEST_VALIDATION_EVIDENCE/EVIDENCE/  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 8/10 — Plan/mapping structure is sound; Status column corrected from MEMORY_BANK narrative and direct folder checks, and now cross-checked against populated `EVIDENCE/<REQ-ID>/EVIDENCE.md` files (RESOLVED 2026-07-06, GG-075 — see `03_DECISIONS/GOVERNANCE_GAP_LOG.md`)

---

## Validation Mapping — Functional Requirements

| FR ID | Requirement | Validation Method | Evidence Location | Gate | Status |
|-------|------------|------------------|------------------|------|--------|
| FR-01 | Signal Ingestion (schema validation, snapshot assignment) | TC-003, TC-004; integration test C1→C2 | EVIDENCE/FR-01/ | Phase 3 | ✅ Phase 3 CLOSED — operationally demonstrated in 2,282-test suite; formal evidence folder not populated |
| FR-02 | Forecast Generation (p_estimate + CI + snapshot_id + model_version) | Integration test; inspect C3 output fields against IF-C2-C3 | EVIDENCE/FR-02/ | Phase 3 | ✅ Phase 3 CLOSED — same caveat |
| FR-03 | Calibration Evaluation (Brier + log loss vs null model) | ≥3 experiments in EXPERIMENT_LOG; TC-005 | EVIDENCE/FR-03/ | G4 | ✅ G4 CLOSED 2026-05-28 (G4_VALIDATION_REPORT.md) vs 0.50 null; **vs real market price, EXP-017 has now run (2026-07-06): n=151, EV=+$0.1009/bet, DIRECTIONAL_POSITIVE — informally "Tier 1 REACHED" per GG-004, but ADR-0024's actual formal bar ("≥500 unique markets, OR ≥2 sports each n≥150") is not yet met (NBA n=0); GG-004 stays OPEN, G6_GATE_CHECKLIST.md T0-A stays BLOCKING** |
| FR-04 | Decision Recording (append-only log) | TC-009; audit log hash verification | EVIDENCE/FR-04/ | Phase 3 | ✅ Phase 3 CLOSED — same caveat |
| FR-05 | Kill Switch (≤60 seconds, all components) | TC-007 kill switch drill | EVIDENCE/FR-05/ | G5 | ✅ G5 CLOSED — drill PASSED 0.340ms, KS-C8D7D90AF942, APR-0013; formal evidence folder not populated despite a real recorded result |
| FR-06 | Backtesting Framework (pinned snapshots, look-ahead detection) | TC-001, TC-002; experiment reproducibility test | EVIDENCE/FR-06/ | Phase 3 | ✅ Phase 3 CLOSED — Data Snapshot Discipline actively enforced across all EXP runners |
| FR-07 | Simulated Order Placement | Paper trading system test (PIPE-03) | EVIDENCE/FR-07/ | ADR-0004 | ✅ ADR-0004 ACCEPTED 2026-05-28; PaperTrader live since 2026-05-29, MLB (49 resolved) + NBA (158 resolved) as of 2026-07-02 |
| FR-08 | Live Order Execution | Live system test (PIPE-04); TC-010 | EVIDENCE/FR-08/ | G6 | 🔴 Genuinely Pending — G6 not cleared, no live capital, unchanged by this review |
| FR-09 | Risk Limit Enforcement | TC-006; risk limit breach test | EVIDENCE/FR-09/ | ADR-0004 | ✅ ADR-0004 ACCEPTED; `_HARD_LIMITS` enforced on every live paper order. **GG-071 open question:** sufficiency at cadence, not enforcement — see RISK_APPETITE_CONSTRAINTS.md |

---

## Validation Mapping — Non-Functional Requirements

| NFR ID | Requirement | Validation Method | Evidence Location | Gate | Status |
|--------|------------|------------------|------------------|------|--------|
| NFR-01 | Reproducibility (100% pinned artifacts) | Reproduce EXP-001 from scratch on clean env; results match within tolerance | EVIDENCE/NFR-01/ | G4 | ✅ G4 CLOSED — Data Snapshot Discipline enforced; formal reproducibility re-run not filed here |
| NFR-02 | Auditability (append-only structured logs) | TC-009; log format inspection; hash mismatch test | EVIDENCE/NFR-02/ | Phase 3 | ✅ Phase 3 CLOSED — C6 in continuous production use |
| NFR-03 | Safety/Kill Switch (≤60s auto-trigger) | TC-007 timed drill | EVIDENCE/NFR-03/ | G5 | ✅ G5 CLOSED — MET, see FR-05 |
| NFR-04 | Data Integrity (no leakage, chronological splits) | TC-001, TC-002; temporal overlap check in all experiments | EVIDENCE/NFR-04/ | Phase 3 | ✅ Phase 3 CLOSED — chronological split enforced by design |
| NFR-05 | Secrets Management (zero hardcoded secrets) | bandit scan; manual code review; no credentials in VCS | EVIDENCE/NFR-05/ | Phase 3 | ✅ **MET — independently re-verified 2026-07-06.** Fresh bandit + detect-secrets scan: 0 real hardcoded-credential findings (1 `B105` false positive on a `DIR_PASS="PASS"` enum literal), 0 files with detected secrets. |
| NFR-06 | Observability (structured JSON logs) | Log format inspection; required fields check | EVIDENCE/NFR-06/ | Phase 3 | ✅ Phase 3 CLOSED — C7/C8 consume structured JSONL in production |
| NFR-07 | Portability (dev env no live dependencies) | Run PIPE-01 without any live API credentials; confirm no network calls to venue | EVIDENCE/NFR-07/ | Phase 3 | ✅ Phase 3 CLOSED — full 2,282-test suite runs with mocked/injected external calls, zero live network calls in CI (SESSION 110 note) |
| NFR-08 | Change Control (ADR for major changes) | ADR count matches major changes in CHANGELOG; no undocumented major decisions | EVIDENCE/NFR-08/ | G2 | ✅ G2 CLOSED, ONGOING discipline — 38 ADR slots / 71 governance gaps actively tracked. **This remediation pass is itself evidence the underlying intent (catch drift) periodically fails without an explicit trigger** — see 01_SPEC/ACCEPTANCE_CRITERIA.md's matching note. |

*(Status columns corrected 2026-07-02, evidence pointers upgraded 2026-07-06 (GG-075) — see header note. "✅ [Gate] CLOSED" means the gate formally passed and the capability is operationally demonstrated; `EVIDENCE/<REQ-ID>/` folders are now populated with an `EVIDENCE.md` grounding the claim in real test files/artifacts. Remaining `(empty)` markers below for `TEST_CASES/`/`UAT_SIGNOFFS/`-adjacent items reflect a deliberate scope decision, not an oversight — see GG-075's resolution narrative.)*

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
