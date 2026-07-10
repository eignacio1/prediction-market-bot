# Execution Plan — Prediction Market Trading Bot

**Purpose:** The authoritative, actionable delivery plan. Maps work to phases, owners, and milestones. Updated at each gate and weekly during active phases.  
**Owner (role):** Execution Lead (EL)  
**Last reviewed:** 2026-07-10 (Workstream B — T-322/T-323/T-324 close-out, session-end) — Resolved the edge-sign question to a new, more specific finding: extended `scripts/run_band_monitor.py` (T-322) to run the GG-100 edge-monotonicity Fisher test + calibration reliability curve per band on `clean_n` only; found **T4M-PROJ ANTI-PREDICTIVE on clean data (Fisher p=0.024, registered GG-105, OPEN HIGH)** while **T1 reads INCONCLUSIVE** (underpowered, `clean_n=65`, not confirmed-negative). T-323 built `scripts/run_power_calc.py` computing `n*` (clean bets needed for 95%-power edge>0-vs-edge=0 discrimination) per band, feeding GG-004 directly — T4M-PROJ's higher cadence puts it materially closer to an adequately-powered verdict than T1. T-324 (analysis-only memo) traced the T1/T4M-PROJ sign divergence to cadence/window-length/power differences, not a modeling contradiction. Also registered GG-106 (`TestT1RegressionAnchor` drift, not yet investigated). **No deliverables-table impact — a methodology/monitoring finding, not a Phase 6 milestone line item, same treatment as prior sessions' infra/analysis entries.** Full detail: MEMORY_BANK.md Current State Snapshot 2026-07-10 (Workstream B), DECISION_LOG.md 2026-07-10 (Workstream B row), GOVERNANCE_GAP_LOG.md GG-105/GG-106, TODO_NEXT.md T-322/T-323/T-324.

**Last reviewed (prior):** 2026-07-10 (T-320/T-321 close-out, session-end) — T-320 (logic-epoch write-path register) + T-321 (backfill + `clean_n`/`raw_n` reporting) both DONE end-to-end: merged, deployed, backfilled both live MLB portfolios (`MLB T1: raw_n=214 clean_n=65, MLB T2: raw_n=2 clean_n=0, MLB T4M-PROJ: raw_n=159 clean_n=159`), governance hook + C8 dashboard confirmed live. Discovered and mitigated **GG-104** (`deploy.yml` never restarts persistent systemd services `t4-mlb`/`pmbot-web-dashboard`, leaving T4M-PROJ silently running stale write-path code ~2 days post-merge); permanent fix registered as T-328 (not yet built; renumbered same-session from an initially-assigned T-322 after a concurrent-session claim collision was caught pre-push — see DECISION_LOG.md). **No deliverables-table impact — a governance/data-provenance infra build, not a Phase 6 milestone line item, same treatment as prior sessions' infra/bug-fix entries.** Full detail: MEMORY_BANK.md Current State Snapshot 2026-07-10, DECISION_LOG.md 2026-07-10 (three rows), GOVERNANCE_GAP_LOG.md GG-104, TODO_NEXT.md T-320/T-321/T-328. *(Previous, GG-102/T-261 closeout, session-end):* RESOLVED: `deploy.yml`'s dirty-tree guard regression (GG-073 whack-a-mole recurrence, `git status --porcelain` was blocking on ANY untracked file, not just modified tracked ones) fixed to `--untracked-files=no`, plus 3 VPS-live-regenerated tracked result files (`EXP-ARITH-MLB-01_results.json`, `EXP-FLOW-MLB-01_results.json`, `band_monitor_results.json`) untracked per operator direction (same shape as T-171). Self-caught and corrected a `git commit <pathspec>` no-op mid-fix (`b918f4b`→`9b06a31`). VPS content preserved/restored byte-identical. Confirmed fully green via manual `gh workflow run deploy.yml` (run `28984294745`, `success`) — first clean pass since the GG-073 regression. Committed `41e46b2`/`b918f4b`/`9b06a31`/`a53d65e`/`ffb56b3`, pushed. **No deliverables-table impact — a CI/git-hygiene fix, not a Phase 6 milestone line item, consistent with prior sessions' bug-fix entries.** No code, test, gate, phase, or bankroll changes. Full detail: GOVERNANCE_GAP_LOG.md GG-102 (RESOLVED), DECISION_LOG.md 2026-07-09, TODO_NEXT.md T-261 row. *(Previous, Terminal 2, session-end:)* T-255/T-257/T-258 DONE, GG-099's per-band monitor chain code-complete: `scripts/run_band_monitor.py` runs the GG-037/GG-077-safe Fisher edge-monotonicity + calibration-slope/CI/ECE checks per band (T1/T2/T3 from the band-tagged book, T4M-PROJ from the T-254 ledger), gated by `MIN_N=30` (GG-098). Live: T1 n=167 INCONCLUSIVE p=0.2462, T4M-PROJ n=273 INCONCLUSIVE p=0.2582 (first-ever T4M-PROJ coverage), no alarm. `tests/test_band_monitor.py` 19/19 passing, incl. the T-258 guardrail proving a synthetic NO-majority fixture cannot fool the monitor into repeating the GG-100 inversion. T-257: weekly cron entry added to `deploy/cron.conf` (warn-only, no auto-kill) — **not yet installed on the live VPS crontab**, flagged for next session. Committed `5da8a24`, pushed; no deliverables-table impact (a monitoring build, not a milestone line item). *(Previous, cowork Terminal 1 session, session-end:)* GG-100 (false ANTI-PREDICTIVE Fisher finding, n=169, p=0.0236) RESOLVED as a GG-077 sign-bug artifact, not a genuine no-alpha signal: `run_t177_edge_monitor.py` was loading each closed position's stored, YES-framed `fee_net_edge` field without correcting sign for NO-direction bets. Hardened the loader to recompute edge direction-aware via a new `_recompute_edge()` helper delegating to the audited `run_exp017_mlb.compute_fee_net_edge()`, added an `edge_source` field (`recomputed` vs `stored_fallback`) with a stderr warning on any fallback, added 3 regression tests (32/32 passing on `test_t177_edge_monitor.py`, including a permanent guard reproducing the old false-positive on the raw-stored-edge path), and re-ran live: verdict flips ANTI-PREDICTIVE (p=0.0236) → INCONCLUSIVE (p=0.2468). Explicitly did **not** touch the underlying negative P&L (real, variance-driven, unchanged) — only the mislabeled monotonicity verdict was the bug. GG-004 refreshed in the same pass: n=169, aggregate P&L −$44.76 (sign-flipped from +$15.23 at n=151), win rate 47.9%, framed as an open variance/sample question (GG-004 remains OPEN), not a re-litigated no-alpha verdict. Committed `016357e`, pushed, VPS deployed (manually-invoked script, no service restart required). No production `src/` files touched — this was a monitoring-script + governance-doc fix, so the full pytest suite count is unchanged from SESSION 127's 2,376 passed / 7 skipped / 1 pre-existing unrelated failure. T-255 (per-band anti-predictive + calibration monitor) remains the next item in the GG-099/GG-100 chain, unaffected by this fix since it already specs the direction-aware `compute_fee_net_edge()` helper. See MEMORY_BANK.md and TODO_NEXT.md SESSION 2026-07-08 (cowork Terminal 1) entries, DECISION_LOG.md 2026-07-08, and GOVERNANCE_GAP_LOG.md GG-100/GG-004 for full detail. *(Previous, SESSION 127 (session-end):)* T-253 DONE: added an explicit `band` field to `PaperTrader.open_position()`, threaded through all six write-path callers (T1/T2/T4/T4M-PROJ MLB + NBA T4 legacy), and backfilled the live MLB book from `forecast_id` prefix (`FCST-M`→T1, `T2-MLB`→T2, etc.) via `scripts/backfill_band_field.py`. This closes the last open item in GG-099's fix set — T-253/T-254/T-256 are now all DONE, GG-099 fully RESOLVED — and clears confound (b) (missing band-tagging) on GG-100's anti-predictive finding; confound (a) (GG-077 fee-sign no-op) remains open. No deliverables-table impact (a schema addition + backfill enabling per-band monitoring, not a new milestone line item, consistent with prior sessions' bug-fix entries). Committed `aa68437` (code) + `b99957c` (docs), pushed. VPS deployed: fast-forward to `aa68437` after clearing a content-verified-identical untracked leftover script; `t4-mlb.service` restarted with explicit operator confirmation (live-trading-interruption risk). Full test suite: 2,376 passed / 7 skipped / 1 pre-existing unrelated failure, up from 2,374 (2 new band-field tests). T-255 (per-band anti-predictive + calibration monitor) is now unblocked and is next in the GG-099/GG-100 chain. GG-004's n=151/n=169 baseline still needs a fresh refresh — not done this session. See MEMORY_BANK.md and TODO_NEXT.md SESSION 127 entries, DECISION_LOG.md 2026-07-08, and GOVERNANCE_GAP_LOG.md GG-099/GG-100 for full detail. *(Previous, SESSION 125 (session-end):)* T-256 fix (`run_t177_edge_monitor.py` repointed from the legacy NBA book to the live MLB book, GG-099 item 3 RESOLVED) surfaced a new ANTI-PREDICTIVE finding on the ACTIVE MLB book (n=169, Fisher p=0.0236, OR=0.350), registered as GG-100. Committed `691a978`, pushed. *(Previous, SESSION 124 (session-end):)* GG-095 (Brier drift ladder mismatch near the kill switch, `monitor.py` firing `ALERT_L4_KILL` instead of `ALERT_L3_PAUSE` at the `BRIER_L3_DELTA` crossing) RESOLVED via T-247. No deliverables-table impact (a C7 monitoring bug fix confirming the module's own already-intended 3-tier design, not a new milestone line item, same treatment as prior sessions' bug-fix entries). Full suite: 2,374 passed / 7 skipped / 1 pre-existing unrelated failure, up from 2,370. Committed `d854fd3`, pushed. VPS: `t4-mlb.service` needed no restart (doesn't import `monitor.py`); `pmbot-web-dashboard.service` restarted and confirmed healthy. Non-blocking follow-up surfaced to Earl (not built): whether `ALERT_L3_PAUSE` should gain real C4-enforced position-halt behavior. T-247 numbering briefly collided with a concurrent Opus-driven strategic session (EXP-017B/C/D + GG-098/ADR-0042); resolved via `SESSION_CLAIMS.md` reconciliation note, self-corrected by that session before this one closed. Operator noted (verbal, session close) a separate parallel strategic review is underway focused on calibrating the model math for edge extraction rather than continued infra/ops work — check for its output before defaulting to the existing governance-gap backlog. See MEMORY_BANK.md and TODO_NEXT.md SESSION 124 entries, DECISION_LOG.md 2026-07-07, and GOVERNANCE_GAP_LOG.md GG-095 for full detail.
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
