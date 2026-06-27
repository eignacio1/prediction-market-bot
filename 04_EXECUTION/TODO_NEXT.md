# TODO Next — Prediction Market Trading Bot

**Purpose:** The immediate action list for the current work session. Only contains tasks executable in the next 1–3 sessions. Longer-horizon tasks belong in PLAN.md.  
**Owner (role):** Execution Lead (EL)  
**Last reviewed:** 2026-06-26 SESSION 93 CLOSE — **GOVERNANCE CORRECTION + T-202 COMPLETE. (1) SESSION 90 governance failure corrected: PIPE-05 (T1) and PIPE-05.5 (T2) paused in `deploy/cron.conf` — MLB arm not complete until T4 live (T-204). T1/T2 bets must not fire before T4. Committed `7b0730b`, deployed to VPS. (2) T-202: MLB T4 dry-run mode built. `T4_MLB_DRY_RUN=true` env flag: computes all evaluations, logs to `logs/t4_mlb_dryrun_YYYYMMDD.jsonl`, skips `trader.open_position()`. JSONL fields: ts/cycle_id/session_id/ticker/player_name/player_id/threshold/p_t4/mip/vig/gross_edge/net_edge/ba_l10/h_so_far/ab_so_far/ab_remaining/inning/batting_slot/would_fire. `_append_dryrun_record()` helper. C4 not called in dry-run. Budget cap not enforced. T4 MLB cron enabled with dry-run flag (22:00 UTC). 13 new tests (TestDryRunMode). Suite 2070→2083. Committed `863eccc`, deployed to VPS. (3) T4 throughput gap analyzed: ESPN returns current-batter-only state (Gap 1 — needs box score query for all batters); decision tree flat (Gap 2 — no sub-bands; Phase 8 blocked); `already_open` caps fires at ~95/game (Gap 3 — correct risk behavior). Logged in DECISION_LOG. Next: T-203 after ≥1 real game night of JSONL data.** *(Previous S92:)* **T-200 + T-201 COMPLETE. Inning-aware `ab_remaining` formula in `run_t4_mlb_live.py` (`_AB_BY_SLOT`, `_compute_ab_remaining()`, `_load_t2_batting_slots()`). Dual-pool resolution in `run_resolve_mlb.py` (`_resolve_pool()` helper; T4 pool alongside T1/T2 in single PIPE-05R run). 2044→2070 tests (+26). Committed 69a6b61, pushed, VPS deployed. MLB T4 iteration plan active (T-200 ✅ T-201 ✅ — T-202 dry-run mode next).** *(Previous S90:)* 2026-06-27 SESSION 90 CLOSE — **MLB-G1 gate CLOSED. T-194 through T-199 COMPLETE. ADR-0032 ACCEPTED. 6 MLB crons enabled on VPS. 2044/2044 tests. T-194: `mark_aged_open()` in-place tagging (15 tests). T-195: permissive-with-logging for silent exception handlers (17 tests). T-196: cron timing comment fixed (03:00→11:00 UTC). T-197: kill switch drill APR-0023 (halt_time_ms=0.116 PASS). T-198: GG-043 + GG-044 registered. T-199: integration tests + cron re-enable + VPS deploy + ADR-0032. NOT enabled: T4 MLB (GG-007), calib monitor (GG-044). Next milestones: await first MLB paper bets (11:00 UTC), first resolutions (06:30 UTC), GG-043/GG-044 resolution pre-MLB-G6.** *(Previous S88:)* **Phase MLB-G1 INITIATED. T-192 COMPLETE: integration test suite `tests/integration/` (conftest.py + 3 test files: API connectivity, name matching ≥90% gate, pipeline smoke). ALL 9 MLB crons PAUSED on VPS (deploy/cron.conf, deployed + verified). Phase MLB-G1 tasks T-193 through T-199 registered — MLB arm will not fire until ALL complete. Strategic decision: Earl directive to build MLB arm with full institutional rigor before any bets fire. MLB bankroll preserved at $1,000, 0 open, 0 closed. Next: T-193 (freshness guard), T-194 (resolution age-out), T-195 (silent fallback audit), T-196 (T1 timing comment fix), T-197 (kill switch drill), T-198 (governance gaps), T-199 (MLB-G1 gate close + re-enable).** *(Previous S87:)* **T-191 COMPLETE — **T-191 COMPLETE — MLB arm institutional completion (T1–T4; T5 out of scope). 1918→1947/1947 tests (+29). (1) T4 bugs fixed: stat group filter `!= "batting"` (was `not in ("batting", "")` which passed empty-name groups through), `MIN_EDGE_T4` dead constant removed, NFR-03 kill switch moved inside game_pk loop (was only at while-loop top; worst-case 195s halt → now ≤45s + ESPN timeout). (2) T1 timing fixed: `timedelta(days=1)` targeted tomorrow; cron moved 23:30→03:00 UTC; Kalshi confirmed to publish same-day markets by ~01:58 UTC (VPS log evidence). (3) T3 MLB cron: two missing entries added (S85 gate breach). (4) T2 MLB BUILT: `run_t2_mlb_sameday.py` (280+ lines, PIPE-05.5, 19:30 UTC), `MLBIngestionClient.fetch_lineups()`, DS-04 MLB designation `03_DECISIONS/DS-04_mlb-t2-lineup-source.md`, 29 tests `tests/test_t191_mlb_t2.py`. T2 shares `paper_portfolio_mlb.json` with T1; per-game contamination guard (not global); idempotency from PaperTrader. Git HEAD `2f13a35`. VPS deployed + crontab installed. Next: monitor first T1 bet at 03:00 UTC Jun 26, T2 at 19:30 UTC, T3 at 20:00 UTC, T4 at 22:00 UTC.** *(Previous S86:)*  **T-190 COMPLETE — full MLB arm built (pregame + T3 + T4 in-play). 55 new tests (`tests/test_run_t4_mlb_live.py`, all passing). Suite 1819→1918/1918. Three files built: `run_mlb_pregame.py` (S85/S86 Step 1), `run_t3_mlb_pretip.py` (Step 2), `run_t4_mlb_live.py` (Step 3). `deploy/cron.conf` PIPE-07 MLB block added (paused). Next: deploy to VPS (scp 3 files, run tests, uncomment 5 MLB cron lines, reinstall crontab) → MLB accumulation restarts at $1,000 fresh bankroll.** *(Previous S85:)* **MLB ARM AUDIT: CLAUDE.md T4 status corrected (was "future/post-G6" — WRONG; NBA T4 is DEPLOYED, MLB T4 NOT BUILT). All 4 MLB cron lines PAUSED (deploy/cron.conf `aab7337`). T-190 REGISTERED: 3-step build sequence before MLB accumulation restarts: (1) `run_mlb_pregame.py`, (2) `run_t3_mlb_pretip.py`, (3) `run_t4_mlb_live.py`. MLB bankroll preserved at $1,000 fresh start, 0 open, 0 closed.** *(Previous S84:)* **T-189 COMPLETE: PIPE-05 three-concern remediation (GAME_DATE=tomorrow, market date filter, ensure_persisted(), hydrate fix, PIPE-05FX cache preservation). 29 new tests. 1819/1819 tests. VPS deployed. MLB portfolio reset to $1,000. Monte Carlo: CLEAN, GREEN, ON AUTO. PIPE-05 ready for June 25 slate.** Next: monitor PIPE-05 logs at logs/paper_mlb_cron.log after 23:30 UTC; run EXP-017 after ≥20 closed MLB positions. *(Previous S83:)* **T-189 COMPLETE: PIPE-05 three-concern remediation (GAME_DATE=tomorrow, market date filter, ensure_persisted(), hydrate fix, PIPE-05FX cache preservation). 29 new tests. 1819/1819 tests. VPS deployed. MLB portfolio reset to $1,000. Monte Carlo: CLEAN, GREEN, ON AUTO. PIPE-05 ready for June 25 slate.** Next: monitor PIPE-05 logs at logs/paper_mlb_cron.log after 23:30 UTC; run EXP-017 after ≥20 closed MLB positions. *(Previous S83:)* **T-188 COMPLETE: MLB bloomberg-terminal curses TUI dashboard (`scripts/run_mlb_dashboard.py`). MLB accumulation LIVE — PIPE-05 first run tonight 23:30 UTC. 1790/1790 tests. VPS HEAD 42bce66.** Next: monitor PIPE-05 cron logs daily; run EXP-017 after ≥20 closed MLB positions. *(Previous S82 mid:)* **T-187E COMPLETE:** `run_resolve_mlb.py` + `settle_position()` + 34 tests (1704→1737). `deploy/cron.conf`: PIPE-05FX (feature refresh, renamed from incorrect PIPE-05R label) + PIPE-05R properly assigned to MLB resolve (06:30 UTC). Next: T-187F (MLB calibration monitor). *(Previous S81:)* **T-187B IN PROGRESS: `generate_mlb_features.py` running locally (PID 17013); after completion: scp CSV → VPS → `train_mlb_model.py` → shadow gate verify → T-187 COMPLETE.** T-187C/A/D COMPLETE. PIPE-05 + PIPE-05R wired. MLB Stats API VPS IP-blocking documented (2024/2025 blocked via Fastly CDN; 2026 OK). Commits eef69e5 + 2f1798b pushed. VPS crontab installed. 1704/1704 tests green. *(Previous S80:)*  **Last reviewed:** 2026-06-24 SESSION 80 — **T-117 COMPLETE: GG-006 RESOLVED. Kalshi Participant Agreement v1.54 formally read: no automation restrictions; security obligation only. Rule 5.13(s): source agency insiders only — inapplicable. Rule 5.15: market conduct rules; single algorithm mention targets Kalshi's own affiliated market makers, NOT retail members. Position Limit moot per DS ($1,000 fresh MLB bankroll). ADR-0005 pre-requisite satisfied; GG-006 CLOSED. MLB book reset: fresh $1,000 separate pool (logged DECISION_LOG S80). T-186 COMPLETE (valid negative): `nba_api.TeamGameLog` omits `PLUS_MINUS`; `pts_allowed` NaN everywhere → F-040/F-042 dead features (imputed 0.0). Fix: `pull_playoff_teamgamelog.py` cross-reference pts_allowed from opponent PTS (338/338 games populated, 22 teams). v2b retrain: F-042 73.8% non-NaN; Brier delta +0.000130 (required ≥0.001) → shadow gate FAIL. Valid negative: deploy v2-065b9510 in October (ADR-0031). 41 new tests (TestPtsAllowedCrossRef + 31 prior). Suite 1609→1650/1650 green. DECISION_LOG T-186 entry written. T-187 REGISTERED: `run_mlb_paper_trade.py` MLB paper trading runner (P0, before August 2026).** *(Previous S79 CLOSE:)*  **Last reviewed:** 2026-06-23 SESSION 79 — **T-184 COMPLETE: EXP-017 MLB commercial validation script. `scripts/run_exp017_mlb.py` (new): full EV analysis (EXP-018 pattern) + ADR-0024 tier checks (Tier 1 n≥150 / Tier 2 n≥500 or multi-sport n≥150×2) + edge monotonicity T-177 guard (Fisher/chi-squared, ANTI-PREDICTIVE/MONOTONIC/INCONCLUSIVE) + MLB threshold breakdown (k=1/2/3). `compute_fee_net_edge`: YES=model_p−mip−0.07×mip×(1−mip), NO=mip−model_p−fee. CI exit codes: 0 OK / 2 CONFIRMED_NEGATIVE / 3 DIAGNOSTIC_SPRINT / 4 insufficient. MLB position schema contract defined (`model_p`, `threshold`, `fee_net_edge` optional). Portfolio empty until August MLB paper trading — INCONCLUSIVE as expected (MIN_N=20). `tests/test_t184_exp017_mlb.py` (99 tests, 12 classes). Suite 1510→1609/1609 green. DECISION_LOG S79 written. Next: T-117 (GG-006, operator action, deadline 2026-06-30 — 7 days).** *(Previous S78 CLOSE:)*  **Last reviewed:** 2026-06-23 SESSION 78 — **T-183 COMPLETE: MLB C3 model training infrastructure. Two new files: `scripts/train_mlb_model.py` + `tests/test_t183_mlb_c3.py` (77 tests). `HOLDOUT_CUTOFF = "2026-01-01"` fixed. Shadow gate: null baseline (class prior) — no prior MLB model. `_NON_FEATURE_MLB` frozenset (leakage prevention for raw `h`). `threshold` as float feature in LR (one model scores any threshold). `_mlb_model_version()`: "mlb-v1-" + sha1[:8]. Artifact schema matches NBA loader contract. `BOT_C4_ACTIVE` test contamination root cause identified + fixed (autouse monkeypatch fixture in `TestEndToEndDryRun`). 1433→1510/1510 total tests (+77), 0 failures. DECISION_LOG S78 entry written. Next: T-184 (EXP-017 MLB commercial validation, P0).** *(Previous S77 CLOSE:)*  **Last reviewed:** 2026-06-23 SESSION 77 — **T-182 COMPLETE: MLB C2 baseball feature set. Two new files: `src/prediction_market_bot/c2_feature_store/mlb_features.py` + `tests/test_t182_mlb_c2.py` (60 tests). MLB_FEATURE_VERSION 1.0.0. TI-01 compliant (shift(1).rolling). Starting pitcher overlay MANDATORY (SP ERA/K9/BB9 from MLBPitcherStatsStore). Sum-then-divide rolling rates (BA/SLG/OBP). Park factors: 30-venue static dict (Coors 1.120, Oracle 0.970, unknown→1.000). C6 audit trail (5 event types). assign_train_test_labels: TRAIN/VALIDATION/TEST/None(NaT excluded). `_ip_to_decimal()` IP notation fix confirmed in C1 (MLB Stats API "5.2" = 5⅔ = 5.667). 1373→1433 total tests (+60), 0 failures. DECISION_LOG S77 entry written. Next: T-183 (MLB C3 model training, P0).** *(Previous S76 CLOSE:)*  **Last reviewed:** 2026-06-23 SESSION 76 — **Pre-MLB governance scrub COMPLETE. (1) KXMLBHIT ticker confirmed via live GET /series — `KXMLBHITS` does not exist; correct ticker is `KXMLBHIT`. `kalshi_client.py` updated; docstring updated with confirmed MLB series spec + structural differences from NBA ticker. (2) DtypeWarning silenced: `low_memory=False` added to `run_paper_trade.py:249` + `run_pregame.py:185`. (3) VPS monthly cron check PASSED — dark-period crons running clean June 18–23; next check end of July. (4) T-117 / GG-006 DEADLINE FLAGGED: formal Kalshi document reads required by 2026-06-30 (7 days) — operator action needed. Reads: (a) Kalshi Participant Agreement; (b) KXMLBHIT Terms & Conditions (PAL/Position Limit). (5) All other OPEN governance gaps verified status-correct — no action required beyond confirmed resolution paths. 1373/1373 tests green. DECISION_LOG S76 entry written. Next: T-182 (MLB C2 feature set, P0).** *(Previous S75 CLOSE:)*  **Last reviewed:** 2026-06-23 SESSION 74 (CLOSE) — **Governance-only session. Three Q6 worries addressed: (1) T-185 registered — v2 deploy runbook + NBA 26-27 book-reset decision A/B/C (DECISION_LOG S74). (2) ADR-0031 Known Limitations section added — F-042 NaN, Brier gain source, T-177 INCONCLUSIVE interpretation, T-186 follow-up, deployment framing ("shadow gate PASSED ≠ alpha confirmed"). (3) Phase 3 task registration: T-181/T-182/T-183/T-184/T-186 (MLB C1/C2/C3/EXP-017/v2b retrain). DARK_PERIOD_PLAN Phase 3/4 updated. MLB paper book = fresh $1,000 separate pool (DECISION_LOG S74). 1293 tests unchanged.** *(Previous S73 CLOSE:)* T-072 COMPLETE: model v2-065b9510 trained + shadow gate PASSED + T-177 INCONCLUSIVE + Phase 3 MLB gate OPEN. ADR-0031 ACCEPTED. FEATURE_VERSION 1.4.0 live on VPS. One item deferred: v2 model deploy + kill switch reset (dark period — action at 2026-27 season start Oct 2026). Next: T-073 (DS-04 injury source, July), VPS first monthly cron check (end of June 2026), MLB Phase 3 build unblocked. *(Previous S73 open:)* Governance logging repair + dark period plan hardening. **(1) ADR-0029 sign-off back-propagated:** DS sign-off (Earl Ignacio, 2026-06-22 S67) was correctly recorded in ADR file + DECISION_LOG + MEMORY_BANK but TODO_NEXT had 4 stale "DRAFT (SCOPED) — pending DS sign-off" entries — all corrected to ACCEPTED. Root cause: session history blocks not updated when same-day sign-off followed the scoping session. **(2) T-148/ADR-0028 stale PENDING entries corrected** to "ACCEPTED SESSION 72." **(3) DARK_PERIOD_PLAN Phase 3 gate hardened:** T-072 λ feature fix + post-fix run_t177 backtest (edge no longer ANTI-PREDICTIVE) now explicit prerequisite before MLB C1 build starts. **(4) VPS cron monitoring added** as dark period standing item. **(5) T-072 dark period Phase 2 tasks noted as ACTIVE.** *(Previous S72:)* ADR-0028 ACCEPTED (DS sign-off Earl Ignacio). T-148 DONE. GG-022 RESOLVED. T-127 deferred to Phase 4 (Oct 2026 / GG-041). Governance-only session; 1280 tests unchanged. *(Previous S71:)* **T-180 Phase 3 (evaluator math) + Phase 4 (live execution path) COMPLETE. T4ProjEvaluator: Gamma-Poisson conjugate update + Poisson survival probability + phase-conditional Kelly schedule (EARLY 0.010 → NEAR_CERTAIN 0.167). T4ArithEvaluator: arithmetic threshold window logic. T4EventEvaluator: event-triggered sub-band. T4FlowEvaluator/Blowout: sustained score-gap detection. T4ExitEvaluator: 3 exit conditions (TIME-FLOOR, REVERSAL, BUFFER-BREACH). Layer1 ordering: T4-PROJ prepended to avoid frozenset randomness. All evaluator math: 185 tests in test_t4_engine.py. t4_live_runner.py (new): T4FastHalt (GG-038 ≤5s design, threading.Event), T4PositionRegistry (thread-safe, pool drawdown accounting), T4PriceCacheUpdater (GG-039 bootstrap REST→WebSocket), T4GameStateBuilder (GG-040 bootstrap ESPN→T4GameState, SCORE_UPDATE detection), build_forecast_record() (EvaluationSignal→C4 dict with kelly_fraction key), T4LiveRunner (full C4/C5/C6/C7 wiring, run_cycle, _handle_entry, _handle_exit). on_game_event() implemented in T4ExecutionEngine (Layer1+Layer2 pipeline, returns tuple[approved, drops]). create_phase8() factory (instance-level _PHASE8_ACTIVE, class default stays False). C4 risk.py: backward-compat kelly_fraction override (fc.get("kelly_fraction", self._kelly_fraction)). 67 new tests in test_t4_live_runner.py. Total: 1280 tests. All T4 paths still BLOCKED/dark behind _PHASE8_ACTIVE=False. *(Previous S69:)* **Option C DS decision: feature-set diagnosis sprint. Root cause: missing playoff-context λ multiplier. T-072 scope updated.** *(Previous S68:)* T-180 Phase 2: engine built. *(Previous, SESSION 67:)*  **T-179 SCOPED: ADR-0029 pre-sign-off review + four corrections (T4-MICRO carved to ADR-0030 → 10 sub-bands; two-tier acceptance model A/B; T4-PROJ/T4-ARITH Kelly tail-calibration holds; DS quote → attributed paraphrase). ADR-0029 ACCEPTED — DS sign-off Earl Ignacio 2026-06-22 S67. ADR-0030 placeholder registered. DECISION_LOG + ADR Index updated. No code changes; 988/988.** *(Previous, SESSION 65:)* **T-148 ADR-0028 REWORK COMPLETE (ACCEPTED SESSION 72, DS sign-off Earl Ignacio 2026-06-22): G6 is T1-only; T4 Activation Gate placeholder pending T-179.** Governance hygiene: T-173 (healthcheck.sh), T-154 (CHANGE_CONTROL decisions_logged: true), T-178 (market_mapper MLB pre-flight verified). VPS HEAD `97e66ae`; 988/988 tests. *(Previous, SESSION 64:)* **GG-036 + GG-035 + GG-037(calibration half) RESOLVED; full-DB assessment complete.** GG-036: G5 41 positions resolved from the re-frozen 158-bet NBA Finals dataset (`data/nba_finals_clean_dataset.csv`); capital unlocked. GG-035: ADR-0026 (APR-0020) C4 two-tier portfolio free-cash invariant shipped (8a solvency KILL, 8b 60%-of-equity REJECT). GG-037: ADR-0027 (APR-0021) C3 temperature calibration on the **production Poisson prob** (NOT Platt — Platt re-fit would have been a no-op); NBA T=2.05 (OOS-validated). **Recalibration DISPROVED the miscalibration hypothesis: edge stays anti-predictive post-calibration (edge>0 winrate 0.356 vs edge≤0 0.747) — GG-037 alpha half + GG-004 stay OPEN; the model has no demonstrated edge vs the Kalshi price.** Committed `897ff4d`, pushed, VPS HEAD `897ff4d`, calibration verified live (NBA 0.97→0.845, MLB identity). Paper book remains halted at drawdown kill switch (25.12% > 20%). 988/988 tests. *(Previous, SESSION 63:)* **T-174 + T-171 DEPLOYED + LIVE BOOK CORRECTED. GG-034 + GG-033 RESOLVED.** VPS HEAD `52607f2`; governance closure `c52d298`. Main book `total_realized_pnl` −8.46 → **−251.21**, drawdown **25.12%**, kill switch un-blinded (code-path verified). T4 book needed no correction. **Two new gaps surfaced by the correction: GG-035 (over-leverage — corrected bankroll −$254.59, $1003.38 = 100.3% of initial deployed, no C4 free-cash invariant) and GG-036 (41 G5 positions unresolvable — nba_api has no 2026-06-13 box scores — $1003.38 locked; outcomes NOT fabricated). Both OPEN.** G6 baseline RATIFIED negative (−$251.21/−25.1% headline, −$302.98/−30.3% clean; SNAP-2026-06-14-001); ratification fixes number-of-record only — Tier 0/EXP-017 (GG-004) remains the binding G6 blocker. 965/965 tests. **CAUTION: still do not trust JSON scalars on books written before HEAD 52607f2 — derive from `closed_positions`/audit log.** *(Previous, SESSION 62:)* GG-034 registered; "let it ride" for G5. **T-179 SCOPED: ADR-0029 pre-sign-off review + four corrections (T4-MICRO carved to ADR-0030 → 10 sub-bands; two-tier acceptance model A/B; T4-PROJ/T4-ARITH Kelly tail-calibration holds; DS quote → attributed paraphrase). ADR-0029 ACCEPTED — DS sign-off Earl Ignacio 2026-06-22 S67. ADR-0030 placeholder registered. DECISION_LOG + ADR Index updated. No code changes; 988/988.** *(Previous, SESSION 65:)* **T-148 ADR-0028 REWORK COMPLETE (ACCEPTED SESSION 72, DS sign-off Earl Ignacio 2026-06-22): G6 is T1-only; T4 Activation Gate placeholder pending T-179.** Governance hygiene: T-173 (healthcheck.sh), T-154 (CHANGE_CONTROL decisions_logged: true), T-178 (market_mapper MLB pre-flight verified). VPS HEAD `97e66ae`; 988/988 tests. *(Previous, SESSION 64:)* **GG-036 + GG-035 + GG-037(calibration half) RESOLVED; full-DB assessment complete.** GG-036: G5 41 positions resolved from the re-frozen 158-bet NBA Finals dataset (`data/nba_finals_clean_dataset.csv`); capital unlocked. GG-035: ADR-0026 (APR-0020) C4 two-tier portfolio free-cash invariant shipped (8a solvency KILL, 8b 60%-of-equity REJECT). GG-037: ADR-0027 (APR-0021) C3 temperature calibration on the **production Poisson prob** (NOT Platt — Platt re-fit would have been a no-op); NBA T=2.05 (OOS-validated). **Recalibration DISPROVED the miscalibration hypothesis: edge stays anti-predictive post-calibration (edge>0 winrate 0.356 vs edge≤0 0.747) — GG-037 alpha half + GG-004 stay OPEN; the model has no demonstrated edge vs the Kalshi price.** Committed `897ff4d`, pushed, VPS HEAD `897ff4d`, calibration verified live (NBA 0.97→0.845, MLB identity). Paper book remains halted at drawdown kill switch (25.12% > 20%). 988/988 tests. *(Previous, SESSION 63:)* **T-174 + T-171 DEPLOYED + LIVE BOOK CORRECTED. GG-034 + GG-033 RESOLVED.** VPS HEAD `52607f2`; governance closure `c52d298`. Main book `total_realized_pnl` −8.46 → **−251.21**, drawdown **25.12%**, kill switch un-blinded (code-path verified). T4 book needed no correction. **Two new gaps surfaced by the correction: GG-035 (over-leverage — corrected bankroll −$254.59, $1003.38 = 100.3% of initial deployed, no C4 free-cash invariant) and GG-036 (41 G5 positions unresolvable — nba_api has no 2026-06-13 box scores — $1003.38 locked; outcomes NOT fabricated). Both OPEN.** G6 baseline RATIFIED negative (−$251.21/−25.1% headline, −$302.98/−30.3% clean; SNAP-2026-06-14-001); ratification fixes number-of-record only — Tier 0/EXP-017 (GG-004) remains the binding G6 blocker. 965/965 tests. **CAUTION: still do not trust JSON scalars on books written before HEAD 52607f2 — derive from `closed_positions`/audit log.** *(Previous, SESSION 62:)* GG-034 registered; "let it ride" for G5.

---

## SESSION 93 — COMPLETE (2026-06-26)

| Task | Status |
|------|--------|
| **Governance correction — PIPE-05 + PIPE-05.5 paused** | ✅ COMPLETE — SESSION 90 governance failure corrected. PIPE-05 (T1 MLB, 11:00 UTC) and PIPE-05.5 (T2 MLB, 19:30 UTC) commented out in `deploy/cron.conf`. Reason: MLB arm not complete until T4 live (T-204). T1/T2 must not fire before entire arm built — per Earl's SESSION 88 directive. Committed `7b0730b`, deployed to VPS, crontab verified. |
| **T-202 — MLB T4 dry-run mode** | ✅ COMPLETE — `T4_MLB_DRY_RUN` env flag (`true/1/yes`) added to `run_t4_mlb_live.py`. When set: all evaluations computed, logged to `logs/t4_mlb_dryrun_YYYYMMDD.jsonl` (one record per evaluation with valid mip), `trader.open_position()` skipped. `_append_dryrun_record()` helper uses `O_WRONLY|O_CREAT|O_APPEND`. `kalshi_fee`/`net_edge` moved before dry-run branch (computed once, used by both paths). `would_fire = net_edge > 0` (no MIN_EDGE applied in dry-run — want unfiltered distribution). C4 not called. Budget cap not enforced. 13 new tests (TestDryRunMode). Suite 2070→2083. |
| **T4 MLB cron enabled (dry-run)** | ✅ COMPLETE — `0 22 * * *` cron in `deploy/cron.conf` ENABLED with `T4_MLB_DRY_RUN=true`. PIPE-05 and PIPE-05.5 remain PAUSED. T4 dry-run fires tonight (22:00 UTC). |
| **T4 throughput gap analysis** | ✅ DOCUMENTED — Three structural gaps identified and logged in DECISION_LOG: Gap 1 (ESPN current-batter-only state — needs box score query for all batters to hit ~1,000 evals/game design target); Gap 2 (flat decision tree — Phase 8 blocked); Gap 3 (`already_open` caps fires at ~95/game — correct risk behavior). |
| **Monte Carlo (4 scenarios, T4 included)** | ✅ RUN — Real June 26 pregame data (96 forecasts, 53 players). Neutral/Edge/Positive/Worst cases. T4 simulation: 477 evals/day (simulation artifact = 1 eval/inning/player; real T4 will differ). T4 fired 36–44 bets/day per scenario. MC output at scratchpad. |
| **DECISION_LOG entries** | ✅ COMPLETE — 3 entries: governance failure + corrective action, T-202 dry-run design, T4 throughput gap analysis. |
| **Commit + deploy** | ✅ COMPLETE — Committed `863eccc` [T-202 COMPLETE], pushed to origin/main, VPS deployed (HEAD confirmed). |

---

## SESSION 92 — COMPLETE (2026-06-26)

| Task | Status |
|------|--------|
| **T-200 — Inning-aware `ab_remaining` formula** | ✅ COMPLETE — `_AB_BY_SLOT` constant (Slots 1-9: 4.2→3.1 ABs/game) added to `run_t4_mlb_live.py`. `_compute_ab_remaining(ab_so_far, inning, batting_slot)` uses min-of-two-signals: `ab_from_inning = expected_total × (innings_remaining / 9.0)` and `ab_from_total = max(0, expected_total − ab_so_far)`. Eliminates ±1 AB / ±14-25% Binomial probability error vs old flat 3.7 formula. `_load_t2_batting_slots()` loads batting slots from today's `t2_mlb_YYYYMMDD_HHMM.json`. Extra-innings known limitation: clamps to 0 (conservative; acceptable for paper trading). 22 new tests. Suite 2044→2051. |
| **T-201 — Dual-pool resolution in PIPE-05R** | ✅ COMPLETE — `_resolve_pool(pool_label, trader, logger, session_id)` helper extracted from `run_resolve_mlb.py`. T4 pool (`paper_portfolio_mlb_t4.json`) now resolves alongside T1/T2 pool in single PIPE-05R cron run. T4 pool silently skipped if file doesn't exist (pre-T4 enable). `SystemMonitor` scoped to T1/T2 only (T4 budget-agnostic at resolution time). Audit log includes `resolved_t4`/`still_open_t4` fields. 5 new tests. Suite 2051→2070. |
| **Decision log entries** | ✅ COMPLETE — T-200 formula architecture + T-201 dual-pool architecture both logged in DECISION_LOG.md. |
| **Commit + deploy** | ✅ COMPLETE — Committed `69a6b61` [SESSION 92 CLOSE], pushed to origin/main, VPS deployed (HEAD confirmed). |

---

## MLB T4 ITERATION PLAN — IN PROGRESS (T-200 → T-204)

| T-NNN | Task | Status | Notes |
|-------|------|--------|-------|
| **T-200** | Inning-aware `ab_remaining` formula | ✅ COMPLETE S92 | `_AB_BY_SLOT` + `_compute_ab_remaining()` + `_load_t2_batting_slots()`. 22 tests. |
| **T-201** | Dual-pool resolution PIPE-05R | ✅ COMPLETE S92 | `_resolve_pool()` helper; T4 resolves with T1/T2 in single cron. 5 tests. |
| **T-202** | Dry-run mode (`T4_MLB_DRY_RUN=true`) | ✅ COMPLETE S93 | 13 tests. JSONL logging. Cron enabled with dry-run flag. Suite 2070→2083. |
| **T-203** | Edge calibration + GG-007 resolution | 🔲 NEXT S94+ | REQUIRES: ≥1 real game night of `t4_mlb_dryrun_YYYYMMDD.jsonl`. Analyze distribution, pick MIN_EDGE_T4, write ADR. Note: current throughput reflects single-batter-per-cycle (Gap 1, ESPN box score). Fix Gap 1 before or alongside T-203 for higher-fidelity calibration. |
| **T-204** | Enable T4 MLB cron + re-enable T1/T2 | 🔲 S94+ | Remove `T4_MLB_DRY_RUN=true` from cron. Re-enable PIPE-05 (T1) + PIPE-05.5 (T2) — both currently PAUSED pending T4 live. T4 live is the gate. |

**GG-007 (T4/T5 threshold constants uncalibrated):** LOW severity now (T4 paused), HIGH severity pre-Phase 8 activation. Formally closed once T-203 calibration ADR is written and accepted.

---

## PHASE MLB-G1 — CLOSED (2026-06-27 SESSION 90)

**MLB arm is LIVE. All 8 tasks complete. ADR-0032 ACCEPTED. 6 crons active on VPS.**

| T-NNN | Task | Status | Notes |
|-------|------|--------|-------|
| **T-192** | Phase MLB-G1 integration test suite (`tests/integration/`) | ✅ COMPLETE S88 | conftest.py + test_mlb_api_connectivity.py + test_mlb_name_matching.py + test_mlb_pipeline_smoke.py. Run with `pytest tests/integration/ -v -m integration`. |
| **T-193** | Feature CSV freshness guard in `run_mlb_paper_trade.py` + C7 alert | ✅ COMPLETE S89 | >3 days → WARNING + logger.warning; >7 days → sys.exit(1) + logger.error. Embedded in main() after feature CSV load, uses _now_utc.date() − df["game_date_dt"].max(). 23 tests (`tests/test_t193_mlb_freshness_guard.py`). |
| **T-194** | Resolution age-out: positions open >48h that can't resolve → `aged_open` + C7 alert | ✅ COMPLETE S90 | `mark_aged_open()` in `paper_trader.py` — in-place tag, position stays in open_positions (bankroll invariant). 48h age-out detection in `run_resolve_mlb.py`. 15 tests (`tests/test_t194_mlb_age_out.py`). |
| **T-195** | Silent fallback audit: MLB `except Exception: pass` in `_is_mlb_game_in_progress()` + `_fetch_live_game_pks()` → permissive-with-logging | ✅ COMPLETE S90 | Added optional `logger` + `session_id` params; emit C6 WARNING on failure; return behavior unchanged (False/empty set). 17 tests (`tests/test_t195_mlb_silent_fallback.py`). |
| **T-196** | Fix T1 cron timing comment in `run_mlb_paper_trade.py` (says 03:00 UTC; must be 11:00 UTC) | ✅ COMPLETE S90 | Module docstring + inline comment block both corrected to "11:00 UTC (7am ET)". |
| **T-197** | MLB kill switch drill + APR record | ✅ COMPLETE S90 | `scripts/run_mlb_kill_switch_drill.py`. halt_time_ms=0.116ms. SLA PASS (NFR-03 ≤60,000ms). APR-0023 written. |
| **T-198** | Register MLB-G1 governance gaps: GG-043 (Kelly fraction) + GG-044 (C7 drift baselines) | ✅ COMPLETE S90 | GG-043: MLB Kelly 0.10 inherited from NBA (LOW, deferred pre-MLB-G6). GG-044: C7 Brier/ECE baselines are NBA G4 values (LOW, calib monitor not enabled). |
| **T-199** | MLB-G1 gate close: all T-192–T-198 ✓ → 2044 tests ✓ → re-enable 6 MLB crons + VPS deploy + ADR-0032 | ✅ COMPLETE S90 | ADR-0032 ACCEPTED. VPS deployed + crontab verified. T4 MLB and calib monitor explicitly deferred (GG-007/GG-044). |

**Next MLB milestones:**
- First paper bets: PIPE-05 at 11:00 UTC daily
- First resolutions: PIPE-05R at 06:30 UTC (typically 24–48h after bets)
- GG-043/GG-044 resolution: pre-MLB-G6 (after ≥30 resolved paper bets)

---

## PRIORITY QUEUE (updated 2026-06-12 SESSION 55 — T-168/T-170 DONE; GG-031 registered)

| Pri | Task | What / Why | Due |
|-----|------|-----------|-----|
| **0 — ✅ DONE (SESSION 47)** | **T-163: ADR-0023 — Remove PAPER_T4_FLAT_SIZING; T4 budget proportional to bankroll (GG-026)** | T4_BAND_WEIGHT=0.27 derived from G4 empirical ($499.95/$1,869.68=0.267→0.27). PAPER_T4_FLAT_SIZING and PAPER_T4_POOL_USD constants removed. _compute_t4_band_budget is single budget path (no RESERVE_MANDATE deduction). pool_isolated=True hardcoded. Flat sizing (1 contract/bet) retained as hardcoded paper policy (ADR-0023). G5 budget ~$504.81. ADR-0023 ACCEPTED. GG-026 RESOLVED. 843/843 tests. Commit 72ba619, VPS deployed. | ✅ 2026-06-11 |
| **0b — ✅ DONE (SESSION 47)** | **EXP-018 Hypothesis C — DS ruling: calibration gap** | n=98, both all-bets and injury-filtered CONFIRMED_NEGATIVE. DS ruling: calibration gap — need to structure math better. NOT T1 Tier 2B FAILS. Multi-sport scale (MLB/NFL) addresses sample size. G5 diagnostic: YES-only mode (filters NO bets to isolate YES vs NO edge; requires YES_ONLY config gate in run_paper_trade.py before G5 cron). G5 fired WITHOUT YES-only gate (gate not implemented in time). G6 if DS ruling still applies. | ✅ 2026-06-11 |
| **0c — ✅ DEPLOYED (SESSION 49)** | **T-164: Throttled order submission (GG-014 G6 gate — 31% failure rate at G5)** | Inter-order sleep 0.5→2.0s; MAX_RETRIES 3→4; RETRY_DELAY_S 1.0→2.0; delay schedule 4/8/16/32s=60s. Root cause: 29-order burst saturates rate-limit window in ~14s. Batch order integrity report added to PIPE-03 run. GG-014 status: PARTIALLY RESOLVED. G6 gate (≤5% failure rate) will be confirmed in next batch run. 852/852 tests. VPS deploy pending. **OPEN until G6 batch confirms ≤5%.** | ✅ 2026-06-11 (monitoring pending) |
| **1 — ✅ DONE (SESSION 51)** | **T-157: Project-level stop criterion (GG-021)** | ADR-0024 ACCEPTED. Tier 1 (n≥150, ≥2 months): EV/bet < -$0.03 → diagnostic sprint. Tier 2 (structurally adequate: n≥500, ≥15 opponents OR ≥2 sports): CONFIRMED_NEGATIVE → halt + ADR-0004 supersession. Passability drift watch standing. EXP-017 scope transition to MLB/regular season logged. GG-021 RESOLVED. | ✅ 2026-06-11 |
| **2 — ✅ DONE (SESSION 59)** | **T-153 (EXPANDED, GG-022): fill-realism haircut on ALL paper P&L** | `scripts/run_t153_haircut.py` implemented and executed. Results (G1–G4, G5 open): T1 haircut $53.50 (p50) / $83.09 (mean); T4 $32.80/$52.71; combined $86.31/$135.81 — HIGH materiality. GG-022 partially resolved; APR-0017 amendment pending DS ruling. ADR-0019 Tier 2 CLOSED. Rerun after G5 resolve for final G1–G5 figures. | ✅ 2026-06-12 |
| **3 — ✅ DONE (SESSION 51)** | **T-158: Dark-period plan (June–Oct 2026)** | DARK_PERIOD_PLAN.md ratified at `04_EXECUTION/DARK_PERIOD_PLAN.md`. Four phases: (1) Post-Finals close — G5 resolve, EXP-017B/018 G5 run, T-153/156/159; (2) July — model retrain, DS-04, Polymarket; (3) Aug-Sep — MLB C1/C2/C3, EXP-017 MLB validation, ADR-0024 Tier 1 check; (4) Oct — GG-014 confirmation, G6 evidence review, ADR-0005. | ✅ 2026-06-11 |
| **4 — ✅ DONE (SESSION 58)** | **T-156: ADR-0012 amendment + daily-loss accumulation tests** | ADR-0025 ACCEPTED — net semantics formalized (`current_daily_loss = max(0, −daily_net_pnl)`; threshold anchored to `initial_bankroll_usd`). 28 new tests in `tests/test_t156_daily_loss.py`: direct accumulation, net offset, cross-day isolation, kill-switch boundary. 885/885 tests. | ✅ 2026-06-12 |
| **5 — ✅ DONE (SESSION 58)** | **T-159: Portfolio state-machine invariant tests + schema owner (LL-014)** | `portfolio_schema.py` created as canonical field-name constant module + `validate_portfolio_state()` validator. 38 new tests in `tests/test_t159_portfolio_invariants.py`: schema validation (9), open/close/exit invariants (19), kill-switch state transitions (5), cross-day accounting (5). Kills stale-state bug class structurally — any field rename/add triggers test failure. 923/923 tests. | ✅ 2026-06-12 |
| **5b — ✅ DONE (SESSION 46)** | **T-161: T4 exit budget-credit semantics (GG-023)** | DS ruling: realized-value credit (ADR-0022, amends ADR-0013). Exits credit budget at realized value — wins restore entry cost, losses consume permanently; band net loss bounded by budget. Restart-safe `_reconstruct_t4_ledger()`; G5 strip starts clean at $0 by game_date keying. 13 new tests; 843/843. GG-023 closed. | ✅ 2026-06-10 |
| **5c — ✅ DONE (SESSION 46)** | **T-162: PIPE-03 in-progress game guard (GG-024)** | ESPN `STATUS_IN_PROGRESS` check added to `run_paper_trade.py` before bet-placement loop. Aborts with `paper_run_skipped_game_in_progress` log entry. Deployed VPS commit `c8a59f2`. G4 Castle+Hart late-cron bets flagged ineligible per APR-0019. GG-024 closed. | ✅ 2026-06-11 |
| **6 — ✅ DONE (SESSION 56)** | **T-160: Root-folder document hygiene** | Strategy/workflow docs → `00_ADMIN/`; assessments (12-Day, PDTP Fable) → `ARCHIVE/2026/assessments/`; PAM v4 docx → `qualitative_data/pam_v4/`; Kalshi CF arbitrage template → `arb/` (reference-only quarantine); stale root team_stats caches → `ARCHIVE/2026/data/`; Word lock file deleted. `.gitignore`: added `.venv311/`, `arb/` (hard rule 1), `team_stats_cache_*.json`, `~$*.docx`. Dead `PAPER_T4_FLAT_SIZING=true` scrubbed from cron.conf T4 line + paper_trader.py docstring (ADR-0023). `run_t4_budget_sim.py` formula fixed: budget = bankroll × weight, no RESERVE_MANDATE deduction; DEFAULT_BAND_WEIGHT 0.10 stub → 0.27. Root folder clean. | ✅ 2026-06-12 |
| **7 — LOW (MLB gate)** | **T-165: Full PAM integration across T2/T3/T5 bands + EnvironmentClassifier ADR (GG-027)** | T1 and T4 archetype register wired (SESSION 50). Remaining scope: (a) EnvironmentClassifier module in C2 — game-level pressure score (elimination_flag, series_momentum, crowd_premium, role_expansion_flag for role players with expanded duties); (b) archetype × environment uncertainty multiplier in C3 (wider confidence interval for sparse-data role players in high-pressure contexts); (c) dynamic MIN_EDGE_TO_APPROVE per environment class in decision tree routing; (d) T2/T3/T5 archetype register wiring matching T1/T4 pattern. Requires new ADR before activation. | Pre-MLB activation |
| **8 — ✅ DONE (SESSION 58)** | **T-166: PIPE-03 idempotency guard — same game_date re-execution (GG-028)** | Per-ticker `_open_tickers` guard shipped S53 (`d6283b1`). Run-level game_date guard shipped S58 (`a361898`): `_game_date_guard_fired` flag set before per-player loop; blocks C4+placement while YES-only counterfactuals still log. Events: `paper_run_game_date_guard_active` + `paper_run_skipped_already_deployed`. 5 new `TestGameDateRunLevelGuard` tests. 857/857. VPS `a361898`. GG-028 fully closed. | ✅ 2026-06-12 |
| **9 — ✅ DONE (prior session — stale entry removed S68 cont.)** | **T-167: MC script rewrite (GG-029 RESOLVED)** | `scripts/run_monte_carlo.py` portfolio mode: reads `paper_portfolio.json`, kelly=0.25/min_edge=0.04 from risk.py (ADR-0020), builds bets from committed `model_p`/`direction`/`mid_price_at_entry`/`size_usd`. Done; see DONE section below. | ✅ |
| **10 — ✅ DONE (SESSION 55)** | **T-168: MC portfolio mode — correlate within-player threshold ladders (GG-030 RESOLVED)** | `simulate_portfolio()` now draws one Poisson score per player; `_infer_lambda()` fits lambda via least-squares on (threshold, model_p) pairs. Bug found+fixed: initial NO-bet inversion. G5 MC: P(profit)=98.3%, kill-switch risk=1.28%, mean P/L=+$244.23. Deployed to VPS. Commit `530e1c3`. | ✅ 2026-06-12 |
| **11 — ✅ DONE (SESSION 56)** | **T-169 (GG-031 RESOLVED): book reconciliation — 9 twin annotations** | DS ruling Option A: 9 late-cron resting positions annotated `duplicate_of` on VPS. EXP-017B/018 reruns exclude twins from per-market n. Double exposure stands ($402.49). "01:00 UTC trigger" = scheduled 01:30 UTC late PIPE-03 window. Backup `paper_portfolio.json.bak_t169`. | ✅ 2026-06-12 |
| **12 — ✅ DONE (SESSION 55)** | **T-170: T4 ledger reconciliation (GG-032 RESOLVED)** | `paper_portfolio_t4.json` corrected on VPS: `bankroll_usd` 1869.68→478.41, `initial_bankroll_usd` 1000→500. Root cause: ADR-0022 `_reconstruct_t4_ledger()` wrote T1 system bankroll to T4 file. True T4 pool = $478.41. Note: do NOT cite T4 "+87% growth" narrative — it was based on the wrong field. Backup at `paper_portfolio_t4.json.bak_t170`. | ✅ 2026-06-12 |

| **12b — ✅ DONE (SESSION 65)** | **T-173: Fix healthcheck.sh false alarms — wrong Python path** | Added `PYTHON="$PROJ/venv/bin/python"` to healthcheck.sh preamble (matches `PYTHON=` in `deploy/cron.conf:16`). Replaced all 5 occurrences of `/usr/local/bin/python3.11` with `$PYTHON`. Checks 1 (Python/OpenSSL), 2 (sklearn), 3 (model), 7 (Kalshi API) will now use the real VPS venv. No functional impact on trading crons. | ✅ 2026-06-22 |
| **13 — ✅ DONE (SESSION 63)** | **T-171: Untrack live portfolio state from git + deploy HEAD verification (GG-033 RESOLVED)** | Executed 2026-06-15 in the same deploy as T-174. `logs/paper_portfolio.json` untracked (`git rm --cached` + `.gitignore`); VPS tree clean; `git pull` no longer clobbers the live book; deploy verified via `git log -1` (HEAD `52607f2`). `paper_portfolio_t4.json` was already untracked. Deploy was MANUAL (GHA aborts on pre-existing untracked VPS files). ✅ 2026-06-15. *(Original runbook retained below for reference.)* `deploy.yml` GHA auto-deploy workflow WRITTEN (SESSION 59). T-171 migration runbook below. Execute on Jun 14+ after G5 resolves and zero open positions confirmed. **Migration sequence:** (1) VPS backup: `ssh prediction-market-vps "cp /opt/prediction-market-bot/logs/paper_portfolio.json /opt/prediction-market-bot/logs/paper_portfolio.json.bak_t171 && cp /opt/prediction-market-bot/logs/paper_portfolio_t4.json /opt/prediction-market-bot/logs/paper_portfolio_t4.json.bak_t171"`. (2) VPS clean working tree: `ssh prediction-market-vps "cd /opt/prediction-market-bot && git checkout HEAD -- logs/paper_portfolio.json logs/paper_portfolio_t4.json"`. (3) Local: `git rm --cached logs/paper_portfolio.json logs/paper_portfolio_t4.json && echo "logs/paper_portfolio.json" >> .gitignore && echo "logs/paper_portfolio_t4.json" >> .gitignore`. (4) Commit + push → `deploy.yml` fires, VPS does `git pull` (which deletes the checked-out tracked files from working tree). (5) VPS restore: `ssh prediction-market-vps "cd /opt/prediction-market-bot && cp logs/paper_portfolio.json.bak_t171 logs/paper_portfolio.json && cp logs/paper_portfolio_t4.json.bak_t171 logs/paper_portfolio_t4.json"`. (6) Verify: `ssh prediction-market-vps "cd /opt/prediction-market-bot && git log -1 --oneline && python3 -c 'import json; p=json.load(open(\"logs/paper_portfolio.json\")); print(\"bankroll:\", p[\"bankroll_usd\"], \"open:\", len(p[\"open_positions\"]))'`. **Do NOT push deploy.yml before T-171 sequence completes** — auto-deploy fires on push and will abort on dirty VPS tree. | Dark period Phase 1, post-G5 resolution (Jun 14+) |
| **13b — ✅ DONE (SESSION 63) — GG-034 RESOLVED** | **T-174: Fix realized-P&L accumulator desync + blind drawdown kill switch (GG-034)** | **DEPLOYED + LIVE BOOK CORRECTED 2026-06-15** (operator OK). Code (ledger-derived `total_realized_pnl`+`bankroll_usd`, load-time `reconcile()`, cross-process `fcntl` lock, double-resolution guard) shipped to VPS HEAD `52607f2`; main book corrected `total_realized_pnl` −8.46 → **−251.21**, drawdown **25.12%**, kill switch un-blinded (code-path verified). C6 `portfolio_pnl_desync` EVT-4CED1860AFCB. T4 book needed no correction (already consistent). **Surfaced GG-035 (over-leverage, bankroll −$254.59) + GG-036 (G5 unresolvable, capital locked).** G6 baseline ratified at the true figure. DS retroactive-halt question folded into the post-season audit; kill switch now halts any future mutation at 25.12%. 965/965 tests. ✅ 2026-06-15. *(Original registration retained below.)* Live book `logs/paper_portfolio.json` stores `total_realized_pnl = −$8.46` (0.85% drawdown) but Σ of its 117 closed-position `pnl` = **−$251.21** (25.1%); C6 audit log corroborates −$251.21 with zero double-resolutions. The 20% `max_drawdown_pct` kill switch (`run_paper_trade.py:274` → `risk.py:418`), C7 monitor, C8 dashboard, and G6 positive-P&L gate all read the corrupted scalar → kill switch never fires on a true −25% loss; G6 gate is measured on a false number. **Root cause:** `total_realized_pnl` is a redundant scalar accumulator of a value derivable from Σ `closed_positions.pnl`, maintained under an in-process lock only while 4 runners (run_paper_trade, run_resolve, run_t4_live, run_t4_resolve_local) load→mutate→save the same JSON — concurrent last-write-wins clobbers increments. `bankroll_usd` also irreconcilable (cash identity implies +$134.00). Same desync in T4 book (stored −$21.59 vs Σ −$47.25). **Fix sequence (dark period, coordinate with T-171):** (1) make `total_realized_pnl` a derived property (Σ closed pnl), not a stored scalar; (2) add load-time reconciliation assert that fails loudly if stored ≠ derived; (3) add cross-process file lock (e.g. `filelock`/`fcntl`) around load→mutate→save on the shared JSON; (4) recompute `bankroll_usd` from initial + Σ pnl + open-position cash, reconcile against C6 audit log; (5) apply identical fix to `paper_portfolio_t4.json`; (6) **DS decision required:** does the true −25% drawdown retroactively halt paper trading / fail a kill-switch invariant, and what is the corrected G6 P&L baseline? Do NOT call G6 until the gate number is recomputed on truth. Supersedes the SESSION 57 "reconciles to the cent" claim. | Dark period Phase 1, post-G5, with T-171 |
| **14 — ✅ DONE (SESSION 72)** | **T-148 (REAFFIRMED S56): segmented promotion thresholds — ADR-0028 / APR-0022** | Initial draft (SESSION 65) declined by DS: "the segmentation for the promotion bands are still not fully aligned with the current structure per band." Root misalignment: ADR-0028 required T4 Tier 2 + T-AGG for G6 closure, but all T4 strategies are BLOCKED in BAND_REGISTRY (Phase 8+). G6 is a T1 live capital gate; T4 cannot generate evidence at Phase 6/7. **Rework completed (SESSION 65):** G6 closure condition reduced to T1-only (6 items). T4 Tier 2 (Mods 6, 7) + T-AGG (Mod 8) moved to new "T4 Activation Gate" section (Phase 8 pre-requisite). Mods 5 (fill-realism) and 9 (YES-only gate) remain at G6 scope. G6_GATE_CHECKLIST.md updated: I-4 corrected ("T4 BLOCKED"), T4 Tier 2 and T-AGG sections re-scoped to T4 Activation Gate. **DS sign-off granted SESSION 72 (Earl Ignacio 2026-06-22):** ADR-0028 ACCEPTED — all 14 checklist items approved. GG-022 RESOLVED. | ✅ 2026-06-22 SESSION 72 |
| **15 — ✅ DONE (SESSION 58)** | **T-172: G6 gate checklist document** | `08_MODEL_RISK_GOVERNANCE/G6_GATE_CHECKLIST.md` created. Mechanical per-criterion checklist: APR-0017/0019 Tier 0–3 structure, all invariants (S46 equity nuance, eligible bets, per-bucket T2 independence), formal gate prerequisites (T-117, GG-014, GG-020, ADR-0005, APR-0008/0009), binding constraint summary. Current verdict: NOT READY — Tier 0 blocked (T0-A). | ✅ 2026-06-12 |

G5 status: game_date=2026-06-13, **41 bets placed** ($1,003.38 deployed, 29 primary + 12 late-cron twins annotated), bankroll $130.62. Corrected MC: P(profit)=98.3%, kill-switch risk=1.28% at $20 trigger. Resolve locally after game using run_resolve_local.py. **EXP-017B/018 G5 reruns** ready once resolved — EXP-018 now auto-excludes `duplicate_of` positions (deployed `9c91bd4`); use `--exclude-failed` for MC scenarios. **YES-only gate LIVE (S56):** `PAPER_YES_ONLY` defaults true in `run_paper_trade.py` + explicit in cron.conf; NO signals logged as `yes_only_gate_filtered` C6 counterfactuals; continuous diagnostic leg per DS ruling — deactivation requires DS ruling. Standing items: T-153 fill-realism haircut; T-156 (ADR-0012 amendment, scope expanded to include session-start bankroll anchoring behavior at low-bankroll states). **MLB build (GG-004 critical path) starts the session after the Finals end** — NBA sessions maximized until then (operator directive S56). **S57 reconciliation note (G6 evidence hygiene):** VPS book reconciles to the cent ($1000 − $848.73 + $134.00 − $154.65 = $130.62); but the S46 reset set free cash to $1,000 with $142.46 of G4 stakes still deployed → effective post-reset equity was $1,142.46. Any P&L computed as equity − $1,000 overstates by $142.46; T-172 checklist must use Σ position `pnl`, never equity − initial.

---

## SESSION 86 — COMPLETE (2026-06-24)

| Task | Status |
|------|--------|
| **T-190 Step 3: `run_t4_mlb_live.py` (PIPE-07 MLB)** | ✅ COMPLETE — 420-line T4 in-play loop. Binomial model `P(hits >= threshold | h_so_far, ba_l10, ab_remaining)` via exact CDF. `AB_PER_GAME_DEFAULT=3.7`. Isolated portfolio `paper_portfolio_mlb_t4.json`, T4_BAND_WEIGHT=0.27, kill switch `logs/t4_mlb_kill_switch.flag`. Ghost protection via StagedOrderStore. 45s poll cycle. BOT_ENV=paper + BOT_C4_ACTIVE=true guards. ESPN MLB scoreboard + summary APIs wired. |
| **`tests/test_run_t4_mlb_live.py`** | ✅ COMPLETE — 55 tests (TestBinomialPmf, TestPHitsGteThreshold, TestKillSwitch, TestComputeT4BandBudget, TestExitBudgetCredit, TestReconstructT4Ledger, TestLoadPregameContext, TestEspnPollOnceMlb, TestRunCycle, TestConstants). All passing. Suite 1819→**1918/1918**. |
| **`deploy/cron.conf` PIPE-07 MLB block** | ✅ COMPLETE — 22:00 UTC `timeout 21600` cron line added (paused). Comment block matches PIPE-07 NBA pattern. PIPE-05 PAUSED comment updated to "MLB arm complete but awaiting post-deploy validation." |
| **T-190 OVERALL** | ✅ COMPLETE — all 3 steps done (Step 1: `run_mlb_pregame.py` S85/86, Step 2: `run_t3_mlb_pretip.py` S85/86, Step 3: `run_t4_mlb_live.py` this session). MLB arm fully built. |
| **DECISION_LOG SESSION 86** | ✅ COMPLETE — implementation-only session entry written. |

**NEXT SESSION: Deploy to VPS + enable MLB accumulation.** (1) `scp src/prediction_market_bot/run_t4_mlb_live.py prediction-market-vps:/opt/prediction-market-bot/src/prediction_market_bot/`. (2) `scp tests/test_run_t4_mlb_live.py prediction-market-vps:/opt/prediction-market-bot/tests/`. (3) `scp deploy/cron.conf prediction-market-vps:/opt/prediction-market-bot/deploy/`. (4) Run 55 tests on VPS. (5) Uncomment all 5 MLB cron lines (PIPE-06pre + PIPE-05 + PIPE-05R + PIPE-05FX + PIPE-07). (6) `crontab /opt/prediction-market-bot/deploy/cron.conf`. MLB accumulation LIVE at $1,000 fresh bankroll (0 open, 0 closed).

---

## SESSION 85 — COMPLETE (2026-06-24)

| Task | Status |
|------|--------|
| **MLB arm audit — CLAUDE.md T4 corrected** | ✅ COMPLETE — `CLAUDE.md:53` replaced. Was: "T4/T5: In-play — future; post-G6" (factually wrong — caused every session to treat T4 as nonexistent). Now: 4-line accurate status: (1) NBA T4 = PIPE-07, deployed, cron-scheduled, dark (off-season); (2) MLB T4 = NOT built; (3) ADR-0029 Tier A `t4_execution_engine.py` = Phase 8 BLOCKED; (4) T5 = not built. |
| **MLB cron PAUSED** | ✅ COMPLETE — All 4 MLB cron lines commented out in `deploy/cron.conf` with "PAUSED — S85: MLB arm incomplete" reason. Commit `aab7337`. VPS deployed; crontab reinstalled. MLB accumulation suspended. |
| **T-190 REGISTERED** | ✅ REGISTERED — 3-step MLB arm completion sequence. Must be done in order (T3 and T4 both depend on pregame JSON): Step 1: `src/prediction_market_bot/run_mlb_pregame.py` → `logs/pregame_mlb_YYYYMMDD.json`. Step 2: `src/prediction_market_bot/run_t3_mlb_pretip.py` (PIPE-06 MLB, `*/15 20-23` + `*/15 0-3`). Step 3: `src/prediction_market_bot/run_t4_mlb_live.py` (PIPE-07 MLB, `0 23 * * * timeout 21600`). All 3 must pass tests on VPS before any MLB cron is re-enabled. |
| **Monte Carlo simulation (June 26 slate)** | ✅ RUN — 15 games, ~1,231 quoted markets. Combined threshold 0.1186+0.04=0.1586 above mid → only 3.4 bets/night (T1 only). MC finding directly motivated MLB T4 audit: T4 (unbuilt for MLB) is what provides design-throughput target of ~1,000 evals/game. |
| **MLB bankroll preserved at $1,000 fresh start** | ✅ CONFIRMED — 0 open, 0 closed. VPS `paper_portfolio_mlb.json` confirmed. Do NOT resume until T-190 complete. |
| **DECISION_LOG SESSION 85** | ✅ COMPLETE — 4 entries appended: CLAUDE.md T4 correction, MLB cron pause, T-190 registration, accountability finding (missed T4 gap when asked "clean, green, on auto"). |

**CRITICAL FOR NEXT SESSION:** T-190 Step 1 first — build `run_mlb_pregame.py`, then T3, then T4. Do not re-enable MLB cron until all 3 complete.

| Priority | Task | Details |
|----------|------|---------|
| **✅ DONE (SESSION 85/86)** | **T-190 Step 1: `src/prediction_market_bot/run_mlb_pregame.py`** | Generates `logs/pregame_mlb_YYYYMMDD.json`. Maps MLB players→T1 forecasts→KXMLBHIT tickers. COMPLETE. |
| **✅ DONE (SESSION 85/86)** | **T-190 Step 2: `src/prediction_market_bot/run_t3_mlb_pretip.py`** | PIPE-06 MLB. CONFIRM/FADE/NEUTRAL momentum scan. Writes `logs/t3_mlb_YYYYMMDD_HHMM.json`. COMPLETE. |
| **✅ DONE (SESSION 86)** | **T-190 Step 3: `src/prediction_market_bot/run_t4_mlb_live.py`** | PIPE-07 MLB. 45-second evaluation loop. Binomial model. 55 tests. 1918/1918 passing. COMPLETE. |
| **P0 — NEXT** | **VPS deploy + MLB cron activation** | (1) scp `run_t4_mlb_live.py` + test file + `cron.conf` to prediction-market-vps. (2) Run 55 T4 MLB tests on VPS. (3) Uncomment 5 MLB cron lines in `deploy/cron.conf` (PIPE-06pre 16:30, PIPE-05 23:30, PIPE-05R 06:30, PIPE-05FX 22:30, PIPE-07 MLB 22:00). (4) `ssh prediction-market-vps "crontab /opt/prediction-market-bot/deploy/cron.conf"`. MLB accumulation restarts at $1,000 fresh bankroll. |

---

## SESSION 84 — COMPLETE (2026-06-25)

| Task | Status |
|------|--------|
| **T-189 — PIPE-05 three-concern remediation** | ✅ COMPLETE — All three operational failures from PIPE-05 first run (23:31 UTC 2026-06-24) fully resolved. 29 new tests in `tests/test_t189_mlb_pipe05_fixes.py`. Suite 1790→**1819/1819**. |
| **Concern 1: Contamination guard fires every night** | ✅ FIXED — `GAME_DATE = (datetime.now(tz=UTC) + timedelta(days=1)).date()` — T1 night-before baseline. Tomorrow's games always "Preview" at 23:30 UTC. Market date filter added: `if _ticker_to_game_date(m.ticker) == GAME_DATE_ISO:` — prevents in-progress today's Kalshi markets from leaking through. |
| **Concern 2: `paper_portfolio_mlb.json` never created** | ✅ FIXED — `PaperTrader.ensure_persisted()` — no-op if file exists, calls `_save()` otherwise. Called in `run_mlb_paper_trade.py` immediately after PaperTrader construction. `_load_or_init()` reverted to NOT write disk (preserves `_reload_locked` invariant — 10 unit tests would have failed). |
| **Concern 3: SP overlay / starters cache destroyed nightly** | ✅ FIXED — (a) hydrate fix: `probablePitcher,team` returns HTTP 200 on DO VPS; `venue` hydrate returns 406 from Fastly CDN — removed. (b) PIPE-05FX cron: removed `starters_2026.json` and `pitcher_logs_2026.parquet` from nightly bust; only `batter_logs_2026.parquet` and `completed_games_2026.parquet` busted. |
| **MLB portfolio reset to $1,000** | ✅ DONE — Fresh start on VPS. 0 open, 0 closed, bankroll=$1,000.00. |
| **Monte Carlo validation** | ✅ PASS — Feature matrix 21,716 rows/419 players (latest 2026-06-24). Model 18 features. 9/9 June 25 games SP data confirmed via live fetch. Contamination guard passes for 2026-06-25. ensure_persisted() present. hydrate no-venue. VERDICT: CLEAN, GREEN, ON AUTO. |
| **Test suite: 3× T-3 passes** | ✅ 1819/1819 (0 failures, 1 skip) — three consecutive clean runs confirmed. |
| **VPS deploy** | ✅ DEPLOYED — HEAD confirmed; crontab reinstalled; portfolio reset. |
| **DECISION_LOG SESSION 84** | ✅ COMPLETE — T-189 entry appended (all 5 architectural decisions + `_reload_locked` invariant + hydrate Fastly finding + cache bust scope + portfolio reset rationale). |

---

## SESSION 83 — COMPLETE (2026-06-24)

| Task | Status |
|------|--------|
| **T-188 — MLB bloomberg-terminal curses TUI dashboard** | ✅ COMPLETE — `scripts/run_mlb_dashboard.py` rewritten as full curses TUI matching `live_terminal.py` architecture. Panels: portfolio (fixed), system (fixed, 4 PIPE timestamps + KS), live_pos, today_slate, resolved, alerts, pipe_log. Background SSH ControlMaster thread (`/tmp/pmbot-mlb-ssh-ctl`). GG-034 P&L helper preserved. Run: `python3 scripts/run_mlb_dashboard.py --remote root@157.230.91.33 --log-dir /opt/prediction-market-bot/logs/`. Commits: 42bce66. No new tests (UI). |
| **MLB accumulation declared LIVE** | ✅ DECLARED — PIPE-05 first run tonight 23:30 UTC. Docs updated (MEMORY_BANK, TODO_NEXT, DARK_PERIOD_PLAN, DECISION_LOG). 5-6 weeks ahead of original August plan. |
| **pyarrow VPS install** | ✅ DONE — 24.0.0 installed before 22:30Z PIPE-05FX cron. Required for parquet cache operations. |
| **Monte Carlo 2026-06-25 slate** | ✅ RUN — Engine hygiene verified: C4 risk engine, calibration identity, YES-only gate, SP overlay fallback, GG-034 P&L all correct. GG-004 caveat applies to EV outputs. |
| **Tests** | ✅ 1790/1790 (unchanged from S82). |
| **VPS HEAD** | ✅ 42bce66 (deployed via osascript Terminal launch). |
| **DECISION_LOG SESSION 83** | ✅ COMPLETE — T-188, MLB live declaration, Monte Carlo entries appended. |

---

## SESSION 82 — IN PROGRESS (2026-06-24)

| Task | Status |
|------|--------|
| **T-187E — `run_resolve_mlb.py` (PIPE-05R)** | ✅ COMPLETE — MLB paper position resolution pipeline. `PaperTrader.settle_position()` added (sport-agnostic; stat_label="actual_hits" for MLB, default "actual_pts" for NBA backward compat). `run_resolve_mlb.py` (new): MLB Stats API gameLog fetch, Regular→Postseason fallback, full resolve loop, C7 monitor, C6 audit. `deploy/cron.conf` corrected: feature refresh renamed PIPE-05FX; PIPE-05R properly assigned to MLB resolve at 06:30 UTC. 34 new tests in `tests/test_t187e_mlb_resolve.py`. Suite 1704→**1737/1737**. |
| **T-187F — `scripts/run_mlb_calib_monitor.py` (PIPE-05C)** | ✅ COMPLETE — MLB calibration monitor. Reads `paper_portfolio_mlb.json` closed positions; computes ECE per threshold (t∈{1,2}; t=3 excluded per GG-042); derives recommended temperature T via `minimize_scalar` on log-loss; reports reliability buckets; anti-predictive check (edge>0 cohort win rate vs edge≤0). T_global derived on combined dataset for statistical power; per-threshold diagnosis reuses T_global to avoid underfitting. Exit codes: 0=CALIBRATED/insufficient, 1=MISCALIBRATED (ECE>0.05), 2=ANTI_PREDICTIVE. Does NOT write to `calibration.py` — temperature changes require ADR. `deploy/cron.conf` PIPE-05C entry: Mondays 14:10 UTC. 35 new tests in `tests/test_t187f_mlb_calib_monitor.py`. Suite 1737→**1772/1772**. |
| **Tests** | ✅ 1790/1790 (0 failures, 1 skipped). |
| **VPS deploy** | ✅ DEPLOYED — 7ca79b9 live; 1789/1789 VPS (2 skipped). |
| **DECISION_LOG SESSION 82** | ✅ COMPLETE — T-187F + T-187G + T-187H entries appended. |
| **T-187G — Live SP overlay for t=3 reconsideration** | ✅ COMPLETE — `run_mlb_paper_trade.py` modified: `_safe_int`, `_SP_OVERRIDE_FIELDS`, `_build_live_sp_override`, `_build_mlb_feature_vector(sp_override=)`. Fetches tonight's actual SPs via `MLBIngestionClient.fetch_game_starters`; looks up opposing SP per player from `team_id`; fetches L5 stats via `MLBPitcherStatsStore`; overrides `opp_sp_*` fields in feature vector at inference time. Falls back to historical SP stats on API failure. 18 new tests (+5 `TestSafeInt`/`TestSpOverrideFields`, +5 `TestBuildMLBFeatureVectorSpOverride`, +8 `TestBuildLiveSpOverride`). Suite 1772→**1790/1790**. |
| **T-187H — t=3 shadow gate re-evaluation (GG-042 resolution)** | ✅ COMPLETE — **VALID NEGATIVE — structural finding confirmed.** GG-042 resolution condition required re-running T-187B with t=3 after T-187G (live SP overlay) completed. Re-evaluation run on full 3-season feature matrix (`exp_output/MLB/mlb_feature_matrix.csv`, 126,421 rows, holdout cutoff 2026-01-01). SP coverage prerequisite verified: 99.9% of t=3 events (h≥3) have `opp_sp_is_known=1` in training data — the GG-042 data quality premise was DISPROVED. Shadow gate outcome: t=3 Brier delta=+0.0002 (FAIL — same as T-187B), ECE=0.0037 (PASS), AUC=0.6141. Score distribution: p50=0.037 (≈ 3.9% base rate); only 487/25,021 holdout predictions exceed 0.08 (Kalshi market price = 1.9%). Root cause is structural: at 3.9% base rate, even AUC=0.61 cannot produce absolute Brier delta ≥0.001 — this is an information-theoretic ceiling, not a data quality problem. **No code changes.** `THRESHOLDS = [1, 2]` and `_EXCLUDED_THRESHOLDS = [3]` in `train_mlb_model.py` unchanged; `_MODEL_THRESHOLDS = frozenset({1, 2})` in `run_mlb_paper_trade.py` unchanged. Tests: 1790/1790 (unchanged). GG-042 status updated to DEFERRED — structural. DECISION_LOG entry appended. |

---

## SESSION 81 — IN PROGRESS (2026-06-24)

| Task | Status |
|------|--------|
| **T-187C — Kalshi client MLB fix** | ✅ COMPLETE (prior session) — `kalshi_client.py` updated to fetch `KXMLBHIT` series markets. Confirmed correct ticker. |
| **T-187A — `generate_mlb_features.py`** | ✅ COMPLETE (prior session) — Script builds MLB feature matrix (3 seasons: 2024/2025/2026) with C6 audit trail. Supports `--seasons` arg for VPS-only 2026 refresh. Cache-resumable. |
| **T-187D — `run_mlb_paper_trade.py`** | ✅ COMPLETE (prior session) — MLB paper runner wired to KXMLBHIT markets, MLB C2/C3 inference, fresh `logs/paper_portfolio_mlb.json` ($1,000 book), C4 risk engine, C6 audit. `MLB_PAPER_YES_ONLY` gate mirrors NBA YES-only policy. Tests: suite 1650→1704/1704 (+54). |
| **PIPE-05 + PIPE-05R cron wired** | ✅ COMPLETE (prior session) — `deploy/cron.conf` updated: PIPE-05 at 23:30 UTC (MLB bet window), PIPE-05R at 22:30 UTC (daily 2026-only feature refresh with cache buster). Crontab installed on VPS. |
| **MLB Stats API IP-blocking (operational constraint found)** | ✅ DOCUMENTED — VPS (DO 157.230.91.33) gets HTTP 406 from Fastly CDN for seasons ≤2025. Season 2026 accessible. Constraint: feature matrix for training must be generated locally → scp to VPS. Daily PIPE-05R refresh uses `--seasons 2026` only. Annual retraining workflow: local full generation + scp. DECISION_LOG entries written. |
| **DECISION_LOG SESSION 81 entries** | ✅ WRITTEN (prior session) — MLB Stats API IP-blocking finding + PIPE-05 scheduling rationale both logged. |
| **Commits/VPS deploy** | ✅ PUSHED — `eef69e5` (main T-187 build) + `2f1798b` (PIPE-05R + IP-blocking docs). VPS crontab installed. |
| **T-187B — Per-threshold architecture (pooled model ECE failure fix)** | ✅ COMPLETE — Per-threshold LR+Platt deployed. Shadow gate PASS on VPS (t=1: ECE=0.0134 PASS, Brier delta=+0.0055 PASS; t=2: ECE=0.0106 PASS, Brier delta=+0.0022 PASS). t=3 excluded (GG-042). Artifact `models/mlb_v1_model.joblib` + `mlb_v1_model_meta.json` saved on VPS. Commit `953fd20` pushed. |
| **Tests** | ✅ 1704/1704 (all passing including per-threshold architecture changes). |

---

## SESSION 80 — COMPLETE (2026-06-24)

| Task | Status |
|------|--------|
| **T-117 — GG-006 RESOLVED: Kalshi Participant Agreement formal read** | ✅ COMPLETE — Three Kalshi legal documents formally read via pypdf. (1) Member Agreement v1.54: no automation restrictions; security obligation only. (2) Rule 5.13(s): source agency insider trading restriction only — inapplicable to Earl. (3) Rule 5.15 + Rulebook: behavioral market conduct rules only; single algorithm mention targets Kalshi's own affiliated market makers, NOT retail members. Position Limits: MOOT per DS ruling (MLB bankroll fresh $1,000; $500 max_bet_usd per position). ADR-0005 GG-006 pre-requisite satisfied; GG-006 CLOSED in GOVERNANCE_GAP_LOG.md. |
| **DS book-reset decision logged** | ✅ LOGGED — MLB paper book = fresh $1,000 separate pool. NBA 26-27 book Options A/B/C remain open per SESSION 74. DECISION_LOG SESSION 80 entry written. |
| **T-186 — F-042 fix: COMPLETE (valid negative finding)** | ✅ COMPLETE — Root cause: `nba_api.TeamGameLog` omits `PLUS_MINUS` for all season types → `pts_allowed` NaN everywhere → F-040 and F-042 both dead features (imputed 0.0). Fix: `pull_playoff_teamgamelog.py` now uses `_fill_pts_allowed_via_crossref()` to look up opponent PTS across team logs; 338/338 games populated (22 teams). Retrain: F-042 76/103 playoff training rows non-NaN (73.8%). v2b Brier improvement: **+0.000130 (required ≥0.001)**. Shadow gate: FAIL. **Outcome: F-042 provides insufficient signal at available sample size. Deploy v2-065b9510 in October as planned (ADR-0031).** 10 new cross-reference tests (TestPtsAllowedCrossRef). Suite 1640→**1650/1650** green. DECISION_LOG SESSION 80 T-186 entry written. |
| **T-187 REGISTERED** | ✅ REGISTERED — `scripts/run_mlb_paper_trade.py` MLB paper trading runner needed before August 2026. Requires: KXMLBHIT market fetching, MLB C1/C2/C3 integration, fresh $1,000 `logs/paper_portfolio_mlb.json` book. No cron entries for MLB in `deploy/cron.conf` (expected; needed before August). |
| **DECISION_LOG SESSION 80 entries** | ✅ COMPLETE — T-117/GG-006 entry + T-186 entry written. CLAUDE.md rule 7. |
| **Tests** | ✅ 1650/1650 (+41 this session: 31 T-186 + 10 cross-ref). |
| **VPS deploy** | ✅ COMPLETE — Commit 89d795c pushed + VPS deployed (HEAD confirmed). |

---

## SESSION 79 — COMPLETE (2026-06-23)

| Task | Status |
|------|--------|
| **T-184 — EXP-017 MLB commercial validation script** | ✅ COMPLETE — `scripts/run_exp017_mlb.py` (new, standalone). `tests/test_t184_exp017_mlb.py` (new, 99 tests). Three analysis layers: (1) EV analysis: EV/bet, win rate, YES/NO split. (2) ADR-0024 tier checks: Tier 1 (n≥150, EV<-$0.03→DIAGNOSTIC_SPRINT), Tier 2 single (n≥500), Tier 2 multi (--nba-n≥150 AND n≥150). EV verdict: CONFIRMED_POSITIVE/DIRECTIONAL_POSITIVE/CONFIRMED_NEGATIVE/DIRECTIONAL_NEGATIVE/DIAGNOSTIC_SPRINT/INCONCLUSIVE. (3) Edge monotonicity: Fisher's exact / chi-squared fallback, ANTI-PREDICTIVE/MONOTONIC/INCONCLUSIVE. MLB threshold breakdown: EV and win rate by k=1/2/3. `compute_fee_net_edge`: YES=model_p−mip−0.07×mip×(1−mip), NO symmetric. CI mode exit codes: 0/2/3/4. Reads `logs/paper_portfolio_mlb.json` by default; `--csv` for batch backtest. MLB position schema contract: requires `model_p`, `threshold`, `outcome`, `pnl`; `fee_net_edge` optional (computed if absent). Portfolio currently empty (August paper trading start); returns INCONCLUSIVE. |
| **tests/test_t184_exp017_mlb.py** | ✅ 99 new tests, all passing. 12 classes: TestKalshiFee (7), TestComputeFeeNetEdge (6), TestComputePnlUnit (6), TestLoadPortfolio (8), TestLoadCsv (5), TestDeduplicate (6), TestEvStats (4), TestThresholdBreakdown (8), TestAdr0024TierCheck (11), TestEvVerdict (7), TestEdgeMonotonicity (8), TestTercileTable (4), TestFisherPvalue (3), TestEndToEnd (11), TestConstantsAndSportLabel (5). Suite 1510 → **1609/1609**. |
| **VPS deploy** | ✅ COMPLETE — git pull + venv install (commit 94882f8, T-183 artifacts; T-184 follows next push). |
| **DECISION_LOG SESSION 79 entry** | ✅ COMPLETE — CLAUDE.md rule 7. |

---

## SESSION 78 — COMPLETE (2026-06-23)

| Task | Status |
|------|--------|
| **T-183 — MLB C3 model training infrastructure** | ✅ COMPLETE — `scripts/train_mlb_model.py` (new). `tests/test_t183_mlb_c3.py` (new, 77 tests). `HOLDOUT_CUTOFF = "2026-01-01"` fixed before training; anti-gaming holdout split. Shadow gate: null baseline (`brier_null = p*(1-p)`, gate `brier_delta >= 0.001 AND ece <= 0.05`). `_build_mlb_target`: each game row → 3 rows (one per threshold k ∈ {1,2,3}); `threshold` as float feature; `y_target = (h >= k)` as Int8/NA. `_NON_FEATURE_MLB` frozenset: excludes raw `h` (leakage), `ab`, other box-score outcomes, metadata, C1 audit cols, training artifacts. Pipeline matches `forecaster.py:354-358` exactly (`StandardScaler → CalibratedClassifierCV(LR, method="sigmoid", cv=3)`). Artifact schema: `{pipeline, feature_names, col_medians, model_version, thresholds: [1,2,3], sport: "mlb"}` — matches NBA loader contract. `_mlb_model_version()`: "mlb-v1-" + sha1[:8] deterministic hash. `calibration.py` confirmed: `CALIBRATION_TEMPERATURE["mlb"] = 1.0` (identity; T-176 deferred). BOT_C4_ACTIVE test contamination: `run_paper_trade.py:59` sets env var at import time; `test_t3_integration.py` triggers import; all `TestEndToEndDryRun` tests fail in full suite. Fix: autouse monkeypatch fixture clears `BOT_C4_ACTIVE` per-test in that class. |
| **tests/test_t183_mlb_c3.py** | ✅ 77 new tests, all passing. 11 classes: TestBuildMlbTarget (13), TestComputeEce (5), TestImpute (4), TestMlbModelVersion (5), TestExtractFeatureMatrix (8), TestNonFeatureSet (10), TestNullBaseline (3), TestShadowGateLogic (6), TestModelArtifact (4), TestEndToEndDryRun (14), TestMultipleThresholds (5). Suite 1433 → **1510/1510**. |
| **DECISION_LOG SESSION 78 entry** | ✅ COMPLETE — CLAUDE.md rule 7. |
| **VPS** | Deploy follows commit+push (governance artifacts + train_mlb_model.py + test file). |

---

## SESSION 77 — COMPLETE (2026-06-23)

| Task | Status |
|------|--------|
| **T-182 — MLB C2 baseball feature set** | ✅ COMPLETE — `src/prediction_market_bot/c2_feature_store/mlb_features.py` (new). `MLB_FEATURE_VERSION = "1.0.0"`. TI-01: `.shift(1).rolling(min_periods=3)`. Rolling L10 batter features via sum-then-divide (ba/slg/obp/ops/h_mean/k_rate/bb_rate/hr_rate). Context: days_rest, b2b_flag, temporal_cutoff. SP overlay MANDATORY: opp_sp_era_l5/k9_l5/bb9_l5/is_known from MLBPitcherStatsStore (L5 starts, min_periods=2, TI-01; K9/BB9 via total ÷ total IP). Park factors: 30-venue static dict (Coors=1.120, Oracle=0.970, unknown→1.000). Opponent: opp_runs_allowed_l10 from MLBTeamStatsStore. Metadata: feature_run_id (prefix "C2MLB-"), feature_version, train_test_label. C6: 5 audit events (derivation_start/complete/error, temporal_integrity_warning, train_test_split_applied). assign_train_test_labels: NaT rows → None (TI-02 excluded); others → TRAIN/VALIDATION/TEST. `_ip_to_decimal()` IP notation fix confirmed in C1 ("5.2" = 5+2/3 = 5.667). |
| **tests/test_t182_mlb_c2.py** | ✅ 60 new tests, all passing. Suite 1373 → **1433/1433**. 5 test classes: TestIpToDecimal (11), TestParkFactorTable (4), TestComputeRollingBatterFeatures (16), TestComputeFeaturesBulk (23), TestAssignTrainTestLabels (5). Key lesson: `np.allclose(series.values, value)` required for float comparisons with pandas (pytest.approx + .all() fails silently). |
| **DECISION_LOG SESSION 77 entry** | ✅ COMPLETE — CLAUDE.md rule 7. |
| **VPS** | Deploy follows this session (governance artifacts + mlb_features.py + test file). |

---

## SESSION 69 — COMPLETE (2026-06-22)

| Task | Status |
|------|--------|
| **DS decision: Option C — feature-set diagnosis sprint** | ✅ LOGGED — DECISION_LOG S69 entry written. Diagnosis conducted on n=103 clean NBA Finals bets. Root cause identified: missing playoff-context λ multiplier. Three feature fixes scoped into T-072. If EXP-017 still ANTI-PREDICTIVE after fix, escalation = Option A. |
| **Feature-set diagnosis (run_t177 Option C sprint)** | ✅ COMPLETE — Key findings: (1) YES bets 38.9% win rate vs NO bets 68.7%. (2) Model error on YES: +0.315 (vs market +0.150); market error on NO: +0.006 — Kalshi is essentially perfectly calibrated on NO bets. (3) Implied λ compression: model assumes λ=14.0/16.1/19.6 at thr=10/15/20; actual scoring implies λ=12.8/12.8/13.8 → compression factors 0.911/0.792/0.703. (4) Within-series compression worsens: G2 avg_pts=17.3 → G5 avg_pts=7.7 as game plans adapt. Root cause: opp_adj_lambda uses regular-season defensive ratings; Finals defensive intensity suppresses scoring 9-30% beyond what the model accounts for. (5) This is a feature engineering gap, NOT a model class failure. Poisson architecture is valid; the λ input is wrong. |

---

## SESSION 68 — COMPLETE (2026-06-22)

| Task | Status |
|------|--------|
| **T-180 Phase 2 — T4 execution engine scaffold** | ✅ COMPLETE — `t4_price_cache.py`: `T4Phase8BlockedError`, `STALENESS_WINDOW_S` (T4-EVENT=2s, T4-LINEUP=5s, all others=30s), `CachedPrice` frozen dataclass, `T4PriceCache` with test-injectable `update()`/`get_raw()`/`is_fresh()`/`get_price()`/`purge()`/`market_count()` + blocked `start_polling()`/`stop_polling()`. `t4_execution_engine.py`: `GamePhase` enum (EARLY/MID/LATE/NEAR_CERTAIN via elapsed_min), `T4PlayerState`/`T4GameEvent`/`T4GameState` frozen dataclasses, `EvaluationSignal`, `QueueEntry` (EXIT=0.0 priority, higher-edge first), `StaleDropRecord`, 8 `SubBandEvaluator` stubs (all BLOCKED, all return `[]`), `T4CorrAdjuster._assert_downward_only()` Principle-6 invariant, `T4ExitEvaluator`, `Layer1EvaluationEngine` event-type dispatch routing (6 event maps), `Layer2ExecutionQueue` heapq with 3-drop-condition staleness arbitration (price_stale / edge_below_min / direction_reversed), `T4ExecutionEngine._PHASE8_ACTIVE=False` class-level gate. `simulate_cycle()` test-usable at Phase 6/7; `on_game_event()`/`start()` raise `T4Phase8BlockedError`. `DECISION_LOG.md` T-180 Phase 2 entry appended (rule 7). |
| **tests/test_t4_engine.py** | ✅ 109 new tests, all passing. Suite 999 → **1108/1108**. Covers: phase classification boundaries, staleness enforcement per sub-band, priority ordering, all 3 drop conditions, downward-only invariant, Phase 8 blocking on all live paths, simulate_cycle→Layer2 end-to-end integration. |
| **T-177 Part (a) — edge inversion monitor** | ✅ COMPLETE — `scripts/run_t177_edge_monitor.py` (415 lines) + `tests/test_t177_edge_monitor.py` (29 tests). Suite 1108 → **1137/1137**. Reads `logs/paper_portfolio.json` or `--csv` path; Fisher's exact test; ANTI-PREDICTIVE/MONOTONIC/INCONCLUSIVE verdict; `--ci` exit codes for pipeline integration. Live VPS result (n=144 clean): p=0.0505 → ANTI-PREDICTIVE. DS decision (A/B/C escalation path) OPEN. |
| **Governance cleanup** | ✅ — T-167 stale priority-queue entry removed (task was done in prior session; DONE section confirms). T-175 confirmed DONE (`run_t4_live.py:682` already patched). Phase 2 dark period tasks (T-072/T-073/T-077/ADR-0005) surfaced as ACTIVE (NBA Finals ended 2026-06-22; Phase 2 starts July 1). DECISION_LOG S68 cont. entry added. |

---

## SESSION 67 — COMPLETE (2026-06-22)

| Task | Status |
|------|--------|
| **T-179 SCOPED — ADR-0029 pre-sign-off alignment review + four corrections** | ✅ COMPLETE — operator-requested adversarial review of S65/66 T4 work, then scoped-down per authorization. **(1) T4-MICRO carved out → ADR-0030 (placeholder created):** no `model_p`, distinct execution-quality strategy class; taxonomy 11→**10 sub-bands**. **(2) Two-tier acceptance:** Tier A (architecture/principles/mechanisms/gate structure) frozen on sign-off; Tier B (sub-band roster + all numerics + alpha hypotheses) provisional, revisable via DECISION_LOG until per-sub-band Activation Gate. Resolves ADR-immutability vs unvalidated-specifics tension. **(3) T4-PROJ NEAR-CERTAIN Kelly anomaly:** inverse-variance formula diverges at low σ_λ (k=0.526 @ 46min); 0.25 is a hard ceiling not a derived value; NEAR-CERTAIN held ≤0.167 pending EXP-PROJ-01 tail calibration; same applied to T4-ARITH 0.22. **(4) DS quote attribution** corrected to paraphrase (handoff l.23) pending DS confirm. Standing rationale recorded: T4 architecture is strategy-agnostic scaffolding ("beat the situation, not the market"); edge math is a separate workstream (T-177). DECISION_LOG + ADR Index updated (rule 7). **ADR-0029 ACCEPTED — DS sign-off Earl Ignacio, 2026-06-22 SESSION 67. Tier A frozen; Tier B provisional.** No code changes. |
| **ADR-0030 — T4-MICRO carve-out placeholder** | ✅ REGISTERED (PLACEHOLDER, not drafted). `03_DECISIONS/ADR-0030_t4-micro-execution-quality-strategy.md`. Documents why T4-MICRO is a distinct no-model strategy class + the 7 items a future drafting session must resolve before it can be considered. Dormant until DS elects to take it up. |
| **Tests** | ✅ 988/988 (no code changes this session — design/governance only) |

## SESSION 66 — COMPLETE (2026-06-22)

| Task | Status |
|------|--------|
| **T-179 (SESSION 66) — ADR-0029 DRAFTED: T4 sub-band architecture** | ✅ DRAFT COMPLETE — ACCEPTED SESSION 67 (DS sign-off Earl Ignacio, 2026-06-22). Full 804-line architecture document written: 11 sub-bands (T4-MICRO, T4-STAGED, T4-EVENT, T4-LINEUP, T4-FLOW, T4-SENTIMENT, T4-PROJ, T4-ARITH, T4-BOUNDARY, T4-CORR, T4-EXIT), three-layer execution architecture, immediate execution principle, dynamic game-phase Kelly schedule for T4-PROJ (supersedes ADR-0010 monolithic T4=0.20), FLOW-BLOWOUT as blowout-consequences architecture, T4-CORR convergence signal formalization, budget partitioning (shared pool within T4_BAND_WEIGHT=0.27). Three amendments: ADR-0010 T4 superseded, ADR-0014 T4 section superseded, ADR-0018/ADR-0019 T4 noise buffer superseded. ADR-0028 T4 Activation Gate PLACEHOLDER completed. Three new governance gaps: GG-038 (T4 kill switch ≤5s, Phase 8 prereq), GG-039 (T4 price cache, Phase 8 prereq), GG-040 (T4 real-time data sources, Phase 8 prereq). DECISION_LOG entry written (CLAUDE.md rule 7). **Code changes in execution_bands.py, t4_execution_engine.py, t4_price_cache.py, c7 kill switch: BLOCKED pending DS sign-off on ADR-0029.** |
| **GG-038/039/040 REGISTERED** | ✅ COMPLETE — GOVERNANCE_GAP_LOG.md updated with three new Phase 8 prerequisite gaps. |
| **Tests** | ✅ 988/988 (no code changes this session — design-only) |
| **VPS** | ✅ HEAD `97e66ae` unchanged (no code deploy — governance artifacts only) |

---

## SESSION 65 — COMPLETE (2026-06-22)

| Task | Status |
|------|--------|
| **T-173 (SESSION 65) — healthcheck.sh false alarms fixed** | ✅ COMPLETE — Added `PYTHON="$PROJ/venv/bin/python"` to healthcheck.sh preamble; replaced all 5 `/usr/local/bin/python3.11` occurrences. Checks 1/2/3/7 now use real VPS venv. No functional trading impact. |
| **T-154 (SESSION 65) — CHANGE_CONTROL.md decisions extracted** | ✅ COMPLETE — Four framework decisions extracted to DECISION_LOG.md Notable Judgment Calls: three-tier classification scheme; SKELETON→ACTIVE Class A requirement; no emergency risk-limit override; conditional-language escalation rule. `decisions_logged: true` set in CHANGE_CONTROL.md header. |
| **T-178 (SESSION 65) — market_mapper.py MLB pre-flight audit** | ✅ COMPLETE — Architecture claim VERIFIED: C4/C6/C7/C8 are sport-agnostic; C5 NBA defaults are caller-supplied (expected); `KXNBAPTS` series ticker is C5-layer, not a C4–C8 violation. Pre-documented constraints C-1 (threshold int type) and C-2 (sport-partitioned runs) stand. |
| **T-148 (SESSION 65) — ADR-0028 rework** | ✅ REWORK COMPLETE — ACCEPTED SESSION 72 (DS sign-off Earl Ignacio, 2026-06-22). Root cause: T4 strategies BLOCKED in BAND_REGISTRY (Phase 8+); G6 is T1 gate; requiring T4 evidence was architecturally wrong. Rework: G6 closure reduced to T1-only (6 items); Mods 6/7/8 (T4 Tier 2 + T-AGG) moved to new T4 Activation Gate (Phase 8 pre-requisite). Mods 5+9 at G6 scope. G6_GATE_CHECKLIST I-4 corrected. APR-0022 updated. **T-148 DONE; GG-022 RESOLVED.** |
| **T-179 (SESSION 65) — T4 sub-band segmentation registered** | ✅ REGISTERED — DS directive: "In-game trading can't be clumped as one aggregate bucket." T4 spans sub-ms execution (pure order-book speed, no model) through multi-minute model-driven holds. T-179 is the next-session design task: taxonomy, `execution_bands.py` split, ADR-0029, ADR-0028 T4 Activation Gate rewrite. DECISION_LOG updated with DS verbatim. ADR-0028 T4 Activation Gate section blocked. |
| **Tests** | ✅ 988/988 (no code changes this session) |
| **VPS** | ✅ HEAD `97e66ae` (governance-only; no code deploy needed) |

---

## SESSION 64 — COMPLETE (2026-06-16)

| Task | Status |
|------|--------|
| **GG-036 RESOLVED — G5 41 positions resolvable** | ✅ COMPLETE — re-froze the 158-bet NBA Finals dataset (`data/nba_finals_clean_dataset.csv`); G5 outcomes sourced (NOT fabricated); capital unlocked. Full-DB assessment ran on this set. |
| **GG-035 RESOLVED (structural) — ADR-0026 / APR-0020** | ✅ COMPLETE — C4 two-tier portfolio free-cash invariant: CHECK 8a solvency KILL (`Σopen+size > equity`), 8b policy REJECT (`> 0.60×equity`; 60% = `1−RESERVE_MANDATE_PCT`). Base = equity (stricter underwater). C4 stays pure via `PaperTrader.exposure_snapshot()`; fail-safe skip when equity=None. Forensic: G5 $1003.38 unreachable (cap $449.27). `risk.py`, `paper_trader.py`, `tests/test_c4_risk.py`. **Coverage gap: only callers passing the snapshot are guarded — run_t4_live / EXP harnesses unguarded → T-175.** |
| **GG-037 RESOLVED (calibration half) — ADR-0027 / APR-0021** | ✅ COMPLETE — C3 temperature scaling `p_cal=σ(logit(p)/T)` on the **production Poisson prob** (root cause: overdispersion, var>mean; Platt is NOT the production prob → re-fit would have been a no-op). `calibration.py` per-sport registry, fail-safe identity T=1.0 (MLB cannot inherit NBA shrink). NBA T=2.05 (OOS-validated, fit G2–G4/test G5; in-sample optimum 3.10 — conservative chosen). Wired at single prob site in `run_paper_trade.py`; `p_estimate_raw` retained for audit. `scripts/derive_calibration.py` re-derives + monitors. 14 new tests. |
| **GG-037 alpha half — DISPROVED miscalibration; STAYS OPEN** | 🔴 OPEN — recalibration corrected overconfidence but edge is **anti-predictive post-calibration**: edge>0 winrate 0.356 vs edge≤0 0.747; highest-edge tercile 0.346 vs lowest 0.792. Edge inversion survives calibration → no demonstrated alpha vs the Kalshi price. GG-004 unrelieved. Deferred to EXP-017 at scale (MLB dark period + NBA regular season). → T-177. |
| **G6 gate checklist updated** | ✅ — T2-A (T1) 🔴 MEASURED-FAILED (19.8pp > 15pp raw; ADR-0027 reduces to ~6pp but historical book traded uncalibrated). T2-C (T1) 🟡 MEASURED (Brier 0.2308 ≤0.265 PASS but masks the calibration failure — do not read as health). |
| **Deploy** | ✅ Committed `897ff4d`, pushed origin/main, VPS HEAD `897ff4d`; calibration verified live (NBA 0.97→0.845, MLB identity). No live behavior change — book halted at drawdown kill switch (25.12% > 20%); CHECK 2 fires before CHECK 8/calibration matters. |
| **Tests** | ✅ 988/988. |

**New tasks registered this session (added to priority queue):**
- **T-175 — ✅ DONE (confirmed S68 cont.):** `run_t4_live.py:682` already passes `portfolio_equity_usd=t4_band_budget if not PAPER_T4_VIRTUAL else None, pool_isolated=True` to `evaluate_forecast()` (T-175 comment on line 671). EXP harnesses are pure analysis — no `evaluate_forecast()` calls. Coverage gap closed.
- **T-176 — HIGH (dark period Phase 3, before MLB launch):** MLB calibration temperature derivation. Run `scripts/derive_calibration.py` on the dark-period MLB resolved dataset once it exists; write the derived T into `CALIBRATION_TEMPERATURE["mlb"]` via an ADR-0027 amendment (currently identity 1.0). **Blocked on MLB data — will unblock in Phase 3 (Aug-Sep).**
- **T-177 — ✅ COMPLETE (SESSION 73, 2026-06-23):** Monitor built (1137 tests, S69). v2 backtest INCONCLUSIVE (p=0.1639 all / p=0.3131 clean, n=114). Phase 3 gate OPEN. Original ANTI-PREDICTIVE finding (p=0.0505, n=144 clean CSV) used full dataset including G5 (June 13); these positions absent from live portfolio JSON — full n=144 replication pending future data pull. GG-037 alpha half + GG-004 still OPEN (require EXP-017 at ADR-0024 adequate sample). Script: `scripts/run_t177_v2_backtest.py`.
- **PHASE 2 NOW ACTIVE (NBA Finals ended 2026-06-22 — July 1 start):**
  - **T-072 — ✅ COMPLETE (SESSION 73, 2026-06-23):** All three parts done. Part A: FEATURE_VERSION 1.4.0 + F-041/F-042/F-043 in C2 (1293 tests). Part B: retrain v2-065b9510 (Brier Δ=+0.001507, ECE=0.0426, shadow gate PASSED). Part C: T-177 INCONCLUSIVE (p=0.1639). ADR-0031 ACCEPTED. **ONE ITEM DEFERRED:** deploy v2 model to VPS + kill switch reset — action at 2026-27 season start (dark period; operator action required). See ADR-0031 acceptance checklist.
  - **T-073 — P1:** DS-04 injury source. KI-011: T2 is injury-blind; without DS-04, T2 activation generates fake alpha. Required before T2 active. Evaluate: Rotoworld / FantasyLabs / ESPN API injury reports.
  - **T-077 — P1 (operator action):** Polymarket KYC. VenueAdapter already built; execution gated on operator KYC completion. Second venue adds line-shopping (+7.8% EV per EXP-014).
  - **ADR-0005 — P2 (draft now, finalize at G6):** Live capital framework parameters. Draft can begin (bankroll size, per-bet limits, reserve fraction, kill-switch thresholds at live scale). Cannot finalize until EXP-017 positive + T-153 haircut complete.

- **PHASE 3 — MLB COMMERCIAL VALIDATION (August–September 2026) — GATE OPEN (T-072 ✅ + T-177 INCONCLUSIVE ✅):**
  - **T-181 — ✅ COMPLETE (SESSION 75, 2026-06-23):** MLB C1 data ingestion module. **DS data source decision:** MLB Stats API (statsapi.mlb.com) via raw HTTP requests; `requests` now explicit in `pyproject.toml`. Three new C1 source files: `mlb_ingestion.py` (`MLBIngestionClient` — `fetch_batter_game_log`, `fetch_pitcher_game_log`, bulk variants, `fetch_game_starters`, `fetch_completed_games`; all `(bool, DataFrame|dict)`; C6 audit trail; 0.6s throttle; `_team_abbr_map` injection for test isolation), `mlb_team_stats_store.py` (`MLBTeamStatsStore` — `get_opp_runs_allowed`/`get_opp_runs_scored`, `build_from_games()`, TI-01, cache), `mlb_pitcher_stats_store.py` (`MLBPitcherStatsStore` — `get_era_l5`/`get_k_per_9_l5`/`get_bb_per_9_l5` via total ER÷IP, relief exclusion, TI-01, cache). IF-C1-C2 contract: batter 24-col schema, pitcher 22-col schema, game starters gamePk dict. `kalshi_client.py`: `SERIES_MLB_PLAYER_HITS = "KXMLBHITS"` placeholder (**UNCONFIRMED** — verify via `GET /series` before MLB paper trading; wrong ticker → empty markets silently, same failure mode as KI-019). 80 new tests (`tests/test_t181_mlb_c1.py`, 0 live HTTP). 1373/1373 total green. DECISION_LOG SESSION 75 entry written.
  - **T-182 — ✅ COMPLETE (SESSION 77, 2026-06-23):** MLB C2 baseball feature set. `src/prediction_market_bot/c2_feature_store/mlb_features.py` (new): `MLBFeatureStore`, `_compute_rolling_batter_features`, `assign_train_test_labels`. `MLB_FEATURE_VERSION = "1.0.0"`. TI-01: `.shift(1).rolling(min_periods=3)`. Rolling (L10): `ba_l10`, `slg_l10`, `obp_l10`, `ops_l10`, `h_l10_mean`, `k_rate_l10`, `bb_rate_l10`, `hr_rate_l10` (sum-then-divide pattern). Context: `days_rest`, `b2b_flag`, `temporal_cutoff`. SP overlay (MANDATORY): `opp_sp_era_l5`, `opp_sp_k9_l5`, `opp_sp_bb9_l5`, `opp_sp_is_known`. Park: `park_factor_hits` (30-venue dict; Coors=1.120; unknown→1.000). Team: `opp_runs_allowed_l10`. Metadata: `feature_run_id` (prefix "C2MLB-"), `feature_version`, `train_test_label`. C6: 5 audit events. `_ip_to_decimal()` IP notation fix confirmed in C1. `tests/test_t182_mlb_c2.py` (60 tests, 5 classes). 1433/1433 total green. DECISION_LOG S77 entry written.
  - **T-183 — P0 (next):** MLB C3 model training. LR + Platt on MLB player props data (HR/hits/strikeouts O/U thresholds on Kalshi). New model version per ADR-0004 feature-version policy. Separate sport registry entry in `calibration.py` (`CALIBRATION_TEMPERATURE["mlb"]` — currently identity; derive via T-176 once resolved data exists). Chronological holdout split (TI-02 per ADR-0031 precedent). Shadow gate (ADR-0009): Brier improvement over null + ECE ≤ 0.05 on holdout.
  - **T-183 — P0:** MLB C3 model training. LR + Platt on MLB player props data (HR/hits/strikeouts O/U thresholds on Kalshi). New model version per ADR-0004 feature-version policy. Separate sport registry entry in `calibration.py` (`CALIBRATION_TEMPERATURE["mlb"]` — currently identity; derive via T-176 once resolved data exists). Chronological holdout split (TI-02 per ADR-0031 precedent). Shadow gate (ADR-0009): Brier improvement over null + ECE ≤ 0.05 on holdout.
  - **T-184 — P0 (commercial validation gate):** EXP-017 MLB run. Backtest MLB model edge vs actual Kalshi MLB market prices — this is the ADR-0024 commercial validation experiment. ADR-0024 Tier 1 check fires at n≥150 unique MLB markets; if EV/bet < −$0.03 at Tier 1: diagnostic sprint per ADR-0024. Tier 2 floor: n≥500, ≥15 opponents. GG-004 remains OPEN until CONFIRMED_POSITIVE at adequate sample.
  - **T-186 — ✅ COMPLETE (SESSION 80) — Valid negative finding:** F-042 fix implemented and retrained. Root cause confirmed: `nba_api.TeamGameLog` returns no `PLUS_MINUS` → `pts_allowed` NaN for all rows → F-040 and F-042 both imputed to 0.0 in all prior training. Fix: cross-reference pts_allowed from opponent PTS (implemented in `pull_playoff_teamgamelog.py`). v2b retrain: F-042 73.8% populated; Brier delta +0.000130 < required 0.001. **Shadow gate FAIL — valid negative.** Deploy v2-065b9510 in October (ADR-0031). 41 new tests (test_t186_v2b_retrain.py); 1650/1650 green. DECISION_LOG SESSION 80 T-186 entry written.
  - **T-176 — HIGH (companion to T-183):** MLB calibration temperature derivation. Run `scripts/derive_calibration.py` on MLB resolved dataset; write derived T into `CALIBRATION_TEMPERATURE["mlb"]` via ADR-0027 amendment. **BLOCKED until MLB data exists and positions begin resolving.**

- **PHASE 4 — PRE-SEASON PREP (October 2026):**
  - **T-185 — P0 (DS decision required before execution):** v2 model deploy + paper trading restart + kill switch reset. **Three prerequisite DS decisions:** (1) NBA 26-27 paper book reset decision: Option A (fresh $1,000), B (continue $751.10), or C (fresh $1,000 with archive) — DECISION_LOG SESSION 74 entry documents the options. (2) Model to deploy: if T-186 completes before October, deploy v2b (F-042 populated) instead of v2-065b9510 (F-042 NaN). (3) Starting pitcher overlay scope: confirm T-182 starting pitcher features are wired before MLB paper trading activates. **Alpha framing (non-negotiable before deploy):** v2 shadow gate PASSED means Brier improved and ECE ≤ 0.05 — model calibration improved. It does NOT mean alpha vs Kalshi prices is confirmed. EXP-017 at adequate sample (ADR-0024) is the alpha gate; GG-004 and GG-037 remain OPEN. Deploying v2 in October is an evidence-collection decision, not a confirmed-alpha deployment. **Runbook (execute in this order):** Step 1 — confirm zero open positions on NBA T1 book; Step 2 — execute DS book-reset decision (A/B/C above); Step 3 — `scp models/v2_model.joblib models/v2_model_meta.json prediction-market-vps:/opt/prediction-market-bot/models/`; Step 4 — `ssh prediction-market-vps "cd /opt/prediction-market-bot && venv/bin/python3 -c 'import joblib; m=joblib.load(\"models/v2_model.joblib\"); print(\"loaded\")'"`; Step 5 — run `deploy/healthcheck.sh` on VPS — all checks green; Step 6 — manual PIPE-03 batch run on Day 1 regular season game; Step 7 — confirm bets placed (not rejected by kill switch or model load error); Step 8 — mark ADR-0031 final checklist `[ ]` item complete. **DS must witness Step 7 before the system is considered restarted.**
  - **T-116 — HIGH (before 2026-27 tip-off, Oct 20):** Pre-season multi-game night pipeline stress test. Regular season has 10+ simultaneous games (400+ markets/night) vs Finals single-game context. PIPE-02 and PIPE-03 untested at this scale. Simulate a 10-game night locally before season start. Verify: (1) `run_pregame.py` captures pregame logs for all cohort players across simultaneous games without silent failures; (2) PIPE-03 processes all players without timing collisions; (3) EXP-017 join succeeds on simulated multi-game pregame directory. See backlog T-116 entry for full test plan.
  - **T-127 — Day 1 action:** Orderbook depth query. Run `scripts/query_orderbook_depth.py` on 2026-27 regular season Day 1 to capture live depth for 3–5 active KXNBAPTS contracts. Input to ADR-0005 `max_order_pct_of_depth` hard limit. GG-041.

- **T-178 — ✅ DONE (SESSION 65):** `market_mapper.py` / C1–C2 MLB pre-flight audit — architecture claim VERIFIED: C4/C6/C7/C8 sport-agnostic; C5 NBA defaults are caller-supplied (expected); `KXNBAPTS` series ticker (C-3) is C5-layer, not a C4–C8 violation. Pre-documented constraints C-1 (threshold int type) and C-2 (sport-partitioned runs) stand.
- **T-179 — ✅ DONE (SESSION 67) — ADR-0029 ACCEPTED (DS sign-off Earl Ignacio, 2026-06-22):** Tier A frozen (immutable — hard rule #3): three-layer execution architecture, six design principles, immediate-execution/staleness-arbitration model, per-sub-band budget mechanism, T4 Activation Gate structure, kill-switch ≤5s requirement (GG-038). Tier B provisional (DECISION_LOG-revisable until each sub-band's Phase 8 Activation Gate): 10-sub-band roster, all Kelly fractions/noise buffers/exposure caps/numerics, alpha hypotheses. T4-MICRO carved to ADR-0030 (placeholder). T4 runtime stays BLOCKED/dark until GG-038/039/040 + Phase 8 activation ADR cleared. See DECISION_LOG S67 acceptance entry.
- **T-180 — HIGH (Phase 8 code implementation, post ADR-0029 Tier A sign-off) — PHASE 2 DONE (engine built S68); evaluator math + infra remain:**
  - ✅ **DONE (S67) — taxonomy:** `execution_bands.py` split — `T4_IN_PLAY` retained as aggregate parent; 10 sub-band `ExecutionBand` values (T4-MICRO excluded — ADR-0030) with per-sub-band `BandConfig`. `T4_SUBBANDS` tuple + `is_t4_subband()`/`t4_parent()`. Per-sub-band `NOISE_BUFFER` (`None`-fallback where EXP-required; `NOISE_BUFFER_BAND_T4=0.19` aggregate default). `T4SubBandSpec` + `T4_SUBBAND_REGISTRY` (all BLOCKED) + `validate_t4_subbands()`. PROJ/ARITH Kelly ≤0.167. Strategy K not redefined. Tests +11 → 999.
  - ✅ **DONE (S68) — the engine (substance of Tier A):** `t4_price_cache.py` (GG-039 architecture; `T4PriceCache` RLock, `STALENESS_WINDOW_S`, `T4Phase8BlockedError`; polling `start_polling` deferred to Phase 8). `t4_execution_engine.py` (`GamePhase`/`classify_game_phase`; `Layer1EvaluationEngine` event-dispatch; `Layer2ExecutionQueue` heapq EXIT-priority + 3 drop conditions [price_stale/edge_below_min/direction_reversed]; 8 BLOCKED sub-band evaluator stubs each guarded by `_assert_sub_band_blocked()`; `T4ProjEvaluator.get_lambda_posterior()` cross-evaluator hook; `T4CorrAdjuster._assert_downward_only` Principle-6; `T4ExecutionEngine._PHASE8_ACTIVE=False`, `simulate_cycle()` test-usable, `start()`/`on_game_event()` raise blocked). `tests/test_t4_engine.py` +109. **Tests → 1108 passing; all execution paths verified blocked.**
  - ✅ **DONE (S70) — sub-band evaluator math:** `T4ProjEvaluator`: Gamma-Poisson conjugate Bayesian update (`_gamma_prior_params`, `_gamma_poisson_update`, `_poisson_survival_p`), phase-conditional Kelly schedule (EARLY=0.010/MID linear 0.032-0.078/LATE linear 0.078-0.167/NEAR_CERTAIN cap 0.167). `T4ArithEvaluator`: arithmetic threshold-window logic. `T4EventEvaluator`: event-triggered scoring. `T4FlowEvaluator`: sustained score-gap detection (blowout). `T4ExitEvaluator`: EXIT-TIME-FLOOR/EXIT-REVERSAL/EXIT-BUFFER-BREACH. Layer1 ordering fix: T4-PROJ prepended to `ordered_ids` (frozenset unordered). 185 tests in `test_t4_engine.py`. **WARNING (λ prior bias): `lambda_t1_prior` = `opp_adj_lambda` calibrated on regular-season data; same Finals scoring-suppression documented in S69 diagnosis still affects T4-PROJ. T-072 must fix before T4-PROJ activation.**
  - ✅ **DONE (S71) — live execution path design:** `t4_live_runner.py` (new): `T4FastHalt` (GG-038 ≤5s, threading.Event), `T4PositionRegistry` (thread-safe, pool drawdown accounting), `T4PriceCacheUpdater` (GG-039 bootstrap REST 2s poll), `T4GameStateBuilder` (GG-040 bootstrap ESPN→T4GameState), `build_forecast_record()` (EvaluationSignal→C4 dict with `kelly_fraction`), `T4LiveRunner` (C4/C5/C6/C7 wiring, pool-kill at 20% drawdown). `on_game_event()` implemented (Layer1+Layer2 returns tuple). `create_phase8()` factory (instance-level `_PHASE8_ACTIVE`). C4 `risk.py`: `kelly_frac = fc.get("kelly_fraction", self._kelly_fraction)` — backward-compat. 67 tests in `test_t4_live_runner.py`. **1280 total tests.**
  - ⬜ **REMAINING (Phase 8 ADRs — code is complete, ADRs needed to activate):** (1) GG-038 resolution ADR — T4FastHalt meets ≤5s design; ADR must sign off design + confirm SLA via test harness before `_PHASE8_ACTIVE=True`. (2) GG-039 resolution ADR — `T4PriceCacheUpdater` REST bootstrap design done; WebSocket production path requires sub-ADR. (3) GG-040 resolution ADR — `T4GameStateBuilder` ESPN bootstrap done; NBA Stats live play-by-play replacement requires sub-ADR. (4) Phase 8 activation ADR — calls `T4ExecutionEngine.create_phase8()`; wires `T4LiveRunner`; sets `_PHASE8_ACTIVE=True`. Until then: BLOCKED/dark.
  - **Per-sub-band roster + numerics are Tier B (provisional) — implement against the architecture (Tier A), not against frozen sub-band values.** Tier A signed off by DS (Earl Ignacio) 2026-06-22 S67. T4 runtime stays BLOCKED/dark until GG-038/039/040 + Phase 8 activation ADR cleared.

---

## SESSION 56 — COMPLETE (2026-06-12)

| Task | Status |
|------|--------|
| **T-169 (GG-031 RESOLVED): Option A twin annotations** | ✅ COMPLETE — 9 VPS positions annotated `duplicate_of`; EXP-018 dedupe filter deployed; close paths verified to preserve annotation. |
| **GG-033 registered + deploy recovery** | ✅ COMPLETE — VPS silently stuck at `cea8a19` since S55; recovered via backup-first dance; T-171 queued (untrack + GHA auto-deploy as one unit, post-G5). |
| **YES-only gate (S47/S56 DS ruling)** | ✅ LIVE — `PAPER_YES_ONLY` default-true in run_paper_trade.py + explicit in cron.conf; NO signals → C6 `yes_only_gate_filtered` counterfactuals; VPS crontab reinstalled. Continuous diagnostic leg; deactivation requires DS ruling. |
| **T-148 DS ruling** | ✅ LOGGED — Still G6 blocker; NOT absorbed by ADR-0024. Segmented per-band promotion thresholds + aggregate P&L/capital goal via APR-0017-superseding ADR. Priority queue item 14. |
| **GG-007 EXP ID collision** | ✅ FIXED — calibration experiments renumbered EXP-020/EXP-021. |
| **GG-004 scan visibility** | ✅ FIXED — status line reformatted; session-start grep now catches it. |
| **T-172 registered** | ✅ — G6 gate checklist doc (criterion/evidence/status), dark period Phase 1. |
| **T-152 census** | ✅ — 244 unique exited positions on VPS (≥50 floor comfortably met); empirical validation of 0.19 buffer runnable in Phase 1 regardless of Finals outcome. |
| **T-160 hygiene sweep** | ✅ COMPLETE — root folder cleaned; dead PAPER_T4_FLAT_SIZING scrubbed; budget sim formula fixed to ADR-0023. |
| **Tests** | ✅ 852/852. |

---

## SESSION 55 — COMPLETE (2026-06-12)

| Task | Status |
|------|--------|
| **T-168 (GG-030 RESOLVED): MC correlated simulation** | ✅ COMPLETE — `simulate_portfolio()` draws one Poisson score per player. `_infer_lambda()` fits lambda via least-squares on (threshold, model_p) pairs. Direction-invariant (NO bets use raw model_p). G5 MC deployed to VPS. |
| **GG-031 registered** | ✅ REGISTERED — 9 duplicated tickers ($402 doubled exposure), not 2. T-169 queued for DS ruling. |
| **GG-032 registered** | ✅ REGISTERED — T4 bankroll irreconcilable; ADR-0022 root cause identified. |
| **T-170 (GG-032): T4 ledger correction** | ✅ COMPLETE — `paper_portfolio_t4.json` on VPS: bankroll_usd→478.41, initial_bankroll_usd→500.0. Backup preserved. |
| **DECISION_LOG SESSION 55 entry** | ✅ COMPLETE |
| **MEMORY_BANK + TODO_NEXT updated** | ✅ COMPLETE |
| **Tests** | ✅ 851/852 (1 pre-existing timing flake in `test_compute_budget`; unrelated) |
| **VPS deploy** | ✅ COMPLETE — Commit `530e1c3` pushed and VPS `git pull` + scp confirmed. |

---

## SESSION 54 — COMPLETE (2026-06-11)

| Task | Status |
|------|--------|
| **Pre-Game-5 hygiene audit** | ✅ COMPLETE — All three Session 53 changes verified clean. No bugs found. |
| **T-166 idempotency verification** | ✅ VERIFIED — `open_positions` schema confirmed OPEN-only (paper_trader removes on close/exit). No status filter needed. `_open_tickers` rebuild per-market-iteration picks up intra-run placements correctly. |
| **T-164 cron timing verification** | ✅ VERIFIED — T3 staleness guard returns `{}` at 18:00 UTC (no T3 reports exist until 20:00 UTC). Primary cron correctly runs as pure T1. Late 01:30 UTC window receives T3 overlays from running games. Architecturally correct. |
| **T-167 MC formula verification** | ✅ VERIFIED — NO bet `win_odds = mid/(1-mid)` confirmed correct: Kalshi NO costs `(1-mid)`, collects $1, net `mid/(1-mid)` per dollar. `p_win = 1 - model_p` confirmed correct: model_p is P(≥threshold), NO wins when score < threshold. |
| **MEMORY_BANK + TODO_NEXT updated** | ✅ COMPLETE — This session. |

---

## SESSION 53 — COMPLETE (2026-06-11)

| Task | Status |
|------|--------|
| **T-166 (GG-028 RESOLVED): PIPE-03 idempotency fix** | ✅ COMPLETE — `run_paper_trade.py`: removed `if not str(p.get("kalshi_order_status", "")).startswith("failed:")` from `_open_tickers` set construction. All open positions block re-entry regardless of Kalshi order status. Root cause of G5 duplicate bets patched. |
| **T-164: Primary cron window shift 22:00→18:00 UTC** | ✅ COMPLETE — `deploy/cron.conf`: health check, T-140, PIPE-02 primary, PIPE-03 primary all shifted to 17:00/17:25/17:55/18:00 UTC. `PAPER_T4_FLAT_SIZING=true` synced to T4 entry. VPS crontab confirmed updated. |
| **T-167 (GG-029 RESOLVED): MC script rewrite** | ✅ COMPLETE — `scripts/run_monte_carlo.py`: portfolio mode default (reads `paper_portfolio.json`, kelly=0.25, min_edge=0.04); `--preview` flag preserves old behavior; `--exclude-failed`, `--yes-only`, `--no-only`, `--haircut` scenario flags; Bernoulli simulation using committed `model_p`. |
| **GG-028 RESOLVED in GOVERNANCE_GAP_LOG** | ✅ COMPLETE |
| **GG-029 RESOLVED in GOVERNANCE_GAP_LOG** | ✅ COMPLETE |
| **DECISION_LOG SESSION 53 entry** | ✅ COMPLETE |
| **VPS deploy** | ✅ COMPLETE — Commit `d6283b1`. 5 files, 419 insertions, 169 deletions. Crontab confirmed. |
| **Tests** | ✅ 852/852 pass |

---

## SESSION 52 — COMPLETE (2026-06-12)

| Task | Status |
|------|--------|
| **G5 portfolio MC** | ✅ COMPLETE — Direct MC on 41 committed positions: EV +$246.67 (24.6% ROI), P(profit)=99.8%, P(kill switch)=0.00%, p50 end bankroll=$382.40. MC script gap documented (GG-029). |
| **Second cron confirmed — GG-028 registered** | ✅ COMPLETE — 22:00 UTC batch (29 bets, expected) + 01:00 UTC batch (12 bets, unexpected, 0% failures). Duplicate Wemby NO 40/35 positions placed. T-166 registered. |
| **GG-014 final snapshot** | ✅ COMPLETE — 22:00 batch: 31% failure (unchanged from pre-T-164). 01:00 batch: 0% failure. T-164 fixes off-peak congestion; primary window still congestion-limited. GOVERNANCE_GAP_LOG updated. |
| **GG-029 registered** | ✅ COMPLETE — MC script analyzes pregame forecasts (kelly=0.1, min_edge=0.02) not committed positions. T-167 registered. |
| **DECISION_LOG SESSION 52** | ✅ COMPLETE |
| **Tests** | ✅ 852/852 pass (no code changes) |

---

## SESSION 51 — COMPLETE (2026-06-11)

| Task | Status |
|------|--------|
| **ADR-0024: Stop/Pivot Criterion (T-157)** | ✅ COMPLETE — `03_DECISIONS/ADR-0024_stop-pivot-criterion.md`. Tier 1 (n≥150): EV/bet < -$0.03 → diagnostic sprint. Tier 2 (structurally adequate sample): CONFIRMED_NEGATIVE → halt + ADR-0004 supersession. Passability drift watch: standing. GG-021 RESOLVED. |
| **DARK_PERIOD_PLAN.md ratified (T-158)** | ✅ COMPLETE — `04_EXECUTION/DARK_PERIOD_PLAN.md`. Four phases. Phase 3 (Aug-Sep): MLB C1/C2/C3 + EXP-017 MLB commercial validation. Phase 4 (Oct): GG-014 confirmation, G6 review, ADR-0005. |
| **EXP-017 scope transition — DS ruling** | ✅ COMPLETE — NBA Finals sample structurally insufficient. EXP-017 transitions to MLB 2026 + NBA 26-27 regular season. ADR-0024 defines structurally adequate sample standard. GG-004 status updated. |
| **GG-014 dark-period gap documented** | ✅ COMPLETE — T-164 deployed but G5 placed before fix. No additional PIPE-03 runs possible before dark period. GG-014 G6 gate confirmation deferred to 2026-27 Season Day 1. GOVERNANCE_GAP_LOG + DARK_PERIOD_PLAN Phase 4 updated. |
| **DECISION_LOG SESSION 51 entry** | ✅ COMPLETE |
| **Tests** | ✅ 852/852 pass (no code changes) |

---

## SESSION 50 — COMPLETE (2026-06-11)

| Task | Status |
|------|--------|
| **PAM archetype register — `get_archetype()` added to QualitativeSignalStore** | ✅ COMPLETE — `qualitative_store.py`: point-lookup method with QTI-01 temporal guard. Returns `{prf_primary, prf_primary_name, active_modifiers, prf_secondary/name/weight if hybrid}`. None if no snapshot or outside window. |
| **T1 archetype logging (`run_paper_trade.py`)** | ✅ COMPLETE — `_pam = qs.get_archetype(player_id, GAME_DATE_ISO)` per cohort player; `pam_archetype` field in `forecast_rec`; `[PRF-X]` tag in BET print output. Non-cohort players return None (no QS classification). |
| **T4 archetype register wiring (`run_t4_inplay.py`)** | ✅ COMPLETE — `QualitativeSignalStore` imported; `archetype_register` param added to `T4EventLoop.__init__`; `pam_archetype: dict | None = None` field added to `T4RoutingResult`; archetype looked up at event entry and propagated through all routing paths (FIRE_STAGED, FIRE_BAYESIAN, FIRE_T5, NO_ACTION). KILL_SWITCH path receives no archetype (intentional — routing halted before player context matters). |
| **GG-027 registered** | ✅ COMPLETE — Full T2/T3/T5 PAM integration + EnvironmentClassifier not built. LOW now (bands SKELETON/BLOCKED); HIGH pre-MLB activation. |
| **T-165 registered** | ✅ COMPLETE — Full band integration + env classifier ADR — MLB gate. |
| **DECISION_LOG SESSION 50 entry** | ✅ COMPLETE |
| **Tests** | ✅ 852/852 pass |

---

## SESSION 49 — COMPLETE (2026-06-11)

| Task | Status |
|------|--------|
| **ADR-0019-A01: NOISE_BUFFER_BAND_T4 0.139→0.19** | ✅ COMPLETE — EXP-019B/C empirical (G4, n=1199): observed mean=0.182, p50=0.187; EXP-019C p90 spread=0.170. T-152 update gate triggered (>20% deviation from analytic). Value set to 0.19: above p90 (0.170) and mean (0.182); within MEMORY_BANK recommendation ≥0.18–0.20. `execution_bands.py` updated. `test_t146_t147_exit_mechanics.py` updated (3 locations). DECISION_LOG ADR-0019-A01 entry added. |
| **T-164 Part 1: Kalshi retry parameters** | ✅ COMPLETE — MAX_RETRIES 3→4; RETRY_DELAY_S 1.0→2.0; delay schedule 4/8/16/32s=60s. Root cause: T-138's 14s total window insufficient for Kalshi rate-limit reset. `kalshi_client.py` updated. `test_kalshi_client.py` updated (backoff assertion [2.0,4.0]→[4.0,8.0]). |
| **T-164 Part 2: Inter-order sleep raised** | ✅ COMPLETE — sleep 0.5→2.0s in `paper_trader.open_position()`. 29 orders × 2.0s ≈ 58s batch time (acceptable for pre-game cron). |
| **PIPE-03 reserve mandate hygiene** | ✅ COMPLETE — Pre-run health check: deployed %, reserve floor $, bankroll, WARN >80%. Batch order integrity report: submitted/ok/failed/rate, WARN >5% (G6 gate). `run_paper_trade.py` updated. |
| **New test file: test_t164_order_throttle.py** | ✅ COMPLETE — 9 tests: TestRetryConstants (4: max_retries=4, retry_delay=2.0, post delay schedule 4/8/16/32s, get delay schedule, 60s window); TestInterOrderSleep (4: sleep 2.0s when client present, no sleep without client, no sleep without key, exactly 2.0s value). 852/852 total tests pass. |
| **DECISION_LOG SESSION 49 entry** | ✅ COMPLETE — ADR-0019-A01 + T-164 (both parts) + reserve hygiene. All four changes documented with derivation methodology. |
| **GOVERNANCE_GAP_LOG updated** | ✅ COMPLETE — GG-014 status: PARTIALLY RESOLVED. GG-017 T-152 update gate noted. |
| **MEMORY_BANK + TODO_NEXT updated** | ✅ COMPLETE — This session. |
| **VPS deploy** | ✅ COMPLETE — Commit d68d5c2 deployed. `git pull` on VPS: 11 files, fast-forward, DEPLOY OK. |

---

## SESSION 48 — COMPLETE (2026-06-12)

| Task | Status |
|------|--------|
| **G4 positions resolved** | ✅ COMPLETE — run_resolve_local.py: Brunson NO-40 WIN (+$8.57), Vassell NO-25 WIN (+$1.16), OG Anunoby NO-25 LOSS (-$18.20). Net -$8.46. VPS bankroll: $285.27. Portfolio synced. |
| **VPS portfolio discrepancy investigation** | ✅ COMPLETE — VPS has 32 open (3 G4 + 29 G5); local `logs/paper_portfolio.json` was stale pre-G5. G5 bets placed by T1 early cron Jun 11 for game_date=2026-06-13. VPS is authoritative. |
| **G5 YES-only gate** | ❌ NOT IMPLEMENTED PRE-G5 — G5 fired WITHOUT YES-only filter. 20 NO + 9 YES bets placed. G5 data analyzable post-hoc with YES/NO breakdown but not a clean YES-only test. **→ IMPLEMENTED SESSION 56 (2026-06-12): `PAPER_YES_ONLY` gate live in run_paper_trade.py (default true) + cron.conf; DS reaffirmed as continuous leg for all future batches.** |
| **Monte Carlo with ADR-0023 components** | ✅ COMPLETE — G5 MC: 29 bets, $848.73 deployed, EV +$209.70 (+24.71% ROI), P(profit)=97.5%, kill switch risk 0.10%. Reserve mandate exceeded (84.9% > 60%) but batch enforcement deferred. All bets match ADR-0023 parameters. |
| **T4 budget sim (ADR-0023 verification)** | ✅ RUN — Shows $302.89 budget (stale formula: uses RESERVE_MANDATE deduction). Correct ADR-0023 budget = $504.81 ($1,869.68 × 0.27). run_t4_budget_sim.py is stale (simulation tooling only; production run_t4_live.py is correct). |
| **GG-014 G5 update** | ✅ LOGGED — 9/29 = 31% failure rate. T-138 INEFFECTIVE at 29-order burst. T-164 registered. GG-014 status updated: G6 gate BREACHED. |
| **DECISION_LOG SESSION 48 entry** | ✅ COMPLETE — All 4 findings logged. ADR-0023 added to ADR Index. |
| **MEMORY_BANK + TODO_NEXT updated** | ✅ COMPLETE — This session. |

---

## SESSION 47 — COMPLETE (2026-06-11)

| Task | Status |
|------|--------|
| **T-163: ADR-0023 — Remove PAPER_T4_FLAT_SIZING; calibrate T4_BAND_WEIGHT (GG-026)** | ✅ COMPLETE — T4_BAND_WEIGHT=0.27 (G4 empirical: $499.95/$1,869.68). PAPER_T4_FLAT_SIZING + PAPER_T4_POOL_USD removed entirely. _compute_t4_band_budget single budget path (no RESERVE_MANDATE — T4 pool is isolated capital). pool_isolated=True hardcoded. Flat sizing (1 contract at mip) retained as hardcoded T4 paper policy. G5 budget: ~$504.81. ADR-0023 ACCEPTED. GG-026 RESOLVED. 4 test patches removed (test_t146_t147 × 4, test_t149 × 2 → removed 4 of those patches). 843/843 tests. Commit 72ba619, VPS deployed. |
| **EXP-018 Hypothesis C DS ruling** | ✅ RULED (SESSION 47) — DS: calibration gap. n=98, both all-bets and injury-filtered CONFIRMED_NEGATIVE. NOT T1 Tier 2B FAILS. Multi-sport scale (MLB/NFL) addresses sample size. G5 diagnostic: YES-only mode to isolate YES vs NO edge. |
| **EXP-019B empirical validation** | ✅ COMPLETE — TP rate = 0.281 (analytic predicted 0.799). DIVERGED. Root cause: market-lag assumption fails; Kalshi semi-efficient; mip and p_t4 move together. ADR-0019 Tier 2 OPEN. Script: `scripts/run_exp019b_empirical.py`. Results: `exp_output/EXP-019/EXP-019B_empirical_results.json`. |
| **EXP-019C spread model** | ✅ COMPLETE — p90 spread=0.170 > NOISE_BUFFER_BAND_T4=0.139. Buffer needs raising to ≥0.18–0.20. Results: `exp_output/EXP-019/EXP-019C_results.json`. |
| **DECISION_LOG SESSION 47 entry** | ✅ COMPLETE — ADR-0023 decision entry with full derivation methodology, all code changes, 843/843 test count, GG-026 RESOLVED. |
| **MEMORY_BANK + TODO_NEXT updated** | ✅ COMPLETE — This session. |

---

## SESSION 45 — G4 PRE-TIP SPRINT (2026-06-10)

| Task | Status |
|------|--------|
| **T1 stale daily-loss kill switch (G4 early cron fired KILL_SWITCH, 0 bets)** | ✅ FIXED — `run_paper_trade.py:261` date-reset guard (same class as a300a51, T1 path). Commit `b6cedd0`, deployed. Manual PIPE-03 recovery run 23:50 UTC: 33 bets, $757.69 deployed, 0 order failures (15 resting/18 executed — T-139 ≤5% met). |
| **Daily-loss net semantics (gross → net)** | ✅ DEPLOYED — `paper_trader._accumulate_daily_loss()`: wins offset losses; `current_daily_loss = max(0, -daily_net_pnl)`. Commit `424698a`. Tonight-critical: exits active → T4 gross losses would cross $150 mid-game. |
| **T-156: ADR-0012 amendment — formalize net daily-loss semantics + add accumulation tests** | ⬜ REGISTERED — no test covered accumulation (817 passed untouched by semantics change). Draft ADR amendment post-G4. |
| **T4 process restart with new code** | ✅ DONE — old process predated deploys; relaunched 00:00 UTC (PID 372067, timeout 18000). Note: first attempt left T4 down ~3 min (local tmp ENOSPC); verified recovery. |
| **Portfolio MC on actual G4 book (33 positions, N=100k)** | ✅ DONE — EV=+$152.08, P(profit)=95.3%, P(trip 20% system kill)=1.07%, worst sim -$310.69. Caveat: same model class missed G3. |
| **EXP-018 Hypothesis C — DS ruling** | ✅ DEFERRED to post-G4 EXP-018 rerun (DS: Earl, 2026-06-10). Rule at larger n tomorrow. |
| **DECISION_LOG SESSION 45 entries** | ✅ COMPLETE — both entries written. |

---

## SESSION 44 — COMPLETE

| Task | Status |
|------|--------|
| **T4 daily-loss stale-date kill switch bug** | ✅ FIXED — `run_t4_live.py:438`: `current_daily_loss=$157.89` from G3 would have fired kill switch on every G4 bet. Added date-check reset: when `portfolio_data.get("daily_loss_date") != today_str`, resets `current_daily_loss=0.0` before entering game loop. Commit `a300a51`, deployed to VPS. |
| **GHA post-game resolve workflow** | ✅ LIVE — `.github/workflows/post_game_resolve.yml` created. Root cause: nba_api 403-blocked on VPS (Akamai WAF) + Mac cron Mac-dependent. Fix: GHA runners (not blocked) run T1+T4 resolve at 05:30 UTC daily via `VPS_SSH_KEY` secret. SSH key written to `~/.ssh/id_ed25519_droplet` (matches hardcoded path in both resolve scripts). `continue-on-error: true` on each step. Both scripts idempotent (0 open positions → clean exit). Verified workflow_dispatch run 27253281067 (35s, all green). Commit `aa263fb`, deployed VPS. Mac `post_game_g4_resolve.sh` cron `0 23 10 6 *` remains as secondary fallback + experiment runner (EXP-017/018). **G4 fully automatic — no operator action required.** |
| **DECISION_LOG entries** | ✅ COMPLETE — Both SESSION 44 decisions logged: T4 stale daily-loss fix + GHA auto-resolve architecture. |
| **MEMORY_BANK + TODO_NEXT updated** | ✅ COMPLETE — This session. |

---

## SESSION 43 — COMPLETED (prior session)

| Task | Status |
|------|--------|
| **APR-0019 ACCEPTED** | ✅ DS: Earl — EXIT_MECHANICS_ACTIVE=True gate added to `run_t4_live.py`. |
| **GG-018 RESOLVED** | ✅ APR-0017 floor derivation amended; T-155 registered. |
| **Kalshi fee 0.07 partial verification** | ✅ GG-020: ≥2 sources support 0.07; T-151 open for receipt confirmation post-G6. |
| **EXIT_MECHANICS_ACTIVE=True deployed** | ✅ Committed + deployed VPS. |
| **MC adj_λ upgrade deployed** | ✅ run_monte_carlo.py updated with TSS adj_λ support. |

---

## SESSION 2026-06-08 SESSION 40 — COMPLETED

| Task | Status |
|------|--------|
| **T-141: PIPE-03 false kill switch root cause + fix (CRITICAL)** | ✅ COMPLETE — `run_paper_trade.py:558`: `daily_loss += approved_size if edge < 0 else 0` removed. NO bets always have `edge < 0` by convention; line was silently accumulating all NO stake sizes as daily losses. Root sequence: G2 realized losses ($130.08 from portfolio) + $43.03 NO stakes → $173.11 ≥ $150 threshold → kill switch. Fix: removed the spurious accumulation; `daily_loss` is loaded from `portfolio.current_daily_loss` only (set correctly by `close_position()`). 783/783 tests pass. |
| **T-142: live_terminal.py T4 log path fix** | ✅ COMPLETE — Both `_data_from_local()` and `_REMOTE_SCRIPT` updated from `t4_live.log` → `t4_live_cron.log`. Active T4 cron (PIPE-07, 23:00 UTC) writes to `t4_live_cron.log`; `t4_live.log` was stale from pre-cron manual run (last line 19:58 UTC). Dashboard now reads live T4 activity. |
| **T-143: run_t4_live.py crash guard** | ✅ COMPLETE — Main `while True` loop body wrapped in `try/except Exception`. ConnectionError/HTTPError no longer kills T4 process. Kill switch check remains OUTSIDE the guard (unbreakable). |
| **T-144: post_game_g3_resolve.sh — automated post-game deploy** | ✅ COMPLETE — `scripts/post_game_g3_resolve.sh` created. 5 steps: (1) T1 resolve, (2) T4 resolve, (3) SCP portfolio to local, (4) VPS git pull (idempotency fix), (5) EXP-017 Part B rerun. Scheduled via Mac crontab `0 23 8 6 *` (11 PM PDT Jun 8 → 06:00 UTC Jun 9). |
| **DECISION_LOG SESSION 40 entry** | ✅ COMPLETE — Entry written: (1) PIPE-03 false kill switch root cause and fix, (2) live_terminal log path, (3) T4 crash guard. |

## SESSION 42 — CURRENT

| Task | Owner | Priority | Notes |
|------|-------|----------|-------|
| **Worry 3: tmpfs ENOSPC fix** | — | ✅ DONE (this session) | `export CLAUDE_CODE_TMPDIR="/Users/earlignacio/.claude/tmp"` added to `~/.zshrc`. Step 1 documentation debt scan unblocked for next session. |
| **T-149: T4 C4 fee gate fix** | — | ✅ DONE (this session) | `run_t4_live.py` now computes `kalshi_fee = 0.07 * mip * (1.0 - mip)` and passes `net_edge` to C4 (not gross). `fc_record["gross_edge"]` preserved for `paper_trader.py` annotation. Approval dict carries both keys. 10 new tests in `tests/test_t149_t4_fee_gate.py`. 793/793 tests pass. GG-019 Part A resolved. **Deploy to VPS before G4 (cron Jun 10).** |
| **T-150: Aggregate fee break-even analysis** | — | ✅ DONE (this session) | Empirical from G2+G3 data. T4: $14.28/game (1,115 bets, avg mip=0.45, avg fee=$0.01281/contract); T1: $12.89/game avg (Kelly-sized, ~45 contracts/bet at paper bankroll). Combined ~$27/game Finals scale. Fee as % of gross EV: T4=4.4%, T1=8.2% — manageable. MIN_EDGE_TO_APPROVE=0.02 > max taker fee (0.0175 at mip=0.50) — C4 always enforces positive net edge post-T-149. ADR-0005 implication: fee structure documented; EXP-017 commercial validation still required before live capital. DECISION_LOG updated. GG-019 Part B resolved. |

---

## SESSION 41 — PRIOR (rolled up)

| Task | Owner | Priority | Notes |
|------|-------|----------|-------|
| **post_game_g3_resolve.sh — COMPLETE** | — | ✅ DONE 05:08Z | ALL STEPS OK. T1: 47 settled, bankroll $876.83, cumulative P&L $-123.17, 12.3% drawdown. T4: 215 positions, +$39.44, pool $1,539.42. EXP-017 Part B: DIRECTIONAL_POSITIVE (n=66). VPS idempotency fix deployed. |
| **MEMORY_BANK + GG-018 + T-148 logged** | — | ✅ DONE (this session) | G3 results, T4 first-run data, GG-018 registered in GOVERNANCE_GAP_LOG.md. |
| **T-148: APR-0017 ≥66-bet floor regression analysis** | DS | HIGH — required before G6 can be called | GG-018: APR-0017 floor derived T1-only; T4 live with 1,115 bets/game. Analysis needed: (1) which bet types count for which Tier evidence requirement; (2) does T4 need its own calibration floor; (3) re-derive statistical floor for mixed-model scenario. Output: ADR superseding or amending APR-0017 Tier 2 + statistical floor sections. Do NOT call G6 until resolved. |
| **T-146: Implement exit_position() in paper_trader.py** | — | ✅ COMPLETE 2026-06-09 SESSION 42 | `exit_position(position_id, exit_mip, p_current, exit_reason, session_id)` method added. YES/NO PnL formulas correct. pool_isolated flag propagated from open → exit (T4 paper: bankroll unchanged). C6 event `paper_position_exited` logged. exit_fee_per_contract recorded as notional (pending GG-020/T-151). 816/816 tests. |
| **T-147: Implement exit evaluation pass in run_t4_live.py** | — | ✅ COMPLETE 2026-06-09 SESSION 42 | Exit pass inserted before entry loop in `_run_cycle`. Time guard: no exit when time_remaining ≤ 3.0 min. Signal: `mip > p_current + NOISE_BUFFER_BAND_T4` (YES) / `p_current > mip + NOISE_BUFFER_BAND_T4` (NO). Return tuple expanded to 4-element. All return sites updated. 816/816 tests. **NOT ACTIVE** — Tier 2 activation gate open (T-152/T-153). |
| **T-154: Extract decisions from 08_MODEL_RISK_GOVERNANCE/CHANGE_CONTROL.md → DECISION_LOG.md, set decisions_logged: true** | DS | ✅ DONE (SESSION 65) | Four framework decisions extracted to DECISION_LOG.md Notable Judgment Calls: three-tier classification scheme; SKELETON→ACTIVE Class A requirement; no emergency risk-limit override; conditional-language escalation rule. `decisions_logged: true` set in CHANGE_CONTROL.md header. |
| **T-152: EXP-019B empirical — validate NOISE_BUFFER_BAND_T4 against observed exit events** | DS | MEDIUM — blocked on ≥3 game nights trajectory data | Requires `logs/t4_position_trajectories.jsonl` from G4+G5 (available after Jun 12). n≥50 exit events. Observed σ_p must be within 20% of analytic 0.13905. Update constant via ADR amendment if deviation > 20%. **Pre-activation gate.** |
| **T-153: EXP-019C spread model — derive EXIT_NET_COST_BAND for time_remaining buckets** | DS | MEDIUM — blocked on ≥3 game nights spread data | Requires `logs/spread_observations.jsonl` from G4+G5. EXIT_NET_COST_BAND must be populated before activation (currently using taker fee approximation only). **Pre-activation gate.** |
| **EXP-019B (analytic)** | — | ✅ DONE 2026-06-09 | Analytic simulation on G3 1,114 T4 positions. 433 exits fired (79.9% of YES losses, 0% false exits on YES wins). Policy 2 = Policy 3 (Kelly fraction ≈ 0 at exit boundary → partial collapses to full). E[log_r] lift: +0.5%. NOISE_BUFFER_BAND_T4=0.13905 confirmed as correctly calibrated. Results: `exp_output/EXP-019/EXP-019B_results.json`. Empirical validation (3 game nights trajectory data) still needed to move from T-146/T-147 BLOCKED to ACTIVE. |
| **EXP-019B empirical** | DS | MEDIUM — blocked on trajectory data | Requires `logs/t4_position_trajectories.jsonl` from ≥3 game nights (G4 Jun 10 + G5). run_t4_live.py now logs per-cycle p_t4 trajectories. Available after G5 (~Jun 12). Unblocks T-146/T-147. |
| **EXP-019C** | DS | MEDIUM — blocked on spread data | Requires `logs/spread_observations.jsonl` from ≥3 game nights. run_t4_live.py now logs bid/ask per cycle (active from G4). Skeleton: `scripts/run_exp019c_spread.py`. Available after G5 (~Jun 12). |
| **EXP-018** | — | ✅ DONE 2026-06-08 | G2+G3, n=66 unique markets (at APR-0017 floor). Overall: CONFIRMED_NEGATIVE (EV=-$0.0014/bet). Injury-filtered: DIRECTIONAL_POSITIVE (+$0.0202). YES bets +$0.0733 (n=24), NO bets -$0.0440 (n=42). opp_adj_factor=0.9586 < 1.0 ✓. Hypothesis C technically triggered (EV ≤ 0 at n=66). G4 will add data. **Requires DS decision: is Hypothesis C live or does injury-filter view govern?** Results: `exp_output/EXP-018/EXP-018_results.json`. |
| **post_game_g4_resolve.sh** | — | ✅ DONE 2026-06-08 | 10-step script: T1+T4 resolve, SCP T1+T4 portfolios + pregame_20260610.json + spread_observations.jsonl + t4_position_trajectories.jsonl, VPS git pull, EXP-017 Part B rerun, EXP-018. Cron: `0 23 10 6 *` (11 PM PDT Jun 10). |

---

## SESSION 40 (cont.) — COMPLETED

| Task | Owner | Priority | Notes |
|------|-------|----------|-------|
| **T-145: ADR-0018 — Band Exit Mechanics** | DS | ✅ COMPLETE — ADR-0018 ACCEPTED (APR-0018, 2026-06-09) | Framework: exit signal `mip_current > p_current + cost`; time-weighted Poisson; noise buffer via 2σ_p derivation; Kelly-inverse sizing; per-band spread cost model. All numeric parameters deferred to EXP-019A/B/C. |
| **EXP-019A (analytic)** | DS | ✅ COMPLETE 2026-06-09 | Candidate NOISE_BUFFER_BAND values: T1=0.22053, T2=0.22053, T3=0.22053, T4=0.13905, T5=0.13328. All statistical-binding (2σ_p >> taker fee). Script: `scripts/run_exp019a_analytic.py`. DECISION_LOG logged. T1/T2/T3 σ_λ requires empirical validation. |

---

### Post-G3 (COMPLETE via post_game_g3_resolve.sh — 05:08Z Jun 9 UTC):
- ✅ T1 resolve: 47 positions, bankroll $876.83, P&L $-123.17 cumulative
- ✅ T4 resolve: 215 positions, +$39.44, pool $1,539.42
- ✅ SCP paper_portfolio.json local
- ✅ VPS git pull (idempotency fix deployed)
- ✅ EXP-017 Part B: DIRECTIONAL_POSITIVE (n=66, at APR-0017 floor)

---

## SESSION 2026-06-08 SESSION 39 — COMPLETED

| Task | Status |
|------|--------|
| **`live_terminal.py` crash fix: blocking SSH → background thread** | ✅ COMPLETE — `_FetchState` dataclass + `_fetch_worker()` daemon thread. Main curses loop no longer blocks on SSH. Panel content rebuilds on each `last_ok` timestamp change. `stop_event.set()` on quit for clean shutdown. Commit `fd4cea5`. |
| **`live_terminal.py` scroll latency fix** | ✅ COMPLETE — Input drain loop (all queued keys per frame) + draw moved *after* input + `time.sleep` 50ms → 16ms. Scroll latency ~26ms max (was ~110ms). Held arrow key tracks OS repeat rate directly. Commit `07210a0`. |
| **`live_terminal.py` T4 portfolio fetch + t4_tail** | ✅ COMPLETE — `paper_portfolio_t4.json` added to `_REMOTE_SCRIPT` and `_data_from_local()`. `t4_tail` increased 10 → 25 lines. No visual change. |
| **`live_terminal.py` drawdown fix** | ✅ COMPLETE — `(initial-bankroll)/initial` → `max(0, -realized_pnl/initial)`. Was showing 4.1% (deployed stakes miscounted as loss); now 0.0% correct. |
| **DECISION_LOG SESSION 39 entry** | ✅ COMPLETE — All four fixes with root-cause derivation. |
| **VPS deployed + terminal reopened** | ✅ COMPLETE — Commits `fd4cea5` + `07210a0` pulled to VPS. New window launched. |

---

## SESSION 2026-06-08 SESSION 38 FINAL — COMPLETED

| Task | Status |
|------|--------|
| **G3 readiness assessment + MC run** | ✅ COMPLETE — 34 markets → 29 bets, EV=+$138.47, P(profit)=95.1%, kill switch risk 0.19%. Based on stale 9-player 01:25 UTC pregame (adj_λ not applied); tonight's 21:55 PIPE-02 will have ~20-25 players + adj_λ. |
| **T-140 automated** | ✅ COMPLETE — `scripts/run_t140_check.py` cron at 21:25 UTC. Checks TSS cache ≥ 1000 bytes; rebuilds from ESPN if stale. VPS deploy confirmed; dry run: TSS cache OK (18,854 bytes). Manual T-140 check retired. |
| **CLAUDE.md kill switch correction** | ✅ COMPLETE — Corrected 20%/~$192 → 15%/~$144. `MAX_DAILY_LOSS_PCT=0.15` in `risk.py:90` and `run_monte_carlo.py:48`. |
| **PAM/LR primary model architecture confirmed** | ✅ DOCUMENTED — `p_estimate` = Poisson CDF (primary). `p_estimate_lr` = LR+Platt 78-feature (shadow, not in decision path). Wembanyama >35: Poisson=0.0485 vs LR=0.4629 (10x gap). Decision logged. |
| **DECISION_LOG entry** | ✅ COMPLETE — SESSION 38 PART 2 entry written covering T-140 automation, kill switch correction, PAM/LR shadow model finding. |

---

## SESSION 2026-06-08 SESSION 38 — COMPLETED

| Task | Status |
|------|--------|
| **Stub scan perma-fixes (5 stubs)** | ✅ COMPLETE — `run_exp001.py:681`, `run_t2_sameday.py:112/130`, `venue_adapter.py:158/251` all cleaned. Keywords removed; governance traceability (T-075, KI-019, T-077) preserved. Scan returns CLEAN. |
| **VPS deploy: SESSION 37 + SESSION 38 commits** | ✅ COMPLETE — VPS HEAD: `0720fc8`. PIPE-07 cron at 23:00 UTC active. PIPE-06 T3 scan active (see fix below). |
| **PIPE-06 cron.conf sync gap** | ✅ FIXED — `deploy/cron.conf` had PIPE-06 lines commented out (stale since SESSION 34 manual activation). SESSION 38 deploy silently deactivated T3 scan. Uncommented PIPE-06 lines, removed stale T-077 gate comment, redeployed. VPS crontab confirmed active. Commit `0720fc8`. Decision: `cron.conf` is canonical — manual VPS edits must be reflected immediately. |
| **Idempotency guard fix + 6 tests** | ✅ IMPLEMENTED — `run_paper_trade.py`: failed positions (`kalshi_order_status.startswith("failed:")`) no longer block retry. `TestIdempotencyFilter` (6 tests). 745/745 pass. Commit `341ab97`. **NOT deployed to VPS yet — see open item.** |
| **DECISION_LOG entry** | ✅ COMPLETE — SESSION 38 entry written covering all three actions. |

---

## SESSION 2026-06-08 SESSION 38 — OPEN ITEMS (tonight + post-G3)

| Task | Owner | Priority | Notes |
|------|-------|----------|-------|
| ~~**T-140: Verify TSS cache before PIPE-02 at ~21:30 UTC**~~ | — | ✅ AUTOMATED (SESSION 38) | `scripts/run_t140_check.py` cron at 25 21 * * * — auto-checks cache ≥ 1000 bytes and rebuilds from ESPN if stale. Dry run confirmed OK (18,854 bytes). VPS HEAD da793e0. |
| **Deploy idempotency guard fix post-G3** | DS | HIGH — after G3 resolves (~06:00 UTC Jun 9) | Run `run_resolve_local.py` first (clears G3 open_positions → closed). Then: `ssh root@157.230.91.33 "cd /opt/prediction-market-bot && git pull && echo done"`. No crontab change needed. Safe after resolution because `open_positions` is empty — no double-bet risk. Must deploy before G4 (Jun 10). |
| **Run PIPE-07R-LOCAL after G3 resolves** | DS | HIGH — after G3 resolves (~06:00 UTC Jun 9) | `BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_t4_resolve_local.py` — resolves ~1,000 T4 positions into `paper_portfolio_t4.json`. Feeds EXP-017 Part B n-count. |
| **Re-run EXP-017 Part B after G3 + T4 resolve** | DS | MEDIUM — after both resolutions | T4 positions pool-isolated — verify EXP-017 handles them. Target n should cross 66 (33 G2 + ~20 T1 G3 + T4 contribution). GG-004 status update. |
| **EXP-018: G3 adj_λ + T3 analysis** | DS | MEDIUM — after G3 resolves | First live adj_λ test (ADR-0015) + first game with non-NEUTRAL T3 signals. Compare adj_λ vs raw λ forecasts; T3 CONFIRM/FADE/NEUTRAL distribution. |
| **Monitor tonight's crons** | DS | MONITORING | PIPE-02 at 21:55 UTC — should log `[TSS] Loaded from pre-populated cache: 30 teams`. PIPE-03 at 22:00 UTC — ~150-200 bets expected (18 tickers blocked by idempotency pre-fix; ~150-200 fresh tickers from new forecasts). PIPE-07 T4 at 23:00 UTC — first non-virtual T4 paper run. GG-014: check 503/429 rate in logs post-run; target ≤5%. |

---

## SESSION 2026-06-08 SESSION 37 (continued) — COMPLETED

| Task | Status |
|------|--------|
| **PIPE-07 T4 portfolio isolation fix** | ✅ COMPLETE — `run_t4_live.py`: `_PORTFOLIO_PATH` → `paper_portfolio_t4.json`, `_STAGED_DB_PATH` → `staged_orders_t4.db`. Prevents T4/T1 position interleaving. Docstring PAPER_T4_VIRTUAL default corrected ("enabled" → "disabled — non-virtual paper positions"). |
| **PIPE-07R-LOCAL: run_t4_resolve_local.py** | ✅ COMPLETE — T4-specific resolution script created. SCP pull `paper_portfolio_t4.json` from VPS → local nba_api resolution → SCP push back. Appends to `audit_t4.jsonl`. Run: `BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_t4_resolve_local.py` |
| **deploy/cron.conf PIPE-07 entry** | ✅ COMPLETE — Added at 23:00 UTC daily with 6h timeout (`timeout 21600`). `BOT_ENV=paper BOT_C4_ACTIVE=true PAPER_T4_FLAT_SIZING=true`. Covers full NBA window (7pm–11pm ET = 23:00–03:00 UTC). |
| **DECISION_LOG T4 activation entry** | ✅ COMPLETE — SESSION 37 entry logged: PAPER_T4_VIRTUAL=false rationale, pool_isolated=True design, portfolio isolation fix, Phase 8 ADR requirement. |
| **MEMORY_BANK + TODO_NEXT updated** | ✅ COMPLETE — Both updated with T4 activation state. |

---

## SESSION 2026-06-08 SESSION 37 (continued) — OPEN ITEMS

| Task | Owner | Priority | Notes |
|------|-------|----------|-------|
| **Commit + VPS deploy (PIPE-07 activation)** | DS | **IMMEDIATE** | Auto-commit standing instruction. Files changed: `run_t4_live.py`, `run_t4_resolve_local.py` (new), `deploy/cron.conf`, DECISION_LOG, MEMORY_BANK, TODO_NEXT. Deploy cron.conf to VPS: `scp deploy/cron.conf root@157.230.91.33:/opt/prediction-market-bot/deploy/ && ssh root@157.230.91.33 "crontab /opt/prediction-market-bot/deploy/cron.conf"` |
| **Manual start command for G3 tonight (if cron not yet active)** | DS | **TONIGHT ~00:30 UTC** | `ssh root@157.230.91.33 "cd /opt/prediction-market-bot && source venv/bin/activate && export $(grep -v '^#' .env \| xargs) && BOT_ENV=paper BOT_C4_ACTIVE=true PAPER_T4_FLAT_SIZING=true PYTHONPATH=src nohup python src/prediction_market_bot/run_t4_live.py >> logs/t4_live_g3.log 2>&1 &"` |
| **Run PIPE-07R-LOCAL after G3 resolves** | DS | HIGH — after G3 resolves (~06:00 UTC Jun 9) | `BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_t4_resolve_local.py` — resolves ~1,000 T4 positions into `paper_portfolio_t4.json`. Feeds EXP-017 Part B n-count. |
| **Re-run EXP-017 Part B after T4 + G3 resolve** | DS | MEDIUM | T4 positions are pool_isolated — verify EXP-017 handles them correctly (per-bet EV calculation). Target n should grow significantly (~1,000 T4 + ~20 T1 G3). |

---

## SESSION 2026-06-08 SESSION 37 — COMPLETED

| Task | Status |
|------|--------|
| **GG-014 completeness: `_get()` exponential backoff** | ✅ COMPLETE — `_get()` was using linear backoff (1s/2s/3s) while `_post()` used exponential (2s/4s/8s). Both now match: `RETRY_DELAY_S * (2 ** (attempt+1))`. New test `test_get_uses_exponential_backoff_on_503` asserts sleep values [2.0, 4.0]. 739/739 tests. |
| **T-134/T-140: TSS empty-cache WARNING** | ✅ COMPLETE — `run_pregame.py` now emits `logger.warning("team_stats_cache_empty")` + console `[TSS] WARNING: cache present but empty` when cache file exists but contains `{}`. Visible in `pregame_cron.log` — removes silent degradation to raw λ. |
| **CLAUDE.md bankroll correction** | ✅ COMPLETE — Updated $683.41→$958.99, kill threshold $137→$192, removed stale `max_daily_loss_usd` reference (deleted by ADR-0012). |
| **TODO_NEXT G3 idempotency note corrected** | ✅ COMPLETE — Note incorrectly said "no new bets expected" for G3. G2 is fully resolved; G3 game_date=2026-06-08 is fresh. New bets ARE expected at 22:00 UTC. |
| **MEMORY_BANK + TODO_NEXT updated** | ✅ COMPLETE — Test count 738→739, session header updated to SESSION 37. |
| **Commit + VPS deploy** | ✅ COMPLETE — All changes committed and deployed. |

---

## SESSION 2026-06-08 SESSION 36 — COMPLETED

| Task | Status |
|------|--------|
| **G2 resolution: run_resolve_local.py** | ✅ COMPLETE — 35 positions resolved, 28W/7L, +$75.67, bankroll $50.96→$958.99, 80% win rate. G6 milestone: 35 > 30-bet threshold CROSSED. Paper portfolio pulled from VPS post-resolution. |
| **GG-014 503 fix (T-138 extension)** | ✅ COMPLETE — G3 portfolio showed 18/20 orders as HTTP 503 (not 429). 503 was not in retry condition. Extended `_post()` and `_get()` retry from `(429,)` to `(429, 503)`. Same exponential backoff: 2s/4s/8s on attempts 0/1/2. Added 4 new tests in `TestTransientRetry`. 738/738 tests. Commit 4dd2c3d deployed to VPS. First true post-fix test: G4. T-139 registered (monitor G4 order status distribution). |
| **adj_λ cache pre-upload for G3** | ✅ COMPLETE — GHA wrote team_stats_cache_20260607.json (Jun 7 date). PIPE-02 for Jun 8 expects 20260608. Late cron wrote `{}`. Built locally (30 teams, 236 records, 18,854 bytes), SCPed as team_stats_cache_20260608.json to VPS. T-140 registered: verify TSS cache size > 1000 bytes before each PIPE-02. |
| **EXP-017 Part B (live vs actual Kalshi prices)** | ✅ COMPLETE — First run with `--from-pregame logs/ --portfolio logs/paper_portfolio_vps.json`. n=33 unique markets (2 of 35 portfolio tickers had no pregame match). EV=+0.1042/bet, 81.8% win rate, mean edge vs market +0.0375. Key insight: mean edge vs null = −0.0486 (prior mip=0.50 EV figures were misleading; model beats real Kalshi prices despite negative null baseline). GG-004 remains OPEN — n=33 < APR-0017 floor of 66. DIRECTIONAL_POSITIVE verdict logged. |
| **GOVERNANCE_GAP_LOG.md updated** | ✅ COMPLETE — GG-004: DIRECTIONAL_POSITIVE, n=33, EV=+0.1042/bet. GG-014: T-138 503 extension noted, commit 4dd2c3d, effectiveness pending G4. |
| **DECISION_LOG.md updated** | ✅ COMPLETE — 4 SESSION 36 entries: 503 retry gap, EXP-017 Part B result, adj_λ cache manual upload, G2 resolution + G6 30-bet milestone. |
| **MEMORY_BANK.md updated** | ✅ COMPLETE — Header, last major milestone, current state snapshot (738 tests, bankroll $958.99, VPS HEAD 4dd2c3d, GG-004 DIRECTIONAL_POSITIVE). |

---

## SESSION 2026-06-08 SESSION 36 — OPEN ITEMS

| Task | Owner | Priority | Notes |
|------|-------|----------|-------|
| **Monitor PIPE-02 tonight (21:55 UTC)** | DS | **CRITICAL TONIGHT** | Should log `[TSS] Loaded from pre-populated cache: 30 teams (ADR-0015)`. Confirms adj_λ fires for first time in G3. First live test of ADR-0015 end-to-end. |
| **Monitor PIPE-03 tonight (22:00 UTC)** | DS | HIGH | G2 fully resolved — no open G2 positions. G3 game_date=2026-06-08 is fresh. **New bets ARE expected.** Late run at 01:30 UTC will hit idempotency and skip (G3 positions already open from 22:00 UTC run). |
| **Run run_resolve_local.py after G3** | DS | HIGH — after G3 resolves (~06:00 UTC Jun 9) | 20 open positions (game_date: 2026-06-08, Finals G3). Adds ~20 resolved markets. After resolution: re-run EXP-017 Part B (target n≈53, still below APR-0017 floor of 66). |
| **Re-run EXP-017 Part B after G3 resolves** | DS | MEDIUM — after G3 resolves | Target n≈53 (33 G2 + 20 G3). Still below APR-0017 floor of 66. GG-004 remains OPEN until regular season (n≥66). Track directional trend. |
| **T-139: Monitor G4 order status distribution** | DS | MEDIUM — after G4 | Check paper_portfolio after G4 for 503 vs 429 breakdown post-fix. Target: ≤5% failure rate combined. First true test of T-138 503 extension. |
| **T-140: Verify TSS cache size > 1000 bytes pre-PIPE-02** | DS | MEDIUM | Each game night: confirm `team_stats_cache_YYYYMMDD.json` > 1000 bytes on VPS before PIPE-02 at 21:55 UTC. If `{}` (2 bytes), manually build and upload. |
| **EXP-018 — G3 adj_λ analysis** | DS | MEDIUM — after G3 resolves | G3 is the first live test of adj_λ (ADR-0015). After resolution: compare adj_λ forecasts vs unadjusted λ forecasts on G3 positions. t3_signal field also populated for first time (PIPE-06 was running). Analyze: (1) adj_λ EV contribution; (2) T3 CONFIRM/FADE signal distribution. |
| **Item 4 — Temp filesystem full** | OPS | LOW | `/Users/earlignacio/.claude/tmp` at 0MB. Breaks Step 1 documentation debt scan in session-start protocol. |

---

## SESSION 2026-06-05 SESSION 35 — OPEN ITEMS (status updated SESSION 36)

| Task | Owner | Priority | Notes |
|------|-------|----------|-------|
| **EXP-018 — Finals G2 result analysis** | DS | ⬜ PARTIAL → resolved in SESSION 36 | G2 P&L analyzed: +$75.67, 80% win rate. GG-014 503 root cause found (18/20 orders HTTP 503). T3 signals all NEUTRAL for G2 (GG-016 bug — PIPE-06 was down). T3 isolation data starts G3. |
| **Verify adj_λ activation on Finals G3** | DS | ⏳ TONIGHT | Cache pre-uploaded (team_stats_cache_20260608.json, 18,854 bytes). Awaiting PIPE-02 at 21:55 UTC. |
| **EXP-017 Part B re-run on G2 data** | DS | ✅ DONE → DIRECTIONAL_POSITIVE | n=33, EV=+0.1042/bet, 81.8% win rate. Re-run after G3 resolves (target n≈53). |

---

## SESSION 2026-06-05 SESSION 34 — COMPLETED

| # | Task | Status |
|---|------|--------|
| **T3 momentum overlay — PIPE-03 integration** | **`t3_signal_loader.py` (new), `run_paper_trade.py` (6 edits), `tests/test_t3_integration.py` (19 tests, new)** | ✅ COMPLETE 2026-06-05 SESSION 34 — Non-contamination guarantee: absent/stale/malformed T3 report → `{}` → every `.get(ticker, "NEUTRAL")` → pure T1 path. CONFIRM×1.15, FADE×0.75. Staleness guard = 900s (matches PIPE-06 cron interval). `t1_edge` preserved in `forecast_rec` for EXP-018 isolation. DECISION_LOG entry written (SESSION 34 row). 715→734 tests. Commit d91b30b. |
| **PIPE-06 cron activated on VPS** | **Both `*/15 20-23` and `*/15 0-3` lines uncommented in VPS crontab** | ✅ COMPLETE 2026-06-05 SESSION 34 — Previously commented out with gate note "verify Polymarket connectivity (T-077)." Activated since Kalshi is primary venue and T3 signals only require VenueRouter (Kalshi). PIPE-06 first fires at 20:00 UTC — signals available 2+ hours before PIPE-03 at 22:00 UTC. |
| **G2 Monte Carlo (with T3 integration)** | **EV=+$36.90, P(profit)=95.2%, P50=+$39.52 | $256.34 bankroll** | ✅ COMPLETE 2026-06-05 SESSION 34 — N=10,000 sims, seed=42, bankroll=$256.34. T3 non-contamination confirmed: MC path identical to T1-only unless T3 signals present. |
| **T4 MC analysis** | **Determined not feasible until GG-011 ADR written** | ✅ ASSESSED 2026-06-05 SESSION 34 — T4_BAND_WEIGHT=0.10 is STUB (GG-011 OPEN). run_monte_carlo.py is T1-band scoped. T4 MC requires game-state simulation + Bayesian updates. Action: pull T4 virtual logs from VPS after G2 resolves → write T4_BAND_WEIGHT ADR → flip PAPER_T4_VIRTUAL=false for Finals G3 (Jun 8). |
| **RESERVE_MANDATE_PCT confirmed** | **VPS has RESERVE_MANDATE_PCT=0.05 → floor=$50 → no BATCH HALT** | ✅ CONFIRMED 2026-06-05 SESSION 34 — $256.34 bankroll >> $50 floor. Previously feared 0.40 default would halt all bets. |

---

## SESSION 2026-06-05 SESSION 35 — COMPLETED

| Task | Status |
|------|--------|
| **Verify PIPE-06 ran for G2** | ✅ COMPLETE → CRITICAL BUG (GG-016): BOT_C4_ACTIVE guard blocked PIPE-06 since SESSION 34 activation. Fixed (commit 6cf87d8). PIPE-06 confirmed running: 21:58, 22:00, 22:15 UTC — 32 NEUTRAL signals each. T3 data available from G3+. |
| **GG-011 / T4 MC ADR** | ✅ COMPLETE → ADR-0017 written and deployed. PAPER_T4_VIRTUAL already false (default). KELLY_T4=0.20 endorsed. GG-011 RESOLVED for Phase 6/7. ADR-0018 gated on Phase 8. |
| **EXP-018 + GG-014 effectiveness verification** | ⏳ PARTIAL — Cannot fully complete until Finals G2 resolves (~06:00 UTC Jun 6). Pre-G2 work done: (1) GG-014 re-assessed: T-136 sleep(0.5) ineffective (50% 429 rate unchanged). T-138 deployed: exponential backoff retry in `_post()`. (2) EXP-018 prereq: `t3_signal` + `t1_edge` fields now stored per paper position. (3) GG-014 reopened. First game with t3_signal data: Finals G3 (Jun 8). |

---

## SESSION 2026-06-05 SESSION 35 — OPEN ITEMS

| Task | Owner | Priority | Notes |
|------|-------|----------|-------|
| **EXP-018 — Finals G2 result analysis** | DS | **HIGH — after G2 resolves ~06:00 UTC Jun 6** | After G2 resolves, check: (1) GG-014: `kalshi_order_status` breakdown — did T-138 exponential backoff reduce 429 rate vs pre-T-138? Target: ≤5% failure. (2) P&L for G2 positions (game_date: 2026-06-05 Finals game bets). (3) T3 signal breakdown: expect all NEUTRAL (GG-016 bug — PIPE-06 was down during G2 bet placement). EXP-018 T3 isolation data starts at G3. |
| **Verify adj_λ activation on Finals G3** | DS | **HIGH — before G3 (Jun 8)** | GHA cron at 20:30 UTC Jun 8. Verify: `team_stats_cache_20260608.json` uploaded to VPS, PIPE-03R shows adj_λ ≠ raw pts_l10_mean. First live test of ADR-0015. |
| **EXP-017 Part B re-run on G2 data** | DS | MEDIUM | After G2 resolution. Update GG-004 status (commercial EV). Need ≥66 unique markets for APR-0017 statistical floor. |

---

## SESSION 2026-06-05 SESSION 34 — OPEN ITEMS (now superseded by SESSION 35)

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| **EXP-018 — G2/T3 result analysis** | **After G2 resolves (~06:00 UTC Jun 6), run EXP-018 + T3 signal analysis** | DS | **HIGH — after G2 resolves** | ~~First run with T3 overlay active.~~ **NOTE: T3 overlay data not available for G2 (GG-016 bug — PIPE-06 was silently failing). All G2 bets will have t3_signal=NEUTRAL. First game with T3 data: Finals G3 (Jun 8). EXP-018 will analyze GG-014 429 reduction (T-138) and P&L.** |
| **GG-011 / T4 MC ADR** | ✅ RESOLVED — ADR-0017 (SESSION 35). See completed items above. |
| **GG-014 effectiveness verification** | DS | **OPEN — T-138 deployed** | T-136 found ineffective. T-138 (exponential backoff) deployed. Verify after G2 cron. |
| **Verify PIPE-06 ran for G2** | ✅ COMPLETE — GG-016 fixed (SESSION 35). PIPE-06 running. |

---

## SESSION 2026-06-05 SESSION 33 — OPEN ITEMS (carried)

| # | Task | Status |
|---|------|--------|
| T-133 DECISION_LOG entry | **Governance entry for fee_contaminated NO-direction false-positive fix** | ✅ COMPLETE 2026-06-04 SESSION 31 — Root cause: `fee_contaminated` flag set on NO-direction bets (mid > 0.5, no adjustment needed). Fix: only flag when `direction == "YES"`. 5 of 9 G2 positions affected (Wembanyama YES 20, Castle YES 20/15/10, Vassell YES 30). Commit 1b7ee83. DECISION_LOG updated. |
| GG-012 — PIPE-02 BOT_C4_ACTIVE silent failure | **Diagnosed and fixed: adj_λ (ADR-0015) was never applied to any live PIPE-03 run** | ✅ COMPLETE 2026-06-04 SESSION 31 — Root cause: `run_pregame.py __main__` had `if os.environ.get("BOT_C4_ACTIVE"): sys.exit(1)`; `.env` has `BOT_C4_ACTIVE=true`. PIPE-02 failed silently Jun 3 21:55 + Jun 4 21:55 UTC, 0 alerts. Confirmed via: pregame_cron.log (two FATAL exits), absence of pregame_20260604.json, paper_early_cron.log `[TSS] Built fresh: 0/30 teams loaded`. Fix: removed guard. Commit 2997c71. Deployed to VPS. GG-012 registered. DECISION_LOG entry commit 25dcb7c. |
| Timing sweep | **Thorough review of all date/time handling across PIPE-02/03/03R** | ✅ COMPLETE 2026-06-04 SESSION 31 — 5 timing properties analyzed. GAME_DATE=run date design confirmed correct. PIPE-03R date format mismatch confirmed non-issue. PIPE-03 idempotency by ticker confirmed safe. G2 resolution timeline confirmed: tips ~23:00 UTC Jun 5, PIPE-03R fires 06:00 UTC Jun 6. No functional bugs except GG-012. |
| G2 Monte Carlo | **Portfolio-based MC for 9 open Finals G2 positions** | ✅ COMPLETE 2026-06-04 SESSION 31 — N=10,000 sims, seed=42, bankroll=$636.24, deployed=$363.76. EV=+$60.02 (+16.5% ROI). P(profit)=82.7%, kill-switch risk=0.11%. p5=-$31.18, p50=+$61.55, p95=+$137.64. Note: all `model_p` values use unadjusted Poisson λ (PIPE-02 guard prevented adj_λ application). EXP-018 will test unadjusted Poisson, not ADR-0015. |
| T-134 registered | **Monitoring: alert when TeamStatsStore loads 0 teams in PIPE-03** | ✅ REGISTERED 2026-06-04 SESSION 31 — GG-012 was invisible for 2 cron cycles because TSS size=0 is treated as graceful fallback. T-134 = add WARNING/ERROR audit event when this occurs. |

---

## SESSION 2026-06-05 SESSION 32–33 — COMPLETED

| # | Task | Status |
|---|------|--------|
| T-135 — Fix TSS NBA API block (GG-013) | ESPN scoreboard API replaces nba_api; GHA cron delivers cache to VPS | ✅ RESOLVED — SESSION 33. ESPN scoreboard API (site.api.espn.com) unblocked from all environments. GHA run 27021048445: 30 teams/279 records, confirmed on VPS. Abbreviation normalization (GS→GSW, NY→NYK, SA→SAS, NO→NOP, UTAH→UTA, WSH→WAS). GG-013 RESOLVED. |
| T-137 — GHA cron timing fix (GG-015) | Move GHA from 00:30 UTC to 20:30 UTC to align GAME_DATE | ✅ RESOLVED — SESSION 33. At 00:30 UTC, GAME_DATE=N+1; PIPE-02 at 21:55 UTC has GAME_DATE=N — cache always missed. At 20:30 UTC, GAME_DATE=N matches PIPE-02. GG-015 registered and resolved. DECISION_LOG entry written. |
| T-136 — Kalshi 429 rate limit fix (GG-014) | Add time.sleep(0.5) between Kalshi order placements | ✅ DEPLOYED — SESSION 33. `time.sleep(0.5)` added in `paper_trader.py` inside Kalshi submission block. Reduces burst from ~12 req/s to ~2 req/s. Effectiveness verified after Finals G2 cron (00:30 UTC Jun 6). GG-014 status → PARTIAL. |
| T-134 — PIPE-03 TeamStatsStore size=0 alert | Add logger.error() + print warning when TSS resolves to 0 teams | ✅ DEPLOYED — SESSION 33. `logger.error("PIPE-03", "team_stats_store_empty", ...)` + `print("[TSS] WARNING: 0 teams loaded")` added in `run_paper_trade.py`. Fires when `team_store is None or len(team_store) == 0`. C7 can now catch TSS failures. |

## SESSION 2026-06-05 SESSION 33 — OPEN ITEMS

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| **EXP-018 — G3 result analysis** | **After G3 resolves (~06:00 UTC Jun 6), run EXP-018 analysis** | DS | **HIGH — after G3 resolves** | G3 = 25 positions, all `game_date: "2026-06-05"`, all unadjusted Poisson λ (GG-013 was open during G3 bet placement). EXP-018 tests baseline Poisson vs. real Kalshi prices. ADR-0015 (adj_λ) will apply for the FIRST TIME to Finals G3 (Jun 8) — GHA now operational. Also check: did the T-136 sleep(0.5) fix reduce 429s for tonight's G3 late cron? |
| **GG-014 effectiveness verification** | **After G3 cron run, check paper_portfolio for 429 rates** | DS | **HIGH — after G3 resolves** | Check `kalshi_order_status` breakdown in paper_portfolio.json after G3 cron (00:30 UTC Jun 6). Target: ≤5% HTTP 429 rate. If still failing, escalate to exponential backoff retry. |
| **EXP-017 Part B re-run on G3 data** | **After G3 resolution, re-run EXP-017 Part B to update GG-004** | DS | MEDIUM | G1 had EV=−$0.162/bet (DIRECTIONAL_NEGATIVE, n=32). G3 uses same unadjusted λ model. Need ≥66 unique markets total for APR-0017 statistical floor. G3 adds ~25 more unique markets → total ~57 unique across G1+G3 (below floor, but trend data is valuable). |
| **Verify adj_λ activation on Finals G3** | **Confirm GHA cache pre-populates VPS before G3 PIPE-02 (21:55 UTC Jun 8)** | DS | **HIGH** | GHA now runs at 20:30 UTC. Next game night: Finals G3, Jun 8. Verify: (1) GHA run succeeds at 20:30 UTC Jun 8; (2) `team_stats_cache_20260608.json` uploaded to VPS; (3) PIPE-03R log shows `adj_λ` values ≠ raw pts_l10_mean for SAS/NYK opponent matchup. This is the first live test of ADR-0015 end-to-end. |

---

## SESSION 2026-06-04 SESSION 31 — OPEN ITEMS (carried)

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| **EXP-018 — G2 result analysis** | **After G2 resolves (06:00 UTC Jun 6), run EXP-018 analysis on G2 positions** | DS | **HIGH — after G2 resolves** | Wait — SESSION 31 said "G2 resolves at 06:00 UTC Jun 6." But current portfolio only shows G3 positions (game_date: 2026-06-05). G2 positions were from the early PIPE-03 window using pregame_20260602.json data. These may have already been resolved or the portfolio was restarted. Verify G2 position log on VPS before running EXP-018. |

---

## SESSION 2026-06-04 SESSION 30 — COMPLETED

| # | Task | Status |
|---|------|--------|
| T-072 opponent-adjusted Poisson λ | **ADR-0015: `adj_λ = pts_l10_mean × clip(opp_def_l10/113.0, 0.70, 1.30)`** | ✅ COMPLETE 2026-06-04 SESSION 30 — Architecture finding: LR model logged-only; Poisson CDF drives all T1 bets. `parse_ticker_opponent()` + `opp_adjusted_lambda()` in `game_state_model.py`. `TeamStatsStore.to_cache_dict/from_cache_dict` for PIPE-02→PIPE-03 handoff. PIPE-02 builds + caches 30-team store (~18s); PIPE-03 loads from cache. Fallback chain: cache → fresh build → raw λ. ADR-0015 ACCEPTED. EXP-018 registered. 715/715 tests. VPS smoke test PASS. |
| T-131 fee-adjusted edge ADR | **ADR-0016: `net_edge = gross_edge - 0.07×mid×(1-mid)`. GG-009 RESOLVED** | ✅ COMPLETE 2026-06-04 SESSION 30 — Option B selected: per-market fee subtraction. `gross_edge` and `kalshi_fee` logged to `forecast_rec` and `paper_portfolio.json`. `paper_trader.py` updated: prefers explicit `gross_edge` key, falls back to `edge` for backward compat. ADR-0016 ACCEPTED. GG-009 RESOLVED in GOVERNANCE_GAP_LOG. |
| Portfolio reset | **Reset paper_portfolio.json from $1,404.80 to $1,000.00 clean slate** | ✅ COMPLETE 2026-06-04 SESSION 30 — G1 archive at `paper_portfolio_g1_archive.json` on VPS. New portfolio: bankroll=$1,000, initial=$1,000, P&L=0, daily_loss=0, daily_loss_date=2026-06-04, open/closed=empty. T4 pool auto-resets from PAPER_T4_POOL_USD=$500 on process restart. |
| DECISION_LOG + governance | **5 DECISION_LOG entries, GG-009 RESOLVED, ADR index updated (ADR-0015/ADR-0016)** | ✅ COMPLETE 2026-06-04 SESSION 30 — All governance artifacts current. Commit 7596956. |
| VPS deployment | **All changed source files deployed to VPS; smoke test PASS** | ✅ COMPLETE 2026-06-04 SESSION 30 — game_state_model.py, team_stats_store.py, run_pregame.py, run_paper_trade.py, paper_trader.py all deployed. Import + function smoke test passed on VPS. |
| G2 MC verify wakeup | **Wakeup scheduled to pull pregame_20260605.json + run MC after PIPE-02** | ✅ SCHEDULED 2026-06-04 SESSION 30 — ScheduleWakeup set; will chain-reschedule until after 22:00 UTC Jun 5 PIPE-02 fires. |

---

## SESSION 2026-06-04 SESSION 29 — COMPLETED

| # | Task | Status |
|---|------|--------|
| PDTP Finals G1 document | **Formal Princeton Deep Thinking Protocol analysis of Finals Game 1** | ✅ COMPLETE 2026-06-04 SESSION 29 — `05_RESEARCH_EXPERIMENTS/EXPERIMENT_LOG/PDTP_FINALS_G1_20260604.md` written and committed (3abae30, pushed). Covers: architecture PASS (T1/T4 separation, pool_isolated, kill switch, audit logs all worked); commercial FAIL (EXP-017 DIRECTIONAL_NEGATIVE); root cause (missing opponent features F-040); T4 IDEMPOTENCY interference pattern (T4 pre-empts late T1 cron, collapses ~33 MC bets to ~3 actual); path to G6 (T-072 first, then EXP-017 v2, then evidence accumulation on FIXED model). |
| T1 vs T4 bet count explanation | **Answered operator question: "33 bets is the total? What happened to the ~1000s of bets?"** | ✅ COMPLETE 2026-06-04 SESSION 29 — 33 = MC prediction for full T1 capacity. Actual G1 T1 = ~3–6 Kelly-sized bets (large Kelly sizes exhaust bankroll fast; T4 IDEMPOTENCY locks remaining tickers). 1,414 = T4 flat-contract in-game bets from $500 pool_isolated pool. Architecture separation worked as designed. Incorporated into PDTP document. |
| VPS deploy (SESSION 28 fixes) | **Push paper_trader.py same-day fix + run_t4_live.py T4_EXPECTED_TOTAL_EDGE=441.38** | ✅ COMPLETE 2026-06-04 SESSION 29 — f32efa9 deployed to VPS via git pull. T4 old process (PID 154947) killed; new T4 (PID 205448) started with SESSION 28 code. 695/695 tests confirmed. |
| DECISION_LOG SESSION 29 entry | **T4 IDEMPOTENCY interference pattern logged** | ✅ COMPLETE 2026-06-04 SESSION 29 — Notable Judgment Calls entry added: T4 pre-empts T1 late cron via ticker namespace overlap; architectural note for T4 ACTIVE ADR. |

---

## SESSION 2026-06-04 SESSION 28 — COMPLETED

| # | Task | Status |
|---|------|--------|
| Finals G1 resolution | **1417 paper positions resolved via `run_resolve_local.py`** | ✅ COMPLETE 2026-06-04 SESSION 28 — Runtime ~37 min (Playoffs season-type fallback: 2 API calls × 0.6s/position). Results: 1417 settled, 0 open, bankroll $1,404.80, P&L −$95.20 (−6.3%), win rate 30.1%, drawdown 9.5%. Portfolio synced to VPS. Same-day resolution bug fixed: `paper_trader.py:resolve_pending()` `<` → `<=`. Root cause: local PDT date = game date = 2026-06-03; strict `<` excluded all same-day games. |
| EXP-017 Part B G1 | **First real commercial validation run with Finals G1 Kalshi prices** | ✅ COMPLETE 2026-06-04 SESSION 28 — n=32 unique markets, win_rate=21.9%, EV=−$0.162/bet, mean_edge_vs_market=+0.1366. DIRECTIONAL_NEGATIVE. Model beats null (Part A +$0.054) but loses to actual Kalshi prices. Root cause: no opponent quality/defensive intensity features. GG-004 remains OPEN. |
| T4_EXPECTED_TOTAL_EDGE calibration | **Calibrated from Finals G1 T4 audit log** | ✅ COMPLETE 2026-06-04 SESSION 28 — 1446 risk_eval_start records, sum(edge)=441.38. Updated `run_t4_live.py` 5.0 → 441.38. T4_BAND_WEIGHT blocked (GG-011 registered). |
| DECISION_LOG SESSION 28 | **G1 resolution, EXP-017 Part B, G6 floor revision flag** | ✅ COMPLETE 2026-06-04 SESSION 28 — 3 new entries added. |
| MEMORY_BANK/TODO update | **State updated to reflect G1 resolution results** | ✅ COMPLETE 2026-06-04 SESSION 28 |

---

## SESSION 2026-06-04 SESSION 28 — OPEN ITEMS

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| **VPS deploy SESSION 28 changes** | **COMPLETE — f32efa9 deployed, same-day fix live, T4 PID 205448** | IO | ~~CRITICAL~~ DONE | Deployed via git pull on 2026-06-04. T4 old PID 154947 killed; new T4 PID 205448 started with SESSION 28 code. 695/695 tests confirmed on VPS. |
| **Finals Game 2 MC verify** | **Wakeup scheduled — run MC after PIPE-02 fires 22:00 UTC Jun 5** | DS | 🟡 IN PROGRESS — wakeup scheduled | Wakeup will fire hourly, chain until after PIPE-02 fires Jun 5. Then pull pregame_20260605.json + run MC; verify adj_λ adjustments in effect. |
| **Portfolio reset** | **COMPLETE — reset to $1,000 clean slate** | DS | ~~MEDIUM~~ DONE | SESSION 30. G1 archive at `paper_portfolio_g1_archive.json`. New portfolio: bankroll=$1,000, clean slate for adj_λ model evidence window. |
| **GG-004 next step / T-072** | **COMPLETE — ADR-0015 adj_λ deployed. EXP-018 registered** | DS | ~~HIGH~~ DONE | SESSION 30. adj_λ = pts_l10_mean × clip(opp_def_l10/113.0, 0.70, 1.30) targets the exact mechanism that caused DIRECTIONAL_NEGATIVE. EXP-018 will validate. No retrain required. |
| **T-131 — Fee-adjusted edge ADR** | **COMPLETE — ADR-0016 ACCEPTED. GG-009 RESOLVED** | DS | ~~HIGH~~ DONE | SESSION 30. net_edge = gross_edge - 0.07×mid×(1-mid). ADR-0016 artifact exists. GG-009 closed in GOVERNANCE_GAP_LOG. |
| **GG-011 — T4_BAND_WEIGHT ADR** | **New ADR required before T4 ACTIVE for per-evaluation sizing** | DS | LOW now / HIGH before T4 ACTIVE | See GG-011 in GOVERNANCE_GAP_LOG. |

---

## SESSION 2026-06-03 SESSION 27 — COMPLETED

| # | Task | Status |
|---|------|--------|
| Bloomberg terminal rewrite | **`scripts/live_terminal.py` — multi-panel curses layout replacing global-scroll single-pad approach** | ✅ COMPLETE 2026-06-03 SESSION 27 — Full rewrite: 8 independent panels (PORTFOLIO, LIVE POSITIONS, MARKET SNAPSHOT, TODAY'S BETS, ALERTS, RECENTLY RESOLVED, SYSTEM STATUS, T4 LOG TAIL), each with its own curses pad and `scroll_y`. 2-column layout (56%/44%). Tab/Shift+Tab cycles panel focus (focused title turns cyan bold + `↕NN%` scroll indicator). Arrow keys / PgUp/PgDn / Home/End scroll within focused panel. Footer shows control hints. Layout adapts to terminal size via `_compute_layout()`. Atomic curses update via `doupdate()` — zero flicker. |
| Curses ordering bug fix | **Fixed blank-panel rendering: stdscr erased content areas; pad writes were invisible** | ✅ COMPLETE 2026-06-03 SESSION 27 — Root cause: `draw_panel()` called `ps.pad.noutrefresh()` inside each panel draw, then `stdscr.noutrefresh()` ran last → stdscr's blank content areas overwrote pad content in curses' virtual screen buffer → `doupdate()` rendered blank panels despite data present. Fix: moved all pad `noutrefresh` calls to a separate `refresh_pad()` pass that runs AFTER `stdscr.noutrefresh()`. stdscr wins on borders; pads win on content. Data confirmed flowing: 1416 T4 positions, $499.95 deployed, 3 T1 bets. |

---

## SESSION 2026-06-03 SESSION 26 — COMPLETED

| # | Task | Status |
|---|------|--------|
| T-109 automation | **`scripts/poll_and_resolve_g1.py` — auto-trigger T-109 when Finals Game 1 reaches STATUS_FINAL** | ✅ COMPLETE 2026-06-03 SESSION 26 — New file `scripts/poll_and_resolve_g1.py`. Polls ESPN scoreboard every 60s (SCHEDULED) / 90s (IN_PROGRESS). Fallback: triggers T-109 at next 07:30 UTC regardless of ESPN status. Fixed initial fallback bug: same-day time-of-day check → `_compute_fallback_dt()` always computes next future occurrence. Restarted with `caffeinate -s` (PID 5865) to prevent Mac sleep. Currently polling `401859963: STATUS_SCHEDULED`, fallback 2026-06-04T07:30Z. |
| tmpfs diagnosis | **Explained recurring "Step 1 still failing on tmpfs" error** | ✅ DIAGNOSED 2026-06-03 SESSION 26 — Root cause: Claude Code internal task output pipe at `/private/tmp/claude-501/...UUID.../tasks/` reports ENOSPC despite 82GB free disk. Workaround: `find ... \| xargs grep -l ...` instead of `grep -rn`. Permanent fix: `export CLAUDE_CODE_TMPDIR="/Users/earlignacio/.claude/tmp"` in `~/.zshrc` — operator action still pending. |
| Pre-game hygiene | **Confirmed all systems green for Finals Game 1** | ✅ CONFIRMED 2026-06-03 SESSION 26 — VPS T4 PID 154947 STATUS_SCHEDULED; VPS cron PIPE-02 21:55 UTC / PIPE-03 22:00 UTC; portfolio $1,000.00 / 0 open positions; fee annotation + pool_isolated both live. |
| T-132 registered | **Register governance debt: CHANGE_CONTROL.md has decisions_logged: false** | ✅ REGISTERED 2026-06-03 SESSION 26 — See T-132 in SESSION 22/23 OPEN ITEMS below. |

---

## SESSION 2026-06-03 SESSION 25 — COMPLETED

| # | Task | Status |
|---|------|--------|
| Fee annotation fields added | **6 fields added to every paper position: `model_p`, `gross_edge`, `fee_per_contract`, `fee_net_edge`, `fee_contaminated`, `probable_injury_signal`** | ✅ COMPLETE 2026-06-03 SESSION 25 — `paper_trader.py:open_position()` computes and records all six fields. `run_paper_trade.py` and `run_t4_live.py` enrich approval dict with `model_p`/`edge` before calling `open_position()`. Backward-compatible: defaults to 0.0 when fields absent. G6 evidence ledger is now self-annotating — fee-clean and injury-clean subgroup filters run directly from `paper_portfolio.json`. DECISION_LOG entry added. 695/695 tests pass. Commit `8321900`. |
| KI-027 registered | **Kalshi HTTP 503/429 in second PIPE-03 window formally registered** | ✅ COMPLETE 2026-06-03 SESSION 25 — KI-027 entry added to `10_INFRA_OPERATIONS/KNOWN_ISSUES.md`. 4 positions with failed-HTTP status (Wembanyama NO 40/35/30, Castle NO 30). Paper resolution unaffected. Root cause investigation deferred. |
| SESSION 20 OPEN ITEMS closed | **"VPS deploy ADR-0013" and "T4 monitor Finals Game 1" marked COMPLETE in TODO_NEXT.md** | ✅ COMPLETE 2026-06-03 SESSION 25 — Both rows updated with SESSION 24 completion context (nohup PID 153790, pool_isolated=True). |
| MEMORY_BANK portfolio update | **Post-SESSION 24 portfolio state reflected in MEMORY_BANK.md** | ✅ COMPLETE 2026-06-03 SESSION 25 — $1,000 reset, 0 open positions, T4 PID state updated. |
| T4 restart with annotation code | **VPS T4 process killed (PID 153790) and restarted (PID 154947) to pick up new annotation code** | ✅ COMPLETE 2026-06-03 SESSION 25 — Startup log confirmed: `PAPER_T4_FLAT_SIZING=true`, `PAPER_T4_VIRTUAL=false`, `Pool=$500.00`, watching `STATUS_SCHEDULED`. New annotated `open_position()` now active for Finals Game 1. |
| DECISION_LOG SESSION 25 entry | **Fee annotation + injury signal architecture decision logged** | ✅ COMPLETE 2026-06-03 SESSION 25 — Notable Judgment Calls entry added: annotate every paper position with 6 fields to make G6 evidence self-annotating without retroactive join. |

---

## SESSION 2026-06-03 SESSION 22/23 — OPEN ITEMS

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| **VPS T4 verify + pool_isolated deploy** | **COMPLETE — dfb16f0 on VPS; T4 running with fix** | IO | ~~CRITICAL~~ DONE | Commit dfb16f0 pushed to remote and pulled to VPS. pool_isolated=True deployed: T4 no longer depletes T1 bankroll (Disconnect 2 resolved). T4 restarted PID 153790. If process dies restart: `ssh root@157.230.91.33 'cd /opt/prediction-market-bot && nohup bash -c "set -a; source .env; set +a; source venv/bin/activate; PYTHONPATH=src python3 src/prediction_market_bot/run_t4_live.py >> logs/t4_live.log 2>&1" > /dev/null 2>&1 &'`. **Critical: must include `set -a; source .env; set +a` — omitting causes VENUE_API_KEY crash.** |
| **RESERVE_MANDATE_PCT fix** | **COMPLETE — 0.20→0.05 on VPS; all 33 T1 bets fire** | IO | ~~HIGH~~ DONE | VPS `.env` updated. Floor dropped from $200 to $50. MC confirmed: 33 bets PLACED, $827 total, no BATCH HALT (Disconnect 1 resolved). Advisory MC warning `82.7% > 60%` is informational display threshold, not the execution gate. |
| **T-132 — CHANGE_CONTROL.md governance debt** | **Extract decisions from `08_MODEL_RISK_GOVERNANCE/CHANGE_CONTROL.md` → DECISION_LOG.md; set decisions_logged: true** | DS | **LOW — before any session that modifies CHANGE_CONTROL.md** | Identified SESSION 26. File has `decisions_logged: false`. No current-session modifications — no urgency. Resolve before any future session that edits the document. |
| **T-131 — Fee-adjusted edge ADR** | **COMPLETE — ADR-0016 ACCEPTED, GG-009 RESOLVED** | DS | ~~HIGH~~ DONE | SESSION 30. Option B: `net_edge = gross_edge - 0.07×mid×(1-mid)`. `gross_edge` and `kalshi_fee` logged to every position record. `paper_trader.py` backward-compat updated. |
| **T-130 — Decision tree rework per bucket** | **COMPLETE — ADR-0014 ACCEPTED** | DS | ~~HIGH~~ DONE | ADR-0014 at `03_DECISIONS/ADR-0014_per-band-decision-tree-mechanics.md`. Both DS questions resolved: (Q1) no T3 multiplier — regression test run, 1.15× arbitrary at KELLY_T3=0.07; (Q2) shared budget is design intent. GG-010 registered and RESOLVED. |
| **Post-Finals G1 T4 calibration** | **Run `run_t4_budget_sim.py --from-log logs/audit_t4.jsonl` after Finals Game 1** | DS | **HIGH — after game** | Extract: (1) T4_BAND_WEIGHT calibration (total_deployed / (bankroll × 0.60)); (2) actual bets placed count vs ~1,050 design throughput. Compare actual fires vs expected at flat sizing. Replace STUB comments in `run_t4_live.py`. Decision log derivation. Redeploy before Finals Game 2. |
| **Post-Finals G1 resolve** | **AUTOMATED — `scripts/poll_and_resolve_g1.py` (PID 5865) will run T-109 automatically when game ends** | DS | ~~HIGH~~ AUTOMATED | `BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_local.py` + `fetch_kalshi_prices.py --portfolio`. SESSION 26: auto-trigger deployed. Script polls ESPN every 60–90s; fallback 2026-06-04T07:30Z. No operator action needed. |
| KI-027 API rate errors | **Investigate Kalshi HTTP 503/429 in second PIPE-03 window** | IO | MEDIUM | 4 positions with failed-HTTP status. Check VPS logs for rate limit (429) or server error (503). May require backoff/retry in `paper_trader.py`. |
| Portfolio reset option | **Evaluate portfolio reset to $1,000 before Finals Game 2** | DS | MEDIUM — post-G1 resolve | After Finals Game 1 resolves: review bankroll, P&L, position outcomes. If mixed signal, reset before Finals Game 2 T1 cron (21:55 UTC Jun 5). |
| Finals Game 2 MC verify | **Run Monte Carlo before Finals Game 2 T1 cron** | DS | HIGH — Jun 5 PDT before 2:55 PM PDT | `BOT_ENV=paper PYTHONPATH=src python3 scripts/run_monte_carlo.py --label pre-g2`. Expect 40–50 bets. If still low: check cursor pagination, reserve floor, market availability. |

---

## SESSION 2026-06-03 SESSION 22/23 — COMPLETED

| # | Task | Status |
|---|------|--------|
| Kalshi operational constraints research | **Sourced Kalshi taker/maker fee formula, confirmed $0.01 actual contract minimum, rate limits (10k/day API), TOS automated trading policy** | ✅ COMPLETE 2026-06-03 SESSION 22/23 — Taker fee: `0.07 × P × (1−P)`. At P=0.50: $0.0175/contract. Maker fee: `0.0175 × P × (1−P)`. Actual Kalshi minimum: $0.01/contract (1 contract at minimum price). Rate limit: 10,000 requests/day standard tier. Automated trading: permitted per TOS. GG-009 registered. |
| MIN_BET_T4_PAPER correction | **Changed from $10.0 (invented heuristic) to $0.01 (actual Kalshi minimum)** | ✅ COMPLETE 2026-06-03 SESSION 22/23 — `run_t4_live.py` line 251. Prior value was $10.0 set in SESSION 18 as "Kalshi practical minimums" — never sourced. Actual Kalshi minimum is 1 contract at market price ($0.01–$0.99). Decision logged. Memory feedback written. |
| PAPER_T4_VIRTUAL default → false | **Default changed from `true` to `false` — actual paper positions now fire** | ✅ COMPLETE 2026-06-03 SESSION 22/23 — `run_t4_live.py` line 252. `PAPER_T4_VIRTUAL = os.environ.get("PAPER_T4_VIRTUAL", "false").lower() in ...`. Previous: virtual-only calibration mode. Now: `trader.open_position()` called, positions recorded in `paper_portfolio.json`. Purpose: validate execution layer throughput at actual bet scale. |
| PAPER_T4_FLAT_SIZING added | **New env var: flat 1-contract sizing (at MIP) overrides Kelly for paper T4 validation** | ✅ COMPLETE 2026-06-03 SESSION 22/23 — `run_t4_live.py` lines 253, ~300–310. `PAPER_T4_FLAT_SIZING = os.environ.get("PAPER_T4_FLAT_SIZING", "true").lower() in ...`. When true: `approved_size = mip; approval = {**approval, "approved_size": approved_size}`. Both local variable AND approval dict updated (trader.open_position uses dict). Purpose: decouple bet COUNT from Kelly sizing — Kelly at t4_band_budget=$60 caps to ~60 bets before exhaustion; flat sizing allows ~1,050 bets at design throughput. |
| PAPER_T4_POOL_USD=500.0 added | **When flat sizing active, band budget override to $500 (bypasses ADR-0013 Kelly computation)** | ✅ COMPLETE 2026-06-03 SESSION 22/23 — `run_t4_live.py` main(). `PAPER_T4_POOL_USD = float(os.environ.get("PAPER_T4_POOL_USD", "500.0"))`. When `PAPER_T4_FLAT_SIZING=true`: `t4_band_budget = PAPER_T4_POOL_USD` (not `_compute_t4_band_budget()`). Rationale: ~1,050 bets × avg $0.50/contract = $525 ≈ $500 pool. ADR-0013 Kelly budget is not superseded — it applies when flat sizing is off. |
| MIN_BET_T1_PAPER added | **`run_paper_trade.py` + `scripts/run_monte_carlo.py` now use configurable floor** | ✅ COMPLETE 2026-06-03 SESSION 22 — `MIN_BET_T1_PAPER = float(os.environ.get("MIN_BET_T1_PAPER", "1.0"))`. Both RiskEngine instantiations in `run_paper_trade.py` receive `min_bet_usd=MIN_BET_T1_PAPER`. VPS `.env` updated with `MIN_BET_T1_PAPER=1.0`. |
| GG-009 registered | **Taker fee absent from edge formula — governance gap formally registered** | ✅ COMPLETE 2026-06-03 SESSION 23 — `03_DECISIONS/GOVERNANCE_GAP_LOG.md` GG-009 added. At P=0.50, taker fee = $0.0175 = 87% of MIN_EDGE=0.02. T-131 ADR required for resolution before G6. |
| VPS old T4 screen killed | **`149029.t4_live` (running PAPER_T4_VIRTUAL=true old code) killed** | ✅ COMPLETE 2026-06-03 SESSION 22/23 — `screen -X -S 149029.t4_live quit` confirmed. VPS `git pull` to commit `00d0525`. |
| VPS new T4 process started | **T4 running on VPS — confirmed 2026-06-03 SESSION 23** | ✅ COMPLETE — PID 152702. Root cause of earlier failures: nohup command didn't source `.env` → VENUE_API_KEY not set → crash at kalshi_client init. Fix: `set -a; source .env; set +a` before activate. Startup confirmed: T4 band budget $500.00 (flat sizing mode), PAPER_T4_FLAT_SIZING=true, PAPER_T4_VIRTUAL=false, ESPN game 401859963 STATUS_SCHEDULED → sleeping 60s. Will auto-activate at tip-off 00:30 UTC Jun 4. |
| DECISION_LOG SESSION 23 entry | **T4 flat sizing architecture decision logged** | ✅ COMPLETE 2026-06-03 SESSION 23 — Notable Judgment Calls entry added: T4 flat 1-contract sizing for paper throughput validation; PAPER_T4_VIRTUAL=false default; MIN_BET_T4_PAPER→0.01. |
| 695 tests | **Test count unchanged — all passing** | ✅ CONFIRMED 2026-06-03 SESSION 23 — 695/695 tests pass locally. |

---

## SESSION 2026-06-02 SESSION 20 (PDT) — OPEN ITEMS

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| **VPS deploy ADR-0013** | ~~Deploy updated `run_t4_live.py` to VPS before Finals G1 tip-off~~ | IO | ~~CRITICAL — before game~~ | ✅ COMPLETE — SESSION 24. VPS on commit `dfb16f0`. Old `140907.t4_live` screen superseded by nohup PID 153790 with `pool_isolated=True` + `PAPER_T4_FLAT_SIZING=True`. ADR-0013 code deployed. |
| **Post-G1 T4 calibration** | ~~Run `run_t4_budget_sim.py --from-log logs/audit_t4.jsonl` after G1 to calibrate stubs~~ | DS | ~~HIGH~~ | ✅ PARTIAL — SESSION 28 (2026-06-04). (1) T4_EXPECTED_TOTAL_EDGE updated 5.0 → 441.38 (G1: 1446 evals, sum edge from risk_eval_start records, KELLY_T4=0.20). DECISION_LOG updated. (2) T4_BAND_WEIGHT cannot be calibrated: calibration script requires VIRTUAL data, G1 ran non-virtual flat-sizing. Critical finding: uncapped Kelly deployment = $81,226 across 1434 bets = 87× any band budget — fractional-allocation formula is architecturally incompatible with high-throughput T4. GG-011 registered. New ADR required before T4 ACTIVE. |
| Finals Game 1 resolve | **Run `run_resolve_local.py` after Finals Game 1 ends (Jun 3 PDT ~11:30 PM EDT)** | DS | **HIGH — immediately after game** | `BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_local.py`. Then `fetch_kalshi_prices.py --portfolio` to sync pregame files for EXP-017. 11 open positions; all resolve on player stats (Kalshi order status irrelevant). EXP-017 n=2 → will grow. |
| T4 monitor Finals Game 1 | ~~Monitor `140907.t4_live` during Finals Game 1~~ | IO | ~~HIGH — game night~~ | ✅ COMPLETE — SESSION 24. `140907.t4_live` screen was dead (old code); replaced by nohup PID 153790 running updated `run_t4_live.py`. Finals Game 1 T4 monitoring complete. |
| KI-027 API rate errors | **Investigate Kalshi HTTP 503/429 in second PIPE-03 window (01:30 UTC Jun 3)** | IO | MEDIUM | 4 positions recorded with failed-HTTP status (Wembanyama NO 40/35/30, Castle NO 30). Paper resolution unaffected. Root cause: rate limit (429) or server error (503)? Check VPS logs. May require backoff/retry logic in `paper_trader.py`. |
| Portfolio reset option | **Evaluate portfolio reset to $1,000 before Finals Game 2 (Jun 5 PDT)** | DS | MEDIUM — post-Finals Game 1 resolve | After Finals Game 1 resolves: review bankroll, P&L, position outcomes. If mixed signal (canceled + failed positions muddy the evidence), reset to $1,000 clean slate before Finals Game 2 T1 cron (21:55 UTC Jun 5). Recommendation from SESSION 19: let Finals Game 1 run; reassess post-resolution. |
| Finals Game 2 MC verify | **Run Monte Carlo before Finals Game 2 T1 cron to verify expected bet count** | DS | HIGH — Jun 5 PDT before 2:55 PM PDT | `BOT_ENV=paper PYTHONPATH=src python3 scripts/run_monte_carlo.py --label pre-g2`. Expect 40–50 bets (vs 11 for Finals Game 1 where first-window architecture was old). If still low: check cursor pagination, reserve floor, market availability. |
| **T-130 — Decision tree mechanics per band** | **Formally specify quantitative computation per T1–T5 bucket: model inputs, probability estimate method, Kelly variant, kill switch tier** | DS | HIGH — before T4 ACTIVE | CLAUDE.md Hard Rule 9 establishes that model computation determines routing. T-130 specifies *what* that computation is per bucket. Longer time horizon = more complex decision tree — this gradient must be documented. Required as one of T4 ACTIVE activation gates (supersedes or supplements ADR-0013 gate 4). Output: new ADR or expansion of ADR-0011 specifying per-band decision mechanics. |

---

## SESSION 2026-06-02 SESSION 20 (PDT) — COMPLETED

| # | Task | Status |
|---|------|--------|
| KI-026 ADR-0013 architecture | **T4 band budget architecture: Kelly scoped to `t4_band_budget`, not full portfolio bankroll** | ✅ COMPLETE 2026-06-02 SESSION 20 — `run_t4_live.py` updated (import RESERVE_MANDATE_PCT, T4_BAND_WEIGHT=0.10 stub, T4_EXPECTED_TOTAL_EDGE=5.0 stub, `_compute_t4_band_budget()`, `_make_engines(t4_band_budget)`, `_run_cycle()` returns updated `t4_deployed_usd`, main loop accumulates `t4_deployed_game`). ADR-0013 written at `03_DECISIONS/ADR-0013_t4-throughput-capital-budget.md`. Syntax OK. |
| run_t4_budget_sim.py | **Write and verify T4 budget Monte Carlo simulation script** | ✅ COMPLETE 2026-06-02 SESSION 20 — `scripts/run_t4_budget_sim.py` written. Parametric mode (pre-G1) and empirical mode (`--from-log`, post-G1 calibration). Verified at $618.03 bankroll: budget=$37.08, avg 37 bets, exhausts at cycle 125/200 (63% into game), all bets floor to $1 paper minimum. Sensitivity: band_weight=0.15 → 73% exhaustion rate; band_weight=0.20 → 6.6% exhaustion rate. |
| T1 Monte Carlo verification | **Confirm T1 Monte Carlo unaffected by T4 architecture changes** | ✅ COMPLETE 2026-06-02 SESSION 20 — `scripts/run_monte_carlo.py --label pre-G1-ADR-0013` ran clean. Same T1 logic, same bet structure. T4 changes isolated to `run_t4_live.py`. |
| DECISION_LOG ADR-0013 entry | **Log ADR-0013 in DECISION_LOG per CLAUDE.md Rule 7** | ✅ COMPLETE 2026-06-02 SESSION 20 — ADR-0013 added to ADR Index table + Notable Judgment Calls with full derivation rationale. |

---

## SESSION 2026-06-02 SESSION 19 (PDT) — OPEN ITEMS (carried forward above)

---

## SESSION 2026-06-02 SESSION 19 (PDT) — COMPLETED

| # | Task | Status |
|---|------|--------|
| Bug H drawdown fix (T4) | **Fix drawdown calculation in `run_t4_live.py` — deployed T1 capital counted as realized loss** | ✅ COMPLETE 2026-06-02 SESSION 19 — `_realized_loss = max(0.0, -portfolio.get("total_realized_pnl", 0.0))`. Old formula: `(initial - current) / initial` counted deployed T1 capital (~$540) as loss → 54% false drawdown → C4 kill switch rejected ALL T4 bets pre-game. Fix matches PIPE-03 reference pattern. Commit `706264b`. |
| PAPER_T4_VIRTUAL mode | **Add virtual mode: C4 evaluates + stages bets without bankroll deduction** | ✅ COMPLETE 2026-06-02 SESSION 19 — `PAPER_T4_VIRTUAL = os.environ.get("PAPER_T4_VIRTUAL", "true").lower() in ("true", "1", "yes")`. Virtual path: `store.mark_fired()` + logger `"T4 VIRTUAL"` line, no `trader.open_position()`. Proves architecture fires at ~1000s/game without depleting T1 capital pool. Commit `706264b`. |
| VPS screen restart | **Kill old screen `139678.t4_live`; restart with Bug H fix** | ✅ COMPLETE 2026-06-02 SESSION 19 — Old screen ran stale code with drawdown bug. `git pull` → commit `706264b`. New screen `140907.t4_live` confirmed running, watching Finals G1 (STATUS_SCHEDULED → will auto-activate at tip-off Jun 3 PDT 8:30 PM EDT). |
| G1/G2 label correction | **Correct game label errors: SESSION 18 mislabeled Finals G1 as G2 and used internal ESPN game IDs as primary labels** | ✅ COMPLETE 2026-06-02 SESSION 19 — SESSION 18 used ESPN game ID as primary label in all docs — replaced with Finals G1/G2/G3. ESPN IDs kept only in technical monitoring commands. Finals schedule pinned: G1=Jun 3 PDT, G2=Jun 5 PDT, G3=Jun 8 PDT. |

---

## SESSION 2026-06-03 SESSION 18 — COMPLETED

| # | Task | Status |
|---|------|--------|
| PIPE-07 T4 live | **`run_t4_live.py` — full PIPE-07 wiring T4EventLoop → staged_order_store → C4 → PaperTrader** | ✅ COMPLETE 2026-06-03 SESSION 18 — `src/prediction_market_bot/run_t4_live.py` built from scratch. 45s poll cycle, ESPN live boxscore, per-cycle `fired_tickers` deduplication, ghost-protection ordering (stage BEFORE open), `MIN_BET_T4_PAPER=1.0` paper override. ESPN API replaces blocked NBA CDN (`cdn.nba.com` / `stats.nba.com` return 403 from DO VPS via Akamai WAF). `KalshiMarketClient.from_env()` fix committed. `BOT_C4_ACTIVE=true` added to VPS `.env`. Commits: `451abf2` (from_env fix), `47e9a2b` (PIPE-07 build), `2446a02` (ESPN main loop). VPS screen watching Finals G1 (NYK vs SAS), sleeping until tip-off Jun 3 PDT 8:30 PM EDT. 695/695 tests on VPS. |
| ESPN API source | **Replace NBALiveFeed with ESPN API for T4 live data** | ✅ COMPLETE 2026-06-03 SESSION 18 — `_espn_game_ids_today()`, `_parse_espn_clock()`, `_espn_poll_once()` implemented in `run_t4_live.py`. Player matching via `name_to_pregame` dict (normalized lowercase). `_load_pregame_context()` updated to return 3-tuple (by_player_id, by_ticker, name_to_pregame). Main loop: `for gid in game_ids: all_states.extend(_espn_poll_once(gid, name_to_pregame))`. Decision logged. |
| risk.py MIN_BET_USD | **Add `min_bet_usd` init param to RiskEngine for paper T4 override** | ✅ COMPLETE 2026-06-03 SESSION 18 — `min_bet_usd: float | None = None` param on `RiskEngine.__init__()`. CHECK 7 uses `self._min_bet_usd` instead of `MIN_BET_USD`. Live path unchanged. Paper T4 uses `$1.0` floor. No ADR required (paper-only). Decision logged. |
| Session documentation | **DECISION_LOG entries (4 decisions), TODO_NEXT, MEMORY_BANK, SESSION_HANDOFF** | ✅ COMPLETE 2026-06-03 SESSION 18 — All governance artifacts updated. |

---

## SESSION 2026-06-03 SESSION 18 — OPEN ITEMS (game night)

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| G1 resolve | **Run `run_resolve_local.py` after G1 tip-off resolves (Jun 4 UTC post-game)** | DS | **HIGH — immediately after game** | After NYK vs SAS **G1** ends (tips 00:30 UTC Jun 4 = Jun 3 PDT 8:30 PM EDT): `BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_local.py`. Then run `fetch_kalshi_prices.py --portfolio` to sync VPS pregame files for EXP-017. EXP-017 n=2 → will grow to n=2 + Finals **G1** market count (~35 markets). |
| T4 monitor | **Monitor t4_live screen session during G1 (00:30–03:30 UTC Jun 4 = Jun 3 PDT evening)** | IO | **HIGH — G1 game night Jun 3 PDT** | `ssh root@157.230.91.33 'tail -f /opt/prediction-market-bot/logs/t4_live.log'`. Watch for: (1) status transitions from STATUS_SCHEDULED → STATUS_IN_PROGRESS; (2) first `_run_cycle()` execution; (3) T4 VIRTUAL log lines (scale proof); (4) any ESPN fetch errors or NameError. Kill switch: `ssh root@157.230.91.33 'touch /opt/prediction-market-bot/logs/t4_kill_switch.flag'` |
| T4 session doc | **Register ESPN API source decision in a new ADR (DS-02 replacement ADR) if T4 goes ACTIVE** | DS | MEDIUM — dark period | ADR-0011 scoped T4 to "NBA Stats API CDN polling" — that's now ESPN API. If T4 evidence (EXP-018) validates the approach, ADR-0011 should be superseded by an ADR that explicitly names ESPN as the DS-02 source and documents its limitations (unofficial API, no SLA guarantee, schema may change). |

---

## SESSION 2026-06-02 SESSION 17 — COMPLETED

| # | Task | Status |
|---|------|--------|
| ~~KI-025~~ | ~~PIPE-02 cron retimed 21:30 → 21:55 UTC + second PIPE-02 at 01:25 UTC~~ | ✅ COMPLETE 2026-06-02 SESSION 17 — Root cause: 30-minute price drift gap between PIPE-02 capture and PIPE-03 execution caused MC to predict 23 bets but only 7 placed on G1. Fix: `deploy/cron.conf` PIPE-02 moved to 55 21 UTC; second PIPE-02 at 25 1 UTC for late window (which previously had 4h-stale prices). KI-025 RESOLVED. |
| Market-first loop | **Cohort-first → market-first in PIPE-02 + PIPE-03** | ✅ COMPLETE 2026-06-02 SESSION 17 — `run_paper_trade.py` + `run_pregame.py`: iterate over all active Kalshi markets, resolve players via cohort lookup or dynamic nba_api fallback. Non-cohort players: `NBAIngestionClient.fetch_player_game_log(season="2025-26")` → `pts_l10_mean` → Poisson-only (`p_est_lr = None`). `_pts_cache` prevents duplicate API calls. Covers 100% of KXNBAPTS-listed players, not just 55-player EXP-005 cohort. |
| Cursor pagination | **`fetch_player_points_markets` now paginates all Kalshi pages** | ✅ COMPLETE 2026-06-02 SESSION 17 — `kalshi_client.py`: while-loop with `cursor` field; break when `cursor` is None or `len(page) < page_size`. Was silently truncating at 200 markets on regular-season nights with 800+ KXNBAPTS markets. |
| Batch reserve gate | **PIPE-03 batch-level reserve floor enforcement** | ✅ COMPLETE 2026-06-02 SESSION 17 — `run_paper_trade.py`: before every `open_position()`, check `bankroll - approved_size < RESERVE_MANDATE_PCT (0.40) * _initial_bankroll`. If true: log warning, set `_reserve_halted = True`, break both loops. Prevents repeat of Jun 1 incident (91.2% bankroll deployed in one run). |
| DECISION_LOG | **Session 17 decisions logged (5 entries)** | ✅ COMPLETE 2026-06-02 SESSION 17 — Market-first loop, dynamic nba_api fallback, batch reserve gate, cron retiming, cursor pagination all logged. |

---

## SESSION 2026-06-02 SESSION 17 — OPEN ITEMS

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| MC verify | **Verify next Finals game bet count with new architecture** | DS | **HIGH — G2 (Jun 5 PDT / Jun 6 00:30 UTC)** | All four fixes are live on VPS. G2 is the first real test of the market-first loop + cursor pagination + cron retiming: expect 40–50 bets (vs 7 in G1 with old architecture). If bet count is still low, check: (1) how many active KXNBAPTS markets Kalshi has for the game; (2) whether non-cohort players resolve via dynamic nba_api path; (3) whether `_reserve_halted` fires prematurely. Run MC after PIPE-02 fires (21:55 UTC) to compare prediction vs actual. Finals schedule: G1=Jun 3 PDT, G2=Jun 5 PDT, G3=Jun 8 PDT, G4=Jun 10 PDT, G5=Jun 13 PDT. |
| EXP-017 | **Re-run EXP-017 after each game to accumulate n toward G6 floor (≥66)** | DS | HIGH | n=2 unique resolved markets as of session end. Every Finals game adds ~7–50 markets. Run T-109 procedure after each game (local resolution, then fetch pregame files from VPS). |

---

## SESSION 2026-06-02 SESSION 16 — COMPLETED

| # | Task | Status |
|---|------|--------|
| Monte Carlo protocol | **`scripts/run_monte_carlo.py` + `03_DECISIONS/MONTE_CARLO_PROTOCOL.md`** | ✅ COMPLETE 2026-06-02 SESSION 16 — CLI-parameterized general assessment tool; mirrors PIPE-03 Path B + Kelly exactly; 10k sims; BOT STATISTICS (bets placed/YES/NO split, bets exp. to WIN/LOSE, MC averages, total staked, reserve, per-player breakdown, bet-level detail, rejected list with reasons) + EV + P/L distribution + governance footer. `--label` + `--out` flags enable before/after comparison. `MONTE_CARLO_PROTOCOL.md` defines 8 trigger conditions, run procedures, output interpretation, known limitations. Decision logged in DECISION_LOG Session 16. Commit d8ec72d; VPS current. |
| G1 T1 cron observation | **7 bets placed / $381.97 deployed (MC predicted 23 / $796)** | ✅ OBSERVED — G1 T1 cron fired 22:00 UTC Jun 2. Bankroll: $1,000 → $618.03. 7 open positions, 0 resolved. MC vs actual discrepancy root-caused and fixed in SESSION 17: (1) 30-min price drift KI-025 → cron retiming; (2) 55-player cohort ceiling → market-first loop; (3) 200-market API cap → cursor pagination. |
| ~~KI-025~~ | ~~**Investigate MC vs actual bet-count discrepancy (23 predicted → 7 placed in G1)**~~ | ✅ RESOLVED 2026-06-02 SESSION 17 — Three root causes identified and fixed. See SESSION 17 COMPLETED above. |

---

## SESSION 2026-06-02 SESSION 15 — COMPLETED

| # | Task | Status |
|---|------|--------|
| ~~KI-018~~ | ~~Fix zombie daily loss limit (max_daily_loss_usd=1000.0 inactive at $1,000 bankroll)~~ | ✅ COMPLETE 2026-06-02 SESSION 15 — `MAX_DAILY_LOSS_PCT=0.15` replaces `max_daily_loss_usd` in `risk.py`. `initial_bankroll` parameter added to `RiskEngine.__init__()`. Daily loss threshold = 15% of initial_bankroll = $150 (fires before 20% drawdown = $200). Two independent kill switches restored. ADR-0012 ACCEPTED. |
| ~~RESERVE_MANDATE_PCT wire~~ | ~~Advisory warning in evaluate_forecast() for single bet exceeding 60% of bankroll~~ | ✅ COMPLETE 2026-06-02 SESSION 15 — `risk_reserve_mandate_warning` log emitted (severity=WARNING) when `approved_size > bankroll * (1 - RESERVE_MANDATE_PCT=0.40)`. Warning-only at paper scale; blocking enforcement deferred to PIPE-03 batch-level check (dark period). |
| ~~T-093~~ | ~~Extract decisions from EXECUTION_ARCHITECTURE.md → DECISION_LOG.md; set decisions_logged: true~~ | ✅ COMPLETE 2026-06-02 SESSION 15 — DECISION_LOG entry logged; header flipped true. |
| ~~T-094~~ | ~~Extract decisions from MONITORING_DRIFT_PLAN.md → DECISION_LOG.md; set decisions_logged: true~~ | ✅ COMPLETE 2026-06-02 SESSION 15 — DECISION_LOG entry logged; header flipped true. |
| ~~T-095~~ | ~~Extract decisions from METHODOLOGY.md → DECISION_LOG.md; set decisions_logged: true~~ | ✅ COMPLETE 2026-06-02 SESSION 15 — DECISION_LOG entry logged; header flipped true. |
| ~~T-096~~ | ~~Extract decisions from VENUE_REGISTRY.md → DECISION_LOG.md; set decisions_logged: true~~ | ✅ COMPLETE 2026-06-02 SESSION 15 — DECISION_LOG entry logged; header flipped true. |
| ~~T-097~~ | ~~Extract decisions from RISK_APPETITE_CONSTRAINTS.md → DECISION_LOG.md; set decisions_logged: true~~ | ✅ COMPLETE 2026-06-02 SESSION 15 — DECISION_LOG entry logged; header flipped true. |
| ~~T-098~~ | ~~Extract decisions from QUALITATIVE_SIGNALS.md → DECISION_LOG.md; set decisions_logged: true~~ | ✅ COMPLETE 2026-06-02 SESSION 15 — DECISION_LOG entry logged; header flipped true. |
| ~~T-099~~ | ~~Extract decisions from ROADMAP_MILESTONES.md → DECISION_LOG.md; set decisions_logged: true~~ | ✅ COMPLETE 2026-06-02 SESSION 15 — DECISION_LOG entry logged; header flipped true. |

---

## SESSION 2026-06-02 SESSION 13/14 — COMPLETED

| # | Task | Status |
|---|------|--------|
| ~~T-129~~ | ~~Fix all-threshold loop: replace LR p_est with Poisson CDF per threshold (GG-008)~~ | ✅ COMPLETE 2026-06-02 SESSION 14 — `run_paper_trade.py`: `p_threshold = 1.0 - _poisson_cdf(thresh_int - 1, pts_mean)` per threshold. LR `p_est` retained as `p_estimate_lr` in C6 log. GG-008 RESOLVED. |
| ~~ADR-0010~~ | ~~Band Kelly hierarchy revision — variance-scaling derivation~~ | ✅ COMPLETE 2026-06-02 SESSION 14 — `ADR-0010_band-kelly-hierarchy-revision.md` ACCEPTED. Kelly hierarchy: T3=0.07 < T1=0.10 < T2=0.13 < T4=0.20 < T5=0.25. `execution_bands.py`, `game_state_model.py` updated. 3 test invariants updated. |
| ~~ADR-0011~~ | ~~Phase 8 paper-scope T4/T5 activation ADR~~ | ✅ COMPLETE 2026-06-02 SESSION 14 — `ADR-0011_phase8-paper-scope-t4t5-activation.md` ACCEPTED. Explicit scope: NBA Stats API CDN polling, file kill switch, paper only. Production blockers deferred. EXP-018/019 gates before ACTIVE. |
| ~~DS-02 adapter~~ | ~~Build ds02_nba_live.py + wire kill switch in run_t4_inplay.py~~ | ✅ COMPLETE 2026-06-02 SESSION 14 — `c1_signal_ingestion/ds02_nba_live.py`: `NBALiveFeed`, `LivePlayerState`, `kill_switch_armed()`, `_parse_game_clock()`. `run_t4_inplay.py`: `_kill_switch_armed()` stub replaced with live `kill_switch_armed(KILL_SWITCH_PATH)` call. |
| ~~Portfolio reset~~ | ~~reset_paper_portfolio.py + VPS reset + deploy~~ | ✅ COMPLETE 2026-06-02 SESSION 14 — `reset_paper_portfolio.py` built; VPS reset confirmed ($1,000 / 0 positions); both commits (d8340ba + 1d10b7e) pushed and pulled on VPS. 692/692 tests on VPS. |
| ~~RESERVE_MANDATE_PCT~~ | ~~Add 40% reserve mandate to risk.py~~ | ✅ COMPLETE 2026-06-02 SESSION 14 — `RESERVE_MANDATE_PCT = 0.40` added to `risk.py`. Warning-only at paper scale; blocking at live capital. |

---

## SESSION 2026-06-02 SESSION 13 — OPEN TASKS (dark period / Phase 8 pre-activation)

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| T-128 | **DS-02 ADR: require live rolling pace as mandatory feed field** | DS | **HIGH — Phase 8 pre-activation** | KI-024: `pace_pts_per_min` is set at T1 from C2 feature store and never refreshed during a game. λ = pace × time_remaining drives both T4 and T5 Poisson CDF — a stale pace propagates linearly into every in-game probability estimate. At T5 (≤3 min remaining), λ is small and pace error translates directly to P(hit threshold) error. The Phase 8 DS-02 ADR must explicitly require live rolling pace as a required feed field, not optional enrichment. Without this constraint, a DS-02 source that provides only score + clock (no pace) would silently degrade T4/T5 inference. Resolution: operator reviews DS-02 ADR draft and adds live pace as a required field before signing. |
| EXP-018 | **T4_MIN_DELTA_P calibration experiment** | DS | **MEDIUM — Phase 8 pre-activation** | GG-007 (item 1): T4_MIN_DELTA_P=0.08 retained for paper prototype to generate calibration data. Requires replay of historical NBA game-state snapshots. Gate: must complete before Phase 8 T4 activation ADR is signed. |
| EXP-019 | **T5 certainty threshold calibration experiment** | DS | **MEDIUM — Phase 8 pre-activation** | GG-007 (item 2): T5_YES_CERTAINTY=0.85 / T5_NO_CERTAINTY=0.15 grounded by Poisson arithmetic (SESSION 14). Requires calibration against historical Q4 ≤3 min game-state data. Gate: must complete before Phase 8 T5 activation ADR is signed. |

---

## SESSION 2026-06-01 SESSION 10 — COMPLETED

| # | Task | Status |
|---|------|--------|
| ~~ADR-0009~~ | ~~Shadow model policy accepted~~ | ✅ COMPLETE 2026-06-01 — `03_DECISIONS/ADR-0009_shadow-model-policy.md` accepted before code per Compass OS invariant. Isolation guarantee: shadow never routes to C4. Promotion gate: shadow_brier_30 ≤ prod_brier - 0.005 over ≥30 events → WARNING; ADR-0010 required for promotion. Frozen model extension: shadow version-pinned at deployment. |
| ~~T-119~~ | ~~Model version hash guard~~ | ✅ COMPLETE 2026-06-01 — `run_pregame.py`: after loading prod_model.joblib, checks `artifact["model_version"]` vs `prod_model_meta.json`. Mismatch → CRITICAL log + exit(1). Absent meta file → guard skips (backward compatible). |
| ~~T-120~~ | ~~ShadowForecaster C3 + PIPE-02 integration~~ | ✅ COMPLETE 2026-06-01 — `c3_forecasting/shadow_forecaster.py`: optional parallel inference; C6-only; non-fatal (_load() + predict_shadow() both catch all exceptions). C7 monitor: `_shadow_window` deque + `record_shadow_outcome()` + shadow Brier computed independently of production window + `shadow_promotion_flag` in DriftSnapshot. PIPE-02 wired: `shadow_p_estimate` + `shadow_model_version` in all forecast records. 15 new C3 shadow tests + 11 new C7 shadow tests. 612/612 pass. |

---

## SESSION 2026-06-01 SESSION 12 — COMPLETED

| # | Task | Status |
|---|------|--------|
| T4/T5 Iteration Plan | **Dark-period T4/T5 roadmap designed** | ✅ COMPLETE 2026-06-01 — Jane Street pre-computation principle applied: detection band ≠ execution band. Phase 7/8/9 sequencing adopted. Three Phase 8 blockers identified (DS-02 ADR, kill switch redesign ADR, Phase 8 infra ADR) — all require operator decision. |
| `game_state_model.py` | **T4 Bayesian engine + T5 late-game arithmetic** | ✅ COMPLETE 2026-06-01 — `src/prediction_market_bot/c3_forecasting/game_state_model.py`. Poisson CDF pure Python stdlib. `GameState`, `GameStateModel.update()` → `T4Signal`, `LateGameArithmetic.evaluate()` → `T5Signal`. Constants: T4_MIN_DELTA_P=0.08, T5_TIME_THRESHOLD_MIN=3.0, T5_YES_CERTAINTY=0.85, T5_NO_CERTAINTY=0.15, KELLY_T4=0.05, KELLY_T5=0.15. 33 tests (test_c3_game_state_model.py). Phase: SKELETON. |
| `staged_order_store.py` | **SQLite pre-staging handoff layer** | ✅ COMPLETE 2026-06-01 — `src/prediction_market_bot/c4_risk_engine/staged_order_store.py`. Append-only, WAL mode. Statuses: STAGED/FIRED/EXPIRED/CANCELLED. `stage_order()`, `get_staged()`, `mark_fired()`, `mark_cancelled()`, `expire_stale()`, `summary()`. Default db_path: `logs/staged_orders.db`. 31 tests (test_c4_staged_order_store.py). |
| `run_t4_inplay.py` | **PIPE-07 skeleton + unified T4 decision tree** | ✅ COMPLETE 2026-06-01 — `src/prediction_market_bot/run_t4_inplay.py`. `T4EventLoop.on_game_state_event()` → `T4RoutingResult`: kill switch (<5ms) → expire_stale → pre-staged lookup → Bayesian (T4) → T5 → NO_ACTION. `--demo` flag runs synthetic scenarios. 16 tests (test_run_t4_inplay.py). BLOCKED: kill switch armed check placeholder; C4 approve + C5 execute placeholders. Phase 8+. |
| `scripts/resolve_procedure.sh` | **T-109 automation script** | ✅ COMPLETE 2026-06-01 — `scripts/resolve_procedure.sh` (chmod +x). Automates full resolve + EXP-017 update procedure after each Finals game. Logs to `logs/resolve_auto.log`. Step 3 reports G6 evidence count. Must run locally (VPS 403 blocks stats.nba.com). |
| `scripts/query_orderbook_depth.py` | **T-127 automation script (KI-023)** | ✅ COMPLETE 2026-06-01 — `scripts/query_orderbook_depth.py`. Queries Kalshi orderbook for 3–5 active KXNBAPTS contracts. Reports total depth, tight depth (±10¢), paper/live cap as % of visible depth. Flags if cap exceeds DEPTH_IMPACT_THRESHOLD_PCT=0.05. Audit log: `logs/orderbook_depth_YYYYMMDD_HHMMSS.json`. |
| scipy/sklearn upgrade | **numpy 2.x compatibility fix** | ✅ COMPLETE 2026-06-01 — scipy 1.12→1.17.1, sklearn 1.4.2→1.8.0. Pre-existing import error (`_ARRAY_API not found`) caused by numpy 2.4.6 in local .venv311. VPS was already working (612 tests). 692/692 tests pass locally after upgrade. |
| Tests | **+80 new tests** | ✅ COMPLETE 2026-06-01 — 612 → 692 total. test_c3_game_state_model.py (+33), test_c4_staged_order_store.py (+31), test_run_t4_inplay.py (+16). |

---

## SESSION 2026-06-01 SESSION 11 — COMPLETED

| # | Task | Status |
|---|------|--------|
| VPS deploy | **Deploy SESSION 8-10 code to VPS** | ✅ COMPLETE 2026-06-01 — git push origin main (SESSION 10 commit 1b325e0); VPS git pull at /opt/prediction-market-bot. VPS now at HEAD 1b325e0. 612/612 tests pass on VPS. T-119 (model hash guard) + T-120 (ShadowForecaster + C7 shadow Brier) now live. Ready for Finals G1 Jun 3 cron window. |
| ~~T-122~~ | ~~EXP-017 exact-ticker join~~ | ✅ CLOSED — already satisfied in run_part_b_live; no code change required (see task detail below). |

---

## SESSION 2026-06-01 SESSION 11 — NEW TASKS (PDTP priority list retrofit)

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| T-127 | **Query KXNBAPTS orderbook depth — DEFERRED to 2026-27 regular season Day 1 (KI-023 / GG-041)** | IO | **Phase 4 — October 2026** | **SESSION 72 2026-06-22: Finals window missed. All KXNBAPTS markets finalized 2026-06-14 post-G5. Live orderbooks empty; single prior run (2026-06-02) captured all-zero pre-game depth. GG-041 registered.** Re-run `scripts/query_orderbook_depth.py` on 2026-27 regular season Day 1 to capture live depth for 3–5 active KXNBAPTS contracts. Use result to set `max_order_pct_of_depth` in ADR-0005 before G6. Until then: ADR-0005 must label any `max_order_pct_of_depth` value provisional. |

---

## SESSION 2026-06-01 SESSION 10 — NEW TASKS

| # | Task | Priority | Notes |
|---|------|----------|-------|
| T-121 | **Wire record_shadow_outcome() to resolve pipeline** | MEDIUM — Finals window | `run_resolve.py` reads pregame logs (which now carry `shadow_p_estimate`). For each resolved bet, extract `shadow_p_estimate` and call `SystemMonitor.record_shadow_outcome(shadow_p, outcome)`. Prerequisite: shadow model artifact must be trained and deployed first — without an artifact, shadow_p_estimate will be None in all pregame logs, so this wiring produces nothing. Register as T-121 but defer execution until shadow artifact is deployed in dark period. |
| ~~T-122~~ | ~~Update EXP-017 Part B to join on exact kalshi_ticker~~ | ✅ CLOSED 2026-06-01 SESSION 11 — `run_part_b_live` (the `--from-pregame` path) already joins on exact `kalshi_ticker` (line 511-517). The ±3 fuzzy match exists only in `run_part_b` (CSV prices path, not invoked by `--from-pregame`). Task description was written before final implementation settled. No code change required. |
| T-123 | **TI-04 enforcement test** | MEDIUM — Track 2 | Assert any feature with `_price` or `_market` in its name has a documented `look_back_window` attribute in `DATA_FLOWS_LINEAGE.md`. Prevents temporal leakage of pricing features in future feature additions. |
| T-124 | **QTI backdating framework — DS-01 PAM to 2021-22** | MEDIUM — dark period | Backdate DS-01 PAM classifications for all 50 cohort players to 2021-22 per QTI-03. Requires `backdated: true` + `backdating_rationale` + second review flag in QS CSV. ~5× qualitative signal training coverage. |
| T-125 | **Polymarket adapter test expansion** | MEDIUM — Track 3 | Empty-market assertion (zero markets returned is an error not silence), `_parse_market()` regex test for edge cases, VenueRouter multi-venue routing test. Required before T-077 Polymarket activation. |
| T-126 | **EXP-014-B line shopping EV at T2/T3** | LOW — dark period | Bound EV range per execution band with Polymarket active. Depends on T-077 (Polymarket KYC) and T-107 (NBA tag confirmed). |

---

## SESSION 2026-05-31 HANDOFF — NEW HIGH PRIORITY TASKS

| # | Task | Priority | Notes |
|---|------|----------|-------|
| ~~T-113~~ | ~~**Draft new G6 promotion gate to supersede APR-0016 — multi-dimensional evidence standard**~~ | ~~**PENDING OPERATOR SIGN-OFF**~~ | ✅ DRAFTED v2 2026-06-01 — APR-0017_g6-multi-dimensional-evidence-standard.md revised. Operator instruction: "no arbitrary gating thresholds — use trend analysis sloping with derived figures." v1 arbitrary counts replaced: T1-A now pipeline error rate ≤ 5% AND slope ≤ 0 (derived from expected API failure rate); T1-C now resolution fidelity rate ≥ 85% AND slope ≥ 0 (derived from 1.5× expected legitimate failure rate); T1-B/T1-D kept zero-tolerance with explicit boolean-by-nature justification; Tier 2 slope directions made explicit on all criteria; statistical floor revised: ≥66 resolved bets (derived from T2-A calibration power formula at α=0.05, 80% power) + ≥5 game nights (derived from slope regression df ≥ 3). Decision logged (DECISION_LOG T-113/APR-0017 v2 entry). **OPERATOR ACTION: Review `00_ADMIN/APR-0017_g6-multi-dimensional-evidence-standard.md` (v2) and sign the approval block at the bottom.** Until signed, APR-0016 remains operative. |
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
| T-109 | **Run run_resolve_local.py after each game day (standing procedure)** | HIGH | VPS 403 blocks nba_api; resolution must run locally. Full procedure: (1) `BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_local.py`; (2) `PYTHONPATH=src python3 src/prediction_market_bot/fetch_kalshi_prices.py --portfolio` (sync pregame files from VPS for EXP-017); (3) re-run EXP-017 once ≥66 markets accumulated (APR-0017 floor). Jun 3 NYK vs SAS positions will be resolvable after Jun 3. |
| T-110 | **G6 evidence tracking: G6 counter reset to 0** | HIGH | Pre-ADR-0006 bets invalidated (2026-05-31 decision). Clean G6 evidence begins Finals G1 Jun 3. 3 open positions (KAT YES, Anunoby NO, Brunson NO). G6 requires ≥66 resolved markets + ≥5 game nights (APR-0017). |
| ~~T-105~~ | ~~**EXP-017 Part B — Collect Kalshi historical prices and run full market validation**~~ | ~~**BLOCKER — G6**~~ | ✅ COMPLETE 2026-06-01 — Part B live mode built (`--from-pregame <dir> --portfolio <path>`). Pulls pre-game logs + resolved portfolio; joins on kalshi_ticker. Run with n=2 unique resolved markets (May 30 game): Fox YES (WIN, EV/unit=+0.55), SGA NO (LOSS, EV/unit=−0.53). Per-market EV=+$0.01/bet. GG-004 OPEN — DIRECTIONAL_POSITIVE but far below APR-0017 floor of ≥66. `fetch_kalshi_prices.py` script built to pull pregame files from VPS after each game. **Standing action**: after each Finals game, run T-109 procedure (step 2) to accumulate data. Re-run EXP-017 once ≥66 resolved markets. Decision logged. |
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

## SESSION 2026-06-01 — NEW TASKS (throughput analysis)

| # | Task | Priority | Notes |
|---|------|----------|-------|
| ~~T-115~~ | ~~**Expand run_paper_trade.py to evaluate ALL thresholds per player (not just closest)**~~ | ~~HIGH — before 2026-27~~ | ✅ COMPLETE 2026-06-01 — `closest = min(player_mkts, ...)` replaced with `for mkt in player_mkts:` loop. `X` and `p_est` computed once per player; each threshold evaluated independently through idempotency check + C4 + PaperTrader. Restores design throughput: ~25–40 bets/game regular season T1 (vs ~3–10 single-threshold). Finals: 175–280 bets across 7 games vs ~70 borderline. KI-022 RESOLVED. 438/438 tests pass. Decision logged. |

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
| T-073 | DS-04 qualitative source registration | RL | LOW — August 2026 | First new qualitative source beyond PAM (coaching fit, matchup context, etc.). Decision required before T2 execution band can become ACTIVE. Timeline: August 2026 before dark period model retrain (T-092) so DS-04 features can be included in T-092 retrained model. |
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
| ~~T-091~~ | ~~C7 paper P&L monitoring alert~~ | ~~EL~~ | ~~MED~~ | ✅ COMPLETE 2026-06-01 — `check_portfolio_pnl()` added to SystemMonitor. L1 (5% loss) → INFO `pnl_alert_l1_watch`; L2 (10% loss) → WARNING `pnl_alert_l2_loss`. Wired into PIPE-03 and PIPE-03R. 8 new tests. 589/589 VPS tests pass. KI-012 RESOLVED. DS sign-off: Earl Ignacio 2026-06-01. |
| T-092 | Elevate T-072 to required pre-2026-27 | DS | MED | Model staleness KI-013 — T-072 must retrain before paper trading resumes in Oct 2026; not optional; needs new ADR |
| T-116 | Pre-season multi-game night pipeline stress test (KI-023) | IO/EL | HIGH — before 2026-27 | PIPE-02 + PIPE-03 have only been tested in single-game Finals context (1 game/night). Regular season (10+ simultaneous games, 400+ markets/night) is structurally different: concurrent nba_api pulls, parallel pregame log writes, overlapping PIPE-03 execution windows. If PIPE-02 fails silently for any player on a multi-game night, EXP-017 cannot join on that game's prices — G6 evidence is silently contaminated. Test plan: simulate a 10-game night locally before 2026-27 season tip-off. Verify: (1) run_pregame.py captures pregame logs for all 75 cohort players across simultaneous games without silent failures; (2) PIPE-03 processes all players without timing collisions; (3) EXP-017 join succeeds on a simulated multi-game pregame directory. Resolve before October 2026 season start. |
| T-117 | **Formal Kalshi TOS + contract Terms review (GG-006 final close)** | DS | **HIGH — Week 1 dark period (by 2026-06-30)** | Two documents to read formally before G6 ADR-0005 can be drafted: **(1) Kalshi Participant Agreement** — the account-level legal document Earl agreed to at account creation. GG-006 partial resolution confirmed automated trading permitted via web search; formal document reading not yet done. Look for: algorithmic trading restrictions, prohibited strategies, account termination triggers. **(2) KXNBAPTS contract-specific Terms and Conditions** — DCM Rulebook v1.26 does NOT contain numerical Position Accountability Levels or Position Limits; those are in each contract's Terms tab on Kalshi's website. Navigate to any active KXNBAPTS contract → Terms and Conditions tab → record: (a) stated Position Accountability Level (soft threshold for disclosure); (b) stated Position Limit (hard cap). If both above $500 (our bet cap), no changes to risk.py required. If either below $500, add `max_position_usd_per_market` to `_HARD_LIMITS` via ADR. Stakes: prevents live capital on disallowed activity — must complete before G6. LOW risk at current paper bankroll ($683, $10–80/bet). |
| T-100 | Fix Bug H — drawdown includes open stakes (KI-015) | EL | HIGH | ✅ COMPLETE 2026-05-30 — `run_paper_trade.py` lines 215+334: `current_drawdown_pct = realized_loss / initial_bankroll`; DS sign-off granted by operator same session; deployed VPS; live check: 0.00% realized drawdown |
| T-101 | Fix Bug G — idempotency check failure (KI-014) | EL | HIGH | ✅ COMPLETE 2026-05-30 — Root cause: `LOG_DIR` was relative path; cron ran from different CWD → fresh portfolio each run → 3× positions. Fix: `_SRC_ROOT / "logs"` absolute default in `run_paper_trade.py` + `run_resolve.py`. Idempotency logging added. Deployed VPS. |

### Governance Debt — decisions_logged: false (registered 2026-05-29)

*These documents contain unlogged strategic decisions. Each must be resolved before the document can be marked CANONICAL. Low priority unless the document is being actively modified — resolve before any session that touches the document.*

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| ~~T-093~~ | ~~Extract decisions from EXECUTION_ARCHITECTURE.md~~ | ~~DS~~ | ~~LOW~~ | ✅ COMPLETE 2026-06-02 SESSION 15 |
| ~~T-094~~ | ~~Extract decisions from MONITORING_DRIFT_PLAN.md~~ | ~~DS~~ | ~~LOW~~ | ✅ COMPLETE 2026-06-02 SESSION 15 |
| ~~T-095~~ | ~~Extract decisions from METHODOLOGY.md~~ | ~~DS~~ | ~~LOW~~ | ✅ COMPLETE 2026-06-02 SESSION 15 |
| ~~T-096~~ | ~~Extract decisions from VENUE_REGISTRY.md~~ | ~~DS~~ | ~~LOW~~ | ✅ COMPLETE 2026-06-02 SESSION 15 |
| ~~T-097~~ | ~~Extract decisions from RISK_APPETITE_CONSTRAINTS.md~~ | ~~DS~~ | ~~LOW~~ | ✅ COMPLETE 2026-06-02 SESSION 15 |
| ~~T-098~~ | ~~Extract decisions from QUALITATIVE_SIGNALS.md~~ | ~~DS~~ | ~~LOW~~ | ✅ COMPLETE 2026-06-02 SESSION 15 |
| ~~T-099~~ | ~~Extract decisions from ROADMAP_MILESTONES.md~~ | ~~DS~~ | ~~LOW~~ | ✅ COMPLETE 2026-06-02 SESSION 15 |

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
