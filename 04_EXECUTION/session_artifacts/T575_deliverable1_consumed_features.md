# Deliverable 1 — Consumed-Feature Inventory (per live model, from code)

Worktree: `PM-worktrees/20260925T015621Z-feature-space-audit`. Read-only audit; no files modified.

---

## 1. T4M-PROJ (MLB) — LIVE, only band currently trading real paper capital

**File:** `src/prediction_market_bot/run_t4_mlb_live.py`
**Core function:** `p_hits_gte_threshold()` (lines 687–711), calling `_binomial_pmf()` (675–684). Call site inside `_run_cycle()` (~1050–1160).

| Input | Type | Source | Point-in-time / rolling |
|---|---|---|---|
| `h_so_far` | int | ESPN live boxscore parse (in-file, ~643–656) | Point-in-time |
| `threshold` | int | Market-cell config (fixed per ticker) | Fixed |
| `ba_l10_shrunk` | float | `c2_feature_store/mlb_features.py` (rolling L10 batting avg, then empirical-Bayes shrunk toward league prior — ADR-0047, K=40, PRIOR=0.2512) | Rolling (shrunk) |
| `ab_remaining` | int | **Derived**, not raw — `_compute_ab_remaining(ab_so_far, inning, batting_slot)` (lines 361–391) | Derived |
| `ab_so_far` | int | ESPN live boxscore parse | Point-in-time |
| `inning` | int | ESPN live game state | Point-in-time |
| `batting_slot` | int | **Cross-band dependency**: `_load_t2_batting_slots()` (line 455) reads a file produced by T2 MLB, not computed within T4 | Point-in-time (same-day lineup) |

**Distinct upstream inputs: 6** (h_so_far, threshold, ba_l10_shrunk, ab_so_far, inning, batting_slot — ab_remaining is a derived intermediate, not an independent input).

**Model class:** Closed-form Binomial survival function (not fitted/trained) — `P(hits ≥ threshold | ba_l10_shrunk)`. **Correction to directive framing:** the live parameter is `ba_l10_shrunk`, not raw `ba_l10` — confirmed at the actual call site.

---

## 2. T1 MLB pregame player-hits model — LIVE (KXMLBHIT sameday, PIPE-05)

**Files:** `src/prediction_market_bot/run_mlb_pregame.py` (inference) + `scripts/train_mlb_model.py` (training/freeze) + `src/prediction_market_bot/c2_feature_store/mlb_features.py` (feature computation).

**Important structural finding:** the exact frozen feature list is **not declared in any Python source**. It is loaded at runtime from `models/mlb_v1_model.joblib` (`run_mlb_pregame.py:269`, `artifact["feature_names"]`). That artifact is git-ignored (`models/`, `*.joblib` in `.gitignore`) and does not exist in this worktree — it is a training-time build product. Ground truth was reconstructed from the training script instead of the artifact itself:

`train_mlb_model.py:_extract_feature_matrix()` (line 193–199): `feature_names = sorted(c for c in df.columns if c not in _NON_FEATURE_MLB)`, where `df` is read from `exp_output/MLB/mlb_feature_matrix.csv` (the `MLBFeatureStore` output) and `_NON_FEATURE_MLB` (lines 100–119) excludes only identity/metadata/raw-outcome columns. So **feature set = MLBFeatureStore's output columns, minus ID/outcome columns** — this is a derivation, not a direct read of the artifact.

Per `mlb_features.py`'s v1.0.0/v1.1.0 docstring (lines 1–120), that resolves to:

| Feature | Type | Rolling/point-in-time |
|---|---|---|
| `ba_l10`, `slg_l10`, `obp_l10`, `ops_l10`, `h_l10_mean`, `k_rate_l10`, `bb_rate_l10`, `hr_rate_l10` | float | Rolling L10, min 3 prior games |
| `is_home_game`, `b2b_flag` | boolean/flag | Point-in-time (per game) |
| `days_rest` | int | Point-in-time |
| `opp_runs_allowed_l10` | float | Rolling L10 (opponent) |
| `opp_sp_era_l5`, `opp_sp_k9_l5`, `opp_sp_bb9_l5` | float | Rolling L5 (opposing starting pitcher overlay — flagged MANDATORY, "structural equivalent of T2 injury overlay") |
| `opp_sp_is_known` | boolean | Point-in-time |
| `park_factor_hits` | float | Static per-venue constant |

**Count: 17 base features.** `ba_l10_shrunk` (v1.1.0, ADR-0047) is explicitly documented as surfaced for audit only — the docstring states T1's own model is *not* repointed to it (only T4M-PROJ is), so it is excluded from this count pending direct confirmation against the actual joblib artifact.

**Caveat (stated explicitly per directive's skepticism requirement):** this list is inferred via the training script's column-selection logic, not read directly out of the deployed artifact — an artifact inspection on the VPS would be the fully rigorous confirmation.

**Model class:** Logistic Regression + Platt scaling (ADR-0004 frozen model class), per-threshold pipelines, 17 features.

---

## 3. T1 NFL moneyline (EXP-027 / HYP-012) — wired, NOT the default model

**Files:** `scripts/exp027_hyp012_nfl_moneyline_backtest.py` (fit logic, `FEATURES` at line 85), `src/prediction_market_bot/nfl_exp027_adapter.py` (adapter), `src/prediction_market_bot/run_t1_nfl_game_market.py` (run script).

| Input | Type | Source | Rolling/point-in-time |
|---|---|---|---|
| `off_epa_home`, `off_epa_away` | float | `NFLTeamStatsStore.get_off_epa()` — exponential-decay recency-weighted mean over last `DEFAULT_WINDOW` games strictly prior to game date | Rolling (decay-weighted) |
| `def_epa_allowed_home`, `def_epa_allowed_away` | float | `NFLTeamStatsStore.get_def_epa_allowed()`, same windowing | Rolling (decay-weighted) |
| `home_rest`, `away_rest` | int | Schedule-derived rest days | Point-in-time |

**Count: 6 features.** Model: `LogisticRegression(C=1.0, class_weight="balanced")` inside `CalibratedClassifierCV(sigmoid, cv=3)`, trained on 2015–2024 seasons, `random_state=42`.

**Status:** pre-registered, verdict **UNDERPOWERED** (HYP-012, pending more 2026 data). Scope: moneyline (`KXNFLGAME`) only — returns `None` (refusal) for spread/total/team_total or any unparseable ticker/missing-data row, never imputes.

**Reachability caveat:** `run_t1_nfl_game_market.py:main()` defaults to `StubNFLForecastModel()` (line 430) — the EXP-027 model is only used if explicitly injected via `main(model=EXP027NFLForecastModel(...))`. Confirm current invocation (cron entry vs. manual) before treating this as "live" in the same sense as T4M-PROJ.

---

## 4. T2 MLB same-day lineup overlay — LIVE (PIPE-05.5)

**File:** `src/prediction_market_bot/run_t2_mlb_sameday.py`, function `_slot_adjust()` (lines 133–165).

| Input | Type | Source | Rolling/point-in-time |
|---|---|---|---|
| `p_t1` | float | T1's own forecast output (upstream, already computed) | N/A (pass-through) |
| `ba_l10` | float | `mlb_features.py` rolling stat (raw, **not** shrunk) | Rolling |
| `batting_slot` | int | Same-day confirmed lineup (MLB Stats API, DS-04) | Point-in-time |
| `threshold` | int | Market-cell config (only 1 or 2 supported; other thresholds pass through unadjusted) | Fixed |

**Count: 3 real inputs** (`p_t1`, `ba_l10`, `batting_slot`) + 1 fixed selector (`threshold`). **Model class:** rule-based Binomial-ratio adjustment (`P(H≥thr|ab_adj)/P(H≥thr|ab_default)`), capped ±15%, applied multiplicatively to `p_t1` — not a fitted model.

## 4b. T2 NBA — NO MODEL (explicit skeleton stub)

**File:** `src/prediction_market_bot/run_t2_sameday.py`. Docstring self-declares `STATUS: SKELETON` — injury/lineup data source (DS-04 NBA) never provisioned; the injury overlay is a `TODO` stub that **returns T1 forecasts unchanged**. No feature consumption occurs. (NBA is also DARK/FROZEN project-wide per current operator directive — doubly inactive.)

---

## 5. T3 (MLB + NBA) — LIVE, read-only momentum signal (not a probability model)

**Files:** `run_t3_mlb_pretip.py`, `run_t3_pretip.py` (near-identical logic per sport), consumed downstream via `t3_signal_loader.py`.

| Input | Type | Source | Rolling/point-in-time |
|---|---|---|---|
| T1 snapshot price | float | T1's pregame context file (`pregame_*.json`) | Point-in-time (frozen at T1 run) |
| Current live market price | float | Kalshi fetch at scan time | Point-in-time |
| `MOMENTUM_THRESHOLD` | float | Hardcoded constant = `0.025` (both sports) | Fixed |

**Count: 2 real inputs + 1 fixed constant.** Output is categorical (`CONFIRM`/`FADE`/`NEUTRAL`), not a probability — never places orders itself; downstream consumers apply it as a confidence adjustment.

---

## 6. T4M-ARITH / T4M-FLOW (MLB) — code complete, structurally BLOCKED, not live-reachable

**File:** `src/prediction_market_bot/t4_mlb_execution_engine.py`.

**Critical finding on reachability:** `T4MlbGameContext` (the dataclass both evaluators consume) has **no construction call site anywhere in `run_t4_mlb_live.py`** (grep for `T4MlbGameContext(` returns zero hits in that file). These evaluators are real, complete, unit-testable code — but are not wired into the live per-cycle orchestrator (`_run_cycle`) at all right now. `__init__` additionally calls `_assert_sub_band_blocked()`, which raises `RuntimeError` unless the band's registry status is `"BLOCKED"` — a safety inversion (construction fails if the gate is ever accidentally lifted without an ADR), consistent with Phase 8 Activation Gate (ADR-0039).

**T4MlbArithEvaluator** (`evaluate()`, lines 161–211): reuses the same `p_hits_gte_threshold()` binomial model as T4M-PROJ, gated by an entry-window/confidence filter.
Inputs: `ctx.threshold`, `ctx.h_so_far`, `ctx.ba_l10` (field name suggests raw, not shrunk — cannot confirm live-population semantics since no construction site exists), `ctx.ab_so_far`, `ctx.inning`, `ctx.batting_slot`, `price.mid`, `price.vig`, plus fixed constants `_ARITH_ENTRY_WINDOW`, `_ARITH_CONFIDENCE_GATE`, `_MIN_EDGE`. Gated on `EXP-ARITH-MLB-01`.

**T4MlbFlowEvaluator** (`evaluate()`, lines 246–310): applies an asymmetric multiplier to `ba_l10` based on sustained blowout state, then re-runs the same binomial model.
Additional inputs beyond ARITH's: `ctx.score_diff`, `ctx.is_batting_team_leading`, `ctx.game_id`, fixed constants `_BLOWOUT_RUN_THRESHOLD`, `_BLOWOUT_SUSTAIN_INNINGS`, `_BLOWOUT_TRAILING_MULT`, `_BLOWOUT_LEADING_MULT`. The class docstring itself notes live ESPN score-diff extraction is **not wired as of T-219** — even `score_diff`/`is_batting_team_leading` have no live data source yet. Gated on `EXP-FLOW-MLB-01`.

## 6b. T4-ARITH / T4-FLOW (NBA) — code exists, entire book DARK

`src/prediction_market_bot/t4_execution_engine.py` contains a parallel, more elaborate NBA T4 sub-band system: `T4StagedEvaluator`, `T4EventEvaluator`, `T4LineupEvaluator`, `T4FlowEvaluator` (line 778, with FLOW-FOUL/FLOW-PACE/FLOW-ROTATION/FLOW-BLOWOUT trees) and a `GamePhase.NEAR_CERTAIN` concept mirroring ARITH. Not audited feature-by-feature here — out of scope while the entire NBA paper book is DARK/FROZEN (operator directive, tabled until ~1 month pre-2026-27 season); flag for re-audit on NBA reactivation.

## 6c. T4NFL-ARITH / T4NFL-FLOW, T4NHL-ARITH / T4NHL-FLOW — NO MODEL (config only)

Confirmed via repo-wide grep: these four bands exist **only** as `ExecutionBand` enum members + `BandConfig`/`T4SubBandSpec` entries in `execution_bands.py` and cell registrations in `c5_execution/market_type_registry.py`. Zero evaluator classes, zero feature logic anywhere. **NHL has no source files in this repo at all** — `find . -iname "*nhl*"` under `src/` returns nothing; there is no NHL C1 ingestion, C2 feature store, or C3 model of any kind, only the band/cell placeholders. This is the clearest "config exists, model does not" case in the codebase.

---

## Summary table

| Band | Status | Model class | Distinct real inputs |
|---|---|---|---|
| T4M-PROJ (MLB) | **LIVE** | Binomial survival (closed-form) | 6 |
| T1 MLB pregame (KXMLBHIT) | **LIVE** | LR + Platt scaling | 17 (inferred from training script; artifact not directly inspected) |
| T1 NFL moneyline (EXP-027) | Wired, not default; UNDERPOWERED | LR + CalibratedClassifierCV(sigmoid) | 6 |
| T2 MLB sameday | **LIVE** | Rule-based Binomial-ratio adjustment | 3 + 1 fixed selector |
| T2 NBA sameday | **NO MODEL** (skeleton stub, pass-through) | — | 0 |
| T3 MLB / NBA | **LIVE** (read-only signal) | Rule-based price-drift comparator | 2 + 1 fixed constant |
| T4M-ARITH (MLB) | Code complete, **BLOCKED**, not wired into any live call site | Binomial survival + entry/confidence gate | 6 real + price + 3 fixed |
| T4M-FLOW (MLB) | Code complete, **BLOCKED**, inputs partly unsourced (score_diff not wired) | Binomial survival + blowout multiplier | 9 real + price + 4 fixed |
| T4-ARITH/T4-FLOW (NBA) | Code exists, book **DARK** | Not audited (out of scope) | — |
| T4NFL/T4NHL-ARITH/FLOW | **NO MODEL** (config only) | — | 0 |
