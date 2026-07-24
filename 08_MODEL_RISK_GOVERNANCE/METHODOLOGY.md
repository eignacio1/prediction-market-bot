# Methodology — Prediction Market Trading Bot

**Purpose:** Document the forecasting methodology, decision-making framework, and key modeling choices. Ensures the approach is transparent and defensible.  
**Owner (role):** Research Lead (RL) + Methodology Validator (MV)  
**Last reviewed:** 2026-07-23 — GG-074 monthly staleness review: re-verified the 2026-07-06 correction note's claims directly against live code — `FEATURE_VERSION = "1.4.0"` (`features.py:120`) and `MIN_EDGE_TO_APPROVE = 0.04` (`risk.py:100`) both confirmed unchanged. Also resolved the one item that note left unverified: `model_version`'s `"v1-"` prefix (`forecaster.py:115-122`, `_model_version_hash()`) is still hardcoded `"v1-"`, derived from `model_class + sorted(feature_names)` hash only — it has no dependency on calibration method, so ADR-0027's temperature-scaling layer would not bump it regardless of whether calibration changed; not drift, just a prefix that was never coupled to calibration versioning in the first place. No new drift found beyond what the 2026-07-06 note already flagged.  
**Prior:** 2026-05-27 (T-038 — updated to reflect actual implemented model, v1.1.0 features, full strategy architecture)  
**Next review:** G4 (methodology confirmed by evidence); after any FEATURE_VERSION bump  
**Staleness triggers:** Model class selected; feature set changed; calibration approach changed; new strategy class activated  
**Upstream links:** RESEARCH_QUESTIONS.md, HYPOTHESES.md, ADR-0002  
**Downstream links:** EXPERIMENT_LOG/, MODEL_CARD.md  
**Decision references:** ADR-0001, ADR-0002, ADR-0003, ADR-0004 (PENDING)  
**Confidence:** 8/10 — Model class and features implemented; specifics (Kelly fraction, hard limits, strategy activation sequence) confirmed at G4
**Decisions logged:** true — T-095 logged 2026-06-02: PRF taxonomy (Player quality/Role-fit/Form), MIN_EDGE_TO_APPROVE=0.02 justification, strategy A–K sequencing (see also 2026-05-29 retroactive entry). See DECISION_LOG.md 2026-06-02.

**⚠️ Corrected 2026-07-06 (GG-074 remediation) — several numeric/status claims below are stale by multiple phases; confirmed directly against `src/prediction_market_bot/c4_risk_engine/risk.py` and `c2_feature_store/features.py`.**
- **FEATURE_VERSION is now 1.4.0**, not the 1.1.0/38-feature set in Section 3 below — the feature set has been revised since this document's last edit (2026-05-27) and Section 3 does not describe the current feature store.
- **`MIN_EDGE_TO_APPROVE` is now 0.04** (raised from 0.02 per ADR-0020), not the `edge ≥ +0.02` threshold stated in Section 1 step 5. The header's "MIN_EDGE_TO_APPROVE=0.02 justification" decision citation is the historical original value, since superseded.
- **Section 8's hard-limits table is stale in three places:** `max_daily_loss_usd: $1,000` was removed and replaced by `MAX_DAILY_LOSS_PCT = 0.15` (ADR-0012) — there is no flat-dollar daily loss limit anymore. `max_concurrent_positions: 10` was deleted outright (ADR-0006, 2026-06-01) — not merely stubbed, it no longer exists as a limit. A fourth limit this table omits entirely, `max_portfolio_deployment_pct` (ADR-0026, aggregate open stake ≤ 60% equity → REJECT), is live in `_HARD_LIMITS` and not listed here at all.
- **Section 1/5's `mid_price = 0.50` Phase 3 placeholder is resolved** — this is the EV-benchmark issue tracked as KI-017/GG-004, resolved for the current system since live Kalshi prices have been used in production for weeks (EXP-017 MLB run: n=151, DIRECTIONAL_POSITIVE, per CLAUDE.md).
- **ADR-0004 (PENDING)** in the Decision references line — accepted 2026-05-28.
- **Section 4's Strategy A status ("C4 gated") and Section 8's "GATED — inactive until BOT_C4_ACTIVE=true"** describe the code-level gate mechanism accurately (it is real and still present in `risk.py`), but underclaim current reality: `BOT_C4_ACTIVE=true` is in fact set in the live VPS production environment — C4 has been actively sizing and approving real MLB paper positions for weeks (151 resolved EXP-017 positions did not size themselves). Do not read "gated"/Section 8's framing as meaning C4 is currently inactive.
- **Resolved 2026-07-23 (GG-074):** the `model_version` `"v1-"` prefix question above (previously unverified) is closed — `_model_version_hash()` (`forecaster.py:115-122`) still emits `"v1-"`, hashed from `model_class + sorted(feature_names)` only. The prefix was never coupled to calibration method, so ADR-0027's temperature-scaling layer does not require a `"v2-"` bump. Section 2 below is accurate as written.
- This document remains NBA/Phase-3-scoped throughout (FEATURE_VERSION, feature list, strategy table) and has never been re-derived for MLB's own feature set or strategy sequencing — treat Sections 3–4 as historical/NBA-only, not a description of the currently active MLB pool's methodology.

---

## 1. Primary Forecasting Framework

The bot uses a **calibrated probability forecasting approach** (ADR-0002):

1. **Signal source:** Rolling box-score statistics (DS-01 via nba_api), schedule context, ERI v0 signals
2. **Model output:** Calibrated probability estimate `p̂ ∈ [0,1]` for the binary YES outcome
3. **Baseline:** Market-implied probability (venue mid-price) = null model — minimum bar to beat
4. **Edge computation (ADR-0003):**
   ```
   edge = p̂ - mid_price(venue) - (spread(venue) / 2)
   where mid_price = (bid + ask) / 2
   ```
   Phase 3 placeholder: `mid_price = 0.50`, `spread = 0` (no live venue prices)
5. **Signal thresholds:** `edge ≥ +0.02` → YES; `edge ≤ -0.02` → NO (fade); otherwise PASS
6. **Position sizing:** Fractional Kelly (C4 Risk Engine) — gated until ADR-0004 + G5

---

## 2. Implemented Model Specification (Phase 3)

**Algorithm:** `LogisticRegression + PlattScaling`

```python
Pipeline([
    ("scaler",  StandardScaler()),
    ("clf",     CalibratedClassifierCV(
                    LogisticRegression(
                        penalty="l2",
                        C=1.0,
                        solver="lbfgs",
                        max_iter=1000,
                        random_state=42,
                        class_weight="balanced",
                    ),
                    method="sigmoid",  # Platt scaling
                    cv=3,
                )),
])
```

**Rationale:** Logistic regression is well-calibrated natively; Platt scaling adds an explicit ECE correction; L2 regularization limits overfit on small datasets; `class_weight="balanced"` handles class imbalance in binary props.

**NaN handling:**
- Training: rows where all features are NaN are dropped; remaining NaN columns imputed with column median
- Inference: NaN imputed with 0.0 (column median not available at inference time)

**Model version:** Deterministic SHA1 hash of feature names + model class:
```python
model_version = "v1-" + sha1(model_class + "|" + sorted_feature_names)[:8]
```
Immutable once an experiment is logged. Changes whenever feature set or model class changes.

**Calibration target:** ECE < 0.05 (10-bin uniform strategy, validation set) per FR-03.

---

## 3. Feature Set — FEATURE_VERSION 1.1.0 (38 features)

All features use only data from prior games (TI-01 compliant). Window = L10 (default).

| Group | Features | Count |
|-------|----------|-------|
| Rolling L10 mean | pts, reb, ast, stl, blk, tov, min, fg_pct, fg3_pct, ft_pct, plus_minus, fgm, fga, fg3m, fg3a, ftm, fta, pf | 18 |
| Rolling L10 std | pts, reb, ast, min, plus_minus | 5 |
| Efficiency composites | ts_pct (true shooting %), usage_proxy (possession rate), ast_tov (assist-to-turnover) | 3 |
| Regime flags | pts_hot_flag, pts_cold_flag (expanding mean ± 1σ) | 2 |
| Season context | games_played_prior, pts_season_mean, min_season_mean | 3 |
| Schedule/load context | season_type_is_playoffs, days_since_last_game, b2b_flag, load_games_l7d | 4 |
| ERI v0 (Emotional Relay Index) | eri_prev_hot, eri_prev_cold, eri_consec_cold_games | 3 |
| **Total** | | **38** |

**Target variable:** `y = 1 if pts ≥ pts_l10_mean` (binary over/under vs player's own rolling 10-game average)

**Limitation (Phase 3):** Target is calibrated to "beats own average," not a bookmaker's published line. Arbitrary-line pricing requires a Poisson/NB scoring distribution model (Phase 4 — OQ-017).

---

## 4. Strategy Architecture (Full Deployment Plan)

The primary +EV forecast model is Strategy A. Strategies B–H are planned for activation in later phases, gated by governance approvals.

| Strategy | Description | Phase Gate | Status |
|----------|-------------|-----------|--------|
| **A: ML +EV / Price Discrepancy** | Calibrated LR model; bet when `p̂ - market_mid > threshold`; fractional Kelly sizing | ADR-0004 + G5 | ✅ Model implemented; C4 gated |
| **B: Data Aggregation Enhancement** | Add home/away, rest days, opponent defensive rating, injury flags to C2 | Phase 4 | 🟡 Partial (schedule features in v1.1.0) |
| **C: Complement Lock Arbitrage** | BUY YES + BUY NO when YES+NO cost < $1 after fees; risk-free | APR-0010 | ❌ Blocked |
| **D: Statistical Arbitrage (Mean Reversion)** | Spread between correlated markets; OU process; enter at z-score threshold | Phase 6 + price feed | ❌ Blocked (DS-02 required) |
| **E: Line Shopping** | Best available price across ≥2 venues | Phase 5 (C5 multi-venue) | ❌ Blocked |
| **F: Correlated Parlays** | Low-correlation multi-leg parlays; Kelly with covariance matrix | Phase 6 | ❌ Blocked (joint distribution required) |
| **G: Kelly Criterion (configurable)** | Quarter-Kelly default; fraction confirmed at G4; multi-position covariance-adjusted | ADR-0004 | 🟡 Skeleton (DEFAULT_KELLY_FRACTION=0.25) |
| **H: Full Risk Constraints** | Drawdown limit, daily loss cap, concurrent positions cap, per-cluster exposure | G5 operational gate | 🟡 Stubs implemented in C4 |

---

## 5. Null Model Baseline

The null model is the market-implied probability:
```
null_prediction = mid_price = (bid + ask) / 2
```

Phase 3 placeholder: `null_prediction = 0.50` (no live venue prices).

The null model's Brier score is computed on the same validation/test set as the model Brier score. A model that does not beat this baseline has no positive edge and must not be deployed (ADR-0002).

**Null model Brier score at p=0.50:** `BS_null = 0.25` for a balanced binary outcome.

---

## 6. Temporal Methodology

All temporal integrity rules enforced in C2 (`features.py`):

| Rule | Description | Mechanism |
|------|-------------|-----------|
| TI-01 | All features use only data from prior games (no look-ahead) | `.shift(1)` before `.rolling()`; `temporal_cutoff` column records latest prior game date |
| TI-02 | Chronological train/val/test split only — no random shuffle | `assign_train_test_labels()` uses date boundaries only |
| TI-03 | Outcome data never enters the feature store | Outcome column excluded; ingested separately |
| TI-04 | Market prices used as features must have a defined look-back window | Phase 6 — price features will specify exact time offset |

**Walk-forward backtesting:** Train on games ≤ `train_end_date`; validate on games in `(train_end_date, val_end_date]`; test set (games > `val_end_date`) reserved for G4 evidence only.

**Minimum training samples:** 30 rows (after NaN removal). Experiments with fewer samples are invalid.

---

## 7. Calibration Approach

1. Fit `CalibratedClassifierCV(method="sigmoid", cv=3)` (Platt scaling) during `ModelForecaster.fit()`
2. Compute ECE on validation set using 10-bin uniform strategy
3. Accept if `ECE < 0.05`; if `ECE ≥ 0.10`, apply additional temperature scaling before paper trading
4. Do NOT recalibrate on the test set

**Wilson score 90% CI:** Reported alongside every `p̂` for uncertainty quantification:
```python
center = (p + z²/2n) / (1 + z²/n)   [z = 1.645 for 90% CI]
margin = (z / (1 + z²/n)) × sqrt(p(1-p)/n + z²/4n²)
```

---

## 8. Position Sizing (Kelly Criterion)

Implemented in `C4 RiskEngine`. **GATED** — inactive until `BOT_C4_ACTIVE=true`.

```
b     = (1 - mid_price) / mid_price        [net odds on YES]
f*    = (p̂ × b - (1-p̂)) / b               [full Kelly fraction]
      = p̂ - mid_price                      [simplified for binary at price mid_price]
f_live = f* × kelly_fraction               [fractional Kelly; default 0.25]
size  = min(f_live × bankroll, MAX_SINGLE_EVENT_EXPOSURE_USD)
```

For a NO direction: probabilities are flipped (`p̂_eff = 1 - p̂`, `mip_eff = 1 - mid_price`).

**Hard limits (stubs — confirmed at G4):**

| Limit | Stub Value | Trigger |
|-------|-----------|---------|
| max_single_event_exposure_usd | $500 | Caps Kelly output per event |
| max_daily_loss_usd | $1,000 | → KILL_SWITCH |
| max_drawdown_pct | 20% | → KILL_SWITCH |
| max_concurrent_positions | 10 | → REJECTED |

---

## 9. Methodology Validation Requirements

Before G4 gate sign-off:

| Check | Method | Status |
|-------|--------|--------|
| No look-ahead bias | TC-001, TC-002; `temporal_cutoff` automated check in backtester | ✅ Automated (test_backtester.py) |
| Brier score correctly computed | TC-005; compare to sklearn reference | ✅ Automated |
| Null model correctly computed | Compare `null_brier = mean((0.5 - y)²)` | ✅ Automated |
| Calibration curve + ECE < 0.05 | Reliability diagram; ECE formula verified | ✅ Automated |
| Kelly sizing formula verified | Unit tests against hand-computed examples | ✅ Automated (test_c4_risk.py) |
| Chronological split verified | All test-set dates exceed all val-set dates | ✅ Automated (test_backtester.py) |
| ERI features no look-ahead | Shift(1) on hot/cold flags | ✅ Automated (test_c2_features.py) |
| ≥3 independent experiments | EXP-001 + EXP-002 + EXP-003 non-overlapping windows | 🟡 Pending operator runs |
