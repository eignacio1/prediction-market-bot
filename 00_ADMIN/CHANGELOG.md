# Changelog — Prediction Market Trading Bot

**Purpose:** Record all significant project-level changes in reverse-chronological order. NOT a git commit log — this tracks architectural, governance, and scope changes.  
**Owner (role):** Directory Steward (DS)  
**Last reviewed:** 2026-05-29 (EXP-016 complete; HYP-009 CONFIRMED; KI-008 RESOLVED; all 9 hypotheses resolved)  
**Next review:** Updated continuously; reviewed weekly at DIR  
**Staleness triggers:** Any major change without a corresponding entry  
**Upstream links:** 03_DECISIONS/DECISION_LOG/ (ADRs are the decision record; this is the timeline view)  
**Downstream links:** 11_MEMORY_HANDOFF/MEMORY_BANK.md  
**Decision references:** ADR-0001  
**Confidence:** 10/10 — Clean slate  

---

## 2026-05-29 — Workflow Hardening: PDTP Audit, LL-008/009, KI-010–013, Phase 6 CP, FAQ Phase 6

**Change type:** Governance / process hardening — closes all structural gaps identified by PDTP assessment of handoff/memory retention workflow  
**Summary:** PDTP surfaced 7 remaining structural gaps after the initial handoff audit repair. All gaps closed in this pass. **(1) Mid-session decision protocol** added to MEMORY_BANK.md — write to DECISION_LOG immediately when a strategic decision is made, not at session end. **(2) 80% context window trigger** documented in /session-end header — mandatory immediate trigger; stop all implementation work and produce handoff when reached. **(3) Conditional language governance** added to CHANGE_CONTROL.md — "may be revised," "could be adjusted," etc. in canonical registers are governance failures requiring immediate escalation; checklist updated to scan for conditional language before session end. **(4) LL-008** — conditional language lesson documented with full impact, mitigation, and APR-0016 as evidence. **(5) LL-009** — pilot-before-infrastructure lesson documented; /new-exp Step 0 added with explicit check before scaffolding. **(6) FAQ.md Phase 6** — 5 stale answers updated: G6 gate (30 bets, APR-0016), dark period plan, model class (ADR-0004 confirmed LR+Platt), G4 status (CLOSED), test count (533/533). **(7) CP-2026-05-29_phase6-active.md** — Phase 6/7 context pack produced (G5 CP was the last; new CP covers full Phase 6/7 operational state, all 16 experiments, all strategic decisions). **(8) KI-010** (inter-series gap), **(9) KI-011** (player injury), **(10) KI-012** (negative P&L — no monitoring threshold; T-091 registered), **(11) KI-013** (model staleness — T-072 elevated to required; T-092 registered) — all 4 risks from the original strategic review edge case table that had never been registered. **(12) KI-008/009** moved to Resolved Issues table. **(13) DECISION_LOG** — 2 sequencing principles added (pilot-first rule, T-072 elevation). **(14) SESSION_HANDOFF template** — state precision standard added for in-flight work. **(15) MEMORY_BANK M5** updated to reflect all 4 new KIs and T-091/092.  
**ADR references:** None new — all governance changes  
**Artifacts created:** CP-2026-05-29_phase6-active.md  
**Artifacts modified:** MEMORY_BANK.md, CHANGE_CONTROL.md, LESSONS_LEARNED.md (LL-008/009), FAQ.md, KNOWN_ISSUES.md (KI-010–013), TODO_NEXT.md (T-091/092), DECISION_LOG.md, /session-end, /new-exp, TEMPLATE_SESSION_HANDOFF.md, CHANGELOG.md  
**Tests:** 533/533 (unchanged)  
**Phase gate status:** G0–G5 ✅ ALL CLOSED | Phase 6 🟢 ACTIVE | G6 gate: 0/30 bets | All workflow structural gaps: CLOSED  
**Changed by:** DS

---

## 2026-05-29 — Handoff Audit + Structural Repair: APR-0016, Dark Period Plan, ctx.md Rewrite

**Change type:** Governance repair + structural fix  
**Summary:** Comprehensive audit revealed that the prior session handoff failed to capture a strategic decision (G6 threshold 50→30 bets) and had no mechanism for retaining judgment calls across context windows. Root cause: handoffs recorded code completions but had no "Strategic Decisions" section. Additionally, ctx.md (the `/ctx` restore command) was critically outdated (267 tests, missing EXP-012–016, wrong G6 threshold, T-072/075/076/080/083/084 incorrectly marked as "Post-G6" or "blocked" when complete). **Fixes applied:** (1) **APR-0016 ACCEPTED** — G6 threshold formally revised 50 → 30 resolved paper bets; seasonal constraint documented; signed DS 2026-05-29. (2) **50→30 sweep** — updated ROADMAP_MILESTONES, KNOWN_ISSUES KI-009 (RESOLVED), MEMORY_BANK, TODO_NEXT T-070, ctx.md. (3) **ctx.md complete rewrite** — tests 267→533, all EXP-012–016 added, cron schedule corrected (22:00 UTC + 06:00 UTC added), all completed Phase 7 tasks marked correctly, dark period build queue added. (4) **ANTI-CONTEXT-EROSION INVARIANTS #8 and #9 added** to MEMORY_BANK — invariant #8 locks G6 gate at 30 bets; invariant #9 requires strategic decisions to be captured in DECISION_LOG + APPROVALS_REGISTER before session end. (5) **DECISION_LOG updated** — 3 judgment call entries added: APR-0016 threshold, dark period plan, handoff procedure upgrade. (6) **TEMPLATE_SESSION_HANDOFF.md created** — mandatory "Strategic Decisions This Session" table; 30-bet gate; resume command format. (7) **FEATURE_VERSION corrected** in MEMORY_BANK snapshot — 1.3.0 → 1.2.0 (1.3.0 was built but FALSIFIED by EXP-012; stays 1.2.0).  
**ADR references:** APR-0016 (new)  
**Artifacts created:** TEMPLATE_SESSION_HANDOFF.md  
**Artifacts modified:** APPROVALS_REGISTER.md (APR-0016), ROADMAP_MILESTONES.md, KNOWN_ISSUES.md (KI-009 RESOLVED), MEMORY_BANK.md, TODO_NEXT.md, DECISION_LOG.md, ctx.md, CHANGELOG.md  
**Tests:** 533/533 (unchanged)  
**Phase gate status:** G0–G5 ✅ ALL CLOSED | Phase 6 🟢 ACTIVE | G6 gate: 0/30 bets  
**Changed by:** DS

---

## 2026-05-29 — EXP-016 Run: HYP-009 CONFIRMED (Playoff Generalization)

**Change type:** Experiment result + governance update  
**Summary:** EXP-016 (session EXP-016-B8BA8CAC) executed using cached playoff data (2021-22 through 2024-25, 1,805 rows). Model trained on regular season TRAIN (9,507 rows, 78 features). Regular TEST Brier = 0.2465; Playoff ALL Brier = 0.2455; Δ = -0.0010 — well within gate (< 0.012). **HYP-009 CONFIRMED**: the production model (v1-28483b21) generalizes to playoff conditions with no material degradation. Paper bets placed during 2026 NBA playoffs are valid G6 evidence at full confidence. No weighting adjustment needed.  
**Governance updates:** HYP-009 → 🟢 CONFIRMED | ASM-011 → ✅ VALIDATED | KI-008 → ✅ RESOLVED (no longer a G6 blocker) | T-072 playoff model refresh demoted to optional post-Finals enrichment  
**ADR references:** ADR-0004 (LR model retained); no new ADR required  
**Artifacts created:** exp_output/EXP-016/EXP-016_results.json  
**Artifacts modified:** HYPOTHESES.md (HYP-009 status + archive), ASSUMPTIONS_REGISTER.md (ASM-011 validated), KNOWN_ISSUES.md (KI-008 resolved), MEMORY_BANK.md (M4/M8 updated), CHANGELOG.md  
**Tests:** 533/533 (unchanged)  
**Phase gate status:** G0–G5 ✅ ALL CLOSED | Phase 6 🟢 ACTIVE | All 9 hypotheses resolved ✅  
**Changed by:** DS

---

## 2026-05-29 — Phase 6 Hygiene Sprint: Dual-Window Cron, MIN_BET Floor, Playoff Ablation, Full Register Update

**Change type:** Operational hygiene + strategic depth — addressed all findings from holistic project review  
**Summary:** (1) **Ingestion date parse fix** — `pd.to_datetime(format="mixed")` on both player and team log paths in ingestion.py (lines 189, 535); eliminates ~150 noisy warnings per EXP run. (2) **C4 MIN_BET_USD floor** — added CHECK 7 in RiskEngine: bets sized below $10 rejected with `min_bet_floor`; sub-threshold Kelly positions logged but not placed; ensures every paper bet carries meaningful P&L signal. (3) **PIPE-03R (run_resolve.py)** — new resolution-only pipeline; runs at 06:00 UTC to settle late-game positions after nba_api updates; does NOT place bets; 9 tests. (4) **Dual-window PIPE-03 cron** — added 22:00 UTC run (6pm ET) to capture 7pm ET tip-off markets that closed before the prior 01:30 UTC run; expected to double bet accumulation rate from ~2 to ~4 bets/game day; directly addresses KI-009. (5) **EXP-016 / HYP-009** — playoff generalization ablation runner created (T-072 advanced from deferred to active); pulls nba_api playoff logs 2021-22 through 2024-25; evaluates Brier on playoff-only rows vs regular TEST; gate Δ < 0.012. (6) **cron.conf cleaned** — inline multi-line Python extracted to `deploy/check_model_freshness.py`; cron.conf now valid and installable without parse error. (7) **VPS crontab replaced** — clean cron.conf installed on 157.230.91.33; duplicate entries removed. (8) **Governance registers updated** — KI-008 (playoff model validity, HIGH, G6 blocker), KI-009 (50-bet gate calendar risk, MEDIUM), ASM-010 (strategy concentration), ASM-011 (playoff generalization, UNVALIDATED), HYP-009 (registered), ROADMAP G6 calendar constraint with APR-0016 extension path. (9) **git author identity** — `git config --global user.email earlignacio1@gmail.com`. (10) **Connectivity assumption corrected** — work wifi blocked (strict outbound policy); all other networks pass WAF; "hotspot required" language removed from all forward-looking registers.  
**ADR references:** ADR-0001/002/003/004 (all unchanged)  
**Artifacts created:** run_resolve.py, run_exp016.py, deploy/check_model_freshness.py, tests/test_run_resolve.py, SESSION_HANDOFF_20260529_2030.md  
**Artifacts modified:** ingestion.py, c4_risk_engine/risk.py, deploy/cron.conf, tests/test_c4_risk.py, KNOWN_ISSUES.md (KI-008/009), ASSUMPTIONS_REGISTER.md (ASM-010/011), HYPOTHESES.md (HYP-009 + corrected HYP-006/007/008 statuses), ROADMAP_MILESTONES.md (G6 calendar note), MEMORY_BANK.md, SESSION_HANDOFF_20260529_2030.md, project memory  
**Tests:** 519 → 533/533 (+5 MIN_BET_USD, +9 run_resolve)  
**Phase gate status:** G0–G5 ✅ ALL CLOSED | Phase 6 🟢 ACTIVE | EXP-016 pending (HYP-009)  
**Changed by:** DS

---

## 2026-05-29 — Phase 3 VPS Deployment: GitHub Repo, VPS Sync, PIPE-03 Verified, EXP-012

**Change type:** Operational milestone — Phase 3 VPS deployment complete  
**Summary:** (1) **GitHub repo created** — `github.com/eignacio1/prediction-market-bot` (private); `gh` CLI installed; deploy key provisioned on VPS (SSH ed25519). (2) **VPS synced** — `git pull` on 157.230.91.33; venv rebuilt (broken bin/ dir); nba_api + kalshi-python reinstalled; sklearn upgraded to 1.8.0 to match production model. (3) **PIPE-03 VenueRouter migration verified** — live run on VPS produced 41 markets, 2 paper bets placed (De'Aaron Fox YES 15+pts $56.55; SGA NO 30+pts $7.18); kalshi_only mode confirmed. (4) **EXP-012 run** — HYP-006 FALSIFIED: opp_def_rating + is_home_game Δ Brier = 0.0000 (gate 0.001); FEATURE_VERSION stays 1.2.0; F-039/F-040 dropped; TeamStatsStore demoted to reference. (5) **sklearn constraint fixed** — pyproject.toml updated from `<1.5` to `>=1.8.0,<2.0`. (6) **VPS git tracking** — `master` branch set to track `origin/main`.  
**ADR references:** ADR-0003 (Kalshi primary), ADR-0004 (LR+Platt retained)  
**Artifacts created:** exp_output/EXP-012/EXP-012_results.json, SESSION_HANDOFF_20260529_1651.md  
**Artifacts modified:** pyproject.toml, deploy/cron.conf, HYPOTHESES.md (HYP-006 FALSIFIED), MEMORY_BANK.md, project memory  
**Tests:** 519/519 (unchanged — EXP-012 is a runner, not a test module)  
**Phase gate status:** G0–G5 ✅ ALL CLOSED | Phase 6 🟢 ACTIVE | VPS fully synced  
**Changed by:** DS

---

## 2026-05-29 — Phase 6 Idle Build: Execution Bands + Multi-Venue Architecture + Strategy Overview

**Change type:** Architecture expansion — Phase 6 idle period (waiting for paper bet accumulation T-070)
**Summary:** Full Phase 7 architecture skeleton deployed during idle period. (1) **ExecutionBand framework** — T1–T5 time-horizon bands (execution_bands.py); BandConfig per band (Kelly fraction, compute budget, SLA, pipeline ID, cron schedule); EXECUTION_BANDS.md canonical spec with PDTP assessment 9/10. (2) **Multi-venue architecture** — VenueAdapter Protocol (structural typing; no inheritance required); KalshiVenueAdapter (wraps existing KalshiMarketClient — zero changes to existing client); PolymarketVenueAdapter stub (T-077 slot-in); DFSPickemVenueAdapter stub (PrizePicks/Underdog/Sleeper, new ADR); VenueRouter (kalshi_only default; best_price routing when Polymarket live); PlayerMarket.venue field added (backward-compatible default "kalshi"); VENUE_REGISTRY.md (V-001–V-005 CA-eligible venues). (3) **PIPE-05 T2 skeleton** — run_t2_sameday.py; injury overlay stub (DS-04 pending T-075); cron 17:00 UTC. (4) **PIPE-06 T3 momentum scan** — run_t3_pretip.py; reads T1 pregame report + live VenueRouter prices; CONFIRM/FADE/NEUTRAL signal; edge adjustment ×1.15/×0.75; Kelly 0.10; cron */15 21-23 UTC. (5) **STRATEGY_OVERVIEW.md** — Section 5 Execution Bands PDTP added (full 4-pass analysis; 9/10 self-assessment); upstream links updated. (6) **62 new tests** — 267→329/329 passing; test_execution_bands.py, test_c5_venue_adapter.py, test_c5_venue_router.py. (7) **Governance** — PIPELINES_JOBS.md (PIPE-05/06); ENVIRONMENTS.md (VENUE_ROUTER_MODE, POLYMARKET_API_KEY, DFS keys); INTERFACES_CONTRACTS.md (IF-VENUE-ADAPTER, IF-ROUTER); ARCHITECTURE_OVERVIEW.md (Phase 6 idle build section). (8) **Slash commands updated** — /ctx /hygiene /pregame /status /retrain all reflect new components.
**ADR references:** ADR-0001/002/003/004 (all unchanged); new ADRs needed for DFS pick'em venues (Phase 7+)
**Artifacts created:** execution_bands.py, c5_execution/venue_adapter.py, c5_execution/venue_router.py, run_t2_sameday.py, run_t3_pretip.py, EXECUTION_BANDS.md, VENUE_REGISTRY.md, test_execution_bands.py, test_c5_venue_adapter.py, test_c5_venue_router.py
**Artifacts modified:** kalshi_client.py (venue field), ARCHITECTURE_OVERVIEW.md, INTERFACES_CONTRACTS.md, PIPELINES_JOBS.md, ENVIRONMENTS.md, STRATEGY_OVERVIEW.md, MEMORY_BANK.md, TODO_NEXT.md, all 8 slash commands
**Tests:** 267 → 329/329 passing
**Phase gate status:** G0–G5 ✅ ALL CLOSED | Phase 6 🟢 ACTIVE | Phase 7 architecture skeleton 🟡 deployed
**Changed by:** DS

---

## 2026-05-29 — Phase 6 Active: VPS Deployed, Paper Trading Live, Qualitative Pipeline Validated

**Change type:** Phase 6 entry — multiple major deliverables across two session days (2026-05-28/29)  
**Summary:** Complete Phase 6 activation. (1) **G5 CLOSED / APR-0007 ACCEPTED** — EXP-004 Parts A+B (HYP-003 🟢 CONFIRMED; EV +$0.0855/bet; 37 live markets); DS-02-B-001 RESOLVED (hotel wifi + datacenter IP both pass Kalshi WAF). (2) **T-058 EXP-005** — 5-season model refresh (2021-26); 15,590 rows; TEST Brier +0.0024/ECE 0.0456 on 2025-26; model v1-9939a6a5. (3) **Qualitative signal pipeline** — Three-layer architecture documented (L1 quant/L2 qual/L3 amplification); QUALITATIVE_SIGNALS.md + QUALITATIVE_REGISTRY.md; QualitativeSignalStore implemented; QS-2026-05-28-001/002 (50 players classified; QS-002 backdated QTI-03); EXP-006 Δ=0 (expected); EXP-007 +0.0017 Brier/+0.0159 ECE POSITIVE SIGNAL; EXP-008 PRF one-hot (prf_w01…prf_w15) negligible vs EXP-007; EXP-009 L3 amplification Δ=-0.0004 (LR cannot exploit); EXP-010 EV +$0.0958/bet (hotel wifi, live vig 0.030); EXP-011 HGBC vs LR — LR RETAINED/ADR-0004 unchanged. (4) **T-059 VPS** — DigitalOcean NYC3 Droplet 157.230.91.33; Ubuntu 24.04; Python 3.12+sklearn 1.8.0 venv; model retrained natively (v1-28483b21); deploy/ infrastructure; 8-point health check all pass. (5) **T-060 PIPE-03** — PaperTrader ($1,000 paper bankroll; nba_api outcome resolution; C4 active); run_paper_trade.py; cron 01:30 UTC daily; tested live.  
**ADR references:** ADR-0001/002/003/004 (all accepted); ADR-0004 confirmed retained after EXP-011  
**Artifacts created:** qualitative_store.py, qualitative_amplifier.py, paper_trader.py, run_paper_trade.py, run_pregame.py, train_and_save_model.py, deploy/, run_exp005–011.py, QS-2026-05-28-001/002, QUALITATIVE_SIGNALS.md, QUALITATIVE_REGISTRY.md, qualitative_data/pam_v4/  
**Artifacts modified:** ENVIRONMENTS.md (ENV-02 VPS), PIPELINES_JOBS.md (PIPE-02 cron), DATA_FLOWS_LINEAGE.md (F-100+/QTI rules), INTERFACES_CONTRACTS.md (IF-DS-Q-C2), OPEN_QUESTIONS.md (OQ-017/020 resolved; OQ-021 added), forecaster.py (all-NaN imputation fix), APPROVALS_REGISTER.md (APR-0007 ACCEPTED), HYPOTHESES.md (HYP-003 CONFIRMED), RID_LOG.md (DS-02-B-001 RESOLVED)  
**Phase gate status:** G0–G5 ✅ ALL CLOSED | Phase 6 🟢 ACTIVE  
**Changed by:** DS

---

## 2026-05-28 — G4 Evidence Gate CLOSED; ADR-0004 Accepted; Phase 5 Active

**Change type:** Phase gate passage — G4 CLOSED; Phase 4 complete; Phase 5 entry  
**Summary:** (1) **FEATURE_VERSION 1.2.0** — F-032–F-038 (schedule + ERI features) pruned from `features.py`; HYP-005 falsified (Δ Brier = +0.0002 below 0.005 threshold); 31 active features; 179/179 tests passing. (2) **ADR-0004 ACCEPTED (APR-0012)** — LR+Platt (`StandardScaler → CalibratedClassifierCV(LogisticRegression, method="sigmoid", cv=3)`) confirmed as Phase 3 model class; model version `v1-9939a6a5`. (3) **G4 TEST set evaluated** — EXP-001 held-out TEST rows (3,254 rows, 2023-24 season, SNAP-2026-05-28-001): Brier 0.2416 (+0.0084 vs null 0.2500), ECE 0.0247 (< 0.05 threshold), AUC-ROC 0.6062. TEST performance stronger than validation average (+0.0044 Brier). (4) **All G4 sign-offs recorded** — MV, EO, AO, DS (Earl Ignacio) signed off 2026-05-28; APR-0006 + APR-0012 in APPROVALS_REGISTER.md. (5) **Visual Dashboard (C8) registered** — ARCHITECTURE_OVERVIEW.md, INTERFACES_CONTRACTS.md, SCOPE_IN_OUT.md updated; IF-C6-C8 + IF-C7-C8 stub interfaces added; evolution policy: panels extended at each phase. (6) **PM Template gap fill** — PERFORMANCE_METRICS.md, VALIDATION_SIGNOFF.md, ASSUMPTIONS_LIMITATIONS.md, SENSITIVITY_STRESS_TESTS.md created; ROADMAP_MILESTONES.md rewritten; G4_VALIDATION_REPORT.md complete; CP-2026-05-28 Context Pack produced.  
**ADR references:** ADR-0001, ADR-0002, ADR-0003, ADR-0004 (ACCEPTED)  
**Artifacts created:**
- `exp_output/EXP-001/EXP-001_test_evaluation.json` (G4 TEST set evidence)
- `08_MODEL_RISK_GOVERNANCE/PERFORMANCE_METRICS.md`
- `08_MODEL_RISK_GOVERNANCE/VALIDATION_SIGNOFF.md`
- `08_MODEL_RISK_GOVERNANCE/ASSUMPTIONS_LIMITATIONS.md`
- `08_MODEL_RISK_GOVERNANCE/SENSITIVITY_STRESS_TESTS.md`
- `07_TEST_VALIDATION_EVIDENCE/VALIDATION_REPORTS/G4_VALIDATION_REPORT.md`
- `11_MEMORY_HANDOFF/CONTEXT_PACKS/CP-2026-05-28_G4-gate-readiness.md`
- `03_DECISIONS/ADR-0004_model-class-selection.md`  
**Artifacts modified:** features.py (v1.2.0), test_c2_features.py (179 tests), DATA_FLOWS_LINEAGE.md, MODEL_CARD.md, ARCHITECTURE_OVERVIEW.md (C8), INTERFACES_CONTRACTS.md (IF-C6/7-C8), SCOPE_IN_OUT.md, ROADMAP_MILESTONES.md, PLAN.md, TODO_NEXT.md, MEMORY_BANK.md, DECISION_LOG.md, APPROVALS_REGISTER.md (APR-0006, APR-0012), CHANGELOG.md (this entry)  
**Phase gate status:** G0 ✅ | G1 ✅ | G2 ✅ | G3 ✅ | G4 ✅ CLOSED 2026-05-28 | Phase 5 🟡 Active  
**Changed by:** DS

---

## 2026-05-26 — Phase 3 Research Build: C1–C4 Implemented; ADR-0003 Accepted; OQ-006 + OQ-015 Resolved

**Change type:** Phase milestone — T-031 through T-034 complete; four components implemented  
**Summary:** Phase 3 research build milestone complete. (1) **nba_api added** — `nba_api==1.4.9` added to requirements-base.txt as Phase 3 data proxy; `DEFAULT_REQUEST_DELAY_S = 0.6`; `SUPPORTED_SEASONS = ("2021-22", "2022-23", "2023-24")`; OQ-015 (Synergy/Second Spectrum access) resolved — nba_api confirmed viable Phase 3 proxy, reclassified from blocking to Phase 5 enrichment. (2) **C6 AuditLogger implemented** — `audit_logger.py`; JSONL write-through; kill switch return semantics (`bool, ...` tuple contract); secret redaction on 11 key patterns; `AuditLogger` exported from `c6_audit_logger/__init__.py`. (3) **C1 NBAIngestionClient implemented** — `ingestion.py`; PlayerGameLog pull via nba_api; IF-C1-C2 schema (29 columns) enforced; C6 write-failure kill switch; snapshot_id + ingestion_run_id metadata; `NBAIngestionClient` exported from `c1_signal_ingestion/__init__.py`. (4) **C2 FeatureStore implemented** — `features.py`; `FEATURE_VERSION = "1.0.0"`; L10 rolling window (`DEFAULT_WINDOW = 10`, `MIN_PERIODS = 3`); 18 rolling mean + 5 rolling std stats; efficiency metrics (ts_pct, usage_proxy, ast_tov); regime flags (pts_hot_flag, pts_cold_flag); season context features; TI-01 enforced via `.shift(1).rolling()`; `temporal_cutoff = game_date.shift(1)`; chronological train/val/test split; IF-C2-C3 output schema; `FeatureStore` exported from `c2_feature_store/__init__.py`. (5) **C3 ModelForecaster implemented** — `forecaster.py`; `MODEL_CLASS = "LogisticRegression+PlattScaling"`; `CalibratedClassifierCV(LogisticRegression, method="sigmoid", cv=3)`; deterministic `model_version = "v1-{sha1[:8]}"` from feature names + model class; TI-02 enforced (TRAIN-only fit check with CRITICAL audit event on violation); Wilson score 90% CI; edge = p̂ − mid_price (spread/2 deferred Phase 6); IF-C3-C4 output schema; `ModelForecaster` exported from `c3_forecasting/__init__.py`. (6) **C4 RiskEngine implemented** — `risk.py`; `DEFAULT_KELLY_FRACTION = 0.25` (quarter-Kelly); `MIN_EDGE_TO_APPROVE = 0.02`; phase gate via `BOT_C4_ACTIVE` env var (NEVER ENV-01/ENV-02); kill switch on daily_loss_limit or drawdown_limit breach; check order: phase gate → daily loss → drawdown → concurrent positions → edge threshold → direction actionable → Kelly size positive → APPROVED; hard limit stubs (finalized at G4); `RiskEngine` exported from `c4_risk_engine/__init__.py`. (7) **ADR-0003 formally accepted** — OQ-006 resolved: Kalshi confirmed CFTC-DCM, all 50 states, NBA markets available; Polymarket US noted as Phase 6+ secondary (CFTC-regulated Dec 2025 relaunch); APR-0011 signed; DECISION_LOG.md updated (PENDING → ACCEPTED 2026-05-23); VENDOR_RISK.md VND-01 updated.  
**ADR references:** ADR-0001, ADR-0002, ADR-0003 (ACCEPTED)  
**Artifacts created:**
- `src/prediction_market_bot/c6_audit_logger/audit_logger.py` (Phase 3 2026-05-26)
- `src/prediction_market_bot/c1_signal_ingestion/ingestion.py` (Phase 3 2026-05-26)
- `src/prediction_market_bot/c2_feature_store/features.py` (Phase 3 2026-05-26)
- `src/prediction_market_bot/c3_forecasting/forecaster.py` (Phase 3 2026-05-26)
- `src/prediction_market_bot/c4_risk_engine/risk.py` (Phase 3 2026-05-26)  
**Artifacts modified:** requirements-base.txt (nba_api added), c6/c1/c2/c3/c4 `__init__.py` (exports updated), DECISION_LOG.md (ADR-0003 ACCEPTED), APPROVALS_REGISTER.md (APR-0011 added), TODO_NEXT.md (T-031–T-034 complete; OQ-006/OQ-015 resolved), CHANGELOG.md (this entry), VENDOR_RISK.md (VND-01 Kalshi confirmed)  
**Open questions resolved:** OQ-006 (Kalshi primary confirmed; CA multi-venue TBD Phase 6) | OQ-015 (nba_api confirmed Phase 3 proxy; Synergy/Second Spectrum deferred to Phase 5)  
**Phase gate status:** G0 ✅ | G1 ✅ | G2 ✅ | G3 ✅ | Phase 3 🟡 In Progress (T-035/T-036 remaining; target 2026-07-26)  
**Changed by:** DS

---

## 2026-05-22 — G3 Execution Gate CLOSED; Phase 3 (Research Build) Initiated

**Change type:** Phase transition — G3 complete; Phase 3 initiated  
**Summary:** G3 Execution Gate formally closed (APR-0005 signed). All core G3 deliverables complete: (1) RUN_INSTRUCTIONS.md promoted to CANONICAL (G3) — Python 3.11 venv setup, Steps 0–6 run procedure, reproducibility checklist; Phase 3 pipeline commands marked TBD-at-build. (2) ENVIRONMENTS.md promoted to CANONICAL (G3) — ENV-01/02/03 fully defined; 7 environment health checks documented; VENUE_ID env var added per ADR-0003 parameter requirement; DEPENDENCY_LOCKS/ structure confirmed. (3) RID_LOG.md promoted to CANONICAL (G3) — RID-D002 (OQ-001 provenance) and RID-D003 (OQ-003 market category) archived as RESOLVED 2026-05-22; RID-D001 updated to reflect ADR-0003 skeleton existence and OQ-006 as remaining blocker; RID-003 updated with partial mitigation note (G2 interface contracts CANONICAL). ADR-0003 formal acceptance (T-028) excepted from gate closure per standing operator authorization — blocked by OQ-006 (CA-legal venue enumeration; operator action only); noted in APR-0005 evidence. PLAN.md updated: Phase 2/G3 → COMPLETE, Phase 3 → 🟡 In Progress. MEMORY_BANK.md, CHANGELOG.md, APPROVALS_REGISTER.md, TODO_NEXT.md all updated.  
**ADR references:** ADR-0001, ADR-0002, ADR-0003 (PENDING)  
**Artifacts promoted to CANONICAL:**
- 06_CODE_EXECUTION_REPRODUCIBILITY/RUN_INSTRUCTIONS.md (G3 2026-05-22)
- 06_CODE_EXECUTION_REPRODUCIBILITY/ENVIRONMENTS.md (G3 2026-05-22)
- 04_EXECUTION/RID_LOG.md (G3 2026-05-22)  
**Artifacts modified:** APPROVALS_REGISTER.md (APR-0005 signed), PLAN.md (G3 CLOSED → Phase 3 In Progress), MEMORY_BANK.md (G3 closed; Phase 3 state), CHANGELOG.md (this entry), TODO_NEXT.md (G3 tasks done; Phase 3 queue)  
**Operator actions pending:** T-015 (Python ENV-01 local setup); OQ-006 (CA-legal venue enumeration — blocks ADR-0003 formal acceptance); OQ-015 (Synergy/Second Spectrum data access — blocks Phase 3 experiment design; target 2026-07-12)  
**Phase gate status:** G0 ✅ CLOSED | G1 ✅ CLOSED (APR-0003 2026-05-22) | G2 ✅ CLOSED (APR-0004 2026-05-22) | G3 ✅ CLOSED (APR-0005 2026-05-22) | Phase 3 🟡 In Progress (target 2026-07-26)  
**Changed by:** DS

---

## 2026-05-22 — G2 Architecture Gate CLOSED; G3 (Execution Gate) Started

**Change type:** Phase transition — G2 complete; G3 initiated  
**Summary:** G2 Architecture Gate formally closed (APR-0004 signed). All G2 exit criteria met: (1) ARCHITECTURE_OVERVIEW.md promoted to CANONICAL — C4/C5 naming corrected (C4=Risk Engine, C5=Execution Engine), tech stack confirmed (Python 3.11, JSON Lines, pip/pyproject.toml); (2) INTERFACES_CONTRACTS.md promoted to CANONICAL — interface IDs corrected (IF-C3-C4, IF-C4-C5, IF-C5-VENUE), component labels corrected in IF-ALL-C6; (3) RESILIENCE_FAILURE_MODES.md promoted to CANONICAL — FM-04 and FM-05 component references corrected; (4) THREAT_MODEL.md promoted to CANONICAL — TH-02, TH-04, TH-05, TH-07 component references corrected; RCO sign-off confirmed (sole operator). C4/C5 naming was a systematic transposition bug inherited from the initial G0 build; corrected consistently across all 4 G2 artifacts. PLAN.md updated: Phase 2/G2 → COMPLETE, Phase 2/G3 → 🟡 In Progress. MEMORY_BANK.md, CHANGELOG.md, APPROVALS_REGISTER.md all updated.  
**ADR references:** ADR-0001, ADR-0002  
**Artifacts promoted to CANONICAL:**
- 02_ARCHITECTURE_DESIGN/ARCHITECTURE_OVERVIEW.md (G2 2026-05-22)
- 02_ARCHITECTURE_DESIGN/INTERFACES_CONTRACTS.md (G2 2026-05-22)
- 02_ARCHITECTURE_DESIGN/RESILIENCE_FAILURE_MODES.md (G2 2026-05-22)
- 02_ARCHITECTURE_DESIGN/THREAT_MODEL.md (G2 2026-05-22)  
**Artifacts modified:** APPROVALS_REGISTER.md (APR-0004 signed), PLAN.md (G2 CLOSED → G3 In Progress), MEMORY_BANK.md (G2 closed; G3 state), CHANGELOG.md (this entry)  
**Operator actions pending:** T-015 (Python ENV-01 local setup); OQ-006 (CA-legal venue enumeration — blocks ADR-0003 G3 acceptance); OQ-015 (Synergy/Second Spectrum data access — blocks Phase 3 design)  
**Phase gate status:** G0 ✅ CLOSED | G1 ✅ CLOSED (APR-0003 2026-05-22) | G2 ✅ CLOSED (APR-0004 2026-05-22) | G3 🟡 In Progress (target 2026-06-21)  
**Changed by:** DS

---

## 2026-05-22 — G1 Spec Gate CLOSED; Phase 2 Started

**Change type:** Phase transition — G1 complete; Phase 2 initiated  
**Summary:** G1 Spec Gate formally closed (APR-0003 signed). All 5 G1 exit criteria met: (1) requirements testable ✅ — REQUIREMENTS.md FROZEN with 9 FRs + 8 NFRs, all with measurable acceptance criteria and evidence pointers; (2) priorities explicit ✅ — P0/P1/P2 designations confirmed; (3) ≥5 assumptions ✅ — ASM-001 through ASM-007 in ASSUMPTIONS_REGISTER.md; (4) OQ-003 resolved ✅ — NBA basketball, dynamically agnostic, Kalshi primary; (5) OQ-001 resolved ✅ — DS-01 provenance documented; SNAP-001 registered. ENV-01 scaffolding verified (pyproject.toml, .pre-commit-config.yaml, C1-C7 skeleton, DEPENDENCY_LOCKS/ — all correct; T-015 local execution pending operator Python 3.11 setup). PLAN.md updated: Phase 1 → COMPLETE, Phase 2 → 🟡 In Progress. Phase 2 task queue T-022 through T-030 registered in TODO_NEXT.md. MEMORY_BANK.md, CHANGELOG.md, APPROVALS_REGISTER.md all updated.  
**ADR references:** ADR-0001, ADR-0002, ADR-0003 (PENDING)  
**Artifacts modified:** APPROVALS_REGISTER.md (APR-0003 signed), PLAN.md (G1 CLOSED → Phase 2 In Progress), TODO_NEXT.md (Phase 2 task queue T-022–T-030), MEMORY_BANK.md (G1 closed; Phase 2 state), CHANGELOG.md (this entry)  
**Operator actions pending:** T-015 (Python ENV-01 local setup); OQ-006 (CA-legal venue enumeration — blocks ADR-0003 G3 acceptance); OQ-015 (Synergy/Second Spectrum data access — blocks Phase 3 design)  
**Phase gate status:** G0 ✅ CLOSED | G1 ✅ CLOSED (APR-0003 2026-05-22) | G2 🟡 In Progress (target 2026-06-15)  
**Changed by:** DS

---

## 2026-05-22 — Phase 1: Literature Review Section 4 Expanded; ADR-0003 Skeleton Drafted; OQ-015 Registered

**Change type:** Research milestone — T-020 and T-021 complete; new open question registered  
**Summary:** T-020 complete: LITERATURE_REVIEW.md Section 4 expanded from generic sports placeholder to NBA-specific baseline (Sections 4.1–4.6). Coverage: NBA market structure and efficiency (Paul & Weinbach 2005; Avery & Chevalier 1999), NBA predictive features (Kubatko 2007; Oliver 2004; Engelmann 2017; Franks et al. 2015; Cervone et al. 2016; Witus 2013), Kalshi-specific dynamics with edge formula, signal decay and temporal integrity (10-game window; playoff regime; M-19 → FR-03 mapping), and DS-01 feature operationalization schema (30-dim soft encoding; modifier vector; M-19 health_factor). 11 new NBA-specific papers added to Papers Under Review table. Key Empirical Benchmarks and Research Gaps tables updated. OQ-015 registered: Synergy Sports / Second Spectrum data access for Phase 3 (new open question; blocks experiment design). T-021 complete: ADR-0003 skeleton drafted (venue selection); Kalshi primary confirmed; Option B multi-venue (CA-legal) is target architecture for full deployment; PENDING G3 formal acceptance pending OQ-006 resolution. DECISION_LOG.md ADR index corrected and updated.  
**ADR references:** ADR-0002, ADR-0003 (PENDING)  
**Artifacts created:**
- 03_DECISIONS/ADR-0003_venue-selection.md (PENDING G3 acceptance)  
**Artifacts modified:** LITERATURE_REVIEW.md (Section 4 NBA-specific; benchmarks; gaps), OPEN_QUESTIONS.md (OQ-015 added), DECISION_LOG/DECISION_LOG.md (ADR-0003 registered; ADR index corrected), TODO_NEXT.md (T-020/T-021 done; T-018 resolved), MEMORY_BANK.md (OQ-015; ADR-0003 status; T-020/T-021 done)  
**Operator actions pending:** T-010 (freeze REQUIREMENTS.md); T-011 (freeze ACCEPTANCE_CRITERIA.md); T-015 (Python ENV-01 setup); OQ-006 (CA-legal venue enumeration — blocks ADR-0003 G3 acceptance); OQ-015 (Synergy/Second Spectrum data access — blocks Phase 3 design)  
**Phase gate status:** G0 ✅ CLOSED | G1 🟡 In Progress — 2/5 G1 exit criteria met  
**Changed by:** DS

---

## 2026-05-22 — Phase 1: OQ-001 + OQ-003 Resolved; DS-01 Staged

**Change type:** Research milestone — two critical path open questions resolved; DS-01 fully documented  
**Summary:** OQ-001 (DS-01 provenance) resolved: creator = Earl Ignacio, date = 2026-05-21, sport = NBA basketball, document = "Weighted Hybrid PRF System — A Dynamically Agnostic Framework for Player Archetype Classification" (v4.0), underlying data = NBA box score stats + Synergy tracking + Second Spectrum tracking + game logs. OQ-003 (target market category) resolved: NBA basketball, dynamically agnostic event types, Kalshi as primary venue for initial deployment, multi-venue (CA-legal) for full deployment. SNAP-001 registered. DATA_PROVENANCE.md updated from 3/10 to 7/10 confidence. OPEN_QUESTIONS.md: OQ-001 and OQ-003 archived; OQ-006 narrowed to CA-venue enumeration. Two new tasks added: T-020 (NBA-specific literature expansion) and T-021 (ADR-0003 skeleton).  
**ADR references:** ADR-0002  
**Artifacts created:**
- 05_RESEARCH_EXPERIMENTS/DATA_SOURCES/ (new directory)
- 05_RESEARCH_EXPERIMENTS/DATA_SOURCES/README.md (governance + registry)
- 05_RESEARCH_EXPERIMENTS/DATA_SOURCES/DS-01_Player_Attribute_Matrix_v4.docx (SNAP-001)
**Artifacts modified:** DATA_PROVENANCE.md, OPEN_QUESTIONS.md, DATA_SNAPSHOTS_INDEX.md, PLAN.md, TODO_NEXT.md, MEMORY_BANK.md  
**Operator actions pending:** T-015 (Python ENV-01 setup — operator runs locally); T-010 (freeze REQUIREMENTS.md); T-011 (freeze ACCEPTANCE_CRITERIA.md)  
**Phase gate status:** G0 ✅ CLOSED | G1 🟡 In Progress — 2/5 G1 exit criteria met (OQ-001 ✅ OQ-003 ✅)  
**Changed by:** DS

---

## 2026-05-22 — Phase 1: Start (G0 Gate Closed)

**Change type:** Phase transition — G0 complete; Phase 1 initiated  
**Summary:** G0 gate formally closed (APR-0002 signed). Phase 1 execution begun. Python ENV-01 scaffolding created (pyproject.toml, .gitignore, .env.example, .pre-commit-config.yaml, src/ structure, DEPENDENCY_LOCKS/). Literature review expanded from 5-topic placeholder to substantive baseline covering all 5 research areas with empirical benchmarks and research gaps. PLAN.md, TODO_NEXT.md, MEMORY_BANK.md updated for Phase 1. Status report posted.  
**ADR references:** ADR-0001, ADR-0002  
**Artifacts created:**
- pyproject.toml (project root)
- .gitignore (project root)
- .env.example (project root)
- .pre-commit-config.yaml (project root)
- src/prediction_market_bot/ (C1-C7 package skeleton)
- tests/__init__.py
- 06_CODE_EXECUTION_REPRODUCIBILITY/DEPENDENCY_LOCKS/ (requirements-base.txt, requirements-dev.txt, README.md)
- 04_EXECUTION/STATUS_REPORTS/STATUS_Phase1_start.md
**Artifacts modified:** APPROVALS_REGISTER.md (APR-0002 signed), PLAN.md (Phase 0 closed, Phase 1 opened), TODO_NEXT.md (Phase 1 tasks), MEMORY_BANK.md (Phase 1 state), LITERATURE_REVIEW.md (DRAFT → ACTIVE, substantive content written)  
**Operator actions pending:** OQ-001 (DS-01 provenance — due 2026-06-03), OQ-003 (market category — due 2026-06-01)  
**Phase gate status:** G0 ✅ CLOSED | G1 🟡 In Progress (target 2026-06-07)  
**Changed by:** DS

---

## 2026-05-22 — Phase 0: Directory Build Complete (G0 Deliverable)

**Change type:** Major milestone — G0 directory build complete  
**Summary:** All 11 project modules fully built. 74 artifacts created across governance, spec, architecture, decisions, execution, research, code reproducibility, test/validation, model governance, security/compliance, infra/operations, and memory/handoff. Full Compass OS governance framework instantiated.  
**ADR references:** ADR-0001, ADR-0002  
**Artifacts created (this session):**
- 09_SECURITY_PRIVACY_COMPLIANCE/: CONTROL_MAPPING.md, ACCESS_CONTROL_MATRIX.md, POLICY_REQUIREMENTS.md, DATA_RETENTION_DELETION.md, VENDOR_RISK.md, AUDIT_EVIDENCE/ skeleton
- 10_INFRA_OPERATIONS/: SLA_SLO_SLI.md, OBSERVABILITY.md, RUNBOOKS/RUNBOOK_kill-switch.md, RUNBOOKS/RUNBOOK_model-drift.md, ONCALL.md, KNOWN_ISSUES.md
- 11_MEMORY_HANDOFF/: MEMORY_BANK.md, CP-2026-05-22_baseline-handoff.md, LESSONS_LEARNED.md, FAQ.md
**Link integrity:** 22/22 critical cross-references verified present  
**Header audit:** All 16 new artifacts have complete universal headers  
**G0 exit criteria:** All 11 modules present ✅ | ADR-0001/0002 accepted ✅ | MEMORY_BANK.md populated ✅ | Invariants encoded ✅  
**Pending (operator action):** APPROVALS_REGISTER.md G0 sign-off  
**Phase gate status:** G0 complete — pending formal operator sign-off  
**Changed by:** DS

---

## 2026-05-21 — Phase 0: Project Reset and Directory Instantiation

**Change type:** Major — New project (clean start)  
**Summary:** Full project directory instantiated from scratch using Enhanced Project Directory Template + Compass OS governance framework. Previous iteration retired due to context rot and data contamination.  
**ADR references:** ADR-0001 (adopt Compass OS), ADR-0002 (strategy class: forecast-only research)  
**Artifacts created:** All 12 modules + ARCHIVE/; MEMORY_BANK.md; PROJECT_CHARTER.md; baseline Context Pack  
**What was retired:** Previous bot iteration (no formal ARCHIVE entry — prior artifacts were externally stored; not incorporated)  
**Phase gate status:** Working toward G0 Intent Gate  
**Changed by:** DS  

---

*Future entries will be prepended above this line.*
