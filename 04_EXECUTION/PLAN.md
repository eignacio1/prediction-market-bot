# Execution Plan — Prediction Market Trading Bot

**Purpose:** The authoritative, actionable delivery plan. Maps work to phases, owners, and milestones. Updated at each gate and weekly during active phases.  
**Owner (role):** Execution Lead (EL)  
**Last reviewed:** 2026-06-26 SESSION 94 CLOSE — **FULL MLB ARM LIVE. T-200 through T-204 ALL COMPLETE. MLB T4 iteration plan CLOSED. ADR-0033 ACCEPTED (provisional edge threshold). All 7 MLB crons active on VPS. First MLB T4 live evaluations tonight (22:00 UTC). First MLB T1 bets June 27 (11:00 UTC). GG-045 + GG-046 registered. 2083/2083 tests.** *(Previous S92:)* **T-200 + T-201 COMPLETE. MLB T4 ab_remaining inning-aware fix + dual-pool resolution. 2070/2070 tests. MLB T4 iteration plan active (T-202 dry-run mode next).** *(Previous S90:)* 2026-06-27 SESSION 90 CLOSE — **MLB-G1 gate CLOSED. T-194 through T-199 COMPLETE. ADR-0032 ACCEPTED. 6 MLB crons enabled. 2044/2044 tests. MLB paper trading arm live.** *(Previous S87:)* **T-191 COMPLETE: MLB arm institutional completion. T2 built (PIPE-05.5), DS-04 MLB designated, T4 bugs fixed (NFR-03, stat group filter, dead constant), T1 timing fixed (03:00 UTC same-day), T3 cron gate breach resolved. 1947/1947 tests. VPS HEAD `2f13a35`. All 7 MLB cron entries active. Next: monitor accumulation, EXP-017 MLB when ≥150 closed positions (Tier 1) or ≥500 (Tier 2).** *(Previous S86:)* **T-190 COMPLETE: full MLB arm built (pregame + T3 + T4). 1918/1918 tests. Next: VPS deploy + MLB cron activation.** *(Previous S85:)* **MLB arm audit: CLAUDE.md T4 corrected, MLB cron PAUSED, T-190 registered (3-step: pregame + T3 + T4 MLB). MLB accumulation suspended until all 3 components built and tested. 1819/1819 tests unchanged.** *(Previous S84:)* **T-189 COMPLETE: PIPE-05 three-concern remediation (GAME_DATE=tomorrow, ensure_persisted(), hydrate fix, cache bust scope). 1819/1819 tests. MLB portfolio $1,000 fresh start. PIPE-05 ready for June 25 slate.** *(Previous S83:)* **T-188 COMPLETE: MLB curses TUI dashboard. MLB accumulation LIVE as of 2026-06-24 (PIPE-05 first run tonight 23:30 UTC). 1790/1790 tests. VPS HEAD 42bce66.** T-187E (PIPE-05R resolve), T-187F (PIPE-05C calibration monitor, Mondays 14:10 UTC), T-187G (live SP overlay), T-187H (t=3 shadow gate re-evaluation — VALID NEGATIVE, GG-042 DEFERRED structural). 1790/1790 tests. VPS HEAD 6447fea. *(Previous S81:)* T-187B COMPLETE: per-threshold MLB LR+Platt models. Shadow gate PASS on VPS. PIPE-05 + per-threshold model live. 1704/1704 tests. T-187E/F/G remain.** *(Previous S80:)* **T-117 COMPLETE + GG-006 CLOSED + T-186 COMPLETE (valid negative). Kalshi Participant Agreement read — no automation restrictions; ADR-0005 pre-requisite satisfied. MLB paper book: fresh $1,000. T-186: PLUS_MINUS absent from nba_api.TeamGameLog (F-040/F-042 dead since EXP-005); cross-reference fix applied; v2b Brier +0.000130 < 0.001 → shadow gate FAIL → deploy v2-065b9510 October 2026. 1650/1650 tests. Commit 89d795c, VPS HEAD confirmed. T-187 REGISTERED: `scripts/run_mlb_paper_trade.py` (P0, before August 2026).** *(Previous S75:)* **T-181 COMPLETE: MLB C1 data ingestion module (3 new source files, 80 tests, 1373/1373 green). MLB Stats API data source decision logged. IF-C1-C2 MLB contract established. Next: T-182 (MLB C2 feature set, P0).** *(Previous S74:)* Governance-only. MLB $1K fresh paper book decision. Phase 3 task registration: T-181/T-182/T-183/T-184/T-186. T-185 v2 deploy runbook. ADR-0031 Known Limitations added. DARK_PERIOD_PLAN updated. 1293 tests unchanged. *(Previous S72:)* **Governance-only. ADR-0028 ACCEPTED (DS sign-off Earl Ignacio); T-148 DONE; GG-022 RESOLVED; GG-041 registered (T-127 KI-023 Finals window miss; deferred Phase 4 Oct 2026). 1280 tests unchanged.** *(Previous S68:)* **T-180 PHASE 2 COMPLETE: the T4 routing engine built (substance of ADR-0029 Tier A; resolves S67 Q6 flag). `t4_price_cache.py` (GG-039 architecture; `T4PriceCache`/`STALENESS_WINDOW_S`/`T4Phase8BlockedError`; polling deferred to Phase 8) + `t4_execution_engine.py` (`GamePhase`, `Layer1EvaluationEngine` event-dispatch, `Layer2ExecutionQueue` heapq EXIT-priority + 3 drop conditions, 8 BLOCKED evaluator stubs, `T4CorrAdjuster._assert_downward_only` Principle-6, `_PHASE8_ACTIVE=False`) + `tests/test_t4_engine.py` (+109). VERIFIED 1108/1108 green; all execution paths provably blocked. T4 STILL DARK (gated GG-038/039/040); evaluator math still empty stubs — remaining T-180 / Phase 8. Engine commit + no-op VPS deploy this session.** *(Previous, SESSION 67:)* **ADR-0029 ACCEPTED (Tier A frozen, DS sign-off Earl Ignacio; Tier B provisional). T-180 SCAFFOLD landed: `execution_bands.py` split — `T4_IN_PLAY` kept as aggregate parent, 10 sub-bands added beneath via `T4_SUBBANDS`/`is_t4_subband()`/`t4_parent()`; `T4SubBandSpec`+`T4_SUBBAND_REGISTRY` (all BLOCKED) encode Tier B in code + `validate_t4_subbands()` invariant; PROJ/ARITH Kelly ≤0.167; Strategy K not redefined (ADR-0030 overlap OPEN). 999/999 tests.** *(Previous, SESSION 66:)* **T-179 ADR-0029 drafted (PENDING DS SIGN-OFF): T4 11-sub-band architecture; GG-038/039/040 registered; code changes blocked pending sign-off; 988/988 tests; no VPS deploy.** *(Previous, SESSION 65:)* **T-148 ADR-0028 rework complete (PENDING DS SIGN-OFF): G6 is T1-only; T4 Activation Gate created as Phase 8 placeholder; T-179 registered.** *(Previous, SESSION 64:)* Pre-MLB governance sprint complete: GG-036 + GG-035 + GG-037(calibration half) RESOLVED; full-DB assessment done. VPS HEAD `897ff4d`; 988/988 tests. GG-036: re-froze 158-bet NBA Finals dataset, G5 resolved (NOT fabricated). GG-035 (ADR-0026/APR-0020): C4 two-tier portfolio free-cash invariant shipped. GG-037 (ADR-0027/APR-0021): C3 temperature calibration on production Poisson prob (NOT Platt); NBA T=2.05 OOS, MLB fail-safe identity. **Recalibration DISPROVED miscalibration — edge anti-predictive post-calibration; GG-037 alpha half + GG-004 stay OPEN; no demonstrated alpha vs Kalshi.** New tasks: T-175 (ADR-0026 caller coverage), T-176 (MLB T derivation, dark period), T-177 (edge-inversion/no-alpha, G6 blocker), T-178 (market_mapper MLB pre-flight). Paper book remains halted at drawdown kill switch (25.12%). MLB C1 data-source selection still pending operator/DS. *(Previous, SESSION 63:)* T-174 + T-171 DEPLOYED + live book corrected; GG-034 + GG-033 RESOLVED (VPS HEAD `52607f2`); G6 baseline RATIFIED negative — Tier 0/EXP-017 (GG-004) still the binding G6 blocker.  
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
| Accumulate paper evidence ≥66 bets / ≥5 nights (T-110, APR-0017) | DS | HIGH | 🟡 IN PROGRESS — T1: 114+29(G5 open)/66 bets ✓; G5 closes 5/5 game nights ✓; GG-004 OPEN (EXP-017B DIRECTIONAL_NEGATIVE, -$0.0361/bet vs Kalshi prices); GG-014 BREACHED (9/29=31% G5 order failures, T-164 registered); VPS bankroll $285.27; ADR-0023 deployed |
| PIPE-07 T4 in-play paper trading (PIPE-07) | EL | HIGH | ✅ 2026-06-08 SESSION 37 — portfolio isolation fix, cron.conf 23:00 UTC, PIPE-07R-LOCAL script |
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
