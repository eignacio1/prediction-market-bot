# Execution Plan — Prediction Market Trading Bot

**Purpose:** The authoritative, actionable delivery plan. Maps work to phases, owners, and milestones. Updated at each gate and weekly during active phases.  
**Owner (role):** Execution Lead (EL)  
**Last reviewed:** 2026-06-02 SESSION 14 (ADR-0010 band Kelly hierarchy accepted; ADR-0011 Phase 8 paper-scope ADR accepted; T-129 Path B Poisson CDF fix in run_paper_trade.py; DS-02 adapter + kill switch wired; portfolio reset to $1,000 on VPS; GG-008 RESOLVED; 692/692 tests)  
**Next review:** Weekly; update on any milestone slip > 3 days; update at each gate  
**Staleness triggers:** Milestone complete; milestone slips; scope change; resource change  
**Upstream links:** ROADMAP_MILESTONES.md, REQUIREMENTS.md, ARCHITECTURE_OVERVIEW.md  
**Downstream links:** TODO_NEXT.md, RID_LOG.md, STATUS_REPORTS/  
**Decision references:** ADR-0001, ADR-0002, ADR-0003 (PENDING)  
**Confidence:** 8/10 — G4 CLOSED 2026-05-28; Phase 5 Operational Readiness active; later phases planned at lower fidelity

---

## Phase 0 — Directory Scaffolding + Governance Spine ✅ COMPLETE

**Gate:** G0 Intent | **Completed:** 2026-05-22 | **Status:** ✅ Complete — APR-0002 signed 2026-05-22

### Phase 0 Work Plan

| # | Task | Owner | Due | Status | Blocker |
|---|------|-------|-----|--------|---------|
| 0.1 | Full directory skeleton | DS | 2026-05-21 | ✅ Done | — |
| 0.2 | 00_ADMIN complete (all 9 files + templates) | DS/PO | 2026-05-22 | ✅ Done | — |
| 0.3 | 01_SPEC complete (all 8 artifacts) | PO | 2026-05-22 | ✅ Done | — |
| 0.4 | 02_ARCHITECTURE_DESIGN complete | AO | 2026-05-22 | ✅ Done | — |
| 0.5 | 03_DECISIONS complete (ADR-0001, ADR-0002, registers) | DS | 2026-05-22 | ✅ Done | — |
| 0.6 | 04_EXECUTION complete (PLAN, TODO, RID) | EL | 2026-05-22 | ✅ Done | — |
| 0.7 | 05_RESEARCH_EXPERIMENTS complete | RL | 2026-05-22 | ✅ Done | — |
| 0.8 | 06_CODE_EXECUTION_REPRODUCIBILITY complete | AO | 2026-05-22 | ✅ Done | — |
| 0.9 | 07–10 modules complete | Multiple | 2026-05-22 | ✅ Done | — |
| 0.10 | 11_MEMORY_HANDOFF: MEMORY_BANK.md + baseline CP | DS | 2026-05-22 | ✅ Done | — |
| 0.11 | First DIR; health report | DS | 2026-05-22 | ✅ Done | — |
| 0.12 | G0 exit checklist complete | DS/PO | 2026-05-22 | ✅ Done | — |

### G0 Exit Criteria

- [x] Charter frozen (PROJECT_CHARTER.md — FROZEN status)
- [x] All 00_ADMIN artifacts in CANONICAL or FROZEN state
- [x] MEMORY_BANK.md initialized with all canonical links
- [x] Baseline Context Pack produced (CP-2026-05-22_baseline-handoff.md)
- [x] First DIR completed — M1 all artifacts stamped 2026-05-22 ✅
- [x] ADR-0001 and ADR-0002 accepted; APR-0002 signed 2026-05-22

---

## Phase 1 — Spec + Research Framing ✅ COMPLETE

**Gate:** G1 Spec | **Completed:** 2026-05-22 | **Status:** ✅ Complete — APR-0003 signed 2026-05-22

### Phase 1 Work Plan

| # | Task | Owner | Due | Status |
|---|------|-------|-----|--------|
| 1.1 | REQUIREMENTS.md frozen (all FR/NFR complete) | PO | 2026-05-31 | ✅ Done — FROZEN 2026-05-22 (T-010) |
| 1.2 | ACCEPTANCE_CRITERIA.md frozen | EO | 2026-06-01 | ✅ Done — FROZEN 2026-05-22 (T-011) |
| 1.3 | RESEARCH_QUESTIONS.md confirmed CANONICAL | RL | 2026-06-01 | ✅ Done (written at G0) |
| 1.4 | HYPOTHESES.md confirmed CANONICAL | RL | 2026-06-03 | ✅ Done (written at G0) |
| 1.5 | Player_Attribute_Matrix staged in 05_RESEARCH/ with snapshot header | RL | 2026-06-03 | ✅ Done — SNAP-001 registered 2026-05-22 |
| 1.6 | ADR-0002 confirmed (APR-0002 signed) | DS | 2026-05-22 | ✅ Done |
| 1.7 | ASSUMPTIONS_REGISTER.md populated (≥5 assumptions) | RL/AO | 2026-06-05 | ✅ Done (7 at G0) |
| 1.8 | OQ-001 resolved (Player_Attribute_Matrix provenance) | RL | 2026-06-03 | ✅ Done — resolved 2026-05-22; DATA_PROVENANCE.md updated |
| 1.9 | OQ-003 resolved (target market category) | RL/PO | 2026-06-01 | ✅ Done — NBA, dynamically agnostic, Kalshi primary; resolved 2026-05-22 |
| 1.10 | G1 exit checklist | PO/DS | 2026-06-07 | ✅ Done — all 5 criteria met; APR-0003 signed 2026-05-22 |

### G1 Exit Criteria

- [x] Requirements are testable (all FR/NFR have measurable acceptance criteria — REQUIREMENTS.md FROZEN)
- [x] Priorities are explicit (P0/P1/P2 designations confirmed — REQUIREMENTS.md FROZEN)
- [x] ASSUMPTIONS_REGISTER.md has ≥5 research assumptions (ASM-001 through ASM-007)
- [x] Target market category confirmed (OQ-003 resolved 2026-05-22 — NBA, dynamically agnostic, Kalshi primary)
- [x] Player_Attribute_Matrix provenance documented (OQ-001 resolved 2026-05-22 — DATA_PROVENANCE.md; SNAP-001)

---

## Phase 2 — Architecture + Infrastructure Design ✅ COMPLETE

**Gates:** G2 Architecture | **Completed:** 2026-05-22 | **Status:** ✅ Complete — APR-0004 signed 2026-05-22

### Phase 2 Deliverables

| Deliverable | Owner | Due | Gate | Status |
|------------|-------|-----|------|--------|
| ARCHITECTURE_OVERVIEW.md reviewed + promoted | AO | 2026-06-11 | G2 | ✅ Done — CANONICAL 2026-05-22 |
| INTERFACES_CONTRACTS.md reviewed + promoted | AO | 2026-06-13 | G2 | ✅ Done — CANONICAL 2026-05-22 |
| RESILIENCE_FAILURE_MODES.md reviewed + promoted | AO | 2026-06-15 | G2 | ✅ Done — CANONICAL 2026-05-22 |
| THREAT_MODEL.md reviewed + promoted; RCO sign-off | AO/RCO | 2026-06-15 | G2 | ✅ Done — CANONICAL 2026-05-22 |
| G2 gate signed (APR-0004) | AO | 2026-06-15 | G2 | ✅ Done — 2026-05-22 |

### G2 Exit Criteria

- [x] All core architecture artifacts CANONICAL (ARCHITECTURE_OVERVIEW, INTERFACES_CONTRACTS, RESILIENCE_FAILURE_MODES, THREAT_MODEL)
- [x] C4/C5 naming consistent across all architecture artifacts (C4=Risk Engine, C5=Execution Engine)
- [x] Interface contracts versioned and downstream-acknowledged
- [x] Technology stack confirmed (Python 3.11, JSON Lines logging, pip/pyproject.toml)
- [x] APR-0004 signed 2026-05-22

---

## Phase 2 (G3) — Execution Infrastructure Design ✅ COMPLETE

**Gate:** G3 Execution | **Completed:** 2026-05-22 | **Status:** ✅ Complete — APR-0005 signed 2026-05-22

### Phase 2/G3 Key Deliverables

| Deliverable | Owner | Due | Gate | Status |
|------------|-------|-----|------|--------|
| RUN_INSTRUCTIONS.md + ENVIRONMENTS.md reviewed + promoted | EL | 2026-06-17 | G3 | ✅ Done — CANONICAL 2026-05-22 (T-026) |
| DEPENDENCY_LOCKS/ confirmed | EL | 2026-06-17 | G3 | ✅ Done — confirmed at G3 |
| PLAN.md + RID_LOG.md baselined | EL | 2026-06-19 | G3 | ✅ Done — CANONICAL 2026-05-22 (T-027) |
| ADR-0003 formal acceptance (pending OQ-006) | AO | 2026-06-21 | G3 | ⚠️ Excepted — OQ-006 operator action; gate closed with exception |
| G3 gate signed (APR-0005) | EL/DS | 2026-06-21 | G3 | ✅ Done — 2026-05-22 |

### G3 Exit Criteria

- [x] RUN_INSTRUCTIONS.md CANONICAL — environment setup and pipeline run commands documented (Python 3.11, venv, requirements-dev.txt, pre-commit)
- [x] ENVIRONMENTS.md CANONICAL — ENV-01/02/03 defined; environment variables confirmed; health checks documented
- [x] RID_LOG.md baselined at G3 — RID-D002/D003 archived (OQ-001/003 resolved); RID-D001 updated (ADR-0003 skeleton); RID-003 partially mitigated
- [x] PLAN.md baselined for Phase 3 entry
- [⚠️] ADR-0003 formal acceptance — skeleton CANONICAL PENDING; OQ-006 excepted per standing operator authorization; must resolve before Phase 3 data integration

---

## Phases 3–4 — ✅ COMPLETE (2026-05-22 – 2026-05-28)

**Phase 3 (Research Build):** G3 CLOSED 2026-05-22 — C1–C6 implemented; ADR-0003 accepted  
**Phase 4 (Evidence Capture):** G4 CLOSED 2026-05-28 — TEST Brier +0.0084/ECE 0.0247; ADR-0004 ACCEPTED (APR-0012)

| Deliverable | Owner | Status |
|------------|-------|--------|
| ADR-0003 formal acceptance | AO | ✅ 2026-05-23 — APR-0011 |
| C1–C6 implementation | EL | ✅ 2026-05-26 — T-032/033/034 |
| EXP-001/002/003 (50-player, SNAP-2026-05-28-001) | RL | ✅ 2026-05-28 — T-043; G4 criteria MET |
| FEATURE_VERSION 1.2.0 (31 features, HYP-005 falsified) | EL | ✅ 2026-05-28 — T-046 |
| ADR-0004 (LR+Platt model class confirmation) | AO | ✅ 2026-05-28 — T-047; APR-0012 ACCEPTED |
| G4 TEST set evaluation | MV | ✅ 2026-05-28 — T-048; Brier +0.0084/ECE 0.0247/AUC 0.6062 |

## Phase 5 — Operational Readiness ✅ COMPLETE

**Gate:** G5 Operational | **Closed:** 2026-05-28 | **Status:** ✅ APR-0007 ACCEPTED

| Deliverable | Owner | Status |
|------------|-------|--------|
| C7 Monitoring + Kill Switch (T-049) | EL | ✅ 0.340ms drill; APR-0013 |
| C8 Visual Dashboard (T-050) | EL | ✅ 3 panels; CLI |
| Kill switch drill TC-007 (T-051) | EL/DS | ✅ KS-C8D7D90AF942 |
| EXP-004 HYP-003 Parts A+B (T-052) | RL | ✅ EV +$0.0855/bet; CONFIRMED |
| Sensitivity tests ST-001–004 (T-053) | MV | ✅ All PASS |

---

## Current Phase: Phase 6 — Paper Trading

**Gate:** G6 Release (live capital) | **Started:** 2026-05-29 | **Status:** 🟢 Active

### Phase 6 Key Deliverables

| Deliverable | Owner | Priority | Status |
|------------|-------|----------|--------|
| Model data refresh 5 seasons (T-058) | EL | HIGH | ✅ 2026-05-28 — EXP-005; Brier +0.0024; v1-9939a6a5 |
| Qualitative pipeline (QS + EXP-006–008) | RL | HIGH | ✅ 2026-05-28/29 — EXP-007 +0.0017 Brier CONFIRMED |
| Gradient boosting experiment (T-065/EXP-011) | EL | MED | ✅ 2026-05-29 — LR RETAINED; ADR-0004 unchanged |
| EV re-estimation (T-069/EXP-010) | RL | HIGH | ✅ 2026-05-29 — +$0.0958/bet; 61.1% win rate |
| VPS provisioning (T-059) | IO | HIGH | ✅ 2026-05-29 — 157.230.91.33; cron active |
| Paper trading pipeline PIPE-03 (T-060) | EL | HIGH | ✅ 2026-05-29 — $1,000 bankroll; running |
| Accumulate paper evidence ≥66 bets / ≥5 nights (T-110, APR-0017) | DS | HIGH | 🟡 IN PROGRESS — 0/66; Finals G1 Jun 3 |
| ADR-0005 live capital authorization (T-061) | AO/DS | LOW | 🔲 After paper evidence |

---

## Phases 3–9 — High-Level Plan

| Phase | Key Work | Gate | Target |
|-------|----------|------|--------|
| 3 Research Build | C1–C3 pipeline; first experiment; backtesting framework | — | **2026-06-21** (compressed — NBA playoffs end) |
| 4 Validation | G4 evidence collection; model card; drift thresholds confirmed | G4 | 2026-08-23 |
| 5 Operational Readiness | C7 wired; kill switch drilled; secrets vault; G5 ops gate | G5 | 2026-09-13 |
| 6 Paper Trading | Full simulated cycle; N events; paper results collected | — | 2026-10-25 |
| 7 Promotion Gate | Paper evidence reviewed; G6 readiness checklist | G6 | 2026-12-06 |
| 8 Live Capital | Real orders; drawdown tracking; governance in steady state | — | 2027-Q1 |
| 9 Self-Service Governance | Automated DIR; quarterly retrieval drills; continuous ops | — | From Phase 8 |

---

## Planning Assumptions

1. Single operator (Earl Ignacio) across all roles
2. Timeline contingent on Player_Attribute_Matrix validation (if falsified at Phase 3, G4 date shifts)
3. Venue selection (ADR-0003) could shift Phase 3 start by 1–2 weeks
4. All dates assume no major operational incident requiring remediation
