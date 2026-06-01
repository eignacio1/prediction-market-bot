# ADR-0009 — Shadow Model Policy: Parallel Calibration Monitoring and Promotion Gate

**Status:** ACCEPTED — 2026-06-01  
**Decision makers:** DS (Earl Ignacio)  
**Supersedes:** —  
**Superseded by:** —  
**Related:** ADR-0004 (production model class), ADR-0006 (risk framework), ADR-0007 (governance gap logging)  
**Motivation:** Multi-arm architecture safeguard against single-component fracture (see STRATEGY_OVERVIEW.md Layer 2)

---

## Context

ADR-0004 freezes the production model class at LR+Platt (v1-28483b21). The frozen model policy is correct — no automated retraining in production. However, it creates a structural risk: if the production model's calibration degrades (concept drift, feature distribution shift), the entire model-edge stack (Strategies A, B, F, I) collapses simultaneously with no warm fallback.

The three-layer multi-arm architecture addresses this:
- **Layer 1:** Type 2 structural edge diversification (Strategies E + C) — active when T-077 (Polymarket KYC) and APR-0010 (arb incorporation) are cleared
- **Layer 2:** Shadow model in C3 (this ADR) — parallel calibration monitoring, warm standby, promotion gate
- **Layer 3:** Strategy I (Poisson/NB universal pricer) — post-G6 EXP; long-run replacement of A for all-lines pricing

This ADR governs Layer 2. The shadow model is NOT a production model. It generates predictions in parallel, logs to C6, and allows C7 to compare calibration trajectories. Promotion requires a new ADR.

---

## Decision

**Add a `ShadowForecaster` to C3 that runs optional parallel inference at PIPE-02 time, governed by the following policy:**

### 1. Isolation guarantee

The shadow model output **never reaches C4**. It is a C6-only output. No bet is ever sized or placed from a shadow estimate. Any code path that routes shadow output to C4 is a production defect.

### 2. Artifact spec

The shadow model is stored at `models/shadow_model.joblib` with the same artifact structure as the production model:
- `pipeline` — fitted sklearn pipeline
- `feature_names` — list of feature column names (may differ from production)
- `col_medians` — per-feature medians for imputation
- `model_version` — deterministic version hash

The shadow model may be any class (LR, GBM, regularized LR with alternative hyperparameters) as long as it accepts the same feature column format and outputs calibrated probabilities in [0, 1].

### 3. Optional presence

The system operates normally if `models/shadow_model.joblib` is absent. Shadow inference is a monitoring enhancement, not a production dependency. PIPE-02 logs `[SHADOW] No shadow model found — production only` and continues.

### 4. C6 logging protocol

Every shadow prediction is logged to C6 with:
- `event_type: shadow_forecast_emitted`
- `shadow: true` in payload
- `shadow_model_version` — shadow artifact version hash
- `shadow_p_estimate` — shadow probability estimate

Shadow predictions are also included in the pregame report JSON under `shadow_p_estimate` per forecast record, enabling EXP-017 comparison and post-game calibration auditing.

### 5. C7 monitoring

`SystemMonitor` maintains a separate `_shadow_window` deque alongside the production window. When forecast outcomes are resolved (T-121 integration), both prod and shadow p_estimates are recorded. C7 computes:
- `shadow_brier_30` — rolling Brier over the shadow window
- Comparison against `rolling_brier` (production)

**Promotion trigger:** If `shadow_brier_30 <= rolling_brier - SHADOW_PROMOTION_DELTA (0.005)` over `SHADOW_MIN_WINDOW (30)` resolved outcomes, C7 emits a `shadow_promotion_flag` WARNING event to C6. This flag is informational — it does not stop the system, does not route shadow to production, does not change any bet. It signals that a human review and new ADR are required.

### 6. Promotion requires a new ADR (ADR-0010)

Shadow promotion to production is a Class A change under ADR-0004 staleness triggers. The promotion gate:
1. C7 emits `shadow_promotion_flag` (automated)
2. Operator reviews shadow vs. prod calibration across ≥ 3 independent game nights
3. ADR-0010 drafted with evidence package: Brier comparison, ECE, AUC, feature set differences
4. DS sign-off required before promotion

Promotion is NOT triggered by the C7 flag alone. The flag is a checkpoint, not an instruction.

### 7. Shadow removal

The shadow model can be removed by deleting `models/shadow_model.joblib`. No ADR required — shadow is not production. Log the removal reason in DECISION_LOG.md.

### 8. Frozen model policy extends to shadow

The shadow model is version-pinned at deployment. No automated retraining. If a better shadow candidate emerges, it is a new file with a new version hash — not a mutation of the existing shadow artifact.

### 9. Model version hash guard (T-119)

The production model must be verified against `models/prod_model_meta.json` at every PIPE-02 startup. If `artifact["model_version"]` ≠ `meta["model_version"]`, PIPE-02 logs a CRITICAL `model_version_mismatch` event and exits 1. This prevents silent model substitution in production.

---

## Options Considered

| Option | Description | Decision |
|--------|-------------|----------|
| **A — Separate shadow artifact (chosen)** | Shadow model is an independent joblib file. Production pipeline unchanged. Shadow output C6-only. | ACCEPTED |
| B — Feature-flagged fork of C3 | Production forecaster gains a `shadow=True` path controlled by env var | Rejected — mixes production and shadow code paths; harder to audit; env var dependency |
| C — Shadow as C3 subclass | ShadowForecaster extends ModelForecaster | Rejected — inheritance couples shadow lifecycle to production class; promotion path becomes ambiguous |
| D — No shadow; retrain triggers ADR-0010 directly | Wait for drift, then swap models via ADR | Rejected — no warm fallback; by the time drift is detected, live capital may have been lost; 30-bet Brier window requires ~1 week of regular season games |

---

## Consequences

**Positive:**
- Decouples model degradation detection from model replacement. The production model can be observed against a challenger without any risk of inadvertent promotion.
- Shadow model is operationally free — it adds ~10ms of inference per player per PIPE-02 run (negligible).
- Provides early warning before L2 drift (Brier > 0.265) forces a kill. C7 can flag that shadow is outperforming prod before the production threshold is breached.

**Negative / Trade-offs:**
- Shadow model must be trained separately, versioned separately, and registered in ARTIFACT_REGISTRY.md separately. Operator overhead is low but non-zero.
- The promotion gate (ADR-0010) adds friction. This is intentional — fast automated promotion of an unvalidated challenger is categorically the wrong outcome.

**Neutral:**
- Does not affect Kelly sizing, execution, or risk framework.
- Does not affect any gate criteria (G6 evidence is based on production bets only).

---

## Implementation

| Task | Description | Status |
|------|-------------|--------|
| T-119 | Model version hash guard in run_pregame.py | This session |
| T-120 | ShadowForecaster in C3 + PIPE-02 integration | This session |
| T-121 | C7 shadow Brier tracking (wire to resolve pipeline) | Finals window |
| Shadow model training | Train GBM or alt-hyperparameter LR challenger before October 2026 | Dark period (pre-T-092) |

---

## Links

- Spec: 02_ARCHITECTURE_DESIGN/STRATEGY_OVERVIEW.md (multi-arm Layer 2)
- Code: `src/prediction_market_bot/c3_forecasting/shadow_forecaster.py`
- Code: `src/prediction_market_bot/c7_monitoring/monitor.py` (shadow window)
- Code: `src/prediction_market_bot/run_pregame.py` (PIPE-02 integration)
- Production model: `models/prod_model.joblib`, `models/prod_model_meta.json`
- ADR-0004: Production model class (governs promotion ADR-0010 requirements)
