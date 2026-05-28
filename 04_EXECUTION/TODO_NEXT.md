# TODO Next — Prediction Market Trading Bot

**Purpose:** The immediate action list for the current work session. Only contains tasks executable in the next 1–3 sessions. Longer-horizon tasks belong in PLAN.md.  
**Owner (role):** Execution Lead (EL)  
**Last reviewed:** 2026-05-28 (T-051 ✅ COMPLETE — kill switch drill PASSED 0.340ms; APR-0013 signed; G5 kill switch gate cleared; all Phase 5 non-blocked tasks complete)  
**Next review:** Start of every work session; end of every session (update status)  
**Staleness triggers:** Any completed task; any new blocker; session end  
**Upstream links:** PLAN.md, RID_LOG.md  
**Downstream links:** STATUS_REPORTS/  
**Decision references:** ADR-0001  
**Confidence:** 9/10 — Immediate tasks are clear; ordering may shift based on blockers

---

## Session: 2026-05-22 — G3 CLOSED; Phase 3 (Research Build) Initiated

**G0 Status:** ✅ COMPLETE — APR-0002 signed 2026-05-22. All 74 artifacts built.  
**G1 Status:** ✅ COMPLETE — APR-0003 signed 2026-05-22. All 5 G1 exit criteria met.  
**G2 Status:** ✅ COMPLETE — APR-0004 signed 2026-05-22. All 4 architecture artifacts CANONICAL; C4/C5 naming corrected.  
**G3 Status:** ✅ COMPLETE — APR-0005 signed 2026-05-22. RUN_INSTRUCTIONS + ENVIRONMENTS + RID_LOG CANONICAL; OQ-006 excepted.  
**OQ-001:** ✅ RESOLVED — DS-01 provenance documented (Earl Ignacio / 2026-05-21 / NBA / PRF framework; SNAP-001 registered)  
**OQ-003:** ✅ RESOLVED — NBA basketball, dynamically agnostic event types, Kalshi primary venue  
**T-010:** ✅ COMPLETE 2026-05-22 — REQUIREMENTS.md FROZEN at G1  
**T-011:** ✅ COMPLETE 2026-05-22 — ACCEPTANCE_CRITERIA.md FROZEN at G1  
**T-015:** ✅ Scaffolding verified (ENV-01 artifacts correct); run locally: `python3.11 -m venv .venv && source .venv/bin/activate && pip install -r 06_CODE_EXECUTION_REPRODUCIBILITY/DEPENDENCY_LOCKS/requirements-dev.txt && pre-commit install`  
**T-016:** ✅ requirements-dev.txt and requirements-base.txt confirmed; lock post-install with `pip freeze > 06_CODE_EXECUTION_REPRODUCIBILITY/DEPENDENCY_LOCKS/requirements-locked.txt`  
**T-017:** ✅ .pre-commit-config.yaml verified; `pre-commit install` after T-015  
**T-019:** ✅ COMPLETE 2026-05-22 — G1 exit checklist passed; APR-0003 signed; PLAN.md updated  
**T-020:** ✅ COMPLETE 2026-05-22 — LITERATURE_REVIEW.md Section 4 expanded (NBA-specific Sections 4.1–4.6); OQ-015 registered  
**T-021:** ✅ COMPLETE 2026-05-22 — ADR-0003_venue-selection.md created; PENDING formal acceptance (OQ-006 exception)  
**T-022:** ✅ COMPLETE 2026-05-22 — ARCHITECTURE_OVERVIEW.md promoted to CANONICAL; C4/C5 corrected; tech stack confirmed  
**T-023:** ✅ COMPLETE 2026-05-22 — INTERFACES_CONTRACTS.md promoted to CANONICAL; IF IDs corrected (IF-C3-C4, IF-C4-C5, IF-C5-VENUE)  
**T-024:** ✅ COMPLETE 2026-05-22 — RESILIENCE_FAILURE_MODES.md promoted to CANONICAL; FM-04/FM-05 corrected  
**T-025:** ✅ COMPLETE 2026-05-22 — THREAT_MODEL.md promoted to CANONICAL; TH-02/TH-04/TH-05/TH-07 corrected; RCO signed  
**T-026:** ✅ COMPLETE 2026-05-22 — RUN_INSTRUCTIONS.md + ENVIRONMENTS.md promoted to CANONICAL (G3); Python 3.11 confirmed; health checks documented  
**T-027:** ✅ COMPLETE 2026-05-22 — RID_LOG.md baselined CANONICAL (G3); RID-D002/D003 archived; RID-D001/RID-003 updated  
**T-028:** ✅ COMPLETE 2026-05-23 — ADR-0003 formally accepted; OQ-006 RESOLVED (Kalshi: CFTC-DCM, all 50 states, NBA markets confirmed primary; Polymarket US: Phase 6+ secondary, CFTC-regulated Dec 2025 relaunch); APR-0011 signed  
**T-029:** ✅ COMPLETE 2026-05-22 — APR-0004 signed; PLAN.md / MEMORY_BANK.md / CHANGELOG.md updated  
**T-030:** ✅ COMPLETE 2026-05-22 — APR-0005 signed; G3 CLOSED

### Priority Queue (Phase 3 — Research Build)

*Phase target: 2026-07-26*

| # | Task | Owner | Due | Status |
|---|------|-------|-----|--------|
| T-031 | ADR-0003 formal acceptance | AO | 2026-05-23 | ✅ COMPLETE 2026-05-23 — APR-0011 signed; OQ-006 resolved |
| T-032 | C1 (Ingestion) implementation | EL | 2026-07-05 | ✅ COMPLETE 2026-05-26 — NBAIngestionClient; nba_api; OQ-015 resolved (nba_api proxy) |
| T-033 | C2 (Feature Derivation) implementation | EL | 2026-07-08 | ✅ COMPLETE 2026-05-26 — FeatureStore; 29-col IF-C1-C2 → IF-C2-C3; TI-01–TI-04 enforced |
| T-034 | C3 (Forecasting) + C4 (Risk) implementation | EL | 2026-07-12 | ✅ COMPLETE 2026-05-26 — ModelForecaster (LR+Platt, ECE<0.05 target); RiskEngine (quarter-Kelly, phase gate, kill switch) |
| T-035 | EXP-001 — First experiment run and logged | RL | **2026-06-10** | ✅ COMPLETE 2026-05-28 — Pipeline ran; val Brier 0.2454 (+0.0046 vs null 0.2500); ECE 0.0596; AUC-ROC 0.5906; C4 phase gate REJECTED (expected); C6 bug fixed (numpy int key); outputs: exp_output/ |
| T-036 | Backtesting framework operational | RL | **2026-06-21** | ✅ COMPLETE 2026-05-28 — EXP-002: Brier −0.0082, ECE 0.0941, AUC 0.5488; EXP-003: Brier −0.0068, ECE 0.0793, AUC 0.4364; G4 NOT MET (1/3 experiments beat null; need 2/3); outputs: exp_output/BACKTEST/ |
| T-037 | C2 Feature Enhancement v1.1.0 | EL | 2026-05-27 | ✅ COMPLETE 2026-05-27 — FEATURE_VERSION 1.1.0; 7 new features (season_type_is_playoffs, days_since_last_game, b2b_flag, load_games_l7d, eri_prev_hot, eri_prev_cold, eri_consec_cold_games); 27 new tests; 89/89 total; ASM-008/009 + HYP-005 + OQ-016/017 filed |
| T-038 | C4 risk engine tests + METHODOLOGY.md + DATA_FLOWS_LINEAGE.md | EL | 2026-05-27 | ✅ COMPLETE 2026-05-27 — test_c4_risk.py (32 tests; phase gate, hard limits, Kelly, approval, C6 failure); METHODOLOGY.md 4/10→8/10 (model spec, feature table, strategy architecture A–H, validation checklist); DATA_FLOWS_LINEAGE.md F-001–F-038 populated; C4/C5 naming corrected; 121/121 tests |
| T-039 | C6 AuditLogger tests | EL | 2026-05-28 | ✅ COMPLETE 2026-05-28 — test_c6_audit_logger.py (38 tests; init, write, write failure, severity filtering, payload redaction, traceability chain, convenience wrappers, from_env, thread safety); 159/159 tests |
| T-039b | C3 ModelForecaster tests | EL | 2026-05-28 | ✅ COMPLETE 2026-05-28 — test_c3_forecaster.py (35 tests; _model_version_hash, _compute_ci Wilson CI, fit() insufficient/TI-02/happy path/C6 failure, predict() not-fitted/schema/edge/direction/CI/series/C6 failure); 194/194 tests |
| T-041 | MODEL_CARD.md Phase 3 population | EL | 2026-05-28 | ✅ COMPLETE 2026-05-28 — MODEL_CARD.md 2/10→7/10; training procedure (pipeline, NaN imputation, edge formula, Wilson CI), feature version 1.1.0, known limitations (8 entries), null model documented; performance metrics pending EXP-001/002/003 |
| T-042 | RUN_INSTRUCTIONS.md Phase 3 commands | EL | 2026-05-28 | ✅ COMPLETE 2026-05-28 — All TBD Phase 3 commands replaced; EXP-001 (run_exp001.py), EXP-002/003 (run_backtest.py), test suite command, audit log verification, reproducibility checklist updated; confidence 6/10→8/10 |

### Phase 4 — Next Tasks (G4 Evidence Gap Remediation)

**Trigger:** G4 evidence requirement NOT met (1/3 experiments beat null; need 2/3). Phase 4 focus: expand training data and validate HYP-005.

| # | Task | Owner | Due | Status |
|---|------|-------|-----|--------|
| T-043 | Expand player set 10→50 players (OQ-018) | EL | 2026-07-15 | ✅ COMPLETE 2026-05-28 — 50 players (SNAP-2026-05-28-001); EXP-001 Brier +0.0056/ECE 0.0345/AUC 0.5785; EXP-002 +0.0049/0.0289/0.5866; EXP-003 +0.0026/0.0369/0.5673; G4 evidence MET (3/3 beat null; ECE<0.05 all) |
| T-044 | HYP-005 feature ablation (OQ-019) | EL | 2026-07-22 | ✅ COMPLETE 2026-05-28 — v1.0.0 ablation: Brier +0.0054/ECE 0.0314 vs v1.1.0 +0.0056/0.0345; Δ Brier=+0.0002 (threshold 0.005); HYP-005 FALSIFIED; --ablation-v10 + --source-csv flags added to run_exp001.py |
| T-045 | MODEL_CARD.md 7/10→10/10 | EL | 2026-05-28 | 🔲 NEXT — Populate performance metrics table with 50-player results; update known limitations (HYP-005 falsified; training data requirement); note G4 readiness |
| T-046 | FEATURE_VERSION 1.2.0 — prune ERI/schedule features | EL | Phase 4 | ✅ COMPLETE 2026-05-28 — F-032–F-038 removed from features.py; FEATURE_VERSION "1.2.0"; 31 features; DATA_FLOWS_LINEAGE.md + MODEL_CARD.md updated; 179/179 tests |
| T-047 | ADR-0004 — model class confirmation | AO | Phase 4/G4 | ✅ COMPLETE 2026-05-28 — ADR-0004 ACCEPTED (APR-0012); TEST Brier +0.0084/ECE 0.0247/AUC 0.6062; G4 gate CLOSED |
| T-048 | G4 formal gate — TEST set evaluation + sign-offs | MV/AO/DS | 2026-05-28 | ✅ COMPLETE 2026-05-28 — TEST set evaluated (3,254 rows, 2023-24 season); PERFORMANCE_METRICS.md + G4_VALIDATION_REPORT.md + VALIDATION_SIGNOFF.md + APPROVALS_REGISTER.md all updated; APR-0006 + APR-0012 accepted |

### Phase 5 — Operational Readiness (G5 gate target)

**Phase 5 unblocked 2026-05-28 by G4 gate closure.**

| # | Task | Owner | Priority | Status |
|---|------|-------|----------|--------|
| T-049 | C7 Monitoring + Kill Switch implementation | EL | HIGH | ✅ COMPLETE 2026-05-28 — `c7_monitoring/monitor.py` (SystemMonitor, DriftSnapshot, KillSwitchResult); 55 tests; rolling Brier/ECE/edge; L1–L4 drift ladder; thread-safe kill switch; drill method |
| T-050 | C8 Visual Dashboard — Phase 5 panels | EL | HIGH | ✅ COMPLETE 2026-05-28 — `c8_dashboard/dashboard.py`; 3 panels (system health, drift metrics, alert feed); reads C6 JSONL; CLI entrypoint; 33 tests; 267/267 total |
| T-051 | Kill switch drill (TC-007, NFR-03) | EL/DS | HIGH | ✅ COMPLETE 2026-05-28 — halt 0.340ms (SLA 60,000ms); KS-C8D7D90AF942; VALIDATION_SIGNOFF.md TC-007 row signed; APR-0013 recorded; G5 kill switch blocker CLEARED |
| T-052 | EXP-004 — HYP-003: edge vs Kalshi vig | RL | HIGH | 🔴 BLOCKED — requires DS-02 (live venue prices); blocked until DS-02 active |
| T-053 | SENSITIVITY_STRESS_TESTS.md — run ST-001 through ST-004 | MV | MEDIUM | ✅ COMPLETE 2026-05-28 — ST-001–004 ALL PASS; results in exp_output/SENSITIVITY_TESTS/; script: run_sensitivity_tests.py |
| T-054 | MODEL_CARD.md 7/10 → 10/10 update | EL | LOW | ✅ COMPLETE 2026-05-28 |
| T-055 | CAPACITY_PLANNING.md — create | EL | LOW | ✅ COMPLETE 2026-05-28 |
| T-056 | Context Pack CP-2026-05-28_G5-readiness | DS | LOW | 🔲 PENDING |

### Operator Actions Remaining

| # | Action | Why It Matters |
|---|--------|---------------|
| T-015 | Run `python3.11 -m venv .venv && source .venv/bin/activate && pip install -r 06_CODE_EXECUTION_REPRODUCIBILITY/DEPENDENCY_LOCKS/requirements-dev.txt && pre-commit install` from project root | Sets up local development environment (Python 3.11+ required; all artifacts verified correct) |

---

## Standing Items (Every Session)

- [ ] Review MEMORY_BANK.md for any broken links
- [ ] Check if any artifact has a staleness trigger that fired
- [ ] Update TODO_NEXT.md before ending session
- [ ] Log any new open questions to OPEN_QUESTIONS.md
- [ ] Log any new RIDs to RID_LOG.md

---

## Blocked Items

| # | Task | Blocked By | ETA to Unblock |
|---|------|-----------|----------------|
| T-052 / ST-005 | EXP-004 / HYP-003 (vig survival test) | DS-02-B-001: Kalshi API TLS/WAF block on this machine — see RID_LOG.md | Install Homebrew interactively + verify API key activation in Kalshi dashboard |
| — | Venue API integration | ENV-03 only; C5 not yet implemented | Phase 6 |
| — | BOT_C4_ACTIVE=true | Phase gate — not set until G5 | G5 |
| — | arb/ incorporation | APR-0010 pending | Indefinite |

**DS-02-B-001 Detail:** `api.elections.kalshi.com` (Kalshi's current endpoint, CloudFront) drops the TLS handshake from this machine for ALL clients (Python/OpenSSL 3.0, LibreSSL, Apple nscurl, curl_cffi). TCP connects; TLS ClientHello is sent; server closes connection before handshake completes. Root cause: likely CloudFront WAF blocking based on TLS fingerprint or IP. Resolution path:
1. Run `! /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"` (needs interactive sudo)
2. `brew install python@3.11` (will have proper OpenSSL, potentially different fingerprint)
3. Log into Kalshi dashboard and verify API key is active for `api.elections.kalshi.com`
4. Re-test connectivity; if still blocked, contact Kalshi support re: IP allowlisting
