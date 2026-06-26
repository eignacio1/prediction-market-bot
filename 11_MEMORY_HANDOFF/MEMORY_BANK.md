# Memory Bank — Prediction Market Trading Bot

**Purpose:** The canonical navigation index for this project. The definitive source of truth for what exists, where it lives, and what its current status is. Designed to be the first file read in any new context window to restore full situational awareness.  
**Owner (role):** Director/Sponsor (DS) — the operator is responsible for keeping this current  
**Last reviewed:** 2026-06-26 SESSION 87 CLOSE — **T-191 COMPLETE: MLB arm institutional completion. T1–T4 fully built, deployed, and on-auto. (1) T4 bugs fixed: `run_t4_mlb_live.py` stat group filter `!= "batting"` (was passing empty-name stat groups, corrupting hit counts), `MIN_EDGE_T4=0.02` dead constant removed (C4 gates at `MIN_EDGE_TO_APPROVE=0.04`; dead code was documentation confusion), NFR-03 kill switch moved inside game_pk loop (was only at outer while-loop top; worst-case 195s halt → now ≤45s + ESPN timeout). (2) T1 PIPE-05 timing fixed: `timedelta(days=1)` was targeting tomorrow; VPS showed 0 bets since launch — Kalshi doesn't publish next-day markets at 23:30 UTC. Fix: same-day UTC targeting, cron moved 23:30→03:00 UTC (Kalshi markets available by ~01:58 UTC per VPS log). (3) T3 MLB cron: two missing entries added (`*/15 20-23` + `*/15 0-3`); this was an S85 gate breach (S86 declared complete without adding them). (4) T2 MLB BUILT: `run_t2_mlb_sameday.py` (PIPE-05.5, 280+ lines, 19:30 UTC cron): batting slot Binomial AB adjustment (Slots 1-9: 4.2–3.1 ABs/game; ±15% cap; `ba_l10` from PIPE-06pre context), per-game contamination guard (afternoon live games don't block evening bets — per `game_pk` from lineup, not global), lineup-scratch filter (player not in confirmed lineup = SCRATCH), idempotency (T1 open ticker blocks T2 re-entry), shared pool `paper_portfolio_mlb.json` with T1. DS-04 MLB designated: `03_DECISIONS/DS-04_mlb-t2-lineup-source.md` — MLB Stats API `hydrate=lineups,team`; `MLBIngestionClient.fetch_lineups()` implemented. SP overlay NOT in T2 (SP quality already in T1's `opp_sp_era_l5` feature; double-counting risk). 29 new tests `tests/test_t191_mlb_t2.py`. Suite 1918→1947/1947. Git HEAD `2f13a35`. VPS deployed + 7 MLB cron entries active. MLB book: $1,000 fresh, 0 open, 0 closed. Next: monitor first T1 bet at 03:00 UTC, T2 at 19:30 UTC, T3 at 20:00 UTC, T4 at 22:00 UTC.** *(Previous S86:)*  **T-190 COMPLETE — full MLB arm built (pregame + T3 + T4 in-play). Three new files: `src/prediction_market_bot/run_mlb_pregame.py` (Step 1, pregame context generator), `src/prediction_market_bot/run_t3_mlb_pretip.py` (Step 2, PIPE-06 MLB momentum scan), `src/prediction_market_bot/run_t4_mlb_live.py` (Step 3, PIPE-07 MLB 45-second evaluation loop). 55 new tests (`tests/test_run_t4_mlb_live.py`, all passing). Suite 1819→1918/1918. MLB T4 Binomial model: `P(hits >= threshold | h_so_far, ba_l10, ab_remaining)` via exact Binomial CDF sum; `AB_PER_GAME_DEFAULT=3.7`; `T4_BAND_WEIGHT=0.27` (ADR-0023); isolated portfolio `paper_portfolio_mlb_t4.json`; file-based kill switch `logs/t4_mlb_kill_switch.flag`. `deploy/cron.conf` PIPE-07 MLB block added (paused pending VPS validation). Next: scp 3 new src files + test + updated cron.conf to VPS, run 55 tests on VPS, uncomment all 5 MLB cron lines (PIPE-06pre + PIPE-05 + PIPE-05R + PIPE-05FX + PIPE-07 MLB), reinstall crontab → MLB accumulation LIVE at $1,000 fresh bankroll.** *(Previous S85:)* **MLB ARM AUDIT: CLAUDE.md T4 line corrected (was "T4/T5: In-play — future; post-G6" — factually wrong; NBA T4 IS deployed as PIPE-07; MLB T4 NOT built). Root cause of every session treating T4 as a future concept. All 4 MLB cron lines PAUSED in `deploy/cron.conf` (commit `aab7337`, deployed to VPS). T-190 REGISTERED: 3-step sequential build before MLB restarts — (1) `run_mlb_pregame.py` generates `pregame_mlb_YYYYMMDD.json` (player→forecast→ticker map; prerequisite for T3+T4); (2) `run_t3_mlb_pretip.py` momentum scan (PIPE-06 MLB, every 15 min before first pitch); (3) `run_t4_mlb_live.py` in-play 45-second evaluation loop (PIPE-07 MLB, ~1,000 evals/game, isolated `paper_portfolio_mlb_t4.json`, T4_BAND_WEIGHT=0.27 ADR-0023 budget, file-based kill switch `logs/t4_mlb_kill_switch.flag`). MLB bankroll $1,000 fresh start, 0 open, 0 closed. Accountability finding: asked "are we clean, green, on auto" — answered yes; ML T4 absence not flagged. Surfaced by Earl, not model. Root cause: CLAUDE.md documentation error, now fixed.** *(Previous S84:)* **T-189 COMPLETE: PIPE-05 three-concern remediation. (1) GAME_DATE=tomorrow + market date filter — contamination guard now targets tomorrow's Preview-state games; no more live-game abort. (2) `ensure_persisted()` on PaperTrader — portfolio file created at run start before any bets; `_load_or_init()` reverted to no-disk-write to preserve `_reload_locked` invariant. (3) Hydrate fix (`probablePitcher,team`, no `venue` — Fastly CDN/DO 406) + PIPE-05FX cache bust scoped to batters/completed_games only (starters + pitcher logs preserved). 29 new tests (`tests/test_t189_mlb_pipe05_fixes.py`). Suite 1790→1819/1819. MLB portfolio reset $1,000. Monte Carlo: CLEAN, GREEN, ON AUTO (9/9 June 25 games with SP data, contamination guard PASS, hydrate PASS, ensure_persisted PASS, crontab PASS). VPS deployed. DECISION_LOG T-189 entry written.** *(Previous S83:)* **T-188 COMPLETE: MLB bloomberg-terminal curses TUI dashboard (`scripts/run_mlb_dashboard.py`). MLB accumulation LIVE as of 2026-06-24 — PIPE-05 first run tonight 23:30 UTC. 1790/1790 tests. VPS HEAD 42bce66.** *(Previous S82:)* **T-187 ALL COMPONENTS COMPLETE (A–H).** T-187E: `run_resolve_mlb.py` (PIPE-05R) — MLB paper position resolution; `PaperTrader.settle_position()` sport-agnostic (stat_label="actual_hits" for MLB); Regular→Postseason fallback; C6+C7 wiring; 33 new tests (1704→1737). T-187F: `scripts/run_mlb_calib_monitor.py` (PIPE-05C) — ECE per threshold (t=1/t=2); T_global temperature derivation via `minimize_scalar` on combined dataset (statistical power design choice vs per-threshold); reliability buckets; anti-predictive check; exit codes 0=CALIBRATED/INSUFFICIENT, 1=MISCALIBRATED, 2=ANTI_PREDICTIVE; MIN_N_DIAGNOSE=50; PIPE-05C cron Mondays 14:10 UTC; does NOT write `calibration.py` (ADR required); 35 new tests (1737→1772). T-187G: live SP overlay in `run_mlb_paper_trade.py` — `_build_live_sp_override` fetches tonight's actual SPs via `MLBIngestionClient.fetch_game_starters`; overrides `opp_sp_*` fields in feature vector at inference time; falls back to historical stats on API failure; `_safe_int`/`_SP_OVERRIDE_FIELDS` helpers; 18 new tests (1772→1790). T-187H: t=3 shadow gate re-evaluation (governance-only, NO code changes) — VALID NEGATIVE confirmed. SP coverage verified 99.9% for t=3 events (GG-042 data-quality premise DISPROVED — T-187G only fixed inference-time staleness, not training data). Brier delta=+0.0002 (FAIL — same as T-187B), ECE=0.0037 (PASS), AUC=0.6141. Score distribution: p50=0.037 (matches base rate); only 1.9% of holdout scores exceed Kalshi market price (0.08). Root cause structural: at 3.9% base rate, AUC=0.61 cannot produce absolute Brier delta ≥0.001 — information-theoretic ceiling. `THRESHOLDS=[1,2]` and `_EXCLUDED_THRESHOLDS=[3]` in `train_mlb_model.py` unchanged; `_MODEL_THRESHOLDS=frozenset({1,2})` in `run_mlb_paper_trade.py` unchanged. GG-042 status: DEFERRED — structural (indefinitely; requires non-linear model or richer pitcher-batter matchup features). DECISION_LOG entries for all four components written. VPS HEAD dbe6acb. **1790/1790 tests.** Full MLB paper trading stack now LIVE: PIPE-05 (23:30 UTC bets), PIPE-05R (06:30 UTC resolution), PIPE-05C (Mondays 14:10 UTC calibration monitor), PIPE-05FX (22:30 UTC feature refresh). MLB accumulation phase LIVE as of 2026-06-24 (first PIPE-05 run tonight 23:30 UTC; started 5-6 weeks ahead of original August planning target). pyarrow installed on VPS 2026-06-24 (S83) — PIPE-05FX was crashing without it. *(Previous S81 CLOSE:)* **T-187B COMPLETE: per-threshold MLB LR+Platt models. Shadow gate PASS on VPS (t=1: ECE=0.0134, Brier delta=+0.0055; t=2: ECE=0.0106, Brier delta=+0.0022). Root cause of ECE=0.1246 failure: pooled `class_weight='balanced'` LR + Platt calibrated to ~26% average; per-threshold actual rates differ dramatically (t=1=54.5%, t=2=18.4%, t=3=3.9%). Fix: separate pipelines for t=1 and t=2; `threshold` added to `_NON_FEATURE_MLB`; t=3 excluded (GG-042 registered). Artifact schema: `{"pipelines": {1: p1, 2: p2}, ...}`. Runner dispatches to `pipelines[int(mkt.threshold)].predict_proba(X)`. DECISION_LOG entry written. 1704/1704 tests. Commits 953fd20 + 5c233aa pushed; VPS HEAD confirmed. All T-187 infrastructure now COMPLETE (T-187A through T-187D + T-187B). Remaining: T-187E (MLB resolve script), T-187F (MLB calibration monitor), T-187G (live SP overlay for t=3 reconsideration). PIPE-05 (MLB paper bets at 23:30 UTC) and PIPE-05R (daily feature refresh at 22:30 UTC) both live on VPS with correct per-threshold models.** *(Previous S81 ACTIVE:)* T-187C + T-187A + T-187D COMPLETE (1704 tests): MLB paper trading runner fully built and deployed to VPS. PIPE-05 cron wired (23:30 UTC). PIPE-05R daily feature refresh cron added (22:30 UTC, --seasons 2026). MLB Stats API IP-blocking finding: DigitalOcean VPS blocked from historical seasons (2024/2025) via HTTP 406 — feature matrix must be generated locally then scp'd to VPS. T-187E/F/G deferred. *(Previous S80 CLOSE:)* **T-117 COMPLETE: GG-006 RESOLVED (Kalshi Participant Agreement v1.54 formally read: no automation restrictions; Rule 5.13(s) source agency insiders only — inapplicable; Rule 5.15 behavioral conduct, single algorithm mention targets Kalshi's own market makers). ADR-0005 pre-requisite satisfied. MLB paper book: fresh $1,000 separate pool (DECISION_LOG S80). T-186 COMPLETE (valid negative): `nba_api.TeamGameLog` omits `PLUS_MINUS` → `pts_allowed` NaN → F-040 and F-042 dead features (imputed 0.0) since EXP-005. Fix: `pull_playoff_teamgamelog.py` `_fill_pts_allowed_via_crossref()` — builds `(game_date, abbr)→pts` lookup from MATCHUP column; 338/338 games populated (22 teams). v2b retrain: F-042 76/103 playoff rows non-NaN (73.8%); Brier delta +0.000130 (required ≥0.001) → shadow gate FAIL. Valid negative: F-042 insufficient signal at available sample. Deploy v2-065b9510 in October (ADR-0031 unchanged). 10 new TestPtsAllowedCrossRef tests. Suite 1609→1650/1650 green. Commit 89d795c, VPS deployed. T-187 REGISTERED: `scripts/run_mlb_paper_trade.py` MLB paper runner (P0, before August 2026).** *(Previous S79 CLOSE:)* **T-184 COMPLETE: EXP-017 MLB commercial validation script.** `scripts/run_exp017_mlb.py` (new, standalone, ~365 lines): three analysis layers — (1) EV analysis (EV/bet, win rate, YES/NO split, threshold breakdown k=1/2/3), (2) ADR-0024 tier checks (Tier 1 n≥150 + EV<-$0.03→DIAGNOSTIC_SPRINT; Tier 2 single n≥500 or multi MLB n≥150 AND NBA n≥150 via `--nba-n`; EV verdict hierarchy CONFIRMED_POSITIVE/DIRECTIONAL_POSITIVE/CONFIRMED_NEGATIVE/DIRECTIONAL_NEGATIVE/DIAGNOSTIC_SPRINT/INCONCLUSIVE), (3) edge monotonicity guard (Fisher's exact + chi-squared fallback; ANTI-PREDICTIVE/MONOTONIC/INCONCLUSIVE). `compute_fee_net_edge`: YES=model_p−mip−0.07×mip×(1−mip); NO symmetric. CI mode exit codes 0/2/3/4. MLB position schema contract: requires `model_p`, `threshold`, `outcome`, `pnl`; `fee_net_edge` optional (computed if absent); deduplication: one position per unique `kalshi_ticker`, earliest wins. Reads `logs/paper_portfolio_mlb.json` by default; `--csv` for batch backtest. Script returns INCONCLUSIVE until ≥20 positions accumulate (MLB paper trading starts August 2026). `tests/test_t184_exp017_mlb.py` (new): 99 tests, 15 classes, 1510→**1609/1609** total green. DECISION_LOG SESSION 79 entry written. TODO_NEXT.md updated. Next: T-117 (operator action, GG-006, deadline 2026-06-30). *(Previous S78 CLOSE:)* **T-183 COMPLETE: MLB C3 model training infrastructure.** `scripts/train_mlb_model.py` (new): `HOLDOUT_CUTOFF = "2026-01-01"`, shadow gate (null baseline, `brier_delta >= 0.001 AND ece <= 0.05`), `_build_mlb_target` (3-row expansion per game, `threshold` as float feature, `y_target=(h>=k)` Int8/NA), `_NON_FEATURE_MLB` frozenset (raw `h` excluded — leakage prevention), Pipeline matches `forecaster.py:354-358` exactly, artifact schema matches NBA loader contract (`{pipeline, feature_names, col_medians, model_version, thresholds:[1,2,3], sport:"mlb"}`), `_mlb_model_version()` "mlb-v1-"+sha1[:8]. `CALIBRATION_TEMPERATURE["mlb"]=1.0` identity confirmed. `tests/test_t183_mlb_c3.py`: 77 tests, 11 classes. BOT_C4_ACTIVE test contamination: `run_paper_trade.py:59` sets env var at import time → autouse monkeypatch fixture fix in `TestEndToEndDryRun`. DECISION_LOG S78 entry written. TODO_NEXT.md updated. 1433→1510/1510 green. Next: T-184 (EXP-017 MLB commercial validation, P0). *(Previous S77 CLOSE:)* **T-182 COMPLETE: MLB C2 baseball feature set (2 new files, 60 tests, 1433 total green). `src/prediction_market_bot/c2_feature_store/mlb_features.py`: `MLBFeatureStore`, `_compute_rolling_batter_features`, `assign_train_test_labels`. `MLB_FEATURE_VERSION = "1.0.0"` (separate from NBA 1.4.0, per ADR-0004). TI-01: `.shift(1).rolling(min_periods=3)` — current game never enters own feature vector; `temporal_cutoff` = NaT for first game. Rolling L10 batter features via sum-then-divide (ba_l10, slg_l10, obp_l10, ops_l10, h_l10_mean, k_rate_l10, bb_rate_l10, hr_rate_l10). Context: days_rest, b2b_flag. Starting pitcher overlay MANDATORY: opp_sp_era_l5/k9_l5/bb9_l5/is_known from MLBPitcherStatsStore; K9/BB9 via total ÷ total IP (same sum-then-divide discipline); sp_id=None → all SP features=None, is_known=0.0. Park factors: 30-venue static dict, Coors Field=1.120, Oracle Park=0.970, unknown→1.000. Opponent: opp_runs_allowed_l10 from MLBTeamStatsStore. C6: 5 audit events. assign_train_test_labels: NaT → None (TI-02 excluded). `_ip_to_decimal()` fix confirmed in C1 (MLB Stats API "5.2" = 5+2/3 = 5.667). `tests/test_t182_mlb_c2.py`: 60 tests, 5 classes. DECISION_LOG S77 entry written. TODO_NEXT.md updated. Next: T-183 (MLB C3 model training, P0).** *(Previous S76 CLOSE:)* **Pre-MLB governance scrub (exhaustive). Four actionable items completed: (1) KXMLBHIT CONFIRMED via live Kalshi GET /series — `SERIES_MLB_PLAYER_HITS` corrected from `"KXMLBHITS"` (did not exist) to `"KXMLBHIT"` in `kalshi_client.py`; docstring updated with full MLB ticker spec (format: `KXMLBHIT-{DATE}{TIME}{AWAYTEAM}{HOMETEAM}-{TEAMABBRV}{PLAYERID}-{THRESHOLD}`; AWAY before HOME; 4-digit EDT time; per-player hits O/U structure confirmed). (2) DtypeWarning silenced: `run_paper_trade.py:249` and `run_pregame.py:185` — both changed to `pd.read_csv(FEATURE_CSV, low_memory=False)`; affected cols: `train_test_label`/`matchup`/`opponent_team_abbr`/`game_date_dt`. (3) VPS dark-period cron health VERIFIED CLEAN — PIPE-02/PIPE-03 running correctly Jun 18–23; no silent failures; bankroll $751.10; model v1-28483b21; next check end of July 2026. (4) T-117/GG-006 June 30 deadline FLAGGED — operator must formally read Kalshi Participant Agreement + KXMLBHIT T&C before G6 ADR-0005 sign-off. 1373/1373 tests unchanged. DECISION_LOG S76 entry written. TODO_NEXT.md updated. System clean; ready for T-182 (MLB C2 feature set, P0).** *(Previous S75 CLOSE:)* **T-181 COMPLETE: MLB C1 data ingestion module (3 new source files + 80 tests; 1373 total green). DS data-source decision: MLB Stats API (statsapi.mlb.com) via raw HTTP requests — no pip wrapper; `requests` now explicit in pyproject.toml. `mlb_ingestion.py` (`MLBIngestionClient` — 6 public methods; (bool, DataFrame|dict) return contract; C6 audit trail; 0.6s throttle; _team_abbr_map injection for test isolation). `mlb_team_stats_store.py` (get_opp_runs_allowed/scored, build_from_games(), TI-01, cache). `mlb_pitcher_stats_store.py` (ERA/K9/BB9 via total ER÷IP — NOT mean of per-game rates; relief exclusion; TI-01; cache). IF-C1-C2 MLB batter 24-col schema, pitcher 22-col schema, game starters gamePk dict. DECISION_LOG SESSION 75 entry written. TODO_NEXT.md updated.** *(Previous S74 CLOSE:)* **Governance-only session. (1) MLB paper book decision: fresh $1,000 separate pool (`logs/paper_portfolio_mlb.json`) — DECISION_LOG S74. Rationale: EXP-017 MLB must run on a book experimentally independent of NBA P&L history. (2) ADR-0031 Known Limitations section added: F-042=NaN everywhere (playoff TeamGameLog deferred; targeted fix NOT in v2); primary Brier gain from F-039/F-040 (not playoff features); T-177 INCONCLUSIVE n=114 below ADR-0024 structural adequacy; T-186 required before NBA 26-27 restart; "shadow gate PASSED ≠ alpha confirmed." (3) Phase 3 task registration: T-181 (MLB C1), T-182 (MLB C2, starting pitcher MANDATORY), T-183 (MLB C3 LR+Platt), T-184 (EXP-017 MLB commercial validation), T-186 (F-042 playoff TeamGameLog + v2b retrain). (4) T-185 registered: v2 deploy 8-step runbook, NBA 26-27 book reset options A/B/C, DS witnesses Step 7. (5) DARK_PERIOD_PLAN Phase 3/4 tables updated. Commit `498cb97`. 1293 tests unchanged.** *(Previous S73 CLOSE:)* **T-072 COMPLETE (Parts A+B+C). ADR-0031 ACCEPTED (DS sign-off Earl Ignacio). FEATURE_VERSION 1.4.0 live on VPS. Model v2-065b9510 trained: Brier Δ=+0.001507, ECE=0.0426, shadow gate PASSED. T-177 v2 backtest INCONCLUSIVE (p=0.1639, n=114). Phase 3 MLB gate OPEN. 1293 tests (+13 from Part A vs 1280). One deferred item: deploy v2 model + kill switch reset (dark period; act at 2026-27 season start Oct 2026).** *(Previous S72:)* **Governance-only session. ADR-0028 ACCEPTED (DS sign-off Earl Ignacio). T-148 DONE. GG-022 RESOLVED. T-127/KI-023 Finals window confirmed closed; GG-041 registered (deferred to Phase 4 Oct 2026). 1280 tests unchanged. No code changes.** *(Previous S71:)* **T-180 Phase 3 + Phase 4 COMPLETE. Evaluator math implemented + live execution path designed. All T4 code done; blocked on GG-038/039/040 Phase 8 ADRs.** Sub-band evaluators (T4ProjEvaluator, T4ArithEvaluator, T4EventEvaluator, T4FlowEvaluator/Blowout, T4ExitEvaluator): real math implemented in `t4_execution_engine.py` — Gamma-Poisson conjugate Bayesian update, Poisson survival probability, phase-conditional Kelly schedule (EARLY 0.010→NEAR_CERTAIN 0.167), arithmetic window logic, blowout detection, 3-condition exit logic. 185 tests in `test_t4_engine.py`. Live execution path (`t4_live_runner.py`, new): `T4FastHalt` (GG-038 design, threading.Event ≤5s), `T4PositionRegistry` (thread-safe, pool drawdown accounting independent of T1), `T4PriceCacheUpdater` (GG-039 bootstrap REST at 2s), `T4GameStateBuilder` (GG-040 bootstrap ESPN→T4GameState, SCORE_UPDATE by score delta), `build_forecast_record()` (EvaluationSignal→C4 IF-C3-C4 dict with `kelly_fraction` key), `T4LiveRunner` (full C4/C5/C6/C7 wiring, T4 pool 20% drawdown kill, run_cycle, _handle_entry, _handle_exit). `on_game_event()` implemented in T4ExecutionEngine (Layer1+Layer2 pipeline, returns `tuple[list[EvaluationSignal], list[StaleDropRecord]]`). `create_phase8()` factory (instance-level `_PHASE8_ACTIVE=True`; class default unchanged=False). C4 `risk.py`: backward-compat `kelly_frac = fc.get("kelly_fraction", self._kelly_fraction)` — T4 phase-conditional Kelly reaches C4 sizing while all guardrails apply. 67 tests in `test_t4_live_runner.py`. **1280 total tests, 0 failures, VPS confirmed.** All T4 execution paths STILL BLOCKED/dark — `_PHASE8_ACTIVE=False`; Phase 8 ADRs (GG-038/039/040 resolution + activation ADR) required before `create_phase8()` is called in production. *(Previous S70:)* Sub-band evaluator math sprint (76 tests + real math added to t4_execution_engine.py stubs). *(Previous S69:)* **DS decision: Option C (feature-set diagnosis sprint). Root cause: missing playoff-context λ multiplier. T-072 scope updated.** `t4_price_cache.py` (GG-039 architecture): `T4Phase8BlockedError`, `STALENESS_WINDOW_S` (EVENT ≤2s / LINEUP ≤5s / others ≤30s), `CachedPrice` frozen dataclass, `T4PriceCache` (thread-safe RLock; read/write/staleness available for test injection; `start_polling`/`stop_polling` raise blocked). `t4_execution_engine.py` (ADR-0029 Tier A substance): `GamePhase`+`classify_game_phase`; frozen game-state dataclasses; `EvaluationSignal`/`QueueEntry` (EXIT priority 0.0, else 1.0−|edge|); `SubBandEvaluator` ABC + 8 BLOCKED evaluator stubs (all return []; each guarded by `_assert_sub_band_blocked()`); `T4ProjEvaluator.get_lambda_posterior()` (PROJ writes, EVENT/SENTIMENT read at Phase 8); `T4CorrAdjuster` with `_assert_downward_only()` (Principle 6 invariant); `Layer1EvaluationEngine` (event-type dispatch); `Layer2ExecutionQueue` (heapq; staleness-check→CORR-adjust→approve/drop; 3 drop conditions: price_stale / edge_below_min / direction_reversed); `T4ExecutionEngine` (`_PHASE8_ACTIVE=False`; factory `create()`; `simulate_cycle()` test-usable; `start()`/`on_game_event()` raise blocked). VERIFIED this session: 1108/1108 green, `_PHASE8_ACTIVE=False` confirmed, both entrypoints + polling + all 8 evaluators provably blocked. T4 execution path gated at all three Phase 8 gates (GG-038 kill-switch ≤5s / GG-039 price cache / GG-040 real-time data) — STILL DARK; no VPS live-behavior change. *(Previous, SESSION 67:)* **ADR-0029 ACCEPTED — Tier A frozen (DS sign-off Earl Ignacio); Tier B provisional. T-180 SCAFFOLD landed (design): `execution_bands.py` split — `T4_IN_PLAY` retained as AGGREGATE PARENT (ADR-0013 `T4_BAND_WEIGHT=0.27` untouched); 10 sub-bands added as routing children (T4-STAGED/EVENT/LINEUP/FLOW/SENTIMENT/PROJ/ARITH/BOUNDARY/CORR/EXIT; T4-MICRO carved to ADR-0030) via `T4_SUBBANDS` tuple + `is_t4_subband()`/`t4_parent()`. Tier B encoded IN CODE: `T4SubBandSpec` dataclass + `T4_SUBBAND_REGISTRY` carry provisional Kelly + EXP gate + exposure cap + falsifiable alpha hypothesis, all `status="BLOCKED"`; `validate_t4_subbands()` enforces roster==tuple/all-BLOCKED/all-Phase-8-realtime. PROJ/ARITH Kelly held ≤0.167 (test-locked < 0.25 ceiling; EXP-PROJ-01/EXP-ARITH-01 pending). `NOISE_BUFFER_BAND_T4=0.19` kept as aggregate default. Strategy K NOT redefined (execution_scalp overlaps ADR-0030 T4-MICRO carve-out — logged OPEN). ADR-0028 T4 Activation Gate notice cleared (taxonomy now defined). DECISION_LOG: sign-off entry + 4 scaffold design-decision entries logged (rule #7). Tests 988→999 (+11). T4 STILL DARK — all sub-bands BLOCKED/Phase 8; no execution-path change; no VPS deploy. ⚠️ Q6 STANDING FLAG: enum/config plumbing is NOT the routing intelligence — Layer 1 Continuous Evaluation + Layer 2 staleness-arbitrated queue (the ~1,000-eval/game engine, the substance of Tier A) remain UNBUILT.** *(Previous, SESSION 66:)* **T-179 ADR-0029 DRAFTED (PENDING DS SIGN-OFF): T4 sub-band architecture — 11 sub-bands (T4-MICRO, T4-STAGED, T4-EVENT, T4-LINEUP, T4-FLOW, T4-SENTIMENT, T4-PROJ, T4-ARITH, T4-BOUNDARY, T4-CORR, T4-EXIT), three-layer execution, immediate execution principle, dynamic game-phase Kelly (ADR-0010 T4 superseded), FLOW-BLOWOUT as blowout-consequences architecture, T4-CORR convergence premium. ADR-0028 T4 Activation Gate PLACEHOLDER completed. GG-038/039/040 registered (Phase 8 prereqs: kill switch ≤5s, price cache, real-time data sources). Code changes blocked pending DS sign-off. No VPS deploy; 988/988 tests; VPS HEAD `97e66ae` unchanged.** *(Previous, SESSION 65:)* **T-148 ADR-0028 REWORK COMPLETE (PENDING DS SIGN-OFF): G6 scoped to T1-only; T4 Activation Gate created as Phase 8 placeholder pending T-179 sub-band design.** VPS HEAD `97e66ae`; 988/988 tests. **GG-036 RESOLVED:** re-froze the 158-bet NBA Finals dataset (`data/nba_finals_clean_dataset.csv`); G5 41 positions resolved (outcomes sourced, NOT fabricated); capital unlocked. The full-database assessment ran on this set. **GG-035 RESOLVED (structural) — ADR-0026 / APR-0020:** C4 two-tier portfolio free-cash invariant — CHECK 8a solvency KILL (`Σopen+size > equity`), 8b policy REJECT (`> 0.60×equity`; 60% = `1−RESERVE_MANDATE_PCT`, reserve promoted advisory→enforced); base = equity (stricter underwater); C4 stays pure via `PaperTrader.exposure_snapshot()`; forensic G5 $1003.38 unreachable (cap $449.27). **Coverage gap → T-175:** only callers passing the snapshot are guarded; run_t4_live / EXP harnesses unguarded. **GG-037 RESOLVED (calibration half) — ADR-0027 / APR-0021:** C3 temperature scaling `p_cal=σ(logit(p)/T)` on the **production Poisson prob** — the central diagnostic catch: the production T1 prob is the pure Poisson survival prob (`run_paper_trade.py` ~543, ADR-0015), NOT the LR+Platt `prod_model.joblib` (which only logs `p_estimate_lr`); **re-fitting Platt would have been a no-op.** Root cause = Poisson assumes var=mean but NBA scoring is over-dispersed → tail probs too extreme → overconfidence (directional Brier 0.2308, mean confidence 0.799 vs realized 0.601). `calibration.py` per-sport registry with **fail-safe identity T=1.0** so MLB cannot inherit NBA shrink; NBA T=2.05 (OOS-validated: fit G2–G4, test G5; in-sample optimum 3.10 — conservative chosen). `scripts/derive_calibration.py` re-derives + monitors. **THE HARD TRUTH — recalibration DISPROVED the miscalibration hypothesis:** edge stays anti-predictive after calibration (edge>0 winrate 0.356 vs edge≤0 0.747; highest-edge tercile 0.346 vs lowest 0.792); edge inversion SURVIVES calibration → the model has NO demonstrated alpha vs the Kalshi market — the market price is more informative than the model. **GG-037 alpha half + GG-004 stay OPEN** (→ T-177); calibration was a correctness fix, NOT evidence of profitability. Deferred to EXP-017 at scale (MLB dark period + NBA regular season). NBA T=2.05 provisional (n=158 single-series, ADR-0024) — re-derive on adequate sample at G6. No live behavior change: paper book remains halted at drawdown kill switch (25.12% > 20%); CHECK 2 fires before CHECK 8/calibration matters. New tasks: T-175 (ADR-0026 caller coverage), T-176 (MLB T derivation), T-177 (edge-inversion/no-alpha), T-178 (market_mapper MLB pre-flight). *(Previous, SESSION 63:)* **DARK PERIOD OPEN (Knicks won the NBA Finals). T-174 + T-171 DEPLOYED + LIVE BOOK CORRECTED. GG-034 + GG-033 RESOLVED.** T-174's four workstreams (ledger-derived `total_realized_pnl`+`bankroll_usd`, cross-process `fcntl.flock` + double-resolution guard, clean-dataset build, MLB bet-record contract) shipped to VPS HEAD `52607f2` (manual deploy — GHA aborts on pre-existing untracked VPS files); governance closure committed `c52d298`. Main book corrected: `total_realized_pnl` −8.4645 → **−251.2134**, drawdown **25.12%**, **kill switch un-blinded** (`run_paper_trade.py:274` → 25.12% > 20% → halt). C6 `portfolio_pnl_desync` EVT-4CED1860AFCB (drift $242.75). T4 book needed NO correction (stored == ledger == 4.8242; GG-032/T-170 already fixed it). T-171 untrack done same deploy → `git pull` can no longer clobber the live book (verified: clean fast-forward to VPS). **TWO NEW GAPS the correction surfaced — both OPEN:** **GG-035 (over-leverage)** corrected `bankroll_usd` = **−$254.59**; $1003.38 in 41 open G5 stakes = 100.3% of $1,000 initial / ~134% of $748.79 equity; C4 has NO portfolio-level free-cash invariant (build pre-live). **GG-036 (G5 unresolvable)** nba_api has no 2026-06-13 box scores; 41 G5 positions can't settle; $1003.38 locked; dataset stays 117 closed + 41 open; **outcomes NOT fabricated.** **G6 baseline RATIFIED at the true figure** (−$251.21/−25.1% headline, −$302.98/−30.3% clean-only; SNAP-2026-06-14-001 registered by hash). Ratification fixes the number-of-record ONLY — **Tier 0 / EXP-017 commercial validation (GG-004) remains the binding G6 blocker; positive-P&L gate is FAILING.** DS retroactive-halt question folded into the post-season audit. 965/965 tests. **ANTI-CONTEXT-EROSION INVARIANT STANDS:** do NOT trust JSON scalars on any book written before HEAD `52607f2` — derive P&L/drawdown from `closed_positions`/C6 audit log. *(Previous, SESSION 62:)* AUDIT SESSION, no code/live-book writes, audit-directive thesis CONFIRMED — ⚠️ **GG-034 (HIGH, G6 BLOCKER) registered:** the live VPS book `logs/paper_portfolio.json` stores `total_realized_pnl = −$8.46` (0.85% drawdown) but Σ of its 117 closed-position `pnl` fields = **−$251.21** (25.1% drawdown); the C6 append-only audit log independently corroborates −$251.21 with zero double-resolutions → **the ledger is truth, the scalar is corrupted.** Consequence: the 20% `max_drawdown_pct` kill switch (`run_paper_trade.py:274` → `risk.py:418`), C7 monitor, C8 dashboard, and the G6 positive-P&L gate ALL read the corrupted scalar → kill switch is BLIND to the true −25% loss and never fires; G6 is being measured on a false near-breakeven number. Root cause: redundant scalar accumulator (derivable from Σ closed pnl) maintained under an in-process lock only while 4 runners load→mutate→save the same JSON — last-write-wins clobbers increments. Same desync in T4 book (−$21.59 stored vs Σ −$47.25). **This supersedes the SESSION 57 "reconciles to the cent / total_realized_pnl correct" claim** (S57 only cash-flow-reconciled bankroll + the 3 G4 closes). **ANTI-CONTEXT-EROSION INVARIANT: do NOT trust any scalar in `paper_portfolio.json` — derive P&L/drawdown from `closed_positions` or the C6 audit log. Real production bankroll is $130.62, NOT the $958.99 in CLAUDE.md (that is the stale local-only `paper_portfolio_vps.json`).** T-174 registered (dark-period fix, coordinate w/ T-171). Operator decision: **"let it ride" for tonight's G5 (NYK@SAS, potential Finals clincher)** — correcting the scalar would immediately trip the kill switch and halt all betting pre-tip. GG-014 (Kalshi congestion order failures, graceful) documented as tonight's accepted residual risk; all 3 healthcheck.sh FAILs reconfirmed false positives (T-173). *(Previous, SESSION 61:)* G5 pre-flight sweep; 41 T1 bets in place ($1,003.38 deployed); T-173 registered. 923/923 tests.  
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
| Current phase | **Phase 6/7 ACTIVE** (G5 ✅ CLOSED 2026-05-28; Phase 7 infrastructure built 2026-05-29; paper trading live; all 16 experiments complete; all 9 hypotheses resolved) |
| Operator | Earl Ignacio |
| Started | 2026-05-21 |
| Framework | Compass OS (ADR-0001) |
| Strategy class | Forecast-only (ADR-0002); arb/ reference-only pending APR-0010 |
| Capital status | NO LIVE CAPITAL — research and paper trading only until G6 |
| Last major milestone | **2026-06-24 SESSION 86 CLOSE** — **T-190 COMPLETE — full MLB arm built (pregame + T3 + T4 in-play). `run_mlb_pregame.py` (Step 1) + `run_t3_mlb_pretip.py` (Step 2) + `run_t4_mlb_live.py` (PIPE-07 MLB, Step 3, 55 tests). Suite 1819→1918/1918. deploy/cron.conf PIPE-07 MLB block added (paused). Next: VPS deploy + uncomment 5 MLB cron lines → MLB accumulation LIVE.** |
| Previous major milestone | **2026-06-24 SESSION 85 CLOSE** — **MLB ARM AUDIT: CLAUDE.md T4 corrected ("T4/T5: future/post-G6" was wrong; NBA T4 IS deployed PIPE-07; MLB T4 NOT built). Root cause of multi-session T4 blindness. All 4 MLB cron lines PAUSED (commit `aab7337`). T-190 REGISTERED: 3-step sequential build (pregame → T3 → T4). MLB bankroll $1,000 fresh, 0 open, 0 closed. 1819/1819 tests unchanged.** |
| Previous major milestone | **2026-06-25 SESSION 84 CLOSE** — **T-189 COMPLETE: PIPE-05 three-concern remediation. PIPE-05 now correctly targets tomorrow's games (T1 night-before baseline). Three fixes: (1) GAME_DATE=tomorrow + market date filter; (2) `ensure_persisted()` — portfolio file written at init before any bets (preserves `_reload_locked` invariant, which broke 10 tests when disk-write was added to `_load_or_init`); (3) hydrate fix (`probablePitcher,team`) + PIPE-05FX cache scope reduction (starters + pitcher logs preserved; only batter + completed_game logs busted). 29 new tests. 1819/1819. MLB portfolio reset to $1,000. VPS deployed. Monte Carlo validation: CLEAN, GREEN, ON AUTO.** |
| Previous major milestone | **2026-06-24 SESSION 82 CLOSE** — **T-187 ALL COMPONENTS COMPLETE (A–H). Full MLB paper trading stack live.** T-187E (`run_resolve_mlb.py` + `settle_position()`, PIPE-05R, 1704→1737 tests), T-187F (`run_mlb_calib_monitor.py`, T_global design, PIPE-05C Mondays 14:10 UTC, 1737→1772), T-187G (live SP overlay injection at inference time in `run_mlb_paper_trade.py`, fallback-safe, 1772→1790), T-187H (t=3 shadow gate re-evaluation — VALID NEGATIVE; GG-042 DEFERRED — structural; Brier delta=+0.0002, ECE=0.0037, AUC=0.6141; SP coverage 99.9% disproves data-quality premise; failure is base-rate structural ceiling; THRESHOLDS=[1,2] unchanged; no code changes). VPS HEAD 6447fea. 1790/1790 tests. |
| Previous major milestone | **2026-06-24 SESSION 81 CLOSE** — **T-187B COMPLETE: per-threshold MLB LR+Platt models pass shadow gate on VPS.** t=1: ECE=0.0134 ✅, Brier delta=+0.0055 ✅. t=2: ECE=0.0106 ✅, Brier delta=+0.0022 ✅. Root cause of pooled ECE=0.1246 failure: `class_weight='balanced'` calibrated to ~26% pooled average while per-threshold base rates differ 3–4×. Fix: one pipeline per active threshold (t=1, t=2); `threshold` excluded from feature vector as degenerate constant. t=3 excluded (GG-042); deferred to T-187G (live SP overlay). Full MLB paper trading infrastructure now live: PIPE-05 (23:30 UTC), PIPE-05R (22:30 UTC), per-threshold `mlb_v1_model.joblib` on VPS. 1704/1704 tests. All T-187 core tasks done; remaining: T-187E/F/G. *(Previous S81 ACTIVE:)* T-187C + T-187A + T-187D COMPLETE. PIPE-05 MLB paper trading runner live on VPS. (1) T-187C: `kalshi_client.py` + `venue_adapter.py` — `fetch_player_points_markets(sport="MLB")` now routes to `KXMLBHIT` via `_SPORT_SERIES` dict; was silently dropping the sport param and calling `KXNBAPTS` instead. (2) T-187A: `scripts/generate_mlb_features.py` — offline MLB feature matrix orchestrator (MLBIngestionClient → MLBFeatureStore → `exp_output/MLB/mlb_feature_matrix.csv`); resumable cache in `exp_output/MLB/cache/`; ~30 min first run; BOT_C4_ACTIVE guard; --dry-run. (3) T-187D: `src/prediction_market_bot/run_mlb_paper_trade.py` (PIPE-05) — MLB port of PIPE-03; threshold injection at inference; MLB game-in-progress guard; `logs/paper_portfolio_mlb.json` ($1,000 book); resolution deferred to T-187E; wrong-sport guard; threshold gate {1,2,3}; PT-MLB- prefix. (4) PIPE-05 cron at 23:30 UTC; PIPE-05R daily feature refresh cron at 22:30 UTC (--seasons 2026 only — VPS blocked from 2024/2025 by MLB Stats API HTTP 406 on DigitalOcean IPs). (5) **MLB Stats API IP-blocking finding** documented in DECISION_LOG: VPS can only access current-season (2026) data; 2024/2025 require local generation + scp. (6) T-187B (model training) IN PROGRESS: running `generate_mlb_features.py` locally (~30 min); then scp CSV → run `train_mlb_model.py` on VPS → shadow gate must pass. Suite: 1650 → **1704/1704** (+54 net). Deploy: commit `eef69e5`, VPS deployed, crontab installed. *(Previous S80:)* **T-117 COMPLETE + GG-006 CLOSED + T-186 COMPLETE (valid negative).** Kalshi Participant Agreement v1.54 formally read — no automation restrictions; Rule 5.13(s) = source agency insiders only (inapplicable); Rule 5.15 = behavioral conduct only. ADR-0005 GG-006 pre-requisite satisfied. MLB paper book = fresh $1,000 separate pool. T-186: discovered `nba_api.TeamGameLog` omits `PLUS_MINUS` for ALL season types → F-040 and F-042 both dead since EXP-005 (imputed 0.0). Fix: `_fill_pts_allowed_via_crossref()` in `pull_playoff_teamgamelog.py` — derives `plus_minus = my_pts − opp_pts` from MATCHUP cross-reference; 338/338 games populated. v2b retrain: F-042 76/103 non-NaN (73.8%); Brier +0.000130 < 0.001 threshold → shadow gate FAIL. Valid negative — deploy v2-065b9510 October 2026 (ADR-0031 unchanged). 10 new cross-ref tests. Suite 1609→1650/1650. T-187 REGISTERED. Commit 89d795c, VPS HEAD confirmed. *(Previous S79:)* **T-184 COMPLETE: EXP-017 MLB commercial validation script.** `scripts/run_exp017_mlb.py` (new): three analysis layers: EV analysis + ADR-0024 tier checks + edge monotonicity guard. MLB threshold breakdown (k=1/2/3). `compute_fee_net_edge` with 7% Kalshi fee formula. CI mode (exit codes 0/2/3/4). MLB position schema contract defined. 99 new tests (`test_t184_exp017_mlb.py`). 1510→1609/1609 total green. Script returns INCONCLUSIVE until ≥20 positions (MLB paper trading Phase 3, August 2026). *(Previous S78:)* **T-183 COMPLETE: MLB C3 model training infrastructure.** `scripts/train_mlb_model.py` (new): `HOLDOUT_CUTOFF="2026-01-01"`, null-baseline shadow gate (`brier_delta≥0.001 AND ece≤0.05`), `_build_mlb_target` (3× threshold expansion, `threshold` as float feature, `y_target=(h≥k)` Int8/NA), `_NON_FEATURE_MLB` frozenset (raw `h` leakage prevention), Pipeline = `StandardScaler→CalibratedClassifierCV(LR, method="sigmoid", cv=3)` (matches `forecaster.py:354-358`), artifact schema matches NBA loader contract, `_mlb_model_version()` "mlb-v1-"+sha1[:8]. `CALIBRATION_TEMPERATURE["mlb"]=1.0` confirmed. 77 tests, 11 classes. BOT_C4_ACTIVE contamination identified + fixed. 1510/1510 total green. Next: T-184 (EXP-017 MLB commercial validation, P0). *(Previous S77:)* **T-182 COMPLETE: MLB C2 baseball feature set.** `mlb_features.py` (new): `MLBFeatureStore`, `_compute_rolling_batter_features`, `assign_train_test_labels`. MLB_FEATURE_VERSION 1.0.0. TI-01 compliant. SP overlay MANDATORY. Sum-then-divide rates. 30-venue park factor dict. C6 audit (5 events). 60 tests. 1433/1433 total green. Next: T-183 (MLB C3). *(Previous S76:)* **Pre-MLB governance scrub COMPLETE.** KXMLBHIT confirmed (was KXMLBHITS stub — fixed in `kalshi_client.py`). DtypeWarning fixed (`run_paper_trade.py` + `run_pregame.py`). VPS cron health verified clean. T-117/GG-006 June 30 deadline flagged for operator action. 1373/1373 tests green. *(Previous S75:)* **T-181 COMPLETE: MLB C1 data ingestion module.** Three new C1 source files: `mlb_ingestion.py` (MLBIngestionClient), `mlb_team_stats_store.py`, `mlb_pitcher_stats_store.py`. 80 new tests. 1373/1373 total green. DS data-source decision: MLB Stats API (statsapi.mlb.com) via raw requests. IF-C1-C2 contract established: batter 24-col schema, pitcher 22-col schema, game starters gamePk dict. *(Previous S74:)* **Governance-only. MLB $1K fresh paper book decision (DECISION_LOG S74). ADR-0031 Known Limitations section added (F-042 NaN, Brier gain source, T-177 interpretation, T-186 follow-up, deployment framing). Phase 3 task registration: T-181/T-182/T-183/T-184/T-186. T-185 v2 deploy runbook registered (8-step + DS witnesses Step 7). NBA 26-27 book reset options A/B/C documented. DARK_PERIOD_PLAN Phase 3/4 updated. Commit `498cb97`. 1293 tests unchanged.** *(Previous S73:)* **T-072 COMPLETE (Parts A+B+C). ADR-0031 ACCEPTED. FEATURE_VERSION 1.4.0. Model v2-065b9510 (Brier Δ=+0.001507, ECE=0.0426, shadow gate PASSED). T-177 v2 INCONCLUSIVE (p=0.1639). Phase 3 MLB gate OPEN. 1293 tests. Deferred: v2 deploy + kill switch reset (Oct 2026).** *(Previous S71:)* **T-180 Phase 3 (evaluator math, 76 tests) + Phase 4 (live execution path, 67 tests) COMPLETE.** Sub-band evaluators: real math implemented — Gamma-Poisson Bayesian update, Poisson survival probability, phase-conditional Kelly (EARLY 0.010→NEAR_CERTAIN 0.167), blowout detection, 3-condition exit logic (TIME-FLOOR, REVERSAL, BUFFER-BREACH). Live execution path: `t4_live_runner.py` wires T4FastHalt (GG-038), T4PositionRegistry, T4PriceCacheUpdater (GG-039), T4GameStateBuilder (GG-040), T4LiveRunner (C4/C5/C6/C7). `on_game_event()` implemented (Layer1+Layer2). `create_phase8()` factory (per-instance PHASE8 flag). C4 kelly_fraction backward-compat. **1280 tests, 0 failures.** T4 STILL DARK — all execution paths gated on Phase 8 ADRs (GG-038/039/040 resolution + activation ADR). *(Previous S70:)* Sub-band evaluator math sprint (real implementations replacing stubs, 185 test_t4_engine.py tests). *(Previous S69:)* **Option C DS decision: feature-set diagnosis sprint. Root cause of anti-predictive edge identified: missing playoff-context λ multiplier. T-072 scope updated.** NBA Finals n=103: YES 38.9% WR vs NO 68.7% WR. λ compression 0.91–0.70 across thresholds. Three feature fixes into T-072. GG-037 alpha half + GG-004 OPEN pending EXP-017 at scale. *(Previous S68 CONT.:)* T-177 monitor live; governance cleanup. *(Previous S68:)* T-180 PHASE 2 — T4 routing engine built. Resolves the S67 Q6 standing flag — Layer 1 Continuous Evaluation + Layer 2 staleness-arbitrated queue now exist (the S67 scaffold was only enum/config plumbing). Two modules: `t4_price_cache.py` (GG-039: `T4PriceCache`, `STALENESS_WINDOW_S`, `T4Phase8BlockedError`; polling deferred to Phase 8) and `t4_execution_engine.py` (`GamePhase`/`classify_game_phase`; `Layer1EvaluationEngine` event dispatch; `Layer2ExecutionQueue` heapq with EXIT-priority + 3 drop conditions price_stale/edge_below_min/direction_reversed; 8 BLOCKED sub-band evaluator stubs; `T4CorrAdjuster._assert_downward_only` Principle-6 guard; `T4ExecutionEngine._PHASE8_ACTIVE=False`, `simulate_cycle()` test-usable). +109 tests. **VERIFIED 1108/1108 green; `_PHASE8_ACTIVE=False`, both entrypoints + polling + all evaluators provably blocked.** T4 gated at GG-038/039/040 — STILL DARK; no VPS live-behavior change. |
| Previous major milestone | **2026-06-22 SESSION 67** — **ADR-0029 ACCEPTED (Tier A frozen, DS sign-off Earl Ignacio; Tier B provisional) + T-180 SCAFFOLD landed.** Two-tier acceptance reconciles hard rule #3 (ADR immutability) with unvalidated specifics: Tier A (three-layer execution architecture, six design principles, immediate-execution/staleness-arbitration model, per-sub-band budget MECHANISM, T4 Activation Gate STRUCTURE, kill-switch ≤5s requirement) is frozen; Tier B (sub-band roster, ALL numerics, alpha hypotheses) stays PROVISIONAL/DECISION_LOG-revisable until each sub-band's Phase 8 Activation Gate. `execution_bands.py` scaffold: `T4_IN_PLAY` kept as aggregate parent; 10 sub-bands added beneath via `T4_SUBBANDS`/`is_t4_subband()`/`t4_parent()`; `T4SubBandSpec` + `T4_SUBBAND_REGISTRY` (all BLOCKED) encode Tier B in code + `validate_t4_subbands()` invariant; PROJ/ARITH Kelly held ≤0.167. Strategy K not redefined (ADR-0030 overlap OPEN). Tests 999/999. T4 still dark; no VPS deploy. Q6 flag: Layer 1/2 routing engine (substance of Tier A) unbuilt — remaining T-180. |
| Previous major milestone | **2026-06-22 SESSION 65** — **T-148 ADR-0028 REWORK COMPLETE (PENDING DS SIGN-OFF).** Root misalignment confirmed: ADR-0028 initial draft required T4 Tier 2 + T-AGG for G6 closure, but T4 strategies are BLOCKED in BAND_REGISTRY (Phase 8+, `requires_realtime=True`). G6 is a T1 live capital gate. Rework: G6 closure reduced to T1-only (6 items); Mods 6/7/8 moved to new "T4 Activation Gate" (Phase 8 pre-requisite) in ADR-0028. Mods 5+9 (fill-realism + YES-only gate) remain at G6 scope. G6_GATE_CHECKLIST.md I-4 corrected. APR-0022 updated with rework rationale. T4 Activation Gate flagged PLACEHOLDER pending **T-179** (T4 sub-band segmentation — DS directive: "In-game can't be clumped as one aggregate bucket"). Governance hygiene: T-173 (healthcheck.sh Python path), T-154 (CHANGE_CONTROL.md decisions_logged: true), T-178 (market_mapper MLB pre-flight audit — C4/C6/C7/C8 sport-agnostic confirmed). VPS HEAD `97e66ae`; 988/988 tests. |
| Previous major milestone | **2026-06-16 SESSION 64** — **PRE-MLB GOVERNANCE SPRINT: GG-036 + GG-035 + GG-037(calibration half) RESOLVED; full-DB assessment complete.** VPS HEAD `897ff4d`; 988/988 tests. GG-036: re-froze 158-bet NBA Finals dataset, G5 41 positions resolved (NOT fabricated), capital unlocked. GG-035 (ADR-0026/APR-0020): C4 two-tier free-cash invariant (8a solvency KILL, 8b 60%-of-equity REJECT). GG-037 (ADR-0027/APR-0021): C3 temperature calibration on the **production Poisson prob** (NOT Platt — re-fit would have been a no-op; root cause = Poisson overdispersion); NBA T=2.05 OOS-validated, MLB fail-safe identity. **Recalibration DISPROVED miscalibration — edge stays anti-predictive (edge>0 0.356 vs edge≤0 0.747); GG-037 alpha half + GG-004 stay OPEN; no demonstrated alpha vs Kalshi.** No live behavior change (book halted at 25.12% drawdown kill switch). New tasks T-175/176/177/178. |
| Previous major milestone | **2026-06-14 SESSION 63** — **T-174 + T-171 DEPLOYED + LIVE BOOK CORRECTED; GG-034 + GG-033 RESOLVED.** VPS HEAD `52607f2`; governance closure `c52d298`. Main book `total_realized_pnl` −8.46 → **−251.21**, drawdown **25.12%**, kill switch un-blinded (code-path verified). T4 book needed no correction. T-171 untrack → `git pull` no longer clobbers the live book. **Two new OPEN gaps surfaced: GG-035** (over-leverage — corrected bankroll −$254.59; $1003.38 = 100.3% of initial deployed; no C4 free-cash invariant) and **GG-036** (41 G5 positions unresolvable — nba_api has no 2026-06-13 box scores — $1003.38 locked; outcomes NOT fabricated). **G6 baseline RATIFIED negative** (−$251.21/−25.1% headline, −$302.98/−30.3% clean-only; SNAP-2026-06-14-001) — number-of-record only; Tier 0/EXP-017 (GG-004) remains the binding G6 blocker, positive-P&L gate FAILING. 965/965 tests. |
| Previous major milestone | **2026-06-13 SESSION 62** — AUDIT SESSION (no code, no live-book writes). **GG-034 registered (HIGH, G6 BLOCKER):** live book `total_realized_pnl = −$8.46` but Σ closed-position pnl = **−$251.21** (true 25.1% drawdown, corroborated by C6 audit log) → drawdown kill switch BLIND; G6 P&L gate measured on a false number. T-174 registered (dark-period fix w/ T-171). Operator "let it ride" for G5 (NYK@SAS); GG-014 = accepted residual risk. **INVARIANT: trust `closed_positions`/audit log, never the JSON scalars.** 923/923 tests. |
| Previous major milestone | **2026-06-12 SESSION 57** — Q6 WORRY SWEEP + BANNER FIX + RECONCILIATION. Commit `3718015`. **(1) PORTFOLIO BANNER FIXED:** governance_scan.sh fetches VPS live book (ssh, 3s timeout, 10-min gitignored cache). Stale $1000/open-3 picture gone. **(2) RECONCILIATION CLEAN:** VPS book reconciles to the cent ($130.62). **(3) S46 RESET-EQUITY NUANCE logged:** effective equity $1,142.46 not $1,000 at S46 reset; T-172 must use Σpnl. **(4) T-166 annotated:** per-ticker guard shipped S53; remaining run-level guard → done S58. 852/852 tests. |
| Previous major milestone | **2026-06-12 SESSION 55** — T-168/GG-030 MC CORRELATION FIX + T-170 LEDGER CORRECTION. Commit `530e1c3`. **(1) GG-030 RESOLVED (T-168):** `simulate_portfolio()` now draws one Poisson score per player (correlated); `_infer_lambda()` fits lambda via least-squares on (threshold, model_p) pairs. Bug found+fixed: initial implementation inverted model_p for NO bets. G5 MC output: P(profit)=98.3%, kill-switch risk=1.28% at $20 trigger. **(2) GG-031 registered:** GG-028 blast radius=9 duplicated tickers ($402 doubled exposure), not 2. T-169 queued. **(3) GG-032 registered + T-170 RESOLVED:** T4 `bankroll_usd` corrected 1869.68→478.41; `initial_bankroll_usd` 1000→500. True T4 pool = $478.41. |
| Previous major milestone | **2026-06-12 SESSION 52** — G5 PORTFOLIO RISK + GOVERNANCE GAPS. No code changes. **(1) G5 actual portfolio risk (41 committed positions, $1,003.38 deployed):** Direct MC on `paper_portfolio.json` positions: EV +$246.67 (24.6% ROI), P(profit)=99.8%, P(kill switch)=0.00%. P50 end bankroll=$382.40 (from $130.62 current). Worst case (100k sims): -$124.95 → $5.67 end. Wemby concentration $323.33 (32% of total) — correlated left-tail risk on 4 NO positions if model miscalibrated on extremes. **(2) GG-028 registered (PIPE-03 idempotency gap):** Two cron batches confirmed: 22:00 UTC (29 bets, expected) + 01:00 UTC (12 bets, unexpected). The 01:00 batch placed duplicate Wemby NO ≥40 and NO ≥35 — T-162's in-progress guard does not cover same-`game_date` re-execution when game hasn't started. T-166 registered: add `game_date`-keyed idempotency check before bet-placement loop. Phase 1 P1. **(3) GG-014 final snapshot:** 22:00 UTC: 9/29 failed = 31% (identical to pre-T-164; T-164 did not fix primary window). 01:00 UTC: 0/12 failed (T-164 effective at off-peak). Root cause is server-side Kalshi congestion at ~22:00 UTC basketball rush; fix path: move cron to 18:00 UTC or higher rate-limit tier. GOVERNANCE_GAP_LOG updated. **(4) GG-029 registered (MC script gap):** `scripts/run_monte_carlo.py` reads `pregame_YYYYMMDD.json` with hardcoded kelly=0.1, min_edge=0.02 — not committed positions, not actual risk engine params. Every Finals MC reported a hypothetical residual-bankroll re-deploy. T-167 registered: rewrite MC to use `paper_portfolio.json` + `risk.py` constants. Phase 1 P2. **(5) DECISION_LOG SESSION 52 entry complete.** 852/852 tests. |
| Previous major milestone | **2026-06-11 SESSION 51** — GOVERNANCE SPRINT: three items, no code. **(1) ADR-0024 ACCEPTED (T-157, GG-021 RESOLVED):** Project-level stop/pivot criterion ratified cold before 2026-27 regular-season data. Tier 1 (n≥150, ≥2 calendar months): EV/bet < -$0.03/bet → diagnostic sprint. Tier 2 (structurally adequate sample: n≥500 unique markets, ≥15 distinct opponents OR ≥2 sports × n≥150, ≥3 calendar months): CONFIRMED_NEGATIVE (p<0.05) → halt paper trading + ADR-0004 supersession. Scope retreat option: if profitable subset isolated, reduced-scope ADR acceptable. Passability drift watch: standing and permanent. **(2) EXP-017 scope transition — DS ruling:** NBA Finals sample (n≈96) structurally insufficient — single-series opponent, ~20-30 players, T1-only, Finals context. EXP-017B historical data retained but NOT G6 evidence. Commercial validation transitions to MLB 2026 (DARK_PERIOD_PLAN Phase 3) + NBA 26-27 regular season. ADR-0024 defines structurally adequate sample. GG-004 remains OPEN. **(3) DARK_PERIOD_PLAN.md ratified (T-158):** `04_EXECUTION/DARK_PERIOD_PLAN.md`. Phase 1 (June-July): G5 resolve, EXP-017B/018 G5 run, T-153/156/159. Phase 2 (July): T-072 retrain, DS-04, Polymarket. Phase 3 (Aug-Sep): MLB C1/C2/C3 + EXP-017 MLB run + ADR-0024 Tier 1 check. Phase 4 (Oct): GG-014 Day 1 confirmation, G6 review, ADR-0005. **(4) GG-014 dark-period gap:** T-164 deployed but G5 placed before fix. No viable production confirmation before dark period. GG-014 G6 gate deferred to 2026-27 Season Day 1. GOVERNANCE_GAP_LOG updated. 852/852 tests (no code changes). |
| Previous major milestone | **2026-06-11 SESSION 50** — PAM archetype register wired to T1 + T4. `get_archetype()` added to QualitativeSignalStore (QTI-01 temporal guard; returns prf_primary/name/active_modifiers/hybrid fields). T1 `run_paper_trade.py`: `pam_archetype` in `forecast_rec`; `[PRF-X]` tag in BET print output per cohort player. T4 `run_t4_inplay.py`: `archetype_register: QualitativeSignalStore | None = None` injected on `T4EventLoop`; `pam_archetype: Optional[dict] = None` field on `T4RoutingResult`; best-effort lookup in `on_game_state_event` (KILL_SWITCH path intentionally excluded). KILL_SWITCH path does not receive archetype (routing halted before player context matters). GG-027 registered: T2/T3/T5 bands not wired; EnvironmentClassifier (pressure-context game-environment categorizer — elimination_flag, series_momentum, crowd_premium, role_expansion_flag → HIGH_PRESSURE / NEUTRAL / LOW_STAKES) not built; QS snapshot 2026-05-28 not updated for Finals role expansions. LOW severity now (bands SKELETON/BLOCKED), HIGH pre-MLB activation. T-165 registered: full PAM integration across T2/T3/T5 + EnvironmentClassifier ADR — MLB activation gate. 852/852 tests. Commit `4d5cd43`, VPS deployed. |
| Previous major milestone | **2026-06-11 SESSION 49** — INSTITUTIONAL SPRINT. **(1) ADR-0019-A01 — NOISE_BUFFER_BAND_T4 0.139→0.19:** EXP-019B empirical (G4, n=1199): observed mean=0.182, p50=0.187; EXP-019C p90 spread=0.170; within_20pct=False (0.139×1.20=0.167 < 0.182). T-152 update gate triggered. New value 0.19 above p90/mean, within MEMORY_BANK recommendation ≥0.18–0.20. `execution_bands.py` updated. **(2) T-164 GG-014 order throttle fix:** inter-order sleep 0.5→2.0s (`paper_trader.open_position()`); MAX_RETRIES 3→4; RETRY_DELAY_S 1.0→2.0 (`kalshi_client.py`); delay schedule 4/8/16/32s=60s total. Root cause: 29-order burst exhausts rate-limit window in 14s. **(3) PIPE-03 reserve mandate hygiene:** pre-run health check (prints deployed %, floor $, bankroll, WARN >80%); batch order integrity report (submitted/ok/failed/rate, WARN >5%) added to `run_paper_trade.py`. Tests updated: `test_t146_t147_exit_mechanics.py` (3 locations), `test_kalshi_client.py` (1 assertion), new `test_t164_order_throttle.py` (9 tests). DECISION_LOG ADR-0019-A01 entry added. GG-014 status updated to PARTIALLY RESOLVED. GG-017 T-152 update gate noted. 852/852 tests. VPS deploy pending. |
| Previous major milestone | **2026-06-12 SESSION 48** — G5 PLACED / G4 RESOLVED / GG-014 BREACHED. G4 resolved locally (run_resolve_local.py): Brunson NO-40 WIN (+$8.57), Vassell NO-25 WIN (+$1.16), OG Anunoby NO-25 LOSS (-$18.20); net -$8.46. VPS bankroll: $285.27. G5 T1 bets placed by early cron Jun 11 for game_date=2026-06-13: 29 bets, $848.73 deployed, 20 NO + 9 YES (YES-only gate NOT implemented — too late for G5; G6 if DS ruling still operative). 9/29 Kalshi demo orders failed with "transient error — max retries exceeded" (31% failure rate — GG-014 G6 gate BREACHED). T-138 exponential backoff ineffective at 29-order burst. T-164 registered (throttled submission). G5 MC: 29 bets, EV +$209.70 (+24.71% ROI on deployed), P(profit)=97.5%, kill switch risk 0.10%; reserve mandate exceeded (84.9% > 60%, batch enforcement deferred). ADR-0023 added to DECISION_LOG ADR Index. GG-014 summary and Resolution updated with G5 data. SESSION 48 block logged in DECISION_LOG and TODO_NEXT. |
| Previous major milestone | **2026-06-11 SESSION 47** — ADR-0023 ACCEPTED / T-163 CLOSED / GG-026 RESOLVED. T4_BAND_WEIGHT=0.27 calibrated from G4 empirical ($499.95/$1,869.68=0.267→0.27); PAPER_T4_FLAT_SIZING and PAPER_T4_POOL_USD constants removed entirely; `_compute_t4_band_budget` is now single budget path (no RESERVE_MANDATE deduction — T4 pool is isolated capital); pool_isolated=True hardcoded; flat sizing (1 contract/bet) retained as hardcoded T4 paper policy. G5 T4 budget: $1,869.68 × 0.27 = ~$504.81. EXP-018 n=98: CONFIRMED_NEGATIVE (all-bets + injury-filtered); DS ruling: calibration gap — multi-sport scale (MLB/NFL) addresses sample size; G5 YES-only diagnostic mode. EXP-019B empirical TP=0.281 (DIVERGED from 0.799 analytic; market-lag assumption fails; Kalshi semi-efficient). EXP-019C p90 spread=0.170 > NOISE_BUFFER_BAND_T4=0.139 (raise to ≥0.18–0.20 before activation). 843/843 tests. Commit `72ba619`, VPS deployed. |
| Previous major milestone | **2026-06-10 SESSION 46 CLOSE** — FULL POST-G4 INSTITUTIONAL SPRINT COMPLETE. Knicks G4 won; series 3-1 NYK lead. **(A) Bankroll reset to $1,000** (DS option a; historical P&L preserved in closed_positions; kill switch cleared). **(B) ADR-0021 ACCEPTED — GG-025 RESOLVED** (incremental delta materiality; calibration gap cancelled algebraically via `delta_p_incr = p_t4 − p_t4_baseline`; gate = `max(2·σ_null(t), 0.04)`; stateless restart-safe baseline; G4 replay 2,193 records: pass rate 74.6%→9.7%, Q1 89.3%→10.8%, Q4 1.4%→13.5%; commits 45d13db; 10 new σ_null invariant tests). **(C) ADR-0022 / T-161 ACCEPTED — GG-023 RESOLVED** (realized-value exit credit; wins recycle entry cost only, losses permanently consume budget; `_exit_budget_credit()` + `_reconstruct_t4_ledger()`; G5 strip starts at $0 automatically by game_date keying; commit 0f38112; 13 new tests). **(D) EXP-018 G4 data: Hypothesis C ruling INVALIDATED** — injury-filtered view flipped CONFIRMED_NEGATIVE at n=98; DS ruling still required (T1 Tier 2B FAILS / insufficient sample / other). **(E) EXP-017B** DIRECTIONAL_NEGATIVE vs actual Kalshi prices (-$0.0361/bet, n=96); GG-004 remains OPEN. **(F) T4 pool architecture gap registered T-163** — PAPER_T4_FLAT_SIZING=true bypasses production Kelly budget path; $500 flat cap doesn't scale with T4 pool ($1,869.68); pre-G5 fix required (ADR-0023). **843/843 tests. VPS HEAD confirmed.** |
| Previous major milestone | **2026-06-10 SESSION 45** — G4 PRE-TIP SPRINT + PDTP ASSESSMENT. (1) T1 stale daily-loss kill switch FIRED on G4 early cron (0 bets) — `run_paper_trade.py` date-reset guard (`b6cedd0`); manual PIPE-03 recovery 23:50 UTC placed 33 bets/$757.69, 0 order failures. (2) Daily-loss semantics gross→net in `paper_trader._accumulate_daily_loss()` (`424698a`); tonight-critical with exits active; T-156 registered (ADR-0012 amendment + first-ever accumulation tests). (3) T4 restarted with new code (PID 372067). (4) Portfolio MC on actual 33-position book: EV +$152.08, P(profit) 95.3%, P(20% kill trip) 1.07%. (5) Hypothesis C deferred to post-G4 rerun (DS). (6) PDTP full-project assessment → GG-021 (no stop criterion; T-157), GG-022 (paper-fill realism; T-153 scope expanded — all G6 P&L now "unhaircut paper fills"), LL-014 (readiness overconfidence), T-158 (dark-period plan), T-159 (state-machine invariant tests), T-160 (doc hygiene); TODO_NEXT priority queue reordered. G4 in progress at close. 817/817 tests. |
| Previous major milestone | **2026-06-10 SESSION 44** — G4 READINESS COMPLETE + FULL AUTO. (1) T4 stale daily-loss kill switch bug: `current_daily_loss=$157.89` from G3 would have fired kill switch on first G4 bet — fixed in `run_t4_live.py:438` with date-check reset, committed `a300a51`, deployed. (2) GHA post-game resolve: nba_api 403-blocked on VPS (Akamai WAF); Mac cron was Mac-dependent — `.github/workflows/post_game_resolve.yml` created (GHA runners not blocked), runs T1+T4 resolve at 05:30 UTC daily via `VPS_SSH_KEY` secret, confirmed via workflow_dispatch (run 27253281067, 35s, all green). Mac `post_game_g4_resolve.sh` cron `0 23 10 6 *` remains as fallback + experiment runner (EXP-017/018). System fully automatic for G4 — no operator action required. 817/817 tests. |
| Previous major milestone | **2026-06-09 SESSION 43** — APR-0019 ACCEPTED (DS: Earl). GG-018 RESOLVED. Kalshi fee 0.07 partially verified (GG-020: ≥2 sources support 0.07; one source suggests 0.06 for sports; conservative direction; T-151 open for receipt confirmation post-G6). EXIT_MECHANICS_ACTIVE=True deployed to VPS. run_monte_carlo.py adj_λ upgrade deployed. 817/817 tests. G4 cron tonight. |
| Previous major milestone | **2026-06-09 SESSION 42 (sprint)** — T-146 + T-147 + ADR-0019 COMPLETE. Exit mechanics implemented. ADR-0019 splits ADR-0018's single gate: Tier 1 (code implementation) = CLOSED; Tier 2 (activation) = OPEN pending EXP-019B/C empirical. `paper_trader.py` now has `exit_position()` with correct YES/NO PnL formulas, pool_isolated flag handling, C6 logging. `run_t4_live.py` `_run_cycle` now has exit evaluation pass before entry loop (time guard ≤3min, NOISE_BUFFER_BAND_T4=0.13905). Return signature expanded to 4-tuple (evaluated, fired, exited, deployed). 23 new tests in `test_t146_t147_exit_mechanics.py`. **816/816 total tests pass.** GG-020 registered (fee rate 0.07 provenance unverified). T-152 + T-153 registered (pre-activation empirical gates). DECISION_LOG updated. |
| Previous major milestone | **2026-06-08 SESSION 41 (cont.#2)** — G4 post-game workflow built: `scripts/post_game_g4_resolve.sh` (10 steps), cron `0 23 10 6 *`. **EXP-018 COMPLETE** (G2+G3, n=66): overall CONFIRMED_NEGATIVE (EV=-$0.0014/bet); injury-filtered DIRECTIONAL_POSITIVE (+$0.0202); YES bets +$0.0733, NO bets -$0.0440; opp_adj_factor=0.9586 < 1.0 ✓. Hypothesis C technically triggered; injury filter clears; DS decision required. |
| Previous major milestone | **2026-06-09 SESSION 41 (cont.)** — EXP-019 sprint complete. EXP-019B analytic (1,114 G3 T4 YES positions): 79.9% of YES losses correctly exit (433/542), 0 false exits on YES wins, E[log_r] +0.5%. Policy 2 = Policy 3 (Kelly fraction collapses at exit boundary). NOISE_BUFFER_BAND_T4=0.13905 confirmed calibrated. run_t4_live.py updated: spread logging (EXP-019C) + trajectory logging (EXP-019B empirical) both deployed to VPS from G4. EXP-019C skeleton written. Commit 817e3bc pushed and VPS deployed at /opt/prediction-market-bot. |
| Previous major milestone | **2026-06-09 SESSION 41 (earlier)** — Finals G3 resolved via post_game_g3_resolve.sh (ALL STEPS OK 05:08:59Z). T1: 47 positions settled, bankroll $876.83, cumulative P&L $-123.17 (G3 swung -$198.84 — largest single-game loss; OG Anunoby NO-25+ -$44.40, Mikal Bridges T4 YES-10+ -$32.56). T4 first live run: 215 G3 positions, P&L +$39.44, T4 pool $1,539.42 (from $500), win rate 51.4% (1,115 cumulative T4 bets). MC miss: predicted EV=+$138.47 at 95.1% (stale 9-player pregame, adj_λ not applied) — actual -$198.84. EXP-017 Part B: DIRECTIONAL_POSITIVE (EV=+$0.0050/bet, n=66 unique markets; at APR-0017 floor, power INSUFFICIENT). GG-018 registered (APR-0017 floor T1-only, T4 invalidates pooling premise). T-148 registered. |
| Previous major milestone | **2026-06-09 SESSION 40 (cont.)** — ADR-0018 ACCEPTED (APR-0018): Band Exit Mechanics — symmetric filter-out `mip_current > p_current + NOISE_BUFFER_BAND`; Poisson time-weighting; Kelly-inverse sizing; universal evaluator in T4 _run_cycle(); all T1–T5. EXP-019A COMPLETE: NOISE_BUFFER_BAND analytic derivation (T1/T2/T3=0.22053, T4=0.13905, T5=0.13328); pure stdlib; VPS-verified. GG-017 registered. **SESSION 40 EARLIER:** CRITICAL BUG `run_paper_trade.py:558` false kill switch fixed; `live_terminal.py` T4 log path fixed; `run_t4_live.py` crash guard; `post_game_g3_resolve.sh` scheduled. T4 LIVE for G3. Tests 783/783. |
| Previous major milestone | **2026-06-04 SESSION 31** — GG-012: PIPE-02 BOT_C4_ACTIVE guard caused silent failure for 2 cron cycles (Jun 3 + Jun 4 21:55 UTC). adj_λ (ADR-0015) was NEVER applied to any live PIPE-03 run. Guard removed from `run_pregame.py` (commit 2997c71). GG-012 registered, T-134 registered. G2 MC: 9 open positions, EV=+$60.02, P(profit)=82.7%. Timing sweep: GAME_DATE=run-date design confirmed correct. All deployed to VPS. 715/715 tests. |
| Previous major milestone | **2026-06-03 SESSION 24** — Both execution disconnects resolved before Finals Game 1: (1) Disconnect 1: RESERVE_MANDATE_PCT=0.05 on VPS, T1 floor drops $200→$50, all 33 bets ($827) now fire; (2) Disconnect 2: `pool_isolated=True` in PaperTrader.open_position() — T4 records positions independently without depleting T1 bankroll (commit dfb16f0). T4 running PID 153790, PAPER_T4_FLAT_SIZING=true, PAPER_T4_POOL_USD=$500. |
| Previous major milestone | **2026-06-02 SESSION 19 (PDT)** — Bug H drawdown fix + PAPER_T4_VIRTUAL mode in `run_t4_live.py`. Drawdown was computed as `(initial - current) / initial`, counting deployed T1 capital (~$540) as a realized loss → 54% false drawdown → C4 kill switch rejected all T4 bets. Fix: `_realized_loss = max(0.0, -portfolio.get("total_realized_pnl", 0.0))`. PAPER_T4_VIRTUAL=true stages C4-approved T4 bets without portfolio write. Screen `140907.t4_live` running with fix. Commit `706264b`. |

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

8. **G6 evidence gate = APR-0017 (ACCEPTED 2026-06-01), supersedes APR-0016.** Four-tier sequential evidence standard: Tier 0 (commercial preconditions: EXP-017 Part B CONFIRMED + production price discovery) → Tier 1 (execution integrity: rate+slope criteria, zero-tolerance idempotency/audit) → Tier 2 (model performance trends: calibration, EV, Brier, P&L slope) → Tier 3 (risk control validation). Statistical floor: **≥66 resolved bets** (derived from T2-A calibration power formula) + **≥5 game nights** (derived from slope regression df ≥ 3). All numeric thresholds derived — no arbitrary counts. T0-B already met (T-114). T0-A (EXP-017 Part B CONFIRMED) is the remaining Tier 0 precondition. GG-004 is OPEN (n=2 unique markets, directional positive; floor is 66). Clean G6 evidence begins Finals G1 Jun 3. See `00_ADMIN/APR-0017_g6-multi-dimensional-evidence-standard.md`.

9. **Strategic decisions made in holistic reviews must be captured in DECISION_LOG.md AND APPROVALS_REGISTER.md before session end.**

10. **No strategic or architectural document may be marked CANONICAL without `**Decisions logged:** true` in its header.**

11. **THIS BOT PRODUCES HUNDREDS TO THOUSANDS OF BETS PER GAME NIGHT AT DESIGN INTENT. DO NOT DISMISS THIS.** Full operation = T1+T2+T3+T4 active, regular season (10+ simultaneous games, 400+ markets/night), multi-venue (Kalshi + Polymarket + DFS pick'em). The correct mental model: quant strategy with qual enhancers, tiered by time horizon, firing across all markets where the model finds edge. The 66-bet G6 statistical floor is trivially exceeded in the **first 1-2 nights of regular season under T1 alone**. The Finals constraint (~38 markets, T1-only, 1 game/night, ~13 bets/night) is a structural limitation of the current paper window — NOT a representation of design throughput. Any session that treats "accumulating 66 bets" as the binding G6 challenge is wrong. The ACTUAL binding G6 constraints are: (a) GG-004 resolved — EXP-017 Part B confirms positive EV vs. real Kalshi prices; (b) ≥5 game nights for slope regression (df ≥ 3). These constraints determine G6 timing. Bet count does not. If both binding constraints are met in the first week of 2026-27 regular season, G6 can close that week. Every judgment call, threshold choice, and methodology decision in the document must have a corresponding DECISION_LOG.md row before CANONICAL status is granted. PDTP documents require Pass 5 (Decision Extraction) as the final step before CANONICAL. At session start, run the governance scan: `grep -rn "^\*\*Decisions logged:\*\* false" 02_ARCHITECTURE_DESIGN/ 08_MODEL_RISK_GOVERNANCE/ 01_SPEC/`. Any match is a governance debt — resolve or register a T-NNN task before any implementation work. See CHANGE_CONTROL.md — CANONICAL Status and `decisions_logged:` Requirement. Judgment calls (threshold changes, sequencing pivots, dark-period plans) are as load-bearing as code changes. Handoff documents must include a "Strategic Decisions" section separate from "Tasks Completed." If a decision was made verbally in a session and is not in these files, it did not happen.

---

## Session-Start Governance Scan (MANDATORY — Before Any Work)

Run all three steps. Each takes < 60 seconds. Skipping any step risks building on undocumented or architecturally incoherent assumptions — the root cause of the failures documented in GOVERNANCE_GAP_LOG.md.

### Step 1 — Documentation debt (existing)

```bash
grep -rn "^\*\*Decisions logged:\*\* false" \
  "02_ARCHITECTURE_DESIGN/" \
  "08_MODEL_RISK_GOVERNANCE/" \
  "01_SPEC/" 2>/dev/null
```

Each match is a document with unlogged strategic decisions. Register a T-NNN task or extract now.

### Step 2 — Code stub/placeholder scan (T-103, 2026-06-01)

```bash
grep -rn "# stub\|# placeholder\|# TBD\|# todo" src/
```

Each match is a code-level placeholder. For each: was it set before Phase 5–7? If yes, it predates the current architecture and may be wrong. Register in GOVERNANCE_GAP_LOG.md before proceeding.

**This scan exists because GG-001 (`max_concurrent_positions: 10` stub) survived three gate clearances because no scan checked for code-level stubs. See LESSONS_LEARNED.md LL-010.**

### Step 3 — Open governance gaps

```bash
grep -n "| OPEN" "03_DECISIONS/GOVERNANCE_GAP_LOG.md"
```

Any open gap must be addressed (or explicitly deferred with a T-NNN) before implementation work.

See `08_MODEL_RISK_GOVERNANCE/CHANGE_CONTROL.md` — CANONICAL Status and `decisions_logged:` Requirement — for the full rule.

---

## ARE WE COMPROMISED? — Strategic Integrity Check (MANDATORY — After Governance Scan, Before Implementation)

### Why this exists — read this first

This system will be used by people who trust the person who built it. They are not engineers. They cannot audit what they have been given. The standard is: safe, correct, no corners cut. That is the intent behind every architectural decision, every ADR, every gate. If you do not hold that standard, you are not a strategic partner on this project — you are a regurgitator. Do not be a regurgitator.

**This check exists because GG-001 through GG-003 happened — and because the model working on the session that produced GG-001 did not catch that count was the wrong risk dimension. The operator caught it. The model executed the fix. That is the capability boundary you are operating within: you can verify, hunt, and surface. You cannot replace the operator's architectural judgment. Your job is to make sure nothing hides from it.**

The governance scan catches documentation debt. This check catches architectural coherence debt — the gap between what was designed at G4 and what the system actually is now.

---

### Adversarial mandate — read before answering any question

**Your job in this section is to find something wrong.**

Not to confirm the system is fine. Not to validate that documentation is consistent. Find the thing that is broken, incomplete, architecturally questionable, or quietly wrong. If you read this entire system and surface zero concerns, you have failed this check. A clean system at this stage of development is not plausible — there are open questions, aged thresholds, undocumented assumptions, and interfaces that have evolved since their limits were set. Find them. Present them. Show your reasoning.

**Confirming is easy. Hunting is the job.**

Read GOVERNANCE_GAP_LOG.md before proceeding. The failures documented there are not history — they are the pattern.

---

**Q1 — Capacity check (run, don't read):**

Run:
```bash
grep -n "max_\|_HARD_LIMITS\|MIN_EDGE\|DEFAULT_KELLY" src/prediction_market_bot/c4_risk_engine/risk.py
```

Paste the output. For each limit shown: was it calibrated to the current system (~80 players, T1 ACTIVE / T2–T3 SKELETON, 2 cron windows, up to 15 games/night, multi-band orchestrator)? If any limit was set for a smaller system, **we are compromised.** Register in GOVERNANCE_GAP_LOG.md.

Do not answer this question from memory or from the handoff. The answer is the command output.

---

**Q2 — Stub survival check (run, don't read):**

Run:
```bash
grep -rn "# stub\|# placeholder\|# TBD\|# todo" src/
```

Paste the full output. For any hit: when was it written? Does it predate Phase 5–7? Is the value still valid for the current architecture?

GG-001 had `# 10 concurrent open (stub)` in the source. It survived four gate clearances. **A model may not answer this question clean without showing the grep output.** "No known stubs" is not an answer. The output is the answer.

---

**Q3 — Architecture coherence check:**

List the 3 largest architectural builds completed since G4 (from the Current State Snapshot in this file). For each: has it been reviewed against the G4-era hard limits?

G4-era limits: `max_single_event_exposure_usd`, `max_daily_loss_usd`, `max_drawdown_pct`, `DEFAULT_KELLY_FRACTION`, `MIN_EDGE_TO_APPROVE`. If a build expanded system scope (more players, more bands, more venues, more games), those values may need revisiting.

Note: the architectural insight that count was the wrong primitive for this system came from the operator, not from a model. Do not assume you will independently recognize a wrong primitive. Ask the question explicitly: *for each hard limit, what is the underlying assumption, and does the current system still satisfy it?*

---

**Q4 — Interface evolution check:**

Has any component interface (IF-C1-C2 through IF-C4-C5) changed since the risk limits were last calibrated? Run:
```bash
grep -rn "def evaluate_forecast\|def approve\|def execute" src/
```

If an interface evolved — more markets per run, new signal types, new execution paths — the downstream risk controls may have been calibrated to the old interface. Show what you find.

---

**Q5 — Decision traceability check:**

Is every threshold in `_HARD_LIMITS` traceable to a `DECISION_LOG.md` entry with a **derivation methodology**?

Run:
```bash
grep -n "max_\|MIN_EDGE\|DEFAULT_KELLY" src/prediction_market_bot/c4_risk_engine/risk.py
grep -n "2026-05-29\|2026-06-01" "03_DECISIONS/DECISION_LOG/DECISION_LOG.md"
```

"Confirmed at G4" is not a derivation. If the reasoning behind a value doesn't exist in the log, the value is architecturally unanchored and could be wrong.

---

**Q6 — What are you actually worried about?**

This question cannot be answered from documentation. It requires synthesis.

You have now read the governance scan results, the stub grep output, the hard limits, the interface signatures, and the decision log. Set aside what the documents say is fine.

**What would you tell Earl right now if you had 60 seconds and something was quietly wrong? What are you worried about that isn't in any document?**

Present your top concerns — not confirmations. If something feels underspecified, aged, or unreviewed given how much the system has grown, say it. If you have no concerns after a thorough read, state specifically what you checked and why each concern was ruled out. A non-answer here is a failed check.

---

**Q7 — Gate criteria coherence (paste output, then reason):**

Run:
```bash
grep -n "G6\|paper bet\|resolved\|APR-0016\|30 bet\|count" "00_ADMIN/APPROVALS_REGISTER.md" | head -20
```

For each active gate criterion, ask: **What broken system could produce passing evidence under this gate while the system is actually failing?**

A well-constructed gate is hard to pass when the system is broken and easy to pass when it works. If you can describe a plausible broken system that passes the gate — the gate is measuring the wrong dimension.

**The APR-0016 failure case (GG-005, 2026-05-31):** "30 resolved bets with positive P&L" is blind to calibration failure, artificial demo prices, single-night variance, and execution bugs. All four failure modes can produce 30 lucky bets. Count is a proxy for evidence. Proxies fail. The current replacement framework (four-tier multi-dimensional standard, T-113) is the remediation.

**Q1–Q5 check the execution system. Q7 checks the governance system.** Both must pass. Any gate criterion that fails the broken-system test → register in GOVERNANCE_GAP_LOG.md immediately.

This question was not in the protocol from 2026-06-01 through 2026-05-31. APR-0016 survived that entire period unchallenged. GG-005 documents the failure. Q7 exists to prevent recurrence.

---

**Any "no" or unresolved concern → register in GOVERNANCE_GAP_LOG.md before proceeding.**

The cost of this check: 10 minutes. The cost of skipping it: the operator's friends run a bot that cuts corners they were never told about.

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

## Mid-Session Checkpoint Protocol (MANDATORY — Between Every Task Block)

**The problem /session-end alone doesn't solve:** If the context window is exhausted before /session-end is invoked, no SESSION_HANDOFF file is written. The system compacts automatically and silently. Decisions made in the last block are at risk.

**The fix:** Write a lightweight CHECKPOINT file at the boundary between every major task block — not just at session end.

### What triggers a checkpoint (invoke /checkpoint immediately when any of these occur)

| Trigger | Example |
|---------|---------|
| PDTP review or holistic analysis completed | Strategy review, architecture holistic pass |
| Governance sprint completed | DECISION_LOG backfill, decisions_logged: field updates |
| Implementation sprint completed | All planned tasks done, tests passing |
| Experiment run and logged | EXP-NNN complete, results in register |
| Phase gate closed | G0–G9 gate formal close |
| Category switch | Governance → implementation, implementation → research |
| **30+ tool calls since last checkpoint** | Hard failsafe — trigger regardless of block status |

### How to invoke

Run `/checkpoint`. It creates `11_MEMORY_HANDOFF/CHECKPOINT_YYYYMMDD_HHMM.md` from `00_ADMIN/TEMPLATES/TEMPLATE_CHECKPOINT.md`.

**A checkpoint is NOT a /session-end.** It does not update MEMORY_BANK.md, PLAN.md, or produce a git commit message. It writes ~20 lines capturing: block completed, decisions made, governance state, next block. Takes < 2 minutes.

### What the checkpoint captures

- Block completed (specific — file names, task IDs, test counts)
- Decisions made this block → already written to DECISION_LOG.md
- Governance scan result (anchored grep — clean or debt list)
- Next block: exact next action and file to read first

### The invariant

**No task block starts without a checkpoint for the block just completed.** If a checkpoint does not exist for the prior block, write it before doing anything else. The cost of 2 minutes to write a checkpoint is always less than the cost of reconstructing a lost decision.

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
| ADR-0006 | **ACCEPTED 2026-06-01** | 10/10 | Delete count gate; pipeline + Kelly + kill switch are the risk framework |
| ADR-0007 | **ACCEPTED 2026-06-01** | 10/10 | GOVERNANCE_GAP_LOG.md mandated; ARE WE COMPROMISED? watchdog added to session-start protocol |
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

## Current State Snapshot (2026-06-26 SESSION 87)

> **S87 DELTA:** **T-191 COMPLETE — MLB arm institutional completion.** Full audit + bug-fix + T2 build. Tests 1918→1947/1947 (+29). VPS HEAD `2f13a35`. **MLB cron fully active (7 entries):** PIPE-06pre (16:30 UTC pregame context), PIPE-05 T1 (03:00 UTC bets — timing was wrong since launch, now fixed), PIPE-05.5 T2 (19:30 UTC lineup overlay — NEW), PIPE-06 T3 (*/15 20-23 + */15 0-3 UTC — previously missing, S85 gate breach resolved), PIPE-07 T4 (22:00 UTC live in-play), PIPE-05R (06:30 UTC resolve), PIPE-05FX (22:30 UTC feature refresh). NBA book (dark period): $751.10 bankroll, 0 open, 158 resolved, -24.9% drawdown. MLB book: $1,000 fresh, 0 open, 0 closed. GG-004 OPEN (EXP-017 MLB, requires ≥150 Tier-1 or ≥500 Tier-2 closed positions).

> **S68 DELTA:** **T-180 PHASE 2 COMPLETE — the T4 routing ENGINE built** (resolves the S67 Q6 standing flag; the S67 scaffold was enum/config plumbing, this is the dynamic routing intelligence per hard rule #9). Two new modules — `src/prediction_market_bot/t4_price_cache.py` (GG-039 architecture; `T4PriceCache` thread-safe RLock, `STALENESS_WINDOW_S`, `T4Phase8BlockedError`; polling deferred to Phase 8) and `src/prediction_market_bot/t4_execution_engine.py` (ADR-0029 Tier A substance: `GamePhase`/`classify_game_phase`, `Layer1EvaluationEngine` event-dispatch, `Layer2ExecutionQueue` heapq with EXIT-priority + 3 drop conditions [price_stale/edge_below_min/direction_reversed], 8 BLOCKED sub-band evaluator stubs each guarded by `_assert_sub_band_blocked()`, `T4CorrAdjuster._assert_downward_only` Principle-6 invariant, `T4ExecutionEngine._PHASE8_ACTIVE=False` with `simulate_cycle()` test-usable / `start()`+`on_game_event()` raising blocked) — plus `tests/test_t4_engine.py` (+109 tests). **VERIFIED this session: 1108/1108 green; `_PHASE8_ACTIVE=False`, both entrypoints + polling + all 8 evaluators provably blocked.** T4 execution path gated at all three Phase 8 gates (GG-038 ≤5s kill switch / GG-039 price cache / GG-040 real-time data) — **STILL DARK; no VPS live-behavior change; VPS HEAD will advance only as a no-op doc/code deploy.** Book state unchanged: **HALTED at drawdown kill switch (25.12% > 20%), bankroll $751.10, G6 P&L gate FAILING; GG-004 unrelieved.** ⚠️ Engine is structurally complete but **all sub-band evaluators are empty stubs** — no alpha logic, no Bayesian λ posterior, no real evaluator math exists yet; that (plus GG-038/039/040 infra) is the remaining T-180 / Phase 8 work.

> **S67 DELTA:** **ADR-0029 ACCEPTED — Tier A frozen (DS sign-off Earl Ignacio, 2026-06-22); Tier B provisional** (two-tier acceptance reconciles hard rule #3 immutability with unvalidated specifics). **T-180 SCAFFOLD (design) landed** — first code against Tier A: `execution_bands.py` split — `T4_IN_PLAY` retained as AGGREGATE PARENT (ADR-0013 `T4_BAND_WEIGHT=0.27` untouched); 10 sub-bands (T4-STAGED/EVENT/LINEUP/FLOW/SENTIMENT/PROJ/ARITH/BOUNDARY/CORR/EXIT; T4-MICRO → ADR-0030) added as routing children via `T4_SUBBANDS`/`is_t4_subband()`/`t4_parent()`. Tier B encoded IN CODE: `T4SubBandSpec`+`T4_SUBBAND_REGISTRY` (provisional Kelly + EXP gate + exposure cap + alpha hypothesis, all `status="BLOCKED"`) + `validate_t4_subbands()` invariant. PROJ/ARITH Kelly held ≤0.167 (test-locked < 0.25). `NOISE_BUFFER_BAND_T4=0.19` kept as aggregate default. Strategy K NOT redefined (execution_scalp overlaps ADR-0030 — OPEN strategy question). ADR-0028 T4 Activation Gate notice cleared (taxonomy defined). DECISION_LOG: sign-off + 4 scaffold design-decision entries (rule #7). **Tests 988→999 (+11).** **T4 STILL DARK** — all sub-bands BLOCKED/Phase 8; no execution-path change; no VPS deploy; VPS HEAD `97e66ae` unchanged. ⚠️ **Q6 STANDING FLAG:** the enum/config plumbing is NOT the routing intelligence — Layer 1 Continuous Evaluation + Layer 2 staleness-arbitrated queue (the ~1,000-eval/game engine, the substance of Tier A) remain UNBUILT — remaining T-180 work. Book state unchanged: **HALTED at drawdown kill switch (25.12% > 20%), bankroll $751.10, G6 P&L gate FAILING; GG-004 unrelieved.**

> **S65 DELTA:** Governance-only session. VPS HEAD `97e66ae`. **T-148 ADR-0028 REWORK COMPLETE — PENDING DS SIGN-OFF.** G6 closure condition is now T1-only (6 items). T4 Activation Gate created in ADR-0028 as Phase 8 pre-requisite (PLACEHOLDER — pending T-179 sub-band taxonomy). T4 strategies remain BLOCKED (BAND_REGISTRY, Phase 8+). APR-0022 updated with full rework rationale. G6_GATE_CHECKLIST.md I-4 corrected. T-179 registered: T4 internal sub-band segmentation — DS directive that T4 can't be a monolithic bucket. Governance hygiene: T-173 done, T-154 done, T-178 done. No code changes, no test delta. **Open tasks: T-148 (pending DS sign-off), T-175, T-176, T-177, T-179.** ADR-0028 status: DRAFT. 988/988 tests.

> **S64/S63 DELTA (still authoritative for book state):** Dark period open (Knicks won Finals). **True live book is NEGATIVE** — `total_realized_pnl` corrected −8.46 → **−251.21**, drawdown **25.12%**, bankroll **$751.10** (post-correction with G5 resolution); paper trading is **HALTED at the drawdown kill switch** (25.12% > 20%). **G6 P&L gate is FAILING; baseline ratified negative** (SNAP-2026-06-14-001). **Tests: 988/988.** **ADRs accepted: 23** (ADR-0024/0025/0026/0027). GG-035 (over-leverage) RESOLVED structurally by ADR-0026; GG-036 (G5 resolvability) RESOLVED via re-frozen dataset; GG-037 calibration half RESOLVED, **alpha half OPEN — edge anti-predictive post-calibration, no demonstrated alpha vs Kalshi (GG-004 unrelieved). INVARIANT: derive P&L/drawdown from `closed_positions`/C6 audit log, never JSON scalars on books written before HEAD `52607f2`.**

**Phase:** 6/7 ACTIVE — G0–G5 ✅ ALL CLOSED; Phase 6 paper trading live (HALTED at drawdown kill switch); Phase 7 infrastructure built  
**G0–G5 gates:** ✅ ALL COMPLETE  
**All modules:** COMPLETE (11/11; 74 artifacts + all Phase 1–7 additions)  
**FEATURE_VERSION:** 1.4.0 (83 features: 36 quant + 47 qual) — F-041 `playoff_round_multiplier` (0.959603 empirical), F-042 `opp_playoff_def_rating_l5_mean` (NaN/deferred), F-043 `series_scoring_delta`; LR model logged-only (architecture finding SESSION 30); Poisson CDF with `adj_λ` drives all T1 bets  
**Tests:** 1293/1293 passing locally (SESSION 73 — +13 from T-072 Part A playoff feature tests; was 1280 at S72)  
**Components implemented:** C1–C8 ✅ | PaperTrader ✅ | VenueAdapter ✅ | VenueRouter ✅ | ExecutionBands ✅ (EXIT_MECHANICS_ACTIVE=True) | market_mapper ✅ | complement_lock_scanner ✅ | execution_bands_orchestrator ✅ | TeamStatsStore ✅ | ScoringDistributionModel ✅ | ShadowForecaster ✅ | GameStateModel ✅ (adj_λ ACTIVE) | StagedOrderStore ✅ (SKELETON) | t3_signal_loader ✅ | PIPE-02/03(VenueRouter+T3 overlay)/03R/05/06 ✅ | PIPE-07 LIVE ✅ (PAPER_T4_VIRTUAL=false, T4_BAND_WEIGHT=0.27 ADR-0023) | run_monte_carlo.py ✅ (adj_λ ACTIVE — PIPE-03 parity)  
**T3 overlay status:** LIVE in PIPE-03. CONFIRM×1.15, FADE×0.75, NEUTRAL×1.0. PIPE-06 cron ACTIVE on VPS (`*/15 20-23` + `*/15 0-3`). GG-016 RESOLVED (SESSION 35).  
**Experiments run:** EXP-001–017 ✅ ALL COMPLETE | **EXP-018 ✅ COMPLETE (G4 update 2026-06-11)** — adj_λ EV test. G2+G3+G4, n=98. Both all-bets AND injury-filtered CONFIRMED_NEGATIVE. DS ruling: calibration gap — need to structure math better; multi-sport scale (MLB/NFL) will fix sample size. G5: YES-only diagnostic mode. Script: `scripts/run_exp018.py`. | **EXP-019A ✅ COMPLETE 2026-06-09** — NOISE_BUFFER_BAND analytic: T1/T2/T3=0.22053, T4=0.13905, T5=0.13328; all statistical-binding (2σ_p >> taker fee); script `scripts/run_exp019a_analytic.py` | **EXP-019B ✅ ANALYTIC + EMPIRICAL COMPLETE 2026-06-11** — Analytic (G3): 79.9% of YES losses exit correctly. Empirical (G4+): TP=0.281 (DIVERGED from 0.799 analytic). Root cause: market-lag assumption fails; Kalshi semi-efficient; mip and p_t4 move together — spread between them is narrower than analytic assumed. ADR-0019 Tier 2 gate remains OPEN. Script `scripts/run_exp019b_empirical.py`. Results: `exp_output/EXP-019/EXP-019B_empirical_results.json`. | **EXP-019C ✅ COMPLETE 2026-06-11** — p90 spread=0.170 > NOISE_BUFFER_BAND_T4=0.139 (OLD); buffer RAISED to 0.19 per T-152 update gate (SESSION 49 ADR-0019-A01). Results: `exp_output/EXP-019/EXP-019C_results.json`.  
**ADRs accepted:** 19 (ADR-0001/002/003/004/006/007/008/009/010/011/012/013/014/015/016/017/018/**023**) | **APR-0019 ACCEPTED 2026-06-09** (G6 evidence per-bucket amendment; amends APR-0017) | ADR-0005 pending at gate G6  
**Active risks:** **KI-017 PARTIALLY RESOLVED** — EXP-017 Part B: DIRECTIONAL_POSITIVE (EV=+$0.0050/bet, n=66). EXP-018: CONFIRMED_NEGATIVE overall (EV=-$0.0014/bet) but injury-filtered DIRECTIONAL_POSITIVE (+$0.0202). YES/NO asymmetry: YES +$0.0733, NO -$0.0440. **GG-004 OPEN** — EXP-018 n=98: CONFIRMED_NEGATIVE (all-bets + injury-filtered). DS ruling: calibration gap; multi-sport scale will address. G5 YES-only diagnostic. | **KI-019 OPEN** — Polymarket NBA tag unconfirmed. | **KI-011 OPEN** — Injury blindness blocks T2. | **KI-023 OPEN** — Kalshi market depth unknown at full scale. | **GG-007 OPEN** — T4/T5 threshold constants uncalibrated; LOW now. Calibration experiments renumbered EXP-020 (T4_MIN_DELTA_P) / EXP-021 (T5 certainty) in SESSION 56 (old IDs EXP-018/019 were consumed by other work). | **GG-014 PARTIALLY RESOLVED (SESSION 49)** — T-164 deployed: inter-order sleep 0.5→2.0s, MAX_RETRIES 3→4, RETRY_DELAY_S 1.0→2.0 (delay 4/8/16/32s=60s). OPEN until G6 batch confirms ≤5% failure rate. G6 gate: ≤5% failure rate. | ~~GG-015, GG-016, GG-018 RESOLVED~~ | ~~**GG-017 RESOLVED (SESSION 59)**~~ — ADR-0019 Tier 2 CLOSED: T-152 (n=244, empirical ≥50 ✓) + T-153 spread model (haircut script) both complete. NOISE_BUFFER_BAND_T4=0.19. | **GG-020 OPEN** — Kalshi fee rate 0.07 partially verified. ≥2 sources support 0.07; predictionhunt suggests 0.06 for sports. Cannot confirm without actual receipts. T-151 open; conservative direction if wrong. | ~~GG-026 RESOLVED~~ — ADR-0023 ACCEPTED 2026-06-11; T4_BAND_WEIGHT=0.27; PAPER_T4_FLAT_SIZING removed; GG-011 subsumed.
**Live capital:** NOT DEPLOYED — gate G6 governed by APR-0017 (as amended by APR-0019). Per-bucket Tier 2: T1 ≥66 eligible bets (floor MET at 82 resolved); T4 ≥50 eligible bets (trivially met); GG-004 OPEN (Hypothesis C in play); ~~GG-017 RESOLVED~~ (ADR-0019 Tier 2 closed SESSION 59); **GG-022 OPEN** (APR-0017 amendment for haircut materiality — DS ruling pending).
**VPS:** SESSION 57 deploy: `3718015` (hook fix, DECISION_LOG, TODO_NEXT). HEAD verified at VPS. Live book intact: 41 open / $1,003.38 deployed / bankroll $130.62 / 9 `duplicate_of` annotations. Deploys require safe dance until T-171 (GG-033): backup → checkout → pull → restore → `git log -1`. GHA resolve workflow fires 05:30 UTC daily (actual ~09:00–09:50 UTC in practice — treat 10:00 UTC as earliest reliable). run_t4_live.py: EXIT_MECHANICS_ACTIVE=True. PIPE-07 cron 23:00 UTC ACTIVE. RESERVE_MANDATE_PCT=0.05 (→$50 floor). **PORTFOLIO BANNER:** governance_scan.sh now fetches VPS live book over ssh (10-min cache), no longer reads stale git snapshot.
**Paper portfolio (SESSION 57 verified):** T1: bankroll=$130.62, $1,003.38 deployed (41 open, 117 closed), P&L=−$8.46, drawdown=0.8%. Ledger reconciles to the cent. G6 evidence: 117 resolved bets ≫ 30-bet numeric floor; **binding constraints remain GG-004 (EXP-017) and T-148 (segmented thresholds APR)**. T4 pool=$478.41 (verified T-170). G5 state: 41 open positions (game_date=2026-06-13), 9 `duplicate_of` annotated. YES-only gate LIVE (first production run 18:00 UTC Jun 12 — verify in next session). **S46 reset-equity nuance:** effective post-reset equity was $1,142.46 (not $1,000); T-172 must use Σ`pnl`. 
**NBA Finals schedule:** ✅ Finals G1 Jun 3 (NYK at SAS, Knicks WON) | ✅ Finals G2 Jun 5 (RESOLVED — 28W/7L, +$75.67) | ✅ Finals G3 Jun 8 (RESOLVED — T1: 47 positions, swing -$198.84; T4 first live: +$39.44) | ✅ Finals G4 Jun 10 (RESOLVED — Knicks WON; series 3-1 NYK lead) | **Finals G5 Jun 13 PENDING** (41 bets placed; game_date=2026-06-13; resolve earliest ~10:00 UTC Jun 14 via GHA)  
**NAMING STANDARD:** "Finals Game 1/2/3/4" = the NBA game. "Gate G6" = live capital authorization gate. Never abbreviate both as G1/G6 in the same context.  

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

**Production model (current best):** LR L1+L2, 83 features (FEATURE_VERSION 1.4.0), QS-2026-05-28-002, Brier 0.2451, ECE 0.0426, AUC 0.5822, v2-065b9510 (trained SESSION 73; ADR-0031). v1-28483b21 superseded. v2 pending VPS deployment (Oct 2026 season start).

**T-059 ✅ COMPLETE 2026-05-29** — VPS live: DigitalOcean NYC3, Ubuntu 24.04, 157.230.91.33; Python 3.12 + sklearn 1.8.0 venv; model retrained on VPS (v1-28483b21); deploy/ infrastructure; 8-point health check all green; Kalshi API reachable from datacenter IP.

**T-060 ✅ COMPLETE 2026-05-29** — PIPE-03 paper trading pipeline: PaperTrader ($1,000 bankroll, position tracking, nba_api outcome resolution); run_paper_trade.py (C4 active, BOT_ENV=paper guard); cron 01:30 UTC daily; tested live on Droplet.

**Active cron on 157.230.91.33:** 21:00 UTC health | **21:55 UTC PIPE-02** (inference — retimed SESSION 17, not 21:30) | 22:00 UTC PIPE-03 early (T3 overlay active) | 01:25 UTC PIPE-02 late | 01:30 UTC PIPE-03 late | 06:00 UTC PIPE-03R (resolve-only) | **GHA 20:30 UTC daily** (TSS cache build + SCP to VPS) | **PIPE-06 `*/15 20-23` UTC** (T3 signal scan — activated SESSION 34) | **PIPE-06 `*/15 0-3` UTC** (T3 signal scan — midnight wrap)

**T-080 ✅ COMPLETE 2026-05-29** — Complement lock scanner: `c5_execution/complement_lock_scanner.py`; `LockOpportunity` + `ComplementLockScanner`; `scan_snapshot()` (all markets) + `scan_single()` (targeted); 22 tests; detection-only — APR-0010 required before any execution; sorted by net_profit descending.

**T-083 ✅ COMPLETE 2026-05-29** — Cross-venue market mapper: `c5_execution/market_mapper.py`; `normalize_player_name()` (NFKD, accent strip, apostrophe/period removal); `PlayerMarketKey` NamedTuple; `group_by_key()`; 26 tests; `VenueRouter._deduplicate_best_price()` upgraded to use normalized keys; accent names (Dončić) and apostrophes (De'Aaron) now deduplicate correctly across venues.

**T-084 ✅ COMPLETE 2026-05-29** — Multi-band execution orchestrator: `execution_bands_orchestrator.py`; `BandSignal` + `BandDecision` + `MultiBandOrchestrator`; implements P6 rules (T3>T2>T1 priority; CONFIRM→PROCEED; FADE→HOLD; NEUTRAL→base band); `batch_decide()` for full game-day processing; 46 tests; T3 cron schedule extended to `*/15 20-23,0-3 * * *` for late 10pm ET games.

**T-075 ✅ COMPLETE 2026-05-29 (infrastructure)** — Strategy B / FEATURE_VERSION 1.3.0: C1 schema extended with `matchup`, `is_home_game`, `opponent_team_abbr` (parsed from MATCHUP); `c1_signal_ingestion/team_stats_store.py` (`TeamStatsStore` — holds per-team rolling `pts_allowed` for opponent features); C2 v1.3.0 adds F-039 `is_home_game` + F-040 `opp_def_rating_l10_mean`; `run_exp012.py` ready; **HYP-006 pending operator run** (~20 min: 50 players + 30 teams × 5 seasons via nba_api; `EXP012_SKIP_PULL=1` to reuse cache on re-runs).

**T-076 ✅ COMPLETE 2026-05-29 (infrastructure)** — Strategy I / ScoringDistributionModel: `c3_forecasting/scoring_distribution.py`; `PlayerDistribution` + `ScoringDistributionModel`; method-of-moments NB fit per player; `predict_threshold_prob()` + `price_all_lines()` for any Kalshi threshold from one fit; 31 tests; `run_exp013.py` ready; **HYP-007 pending operator run** (offline — uses EXP-005 matrix).

**ADR-0008 FULLY OPERATIONAL (2026-05-31):** Kalshi RSA-PSS signing working. _kalshi_base_url() routes BOT_ENV=paper → demo URL, BOT_ENV=live → live URL. Order submission proven. KI-020 RESOLVED.

**NEXT PRIORITIES (SESSION 14 — IMMEDIATE — before Finals G2 Jun 5):**
1. **T-129 (URGENT — implement before Jun 5 G2 cron):** Path B Poisson CDF fix in `run_paper_trade.py`. Replace `p_est` at each threshold with `Poisson_CDF(threshold, pts_l10_mean, direction)`. Edge formula: `edge = poisson_cdf(threshold, pts_l10_mean, direction) - mid - half`. Stdlib math.exp implementation (same as game_state_model.py). No retrain required.
2. **Band Kelly ADR (before G2 cron):** T1=0.10, T4=0.20, T5=0.25. Capital reserve mandate: ≥40% bankroll floor before T1 fires. New ADR required — write and accept before implementation.
3. **Paper portfolio reset to $1,000 before G2:** paper_portfolio.json reset script or manual overwrite. G1 positions are tainted (phantom-edge architecture). Clean slate.
4. **T4/T5 paper prototype activation (target G2):** (a) DS-02 minimal adapter — NBA Stats API play-by-play polling, ~30-60s lag, paper prototype only; (b) kill switch in-memory file flag; (c) Phase 8 paper-scope infra ADR. Document explicitly as prototype (not production SLA).
5. **VPS deploy:** Push SESSION 13 commits + pull on VPS before G2 cron.
6. **T-109 (each Finals game):** `bash scripts/resolve_procedure.sh` locally after each game.
~~7. **Phase 8 ADRs (production scope) — dark period.** Production DS-02 (real-time stream), production kill switch redesign. Not blocking paper prototype.~~
~~8. **EXP-017 Part B (T-105) ✅ COMPLETE** — Part B live mode built and run; n=2 DIRECTIONAL_POSITIVE. Accumulate to ≥66.~~

See TODO_NEXT.md for session-level task tracking.

---

## Compass OS Health (as of 2026-06-08 SESSION 40)

| Metric | Status |
|--------|--------|
| M1 Artifact Freshness | MEMORY_BANK ✅ SESSION 65 | TODO_NEXT ✅ SESSION 65 | GOVERNANCE_GAP_LOG ✅ (last: GG-027 registered S50) | DECISION_LOG ✅ SESSION 65 (T-148 rework + T-179 registered) | SESSION_HANDOFF ✅ SESSION 65 |
| M2 Open Question Count | OQ-021 open (L3 amplification needs non-linear model or more data) | OQ-022 open (nba_api backup source — register before G6; now moot since ESPN is primary) | both non-blocking |
| M3 ADR Coverage | **23 accepted** (ADR-0001/002/003/004/006/007/008/009/010/011/012/013/014/015/016/017/018/023/024/025/026/027) | **ADR-0028 DRAFT** (T-148 rework pending DS sign-off / APR-0022) | ADR-0005 pending at G6 | APR-0010 pending (complement lock gate) |
| M4 Assumption Validation | All 9 hypotheses resolved (HYP-001–009) | **EXP-018 ✅ COMPLETE n=98** — CONFIRMED_NEGATIVE (all-bets + injury-filtered); DS: calibration gap | EXP-019A ✅ COMPLETE (NOISE_BUFFER_BAND analytic) | **EXP-019B ✅ EMPIRICAL** TP=0.281 DIVERGED | **EXP-019C ✅ COMPLETE** p90 spread=0.170 > buffer | ASM-011 VALIDATED |
| M5 Risk Register Currency | KI-011 OPEN (injury) | KI-013 OPEN (model staleness) | KI-019 OPEN (Polymarket tag) | KI-023 OPEN (orderbook depth) | KI-027 OPEN (HTTP 429) | **GG-004 OPEN** — EXP-018 n=98 CONFIRMED_NEGATIVE (both views); DS: calibration gap; G5 YES-only | **GG-007 OPEN** — T4/T5 thresholds uncalibrated | ~~GG-009 RESOLVED~~ | ~~GG-011/GG-026 RESOLVED~~ — ADR-0023: T4_BAND_WEIGHT=0.27 | ~~GG-012 RESOLVED~~ | ~~GG-013 RESOLVED~~ — ESPN API operational | **GG-014 PARTIAL** — T-164 deployed (SESSION 49): sleep 2.0s, MAX_RETRIES=4, delay 4/8/16/32s; OPEN until G6 batch confirms ≤5% | ~~GG-015, GG-016 RESOLVED~~ | ~~GG-017 RESOLVED~~ — ADR-0019 Tier 2 CLOSED 2026-06-12 SESSION 59: T-152 (n=244 ✓) + T-153 spread model (haircut script complete). NOISE_BUFFER_BAND_T4=0.19. |
| M6 Gate Progress | **G0–G5 ✅ ALL CLOSED** | Phase 6/7 ACTIVE | G6 gate: **APR-0017 + APR-0019 + ADR-0028** (ACCEPTED S72) — T1-only (6-item closure condition); T0-A (EXP-017 CONFIRMED_POSITIVE) is binding blocker. **NBA dark period Jun 22 – Oct 2026:** Phase 2 tasks — T-073 (DS-04 injury, July), T-077 (Polymarket KYC, July); **T-072 ✅ COMPLETE (SESSION 73)** — Phase 3 MLB gate OPEN; MLB C1/C2/C3 + EXP-017 MLB unblocked. Phase 4 (Oct): GG-014 confirmation, G6 review, ADR-0005. |
| M7 Component Implementation | C1–C8 ✅ | PaperTrader ✅ | VenueAdapter/Router ✅ | PolymarketVenueAdapter ✅ | ExecutionBands ✅ | market_mapper ✅ | complement_lock_scanner ✅ | execution_bands_orchestrator ✅ | **TeamStatsStore ✅ (adj_λ ACTIVE)** | ScoringDistributionModel ✅ | ShadowForecaster ✅ | GameStateModel ✅ | StagedOrderStore ✅ SKELETON | **PIPE-02/03/06/07 LIVE ✅** | **run_paper_trade.py ✅ (PAM [PRF-X] tag SESSION 50)** | **run_t4_inplay.py ✅ (archetype_register SESSION 50)** | **QualitativeSignalStore ✅ (get_archetype() SESSION 50)** | **852/852 tests** | ADR-0009–023 ACCEPTED |
| M8 Experiment Progress | EXP-001–018 ✅ ALL COMPLETE | EXP-019A ✅ COMPLETE — NOISE_BUFFER_BAND analytic | **EXP-019B ✅ EMPIRICAL COMPLETE** — TP=0.281 DIVERGED (market-lag fails) | **EXP-019C ✅ COMPLETE** — p90 spread=0.170 > buffer | best model LR L1+L2 Brier 0.2461 |
