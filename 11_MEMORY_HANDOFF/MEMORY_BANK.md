# Memory Bank — Prediction Market Trading Bot

**Purpose:** The canonical navigation index for this project. The definitive source of truth for what exists, where it lives, and what its current status is. Designed to be the first file read in any new context window to restore full situational awareness.  
**Owner (role):** Director/Sponsor (DS) — the operator is responsible for keeping this current  
**Last reviewed:** 2026-05-28 (ST-001–004 ALL PASS; ACC-0002 logged; DS-02-B-001 documented; run_sensitivity_tests.py committed; all Phase 5 non-blocked tasks complete)  
**Next review:** Every session; weekly cadence; after every gate clearance  
**Staleness triggers:** Any artifact added, changed, or superseded; any gate cleared; any new context window opened  
**Upstream links:** All artifacts (this file indexes everything)  
**Downstream links:** TODO_NEXT.md (current work); STATUS_REPORTS/ (phase snapshots)  
**Decision references:** ADR-0001 (Compass OS adoption)  
**Confidence:** 10/10 — Reflects complete G4 gate state as of 2026-05-28

---

## Project Identity

| Field | Value |
|-------|-------|
| Project | Prediction Market Trading Bot |
| Current phase | **Phase 4 COMPLETE → Phase 5 Operational Readiness** (G4 ✅ CLOSED 2026-05-28; Phase 5 now active) |
| Operator | Earl Ignacio |
| Started | 2026-05-21 |
| Framework | Compass OS (ADR-0001) |
| Strategy class | Forecast-only (ADR-0002); arb/ reference-only pending APR-0010 |
| Capital status | NO LIVE CAPITAL — research and paper trading only until G6 |
| Last major milestone | **G4 CLOSED 2026-05-28** — TEST set Brier 0.2416 (+0.0084 vs null) / ECE 0.0247 / AUC 0.6062; ADR-0004 ACCEPTED (APR-0012); VALIDATION_SIGNOFF.md all 4 roles signed; Phase 5 (C7 + C8) unblocked |

---

## ANTI-CONTEXT-EROSION INVARIANTS

These 7 rules are absolute. They must be restored to any context that loses them.

1. **arb/ folder = REFERENCE ONLY.** Do not incorporate into any active work, experiment, or component until ADR is accepted (APR-0010 is the future gate). See REJECTED_OPTIONS.md RO-001.

2. **Player_Attribute_Matrix_v4.docx = Research input only.** NOT a canonical spec. Requires independent validation and provenance documentation (OQ-001) before use in any experiment.

3. **ADRs are immutable once accepted.** Changes require a superseding ADR. No silent changes to strategy, risk limits, or model.

4. **No real capital until G6 Release Gate is formally cleared** (APPROVALS_REGISTER.md, DS sign-off, ADR-0005 accepted).

5. **No automated retraining in production.** Frozen model policy. Retraining requires new ADR + new model version + G4-equivalent evidence.

6. **Zero hardcoded secrets** (NFR-05). No API key, password, or token in code, VCS, or logs. Vault/env-var protocol only.

7. **Kill switch must halt all components within ≤60 seconds** (NFR-03). Tested before G5. No bypass path.

---

## Module Index

### 00_ADMIN/ — Project Administration

| Artifact | Status | Confidence | Purpose |
|---------|--------|-----------|---------|
| README.md | CANONICAL | 9/10 | Project entry point and navigation |
| PROJECT_CHARTER.md | CANONICAL | 9/10 | Scope, objectives, success criteria |
| GLOSSARY.md | CANONICAL | 8/10 | Terminology definitions |
| STAKEHOLDERS_RACI.md | CANONICAL | 8/10 | Roles and accountability |
| APPROVALS_REGISTER.md | ACTIVE | 9/10 | Gate sign-offs and ADR approvals |
| ACCESS_REQUESTS.md | ACTIVE | 8/10 | API and data access log |
| CHANGELOG.md | ACTIVE | 10/10 | All project changes |
| COMMUNICATIONS_PLAN.md | CANONICAL | 7/10 | Documentation and review cadence |
| TEMPLATES/ | CANONICAL | 9/10 | Reusable templates |

---

### 01_SPEC/ — Specification

| Artifact | Status | Confidence | Key Content |
|---------|--------|-----------|------------|
| VISION_OUTCOMES.md | CANONICAL | 9/10 | Project vision; what success looks like |
| SCOPE_IN_OUT.md | CANONICAL | 9/10 | In/out of scope; arb/ exclusion documented |
| REQUIREMENTS.md | CANONICAL | 8/10 | FR-01 through FR-09; 8 functional requirements |
| RISK_APPETITE_CONSTRAINTS.md | CANONICAL | 7/10 | Hard limits (all TBD at G4); kill switch triggers |
| NON_FUNCTIONAL_REQUIREMENTS.md | CANONICAL | 8/10 | NFR-01 through NFR-08 including kill switch (NFR-03) |
| ACCEPTANCE_CRITERIA.md | CANONICAL | 8/10 | Gate-by-gate pass/fail criteria |
| DATA_REQUIREMENTS.md | CANONICAL | 7/10 | DS-01, DS-02, DS-03 requirements |
| ROADMAP_MILESTONES.md | ACTIVE | 8/10 | Phase gates G0-G6 with exit criteria |

---

### 02_ARCHITECTURE_DESIGN/ — Architecture

| Artifact | Status | Confidence | Key Content |
|---------|--------|-----------|------------|
| ARCHITECTURE_OVERVIEW.md | **CANONICAL (G2 2026-05-22)** | 9/10 | C1-C7 components; C4=Risk Engine, C5=Execution Engine (corrected); tech stack confirmed |
| DATA_FLOWS_LINEAGE.md | CANONICAL | 8/10 | TI-01 through TI-04 temporal integrity rules |
| INTERFACES_CONTRACTS.md | **CANONICAL (G2 2026-05-22)** | 8/10 | IF-C1-C2, IF-C2-C3, IF-C3-C4, IF-C4-C5, IF-C5-VENUE, IF-ALL-C6 |
| RESILIENCE_FAILURE_MODES.md | **CANONICAL (G2 2026-05-22)** | 7/10 | FM-01 through FM-08; C4/C5 corrected |
| SYSTEM_CONTEXT.md | CANONICAL | 8/10 | System boundary; 5 external actors; arb/ outside boundary |
| EXECUTION_ARCHITECTURE.md | CANONICAL | 8/10 | 4 execution modes; kill switch design; Kelly formula |
| THREAT_MODEL.md | **CANONICAL (G2 2026-05-22)** | 6/10 | STRIDE; TH-01 through TH-09; C4/C5 corrected |
| DEPENDENCIES.md | CANONICAL | 7/10 | Python stack; dependency risk register |

---

### 03_DECISIONS/ — Architecture Decision Records

| Artifact | Status | Confidence | Key Content |
|---------|--------|-----------|------------|
| ADR-0001 | **ACCEPTED — IMMUTABLE** | 10/10 | Compass OS adoption; reason: prior iteration failure |
| ADR-0002 | **ACCEPTED — IMMUTABLE** | 10/10 | Forecast-only strategy; arb/ reference-only |
| ADR-0003 | **ACCEPTED — IMMUTABLE (2026-05-23)** | 9/10 | Venue selection: Kalshi primary (CFTC-DCM, all 50 states, NBA markets); Polymarket US Phase 6+ secondary; APR-0011 signed; OQ-006 resolved |
| ADR-0004 | **ACCEPTED — APR-0012 (2026-05-28)** | 10/10 | LR+Platt confirmed; TEST Brier +0.0084/ECE 0.0247; G4 gate CLOSED |
| ADR-0005 | PENDING (G6) | — | Live capital authorization |
| DECISION_LOG.md | ACTIVE | 9/10 | ADR index; judgment call log |
| ASSUMPTIONS_REGISTER.md | ACTIVE | 8/10 | ASM-001 through ASM-007; falsification conditions |
| OPEN_QUESTIONS.md | ACTIVE | 9/10 | OQ-001 through OQ-014; resolution owners |
| TRADEOFFS.md | CANONICAL | 8/10 | TR-001 through TR-006; explicit trade-off rationale |
| REJECTED_OPTIONS.md | CANONICAL | 9/10 | RO-001 through RO-007; what not to do and why |

**Critical open questions:**
- ~~OQ-001~~ ✅ RESOLVED 2026-05-22 — Earl Ignacio / 2026-05-21 / NBA / PRF framework; SNAP-001
- ~~OQ-003~~ ✅ RESOLVED 2026-05-22 — NBA basketball; dynamically agnostic event types; Kalshi primary venue
- ~~OQ-006~~ ✅ RESOLVED 2026-05-23 — Kalshi confirmed CFTC-DCM primary; Polymarket US Phase 6+ secondary; ADR-0003 ACCEPTED
- ~~OQ-015~~ ✅ RESOLVED 2026-05-23 — nba_api confirmed as Phase 3 data proxy; Synergy/Second Spectrum deferred to Phase 5 enrichment

---

### 04_EXECUTION/ — Execution Tracking

| Artifact | Status | Confidence | Key Content |
|---------|--------|-----------|------------|
| PLAN.md | ACTIVE | 8/10 | G3 CLOSED; Phase 3 Research Build; G0-G9 roadmap |
| TODO_NEXT.md | ACTIVE | 10/10 | Current session tasks; next-up |
| RID_LOG.md | **CANONICAL (G3); updated 2026-05-28** | 8/10 | DS-02-B-001 (Kalshi TLS block, P1) active; RID-D001 partially resolved; RID-006 RESOLVED (APR-0013); RID-D002/D003 archived |
| RESOURCE_BUDGET.md | ACTIVE | 7/10 | Capital budget by phase (all TBD until G6) |
| STATUS_REPORTS/ | ACTIVE | 9/10 | STATUS_2026-05-22.md (current) |

---

### 05_RESEARCH_EXPERIMENTS/ — Research

| Artifact | Status | Confidence | Key Content |
|---------|--------|-----------|------------|
| RESEARCH_QUESTIONS.md | CANONICAL | 8/10 | SQ-001, CQ-001, EQ-001, RQ-001, RSQ-001 |
| HYPOTHESES.md | CANONICAL | 8/10 | HYP-001 through HYP-004; falsification conditions |
| EXPERIMENT_LOG/ | ACTIVE | 9/10 | EXP-TEMPLATE.md; **EXP-001_first-pipeline-run.md** (RUNNING — started 2026-05-27); **EXP-002_backtest-window-2.md** (PLANNED — HYP-001 window 2); **EXP-003_backtest-window-3.md** (PLANNED — HYP-001 window 3 + HYP-004) |
| RESULTS_SUMMARIES/ | ACTIVE | 9/10 | RESULTS_INDEX.md (EXP-001 RUNNING; EXP-002/003 PLANNED; EXP-004 BLOCKED; 0/3 experiments complete) |
| LITERATURE_REVIEW/ | ACTIVE | 7/10 | LITERATURE_REVIEW.md (5 topic areas; **Section 4 NBA-specific** — 4.1–4.6 complete, T-020 done; OQ-015 registered) |
| DATA_SOURCES/ | ACTIVE | 9/10 | SNAP-001: DS-01_Player_Attribute_Matrix_v4.docx registered 2026-05-22; **SNAP-002: EXP-001 raw game logs registered 2026-05-27**; **SNAP-003: Backtest fresh pull pre-registered 2026-05-27 (row count TBD; use --raw-csv to avoid)**; README.md with governance rules |

**Key research constraint:** DS-01 provenance resolved (OQ-001 ✅). OQ-015 resolved — nba_api confirmed Phase 3 proxy. C1–C4 pipeline implemented. EXP-001 runner created (T-035 in progress). SNAP-002 registered. EXP-001 record filed. Pending: Earl runs pipeline locally to produce actual metrics.

---

### 06_CODE_EXECUTION_REPRODUCIBILITY/ — Reproducibility

| Artifact | Status | Confidence | Key Content |
|---------|--------|-----------|------------|
| RUN_INSTRUCTIONS.md | **CANONICAL (G3 2026-05-22)** | 8/10 | Python 3.11 venv setup; EXP-001 command (run_exp001.py); EXP-002/003 command (run_backtest.py); test suite command; audit log verification; reproducibility checklist updated |
| ENVIRONMENTS.md | **CANONICAL (G3 2026-05-22)** | 7/10 | ENV-01/02/03 confirmed; 7 health checks; VENUE_ID env var per ADR-0003 |
| DATA_SNAPSHOTS_INDEX.md | ACTIVE | 9/10 | Snapshot discipline; **2 snapshots registered** (SNAP-001 DS-01; SNAP-002 EXP-001 game logs) |
| SECRETS_HANDLING.md | CANONICAL | 9/10 | NFR-05 protocol; vault TBD at G5 |
| PIPELINES_JOBS.md | CANONICAL | 8/10 | PIPE-01 through PIPE-04; escalation table |
| NOTEBOOKS_POLICY.md | CANONICAL | 9/10 | Exploration only; prohibited patterns |
| ARTIFACT_REGISTRY.md | ACTIVE | 9/10 | Model/feature/config registry; 0 artifacts promoted |

---

### 07_TEST_VALIDATION_EVIDENCE/ — Testing

| Artifact | Status | Confidence | Key Content |
|---------|--------|-----------|------------|
| TEST_STRATEGY.md | CANONICAL | 8/10 | TC-001 through TC-010; 4 test levels; kill switch drill |
| VALIDATION_PLAN.md | CANONICAL | 8/10 | FR + NFR validation mapping; G4 evidence checklist |

**Critical tests:**
- TC-001/002: Temporal integrity (blocks any experiment)
- TC-009/010: Kill switch drill (blocks G5)

---

### 08_MODEL_RISK_GOVERNANCE/ — Model Governance

| Artifact | Status | Confidence | Key Content |
|---------|--------|-----------|------------|
| MODEL_CARD.md | DRAFT | 7/10 | Training procedure documented (pipeline, NaN imputation, edge formula, Wilson CI); known limitations (8 entries); performance metrics pending EXP-001/002/003 |
| MONITORING_DRIFT_PLAN.md | CANONICAL | 6/10 | Drift response ladder L1-L4; thresholds placeholder |
| DATA_PROVENANCE.md | CANONICAL | 7/10 | DS-01 provenance documented (OQ-001 ✅ 2026-05-22); DS-02/DS-03 pending venue confirmation |
| METHODOLOGY.md | CANONICAL | 8/10 | Forecasting framework; calibration approach; model spec; strategy architecture A–H; feature table; validation checklist |
| CHANGE_CONTROL.md | CANONICAL | 8/10 | Class A/B/C change classification |

---

### 09_SECURITY_PRIVACY_COMPLIANCE/ — Security

| Artifact | Status | Confidence | Key Content |
|---------|--------|-----------|------------|
| CONTROL_MAPPING.md | CANONICAL | 6/10 | C-001 through C-010; threat-to-control mapping |
| ACCESS_CONTROL_MATRIX.md | CANONICAL | 7/10 | R-01 through R-06; RES-01 through RES-12; access matrix |
| POLICY_REQUIREMENTS.md | CANONICAL | 4/10 | POL-001 through POL-006; 3 compliance gaps |
| DATA_RETENTION_DELETION.md | CANONICAL | 6/10 | CAT-01 through CAT-08; retention periods |
| VENDOR_RISK.md | CANONICAL | 8/10 | VND-01 Kalshi (primary, ACCEPTED); VND-02–04 unchanged; Polymarket US Phase 6+ secondary noted |
| AUDIT_EVIDENCE/ | SKELETON | — | Evidence directory; populated at G5+ |

---

### 10_INFRA_OPERATIONS/ — Infrastructure

| Artifact | Status | Confidence | Key Content |
|---------|--------|-----------|------------|
| SLA_SLO_SLI.md | CANONICAL | 6/10 | SLOs by component; availability targets by phase |
| OBSERVABILITY.md | CANONICAL | 6/10 | Log standard; metrics; alerting rules ALT-001 through ALT-008 |
| RUNBOOKS/RUNBOOK_kill-switch.md | CANONICAL | 8/10 | Kill switch activation; drill procedure; recovery |
| RUNBOOKS/RUNBOOK_model-drift.md | CANONICAL | 7/10 | L1-L4 drift response; ADR trigger conditions |
| ONCALL.md | CANONICAL | 8/10 | Solo operator on-call protocol; live capital obligations |
| KNOWN_ISSUES.md | ACTIVE | 9/10 | KI-001 through KI-007; severity and gate impact |

---

### 11_MEMORY_HANDOFF/ — Context Continuity

| Artifact | Status | Confidence | Key Content |
|---------|--------|-----------|------------|
| MEMORY_BANK.md | **THIS FILE** | 9/10 | Canonical navigation index |
| CP-2026-05-22_baseline-handoff.md | CANONICAL | 9/10 | G0 baseline Context Pack |
| LESSONS_LEARNED.md | ACTIVE | 8/10 | Prior iteration failures; current mitigations |
| FAQ.md | CANONICAL | 8/10 | Common questions with authoritative answers |

---

## Current State Snapshot (2026-05-28)

**Phase:** 3 (Research Build) — G3 ✅ CLOSED (APR-0005 2026-05-22); Phase 3 target **2026-06-21** (compressed — NBA playoffs end)  
**G0 gate:** ✅ COMPLETE — APR-0002 signed 2026-05-22  
**G1 gate:** ✅ COMPLETE — APR-0003 signed 2026-05-22 (all 5 exit criteria met)  
**G2 gate:** ✅ COMPLETE — APR-0004 signed 2026-05-22 (all 4 arch artifacts CANONICAL; C4/C5 corrected)  
**G3 gate:** ✅ COMPLETE — APR-0005 signed 2026-05-22 (RUN_INSTRUCTIONS + ENVIRONMENTS + RID_LOG CANONICAL)  
**All modules:** COMPLETE (11/11; 74 artifacts + Phase 1–3 additions)  
**Phase 3 build:** T-031–T-034 ✅ COMPLETE (2026-05-26); T-035–T-042 ✅ ALL COMPLETE (2026-05-27/28); **G4 NOT MET** — 1/3 experiments beat null (need 2/3)  
**Components implemented:** C6 AuditLogger ✅ | C1 NBAIngestionClient ✅ | C2 FeatureStore ✅ | C3 ModelForecaster ✅ | C4 RiskEngine ✅ | C5/C7 skeleton only  
**T-043 status:** ✅ COMPLETE 2026-05-28 — 50-player run; EXP-001 +0.0056/ECE 0.0345; EXP-002 +0.0049/0.0289; EXP-003 +0.0026/0.0369; G4 MET  
**T-044 status:** ✅ COMPLETE 2026-05-28 — Ablation: v1.0.0 (31 feat) Δ Brier = +0.0002 vs v1.1.0; HYP-005 FALSIFIED  
**Experiments run:** 3/3 complete — ✅ G4 MET; FEATURE_VERSION 1.2.0 queued (prune 7 v1.1.0 features)  
**Snapshots registered:** 3 (SNAP-001 DS-01; SNAP-002 EXP-001 raw game logs; SNAP-003 backtest fresh pull pre-registered)  
**ADRs accepted:** 3 (ADR-0001, ADR-0002, ADR-0003)  
**ADRs pending:** 2 (ADR-0004, ADR-0005 at correct gates)  
**Open questions:** 11 open (OQ-001 ✅ OQ-003 ✅ OQ-006 ✅ OQ-015 ✅ resolved; remaining OQs non-blocking)  
**Active risks:** 6 (RID-001 through RID-006; RID-D002/D003 archived)  
**Live capital:** NOT DEPLOYED  
**Domain:** NBA basketball — dynamically agnostic event types; Kalshi primary venue (ACCEPTED ADR-0003)  

---

## What Must Happen Next

**Phase 1 — COMPLETE ✅** All tasks done 2026-05-22.
**G2 Gate — COMPLETE ✅** APR-0004 signed 2026-05-22.
**G3 Gate — COMPLETE ✅** APR-0005 signed 2026-05-22. T-026, T-027, T-030 all done.
**ADR-0003 — ACCEPTED ✅** APR-0011 signed 2026-05-23. OQ-006/OQ-015 resolved.
**C1–C4 — IMPLEMENTED ✅** T-031–T-034 complete 2026-05-26.

**Phase 3, 4 — COMPLETE ✅** All tasks done (T-035–T-048). G4 CLOSED 2026-05-28. ADR-0004 ACCEPTED.

**Phase 5 (Operational Readiness) — IN PROGRESS:**

1. **T-049 ✅ COMPLETE 2026-05-28** — C7 `c7_monitoring/monitor.py`; `SystemMonitor` with rolling Brier/ECE/edge; L1–L4 drift ladder; thread-safe kill switch; `run_kill_switch_drill()` method; 55 tests
2. **T-050 ✅ COMPLETE 2026-05-28** — C8 `c8_dashboard/dashboard.py`; 3 panels (system health, drift metrics, alert feed); reads C6 JSONL; CLI entrypoint; 33 tests
3. **T-051 ✅ COMPLETE 2026-05-28** — Kill switch drill PASSED; halt 0.340ms (SLA 60,000ms); KS-C8D7D90AF942; APR-0013 signed; VALIDATION_SIGNOFF.md TC-007 row complete; **G5 kill switch gate CLEARED**
4. **T-052 🔴 BLOCKED** — EXP-004/HYP-003 (edge vs vig); requires DS-02 (Kalshi API creds/ACC-0002)
5. **T-053 ✅ COMPLETE 2026-05-28** — ST-001–004 ALL PASS; `run_sensitivity_tests.py` created; results in `exp_output/SENSITIVITY_TESTS/sensitivity_test_results.json`
   - ST-001 (imputation): PASS — all 3 strategies yield identical Δ Brier (+0.0054)
   - ST-002 (training window): PASS — beats null at 25%/50%/100% window
   - ST-003 (C parameter): PASS — C=1.0 within 0.0008 of best C=0.01
   - ST-004 (permutation importance): PASS — dominant feature `pts_season_mean` at 27% (< 50%)
6. **T-054 ✅ COMPLETE 2026-05-28** — MODEL_CARD.md 10/10; TEST set populated; C7 monitoring wired; LIM-003 updated
7. **T-055 ✅ COMPLETE 2026-05-28** — CAPACITY_PLANNING.md stub created
8. **ACC-0002 ✅ LOGGED 2026-05-28** — Kalshi read-only API key provisioned; ACCESS_REQUESTS.md updated

**DS-02-B-001 BLOCKER (open):** `api.elections.kalshi.com` drops TLS handshake from this machine for all clients. Blocks T-052/ST-005. Resolution: install Homebrew interactively (`! /bin/bash -c "$(curl ...)"` needs sudo), then `brew install python@3.11` + verify API key in Kalshi dashboard. RID_LOG.md DS-02-B-001.

**All Phase 5 non-blocked tasks complete.** T-052 remains blocked (DS-02-B-001 / Kalshi API TLS).

See TODO_NEXT.md for session-level task tracking.

---

## Compass OS Health (as of 2026-05-28)

| Metric | Status |
|--------|--------|
| M1 Artifact Freshness | All Phase 5 artifacts updated 2026-05-28; MEMORY_BANK, TODO_NEXT, RUN_INSTRUCTIONS, MODEL_CARD, SENSITIVITY_STRESS_TESTS, CAPACITY_PLANNING all current ✅ |
| M2 Open Question Count | 11 open OQs — 4 resolved (OQ-001/003/006/015); remaining non-critical-path ✅ |
| M3 ADR Coverage | 4 accepted (ADR-0001/002/003/004); ADR-0005 pending at G6 ✅ |
| M4 Assumption Validation | ASM-001–009; EXP-001–003 validated 3 experiments ✅ |
| M5 Risk Register Currency | 6 active risks; no new risks added in Phase 5 build ✅ |
| M6 Gate Progress | G0–G4 ✅ ALL CLOSED | Phase 5 🟡 In Progress — all non-blocked tasks complete; T-051 drill ✅ APR-0013; T-052 🔴 BLOCKED (DS-02) |
| M7 Component Implementation | C1 ✅ C2 ✅ C3 ✅ C4 ✅ C6 ✅ **C7 ✅ (Phase 5) C8 ✅ (Phase 5)**; Backtester ✅; C5 skeleton only; **267/267 tests** |
| M8 Experiment Progress | EXP-001/002/003 ✅ COMPLETE; G4 MET; ADR-0004 ✅ ACCEPTED; EXP-004 🔴 BLOCKED (DS-02) |
