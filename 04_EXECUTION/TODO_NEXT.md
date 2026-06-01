# TODO Next — Prediction Market Trading Bot

**Purpose:** The immediate action list for the current work session. Only contains tasks executable in the next 1–3 sessions. Longer-horizon tasks belong in PLAN.md.  
**Owner (role):** Execution Lead (EL)  
**Last reviewed:** 2026-06-01 — T-114 COMPLETE (price discovery now always hits production; _price_discovery_url() added; 30 tests; 438/438 passing). PRIORITIES: T-113 (draft new G6 gate) > T-105 (EXP-017 Part B) > T-110 (G6 monitoring) > T-109 (resolve_local after each game day)

---

## SESSION 2026-05-31 HANDOFF — NEW HIGH PRIORITY TASKS

| # | Task | Priority | Notes |
|---|------|----------|-------|
| T-113 | **Draft new G6 promotion gate to supersede APR-0016 — multi-dimensional evidence standard** | **PENDING OPERATOR SIGN-OFF** | ✅ DRAFTED v2 2026-06-01 — APR-0017_g6-multi-dimensional-evidence-standard.md revised. Operator instruction: "no arbitrary gating thresholds — use trend analysis sloping with derived figures." v1 arbitrary counts replaced: T1-A now pipeline error rate ≤ 5% AND slope ≤ 0 (derived from expected API failure rate); T1-C now resolution fidelity rate ≥ 85% AND slope ≥ 0 (derived from 1.5× expected legitimate failure rate); T1-B/T1-D kept zero-tolerance with explicit boolean-by-nature justification; Tier 2 slope directions made explicit on all criteria; statistical floor revised: ≥66 resolved bets (derived from T2-A calibration power formula at α=0.05, 80% power) + ≥5 game nights (derived from slope regression df ≥ 3). Decision logged (DECISION_LOG T-113/APR-0017 v2 entry). **OPERATOR ACTION: Review `00_ADMIN/APR-0017_g6-multi-dimensional-evidence-standard.md` (v2) and sign the approval block at the bottom.** Until signed, APR-0016 remains operative. |
| ~~T-114~~ | ~~**Resolve Kalshi demo price validity question before counting Finals G1 bets toward G6**~~ | ~~HIGH~~ | ✅ COMPLETE 2026-06-01 — `_price_discovery_url()` added to kalshi_client.py: always returns `_KALSHI_LIVE_BASE_URL` regardless of BOT_ENV. `_get()` now uses `_price_discovery_url()` for unauthenticated calls (market data) and `_kalshi_base_url()` for authenticated calls (portfolio/orders). BOT_ENV=paper now suppresses order submission only — price discovery always hits production. 30 tests added in test_kalshi_client.py; 3 URL-routing invariant tests permanently lock the behavior. 438/438 passing. Decision logged. |

---

## SESSION 2026-06-01 — NEW TASKS (ADR-0008 Kalshi auth blocker)

| # | Task | Priority | Notes |
|---|------|----------|-------|
| ~~T-111~~ | ~~**Resolve Kalshi auth: NOT_FOUND on /portfolio/balance**~~ | ~~BLOCKER~~ | ✅ COMPLETE 2026-05-31 — Root cause: wrong base URL. Legacy `api.elections.kalshi.com` serves public endpoints only; authenticated endpoints (portfolio/balance, portfolio/orders) require `external-api.demo.kalshi.co` (demo) or `external-api.kalshi.com` (live). Fix: `_kalshi_base_url()` function reads BOT_ENV at runtime — paper→demo, live→live. Balance endpoint parsing also fixed (flat response, not nested). Confirmed: `Balance: True {'balance_usd': 1000.0, 'portfolio_value_usd': 0.0}`. RSA-PSS signing was correct throughout — only the server was wrong. |
| ~~T-112~~ | ~~**Deploy cryptography + updated kalshi_client.py to VPS**~~ | ~~HIGH~~ | ✅ COMPLETE 2026-05-31 — (1) kalshi_bot.pem copied to VPS `/root/.ssh/` with chmod 600; (2) `cryptography==43.0.3` installed in VPS venv; (3) `VENUE_PRIVATE_KEY_PATH=/root/.ssh/kalshi_bot.pem` added to VPS `.env`; (4) code deployed via git pull (HEAD c9fdb4e); (5) VPS balance check confirmed: `Balance: True {'balance_usd': 1000.0, 'portfolio_value_usd': 0.0}`. Cron intact — next PIPE-03 fire at 22:00 UTC will submit real Kalshi demo orders. |

---

## SESSION 2026-05-31 — NEW TASKS

| # | Task | Priority | Notes |
|---|------|----------|-------|
| T-109 | **Run run_resolve_local.py after each game day (standing procedure)** | HIGH | VPS 403 blocks nba_api; resolution must run locally. `BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_local.py`. Jun 3 NYK vs SAS positions will be resolvable after Jun 3. |
| T-110 | **G6 evidence tracking: 6/30 resolved bets** | HIGH | 6 resolved (3W 3L), +$103.46 P&L, bankroll $1,024.70. Note: 3 of the Fox wins + 3 SGA losses are from a single game (SAS vs OKC May 30) across 3 position-slots (idempotency bug pre-T-101). Operator to confirm whether all 6 count toward G6 or only 2 unique markets. |
| T-105 | **EXP-017 Part B — Collect Kalshi historical prices and run full market validation** | **BLOCKER — G6** | Part A complete (2026-06-01) — sensitivity sweep shows EV positive at ALL market price levels 0.40–0.60. Part B requires operator to collect Kalshi historical prices for TEST period (2025-04-14 onward). **Collection method**: `GET /trade-api/v2/markets?series_ticker=KXNBAPTS&closed=true` via VENUE_API_KEY, or extract from paper_portfolio.json. Save as `exp_output/EXP-017/kalshi_prices.csv` (cols: player_id, game_date, kalshi_threshold, kalshi_mid_price, kalshi_vig). Then: `PYTHONPATH=src python3 src/prediction_market_bot/run_exp017.py --kalshi-prices exp_output/EXP-017/kalshi_prices.csv`. GG-004 closes on CONFIRMED result. |
| ~~T-106~~ | ~~Fix stale T2 activation gate in EXECUTION_BANDS.md~~ | ~~HIGH~~ | ✅ COMPLETE 2026-05-31 — EXECUTION_BANDS.md:190 updated: `FEATURE_VERSION 1.3.0` removed; gate now reads `DS-04 operational (T-075 + commissioning); dedicated EXP confirming injury overlay Brier improvement ≥ 0.001 at N ≥ 100`. Aligns with BAND_ASSIGNMENT_FRAMEWORK.md. Decision logged. |
| T-107 | **Confirm Polymarket NBA tag name before T-077 activates (KI-019)** | HIGH | `venue_adapter.py:251`: `"tag": "nba"` unconfirmed. Wrong tag = silent empty market returns. Before T-077 (Polymarket KYC + activation): test VenueAdapter call, confirm non-empty return, add empty-market assertion. |
| ~~T-108~~ | ~~Document zombie daily loss limit in risk.py (KI-018)~~ | ~~MEDIUM~~ | ✅ COMPLETE 2026-06-01 — `max_daily_loss_usd` comment updated in `risk.py` `_HARD_LIMITS` with KI-018 reference and note that 20% drawdown is the operative kill switch at current bankroll. |

---

## SESSION 2026-05-31 — COMPLETED

| # | Task | Status |
|---|------|--------|
| Bug I | **Fix `pd.to_datetime` format in `resolve_pending`** | ✅ COMPLETE 2026-05-31 — Same T-089 pattern: nba_api returns "Apr 28, 2026" format; `format="mixed"` added to both Regular Season and Playoffs lookups in paper_trader.py. This was the root cause of ALL resolution failures (date parse threw ValueError → swallowed → `actual_pts=None`). |
| Bug J | **Fix misleading `drawdown_pct` in `summary()`** | ✅ COMPLETE 2026-05-31 — `drawdown_pct` removed; replaced by `realized_drawdown_pct` (closed losses / initial) and `deployed_pct` (open stakes / initial). C4 kill switch was already correct; this fixes the report. run_paper_trade.py + run_resolve.py + tests updated. |
| KI-020 | **VPS 403 blocks nba_api resolution** | ✅ DOCUMENTED 2026-05-31 — stats.nba.com hard-blocks DigitalOcean IPs. resolve_pending now logs errors instead of silently discarding. run_resolve_local.py created as the canonical resolution path. VPS run_resolve.py is kept but won't resolve without IP change. |

---

## ⚠️ SESSION 2026-06-01 — OPEN ITEM (operator action required)

| # | Task | Priority | Notes |
|---|------|----------|-------|
| T-104 | **Investigate broken token/context window efficiency auto-flags** | MEDIUM | Earl has flagged this across multiple sessions — the token maximization and context window efficiency auto-flags have never fired once. Zero attention or resolution. This is a Claude Code tooling/config issue, not a bot code issue. Operator should check: (1) Claude Code settings/hooks config; (2) whether the feature requires a specific plan tier or setting to activate; (3) file a report at https://github.com/anthropics/claude-code/issues if no config fix is found. |

---

## ✅ SESSION 2026-06-01 — COMPLETED

| # | Task | Priority | Status |
|---|------|----------|--------|
| T-102 | **Fix max_concurrent_positions stub — count gate deleted (ADR-0006)** | ~~BLOCKER~~ | ✅ COMPLETE 2026-06-01 — `max_concurrent_positions` removed from `_HARD_LIMITS`, `evaluate_forecast()` signature, CHECK 3 block, `run_paper_trade.py`, 2 tests, `RISK_APPETITE_CONSTRAINTS.md`, `EXECUTION_ARCHITECTURE.md`. KI-016 RESOLVED. |
| T-103 | **Add stub/placeholder scan to session-start governance protocol** | ~~HIGH~~ | ✅ COMPLETE 2026-06-01 — 3-step session-start scan + ARE WE COMPROMISED? added to MEMORY_BANK.md per ADR-0007. GOVERNANCE_GAP_LOG.md created. LL-010/011/012 added. |  
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
| T-052 | EXP-004 — HYP-003: edge vs Kalshi vig | RL | HIGH | ✅ COMPLETE 2026-05-28 — Parts A+B: EV +$0.0855/bet (2,481 TEST bets, 59% win rate); Part B live (37 KXNBAPTS markets, session EXP-004-FE3E2169); HYP-003 🟢 CONFIRMED; DS-02-B-001 RESOLVED |
| T-053 | SENSITIVITY_STRESS_TESTS.md — run ST-001 through ST-004 | MV | MEDIUM | ✅ COMPLETE 2026-05-28 — ST-001–004 ALL PASS; results in exp_output/SENSITIVITY_TESTS/; script: run_sensitivity_tests.py |
| T-054 | MODEL_CARD.md 7/10 → 10/10 update | EL | LOW | ✅ COMPLETE 2026-05-28 |
| T-055 | CAPACITY_PLANNING.md — create | EL | LOW | ✅ COMPLETE 2026-05-28 |
| T-056 | Context Pack CP-2026-05-28_G5-readiness | DS | LOW | ✅ COMPLETE 2026-05-28 — `11_MEMORY_HANDOFF/CONTEXT_PACKS/CP-2026-05-28_G5-readiness.md` |

### Phase 6 — Paper Trading (ACTIVE 2026-05-29)

**G5 CLOSED 2026-05-28. Phase 6 ACTIVE. Paper trading running on VPS.**

| # | Task | Owner | Priority | Status |
|---|------|-------|----------|--------|
| T-058 | Model data refresh — 5 seasons 2021-26 | EL | HIGH | ✅ COMPLETE 2026-05-28 — EXP-005; 11,931 TRAIN; Brier +0.0024; model v1-9939a6a5 |
| T-059 | VPS provisioning | IO | HIGH | ✅ COMPLETE 2026-05-29 — DigitalOcean NYC3, 157.230.91.33, Ubuntu 24.04, Python 3.12; health check 8/8 pass; cron installed |
| T-060 | Paper trading pipeline (PIPE-03) | EL | HIGH | ✅ COMPLETE 2026-05-29 — PaperTrader + run_paper_trade.py; $1,000 bankroll; C4 active; nba_api resolution; cron 01:30 UTC |
| T-061 | ADR-0005 — Live capital authorization (G6) | AO/DS | LOW | 🔲 — After 30 resolved paper positions with positive P&L (APR-0016); 0/30 as of 2026-05-29; not yet |
| T-062 | Context Pack for Phase 6 | DS | LOW | 🔲 — Create CP-2026-05-29_phase6-active.md |
| T-063 | OQ-021 Amplification study (EXP-009 done; GBM tried) | RL | MED | ✅ COMPLETE 2026-05-29 — EXP-009 L3 Δ=-0.0004 (LR); EXP-011 GBM Δ=-0.0008; L3 needs more data or context-stratified approach |
| T-064 | PRF coefficient analysis (EXP-008 one-hot) | RL | MED | ✅ COMPLETE 2026-05-29 — prf_w features implemented; encoded as weighted continuous |
| T-065 | Gradient boosting model experiment | EL | MED | ✅ COMPLETE 2026-05-29 — EXP-011 HGBC vs LR; LR RETAINED; ADR-0004 unchanged |
| T-069 | EV re-estimation with refreshed model | RL | HIGH | ✅ COMPLETE 2026-05-29 — EXP-010: EV +$0.0958/bet; win 61.1%; live vig 0.030; 871/2,692 bets |

### Phase 6 — Next Tasks

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| T-070 | Accumulate paper trading evidence (30+ bets) | DS | HIGH | Monitor logs/paper_portfolio.json daily; target **30 resolved positions** (APR-0016: revised from 50 per seasonal constraint); 0/30 as of 2026-05-29; dual-window cron firing; NBA dark period ~2026-06-22 if not reached |
| T-071 | Model cohort expansion (more players for 2025-26) | EL | MED | ✅ COMPLETE 2026-05-29 — `cohort.py` canonical registry; v1=50 players; v2=~80 players; lookup_player_id.py utility added |
| T-072 | Playoff generalization ablation (EXP-016 / HYP-009) | EL | HIGH | ✅ COMPLETE 2026-05-29 — EXP-016-B8BA8CAC; Δ Brier = -0.0010 (gate < 0.012); HYP-009 CONFIRMED; KI-008 RESOLVED; playoff paper bets valid G6 evidence at full confidence |
| T-073 | DS-04 qualitative source registration | RL | LOW | First new qualitative source beyond PAM (coaching fit, matchup context, etc.) |
| T-074 | Session handoffs CP-2026-05-29 | DS | LOW | ✅ COMPLETE 2026-05-29 — SESSION_HANDOFF_20260529_1651.md + SESSION_HANDOFF_20260529_2030.md |
| T-085 | PIPE-03R resolution-only pipeline | EL | HIGH | ✅ COMPLETE 2026-05-29 — `run_resolve.py`; 06:00 UTC cron; resolves late-game positions after nba_api updates; 9 tests |
| T-086 | C4 MIN_BET_USD floor ($10) | EL | MED | ✅ COMPLETE 2026-05-29 — CHECK 7 in risk.py; sub-floor bets → `min_bet_floor` REJECTED; 5 tests |
| T-087 | Dual-window PIPE-03 cron | IO | HIGH | ✅ COMPLETE 2026-05-29 — 22:00 UTC early + 01:30 UTC late; VPS crontab replaced; cron.conf inline Python extracted to check_model_freshness.py |
| T-088 | Governance registers KI-008/009/ASM-010/011/HYP-009 | DS | HIGH | ✅ COMPLETE 2026-05-29 — KI-008 playoff validity (HIGH G6 blocker); KI-009 50-bet calendar gap; ASM-010 strategy concentration; ASM-011 playoff generalization; HYP-009 registered; ROADMAP G6 calendar note + APR-0016 path |
| T-089 | ingestion.py date parse fix | EL | LOW | ✅ COMPLETE 2026-05-29 — `format="mixed"` on both player + team log paths; eliminates ~150 warnings per EXP run |
| T-090 | git author identity + VPS connectivity note | IO | LOW | ✅ COMPLETE 2026-05-29 — `earlignacio1@gmail.com`; "hotspot required" language removed from all forward-looking registers |

### Phase 7 — Planned Tasks (unblocked after G6)

**Prerequisite:** G6 gate cleared (ADR-0005 signed; T-061). Priority order reflects strategy research recommendation — B and I before E+C.

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| T-075 | Strategy B — Opponent def rating + home/away (EXP-012) | EL | HIGH | ✅ COMPLETE 2026-05-29 — EXP-012-54AEB56C; HYP-006 FALSIFIED; v1.3.0 TEST Brier 0.2480 vs v1.2.0 TEST Brier 0.2480; delta_vs_v12 = -7e-06 (negligible); opp_def_rating + home/away carry no additive signal; FEATURE_VERSION stays 1.2.0; Strategy B remains SKELETON |
| T-076 | Strategy I — Poisson/NB scoring distribution model (EXP-013) | EL | HIGH | ✅ COMPLETE 2026-05-29 — EXP-013-436E29C1; HYP-007 FALSIFIED; NB Brier 0.2671 vs LR Brier 0.2461; Δ = -0.0211 (gate ≤ 0.010); NB not competitive for calibration; ScoringDistributionModel retained for multi-line pricing use case only; Strategy I remains SKELETON |
| T-077 | Strategy E — Line Shopping: Polymarket US API access | IO | HIGH | 🟡 INFRASTRUCTURE COMPLETE 2026-05-29 — PolymarketVenueAdapter fully implemented (REST+CLOB, Bearer auth, `_parse_market()` regex, graceful failure); ACC-0003 registered PENDING in ACCESS_REQUESTS.md; RUNBOOK_polymarket-activation.md written; **OPERATOR ACTION REQUIRED: provision API key at polymarket.com → set POLYMARKET_API_KEY in .env → run activation runbook** |
| T-078 | Strategy E — C5 VenueRouter abstraction layer | EL | HIGH | 🟡 SKELETON COMPLETE 2026-05-29 — VenueAdapter Protocol + KalshiVenueAdapter + VenueRouter built; PIPE-05/06 deployed; Polymarket adapter stub ready; activate at T-077 API provisioning |
| T-079 | Strategy E — EXP-014: EV re-estimation with line shopping active | RL | MED | Quantify $/bet improvement from best-price routing vs. Kalshi-only baseline |
| T-080 | Strategy C — Complement lock scanner (cross-venue) | EL | MED | ✅ COMPLETE 2026-05-29 — `c5_execution/complement_lock_scanner.py`; `LockOpportunity` + `ComplementLockScanner`; scan_snapshot() + scan_single(); 22 tests; detection-only (APR-0010 required for execution) |
| T-081 | Strategy C — APR-0010 sign-off | DS | MED | DS governance sign-off to activate arb/ module; unblocks after T-078 VenueRouter is live; replaces "Indefinite" blocker in blocked items |
| T-082 | Phase 7 context pack | DS | LOW | CP-2026-Phase7 handoff |
| T-083 | Cross-venue market mapper (normalization rules) | EL | MED | ✅ COMPLETE 2026-05-29 — `c5_execution/market_mapper.py`; `normalize_player_name()` + `PlayerMarketKey` + `group_by_key()`; accent/apostrophe/period normalization; 26 tests; VenueRouter deduplication upgraded to use normalized keys |
| T-084 | Multi-band execution orchestrator (P6 rules) | EL | HIGH | ✅ COMPLETE 2026-05-29 — `execution_bands_orchestrator.py`; `BandSignal` + `BandDecision` + `MultiBandOrchestrator`; T3>T2>T1 priority; CONFIRM/FADE/NEUTRAL rules; batch_decide(); 46 tests; T3 cron schedule extended to 20-23,0-3 UTC for late games |

### Phase 6 — Newly Registered Tasks (2026-05-29 handoff audit)

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| T-091 | C7 paper P&L monitoring alert | EL | MED | Add to SystemMonitor: WARNING at total_pnl < -$50 (5% bankroll); L2 at < -$100 (10%); KI-012; requires DS threshold sign-off first |
| T-092 | Elevate T-072 to required pre-2026-27 | DS | MED | Model staleness KI-013 — T-072 must retrain before paper trading resumes in Oct 2026; not optional; needs new ADR |
| T-100 | Fix Bug H — drawdown includes open stakes (KI-015) | EL | HIGH | ✅ COMPLETE 2026-05-30 — `run_paper_trade.py` lines 215+334: `current_drawdown_pct = realized_loss / initial_bankroll`; DS sign-off granted by operator same session; deployed VPS; live check: 0.00% realized drawdown |
| T-101 | Fix Bug G — idempotency check failure (KI-014) | EL | HIGH | ✅ COMPLETE 2026-05-30 — Root cause: `LOG_DIR` was relative path; cron ran from different CWD → fresh portfolio each run → 3× positions. Fix: `_SRC_ROOT / "logs"` absolute default in `run_paper_trade.py` + `run_resolve.py`. Idempotency logging added. Deployed VPS. |

### Governance Debt — decisions_logged: false (registered 2026-05-29)

*These documents contain unlogged strategic decisions. Each must be resolved before the document can be marked CANONICAL. Low priority unless the document is being actively modified — resolve before any session that touches the document.*

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| T-093 | Extract decisions from EXECUTION_ARCHITECTURE.md → DECISION_LOG.md; set decisions_logged: true | DS | LOW | Unlogged: 4 execution mode design, paper fill assumptions (mid-price, no slippage), idempotency key requirement, decision cycle ordering |
| T-094 | Extract decisions from MONITORING_DRIFT_PLAN.md → DECISION_LOG.md; set decisions_logged: true | DS | LOW | Unlogged: L1–L4 drift ladder thresholds (Brier 0.255/0.265/0.275/0.280; win rate 54%/52%/48%), monitoring metric selection rationale |
| T-095 | Extract decisions from METHODOLOGY.md → DECISION_LOG.md; set decisions_logged: true | DS | LOW | Unlogged: PRF framework methodology choices, ±0.02 edge threshold selection, strategy architecture A–H sequencing rationale |
| T-096 | Extract decisions from VENUE_REGISTRY.md → DECISION_LOG.md; set decisions_logged: true | DS | LOW | Unlogged: V-001–V-005 venue prioritization order, activation roadmap sequencing, edge formula choices per venue type |
| T-097 | Extract decisions from RISK_APPETITE_CONSTRAINTS.md → DECISION_LOG.md; set decisions_logged: true | DS | LOW | Unlogged: rationale for specific numerical thresholds ($500/bet, $1,000/day, 20% drawdown) attributed to this document specifically |
| T-098 | Extract decisions from QUALITATIVE_SIGNALS.md → DECISION_LOG.md; set decisions_logged: true | DS | LOW | Unlogged: three-layer L1/L2/L3 amplification architecture decision, qualitative signal governance rules |
| T-099 | Extract decisions from ROADMAP_MILESTONES.md → DECISION_LOG.md; set decisions_logged: true | DS | LOW | Unlogged: G7–G9 gate criteria and phase sequencing decisions not yet in DECISION_LOG.md (G0–G5 captured via gate APRs) |

---

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
| T-061 | ADR-0005 live capital | 30 resolved paper positions with positive P&L (APR-0016) | After G6 evidence |
| T-073 | DS-04 qualitative source | Operator decision on which source to register next | When ready |
| T-077 | Polymarket API key (T-077) | polymarket.com KYC approval (1-3 days) | Operator action |
| T-081 | arb/ incorporation (Strategy C) | APR-0010 pending; T-078 VenueRouter required first | Phase 7 — after T-078 complete |
