# Memory Bank — Prediction Market Trading Bot

**Purpose:** The canonical navigation index for this project. The definitive source of truth for what exists, where it lives, and what its current status is. Designed to be the first file read in any new context window to restore full situational awareness.  
**Owner (role):** Director/Sponsor (DS) — the operator is responsible for keeping this current  
**Last reviewed:** 2026-05-29 sprint 4 (handoff audit complete; LL-008/009; FAQ Phase 6; KI-010–013; CP-2026-05-29; T-091/092; APR-0016; all workflow structural gaps closed)  
**Next review:** Every session; weekly cadence; after every gate clearance  
**Staleness triggers:** Any artifact added, changed, or superseded; any gate cleared; any new context window opened  
**Upstream links:** All artifacts (this file indexes everything)  
**Downstream links:** TODO_NEXT.md (current work); STATUS_REPORTS/ (phase snapshots)  
**Decision references:** ADR-0001 (Compass OS adoption)  
**Confidence:** 10/10 — Reflects complete Phase 7 infrastructure state as of 2026-05-29

---

## Project Identity

| Field | Value |
|-------|-------|
| Project | Prediction Market Trading Bot |
| Current phase | **Phase 6/7 ACTIVE** (G5 ✅ CLOSED 2026-05-28; Phase 7 infrastructure built 2026-05-29; paper trading live; experiments EXP-012/013 pending operator run) |
| Operator | Earl Ignacio |
| Started | 2026-05-21 |
| Framework | Compass OS (ADR-0001) |
| Strategy class | Forecast-only (ADR-0002); arb/ reference-only pending APR-0010 |
| Capital status | NO LIVE CAPITAL — research and paper trading only until G6 |
| Last major milestone | **Phase 7 infrastructure complete 2026-05-29** — cross-venue market mapper + complement lock scanner (T-080/083); multi-band orchestrator P6 rules (T-084); FEATURE_VERSION 1.3.0 with opp_def_rating + is_home_game (T-075); ScoringDistributionModel NB/Poisson (T-076); TeamStatsStore for opponent features; EXP-012 + EXP-013 runners ready; 464/464 tests |

---

## ANTI-CONTEXT-EROSION INVARIANTS

These 9 rules are absolute. They must be restored to any context that loses them.

1. **arb/ folder = REFERENCE ONLY.** Do not incorporate into any active work, experiment, or component until ADR is accepted (APR-0010 is the future gate). See REJECTED_OPTIONS.md RO-001.

2. **Player_Attribute_Matrix_v4.docx = Research input only.** NOT a canonical spec. Requires independent validation and provenance documentation (OQ-001) before use in any experiment.

3. **ADRs are immutable once accepted.** Changes require a superseding ADR. No silent changes to strategy, risk limits, or model.

4. **No real capital until G6 Release Gate is formally cleared** (APPROVALS_REGISTER.md, DS sign-off, ADR-0005 accepted).

5. **No automated retraining in production.** Frozen model policy. Retraining requires new ADR + new model version + G4-equivalent evidence.

6. **Zero hardcoded secrets** (NFR-05). No API key, password, or token in code, VCS, or logs. Vault/env-var protocol only.

7. **Kill switch must halt all components within ≤60 seconds** (NFR-03). Tested before G5. No bypass path.

8. **G6 evidence gate = 30 resolved paper bets with positive P&L** (APR-0016, signed 2026-05-29). NOT 50. Seasonally bounded by NBA Finals end (~2026-06-22). Window extends to first 30 days of 2026-27 regular season if not reached. Do not revert to 50 without a new APR.

9. **Strategic decisions made in holistic reviews must be captured in DECISION_LOG.md AND APPROVALS_REGISTER.md before session end.** Judgment calls (threshold changes, sequencing pivots, dark-period plans) are as load-bearing as code changes. Handoff documents must include a "Strategic Decisions" section separate from "Tasks Completed." If a decision was made verbally in a session and is not in these files, it did not happen.

---

## Mid-Session Decision Protocol (Read Before Every Session)

**If a strategic decision is made at any point during a session, write it to `03_DECISIONS/DECISION_LOG/DECISION_LOG.md` immediately — not at session end.**

Context windows compress. /session-end may not run. If it was decided, it goes in the file now.

**A decision is anything that changes:**
- A threshold, limit, or gate criterion
- A sequencing choice or prioritization order
- A hold/unblock/defer ruling on a task or gate item
- A risk assessment conclusion from a holistic review
- A build strategy (pilot-first vs. infrastructure-first, dark period plan, etc.)

**⚠️ Conditional language in canonical registers is a governance failure, not documentation.**
"May be revised," "could be adjusted," "threshold may change" = decision NOT made. If you see this language in APPROVALS_REGISTER, ROADMAP, or KNOWN_ISSUES, treat it as an open gap requiring DS escalation, not as a recorded decision. Replace it with either a signed decision or "TBD — requires APR-XXXX before [date]."

**When context window reaches ~80%:** Stop all implementation work. Run /session-end immediately. Produce SESSION_HANDOFF, commit, and push before context compresses further. This is non-negotiable — the cost of losing a session's decisions exceeds the cost of any implementation delay.

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
| STRATEGY_OVERVIEW.md | **CANONICAL (2026-05-29)** | 9/10 | All 11 strategies (A–K) + T1–T5 execution bands PDTP; mechanics, edge sources, risk profiles, Kalshi constraints, activation gates |
| EXECUTION_BANDS.md | **CANONICAL (2026-05-29)** | 9/10 | T1–T5 time-horizon bands; Kelly/SLA/compute per band; PDTP; activation gates; cron schedules |
| VENUE_REGISTRY.md | **CANONICAL (2026-05-29)** | 8/10 | V-001–V-005 CA-eligible venues; edge formulas by venue type; activation roadmap |

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
| RID_LOG.md | **CANONICAL (G5); updated 2026-05-28** | 9/10 | DS-02-B-001 RESOLVED (EXP-004 Part B on hotspot); RID-006 RESOLVED (APR-0013); RID-D001/D002/D003 archived |
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

## Current State Snapshot (2026-05-29)

**Phase:** 6/7 ACTIVE — G0–G5 ✅ ALL CLOSED; Phase 6 paper trading live; Phase 7 infrastructure built  
**G0–G5 gates:** ✅ ALL COMPLETE  
**All modules:** COMPLETE (11/11; 74 artifacts + all Phase 1–7 additions)  
**FEATURE_VERSION:** 1.2.0 (78 features: 31 quant + 47 qual) — 1.3.0 infrastructure built (F-039/040) but FALSIFIED by EXP-012; version stays 1.2.0  
**Tests:** 533/533 passing  
**Components implemented:** C1–C8 ✅ | PaperTrader ✅ | VenueAdapter ✅ | VenueRouter ✅ | ExecutionBands ✅ | market_mapper ✅ | complement_lock_scanner ✅ | execution_bands_orchestrator ✅ | TeamStatsStore ✅ | ScoringDistributionModel ✅ | PIPE-02/03(VenueRouter)/05/06 ✅  
**Experiments run:** EXP-001–016 ✅ ALL COMPLETE | EXP-012 HYP-006 FALSIFIED | EXP-013 HYP-007 FALSIFIED | EXP-014 line shopping +7.8% | EXP-015 HYP-008 FALSIFIED | EXP-016 HYP-009 CONFIRMED (Δ Brier=-0.0010)  
**Snapshots registered:** SNAP-001 (DS-01) | SNAP-002 (EXP-001 raw) | SNAP-003 (backtest pre-reg) | SNAP-2026-05-28-001/002 (50-player/refreshed)  
**ADRs accepted:** 4 (ADR-0001/002/003/004) | ADR-0005 pending at G6  
**Open questions:** OQ-021 (L3 amplification) | OQ-022 (nba_api backup source) — both non-blocking  
**Active risks:** All non-blocking  
**Live capital:** NOT DEPLOYED — G6 gate requires 30+ resolved paper bets with positive P&L (APR-0016: revised from 50; seasonal constraint; signed 2026-05-29)  
**Domain:** NBA basketball; Kalshi primary venue (ADR-0003)  

---

## What Must Happen Next

**Phase 1 — COMPLETE ✅** All tasks done 2026-05-22.
**G2 Gate — COMPLETE ✅** APR-0004 signed 2026-05-22.
**G3 Gate — COMPLETE ✅** APR-0005 signed 2026-05-22. T-026, T-027, T-030 all done.
**ADR-0003 — ACCEPTED ✅** APR-0011 signed 2026-05-23. OQ-006/OQ-015 resolved.
**C1–C4 — IMPLEMENTED ✅** T-031–T-034 complete 2026-05-26.

**Phase 3, 4 — COMPLETE ✅** All tasks done (T-035–T-048). G4 CLOSED 2026-05-28. ADR-0004 ACCEPTED.

**Phase 5 (Operational Readiness) — ✅ COMPLETE (G5 CLOSED 2026-05-28):**

1. **T-049 ✅** — C7 `c7_monitoring/monitor.py`; `SystemMonitor`; L1–L4 drift ladder; kill switch; 55 tests
2. **T-050 ✅** — C8 `c8_dashboard/dashboard.py`; 3 panels; reads C6 JSONL; CLI; 33 tests
3. **T-051 ✅** — Kill switch drill PASSED; halt 0.340ms; KS-C8D7D90AF942; APR-0013
4. **T-052 ✅ COMPLETE 2026-05-28** — EXP-004 Parts A+B: EV +$0.0855/bet, 59% win rate, 2,481 TEST bets; Part B live (37 KXNBAPTS markets, session EXP-004-FE3E2169); HYP-003 🟢 CONFIRMED; DS-02-B-001 RESOLVED
5. **T-053 ✅** — ST-001–004 ALL PASS; sensitivity tests complete
6. **T-054 ✅** — MODEL_CARD.md 10/10
7. **T-055 ✅** — CAPACITY_PLANNING.md stub created
8. **ACC-0002 ✅** — Kalshi read-only API key provisioned
9. **T-057 ✅ 2026-05-28** — T-3 hygiene check: H-001 (`penalty="l2"` in C3), H-002 (same in sensitivity tests), H-003 (`df.apply()` replaced with `_build_target()` in run_exp004); 267/267 tests green

**APR-0007 ACCEPTED 2026-05-28. G5 CLOSED. Phase 6 ACTIVE.**

**T-058 ✅ COMPLETE 2026-05-28** — EXP-005 data refresh: 5 seasons (2021-26); TEST Brier +0.0024 / ECE 0.0456; model v1-9939a6a5 (SNAP-2026-05-28-002).

**Qualitative pipeline (2026-05-28/29):**
- QUALITATIVE_SIGNALS.md + QUALITATIVE_REGISTRY.md — three-layer architecture documented (L1 quant / L2 qual / L3 amplification)
- QS-2026-05-28-001 (effective_from 2025-10-22) → EXP-006: Δ Brier = 0.0000 (expected — all TRAIN before effective_from)
- QS-2026-05-28-002 (backdated QTI-03; 42 players → 2021-10-19) → EXP-007: **+0.0017 Brier / +0.0159 ECE — POSITIVE SIGNAL**
- EXP-008 (PRF one-hot prf_w01…prf_w15): Δ vs EXP-007 = negligible (LR insensitive to ordinality at this scale)
- EXP-009 (Layer 3 amplification, 35 features): Δ = -0.0004 — L3 needs non-linear model class
- EXP-010 (EV re-estimation, hotel wifi): **EV +$0.0958/bet** (vs EXP-004's +$0.0855); live vig 0.030; 871 bets; 61.1% win rate
- EXP-011 (HistGradientBoosting vs LR): **LR RETAINED** — HGBC Δ = -0.0008 (below ADR trigger 0.003); ADR-0004 unchanged

**Production model (current best):** LR L1+L2, 78 features, QS-2026-05-28-002, Brier 0.2461, ECE 0.0342, v1-28483b21

**T-059 ✅ COMPLETE 2026-05-29** — VPS live: DigitalOcean NYC3, Ubuntu 24.04, 157.230.91.33; Python 3.12 + sklearn 1.8.0 venv; model retrained on VPS (v1-28483b21); deploy/ infrastructure; 8-point health check all green; Kalshi API reachable from datacenter IP.

**T-060 ✅ COMPLETE 2026-05-29** — PIPE-03 paper trading pipeline: PaperTrader ($1,000 bankroll, position tracking, nba_api outcome resolution); run_paper_trade.py (C4 active, BOT_ENV=paper guard); cron 01:30 UTC daily; tested live on Droplet.

**Active cron on 157.230.91.33:** 21:00 UTC health | 21:30 UTC PIPE-02 (inference) | 22:00 UTC PIPE-03 early | 01:30 UTC PIPE-03 late | 06:00 UTC PIPE-03R (resolve-only)

**T-080 ✅ COMPLETE 2026-05-29** — Complement lock scanner: `c5_execution/complement_lock_scanner.py`; `LockOpportunity` + `ComplementLockScanner`; `scan_snapshot()` (all markets) + `scan_single()` (targeted); 22 tests; detection-only — APR-0010 required before any execution; sorted by net_profit descending.

**T-083 ✅ COMPLETE 2026-05-29** — Cross-venue market mapper: `c5_execution/market_mapper.py`; `normalize_player_name()` (NFKD, accent strip, apostrophe/period removal); `PlayerMarketKey` NamedTuple; `group_by_key()`; 26 tests; `VenueRouter._deduplicate_best_price()` upgraded to use normalized keys; accent names (Dončić) and apostrophes (De'Aaron) now deduplicate correctly across venues.

**T-084 ✅ COMPLETE 2026-05-29** — Multi-band execution orchestrator: `execution_bands_orchestrator.py`; `BandSignal` + `BandDecision` + `MultiBandOrchestrator`; implements P6 rules (T3>T2>T1 priority; CONFIRM→PROCEED; FADE→HOLD; NEUTRAL→base band); `batch_decide()` for full game-day processing; 46 tests; T3 cron schedule extended to `*/15 20-23,0-3 * * *` for late 10pm ET games.

**T-075 ✅ COMPLETE 2026-05-29 (infrastructure)** — Strategy B / FEATURE_VERSION 1.3.0: C1 schema extended with `matchup`, `is_home_game`, `opponent_team_abbr` (parsed from MATCHUP); `c1_signal_ingestion/team_stats_store.py` (`TeamStatsStore` — holds per-team rolling `pts_allowed` for opponent features); C2 v1.3.0 adds F-039 `is_home_game` + F-040 `opp_def_rating_l10_mean`; `run_exp012.py` ready; **HYP-006 pending operator run** (~20 min: 50 players + 30 teams × 5 seasons via nba_api; `EXP012_SKIP_PULL=1` to reuse cache on re-runs).

**T-076 ✅ COMPLETE 2026-05-29 (infrastructure)** — Strategy I / ScoringDistributionModel: `c3_forecasting/scoring_distribution.py`; `PlayerDistribution` + `ScoringDistributionModel`; method-of-moments NB fit per player; `predict_threshold_prob()` + `price_all_lines()` for any Kalshi threshold from one fit; 31 tests; `run_exp013.py` ready; **HYP-007 pending operator run** (offline — uses EXP-005 matrix).

See TODO_NEXT.md for session-level task tracking.

---

## Compass OS Health (as of 2026-05-29)

| Metric | Status |
|--------|--------|
| M1 Artifact Freshness | MEMORY_BANK ✅ | TODO_NEXT ✅ | all Phase 7 new modules documented | project_prediction_market_compass.md ✅ |
| M2 Open Question Count | OQ-021 open (L3 amplification needs non-linear model or more data) | OQ-022 open (nba_api backup source — register before G6) | both non-blocking |
| M3 ADR Coverage | 4 accepted (ADR-0001/002/003/004) | ADR-0005 pending at G6 | APR-0010 pending (complement lock execution gate) | ADRs needed for DFS pick'em venues (Phase 8+) |
| M4 Assumption Validation | All 9 hypotheses resolved (HYP-001–009) | HYP-009 ✅ CONFIRMED 2026-05-29 (EXP-016) | T3 momentum signal untested (paper data accumulating) | ASM-011 VALIDATED |
| M5 Risk Register Currency | KI-010 (inter-series gap) | KI-011 (player injury) | KI-012 (negative P&L — no monitoring threshold) | KI-013 (model staleness at 2026-27 open) | KI-008/009 RESOLVED | T-091 (P&L alert) + T-092 (T-072 elevation) registered |
| M6 Gate Progress | **G0–G5 ✅ ALL CLOSED** | Phase 6/7 ACTIVE | T-070 accumulating paper bets (G6 gate: **30 bets**, APR-0016) | T-077 operator-gated (Polymarket API key) | T-081 DS sign-off pending (APR-0010) | **NBA dark period ~2026-06-22 to 2026-10**: use for pre-season build — Polymarket activation, DS-04 qual source, live capital ADR-0005 draft |
| M7 Component Implementation | C1–C8 ✅ | PaperTrader ✅ | VenueAdapter/Router ✅ | PolymarketVenueAdapter ✅ | ExecutionBands ✅ | market_mapper ✅ | complement_lock_scanner ✅ | execution_bands_orchestrator ✅ | TeamStatsStore ✅ | ScoringDistributionModel ✅ | cohort.py ✅ | PIPE-02/03(VenueRouter)/05/06 ✅ | **533/533 tests** |
| M8 Experiment Progress | EXP-001–016 ✅ ALL COMPLETE | EXP-012 ✅ HYP-006 FALSIFIED | EXP-014 ✅ line shopping (+7.8% max EV) | EXP-015 ✅ HYP-008 FALSIFIED (T3 FADE gate only) | **EXP-016 ✅ HYP-009 CONFIRMED** (Δ Brier = -0.0010; gate < 0.012 ✅; KI-008 RESOLVED; playoff paper bets valid G6 evidence at full confidence) | best model LR L1+L2 Brier 0.2461 EV +$0.0958/bet |
