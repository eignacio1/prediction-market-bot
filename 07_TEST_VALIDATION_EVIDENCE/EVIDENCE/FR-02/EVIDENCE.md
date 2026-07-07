# FR-02 Evidence — Forecast Generation

**Requirement:** (a) Forecast output includes: event_id, timestamp, p_estimate, confidence_interval, snapshot_id, model_version; (b) p_estimate ∈ [0,1]; (c) Every output traceable to a Snapshot ID.

**Populated:** 2026-07-06 (GG-075 remediation).

## Test evidence (real, currently passing)

- `tests/test_c3_forecaster.py`, `tests/test_c3_calibration.py`, `tests/test_c3_game_state_model.py`, `tests/test_c3_shadow_forecaster.py` — output schema, calibration (Platt scaling, ADR-0004), and probability-bounds tests.
- `tests/test_t183_mlb_c3.py` — MLB-specific C3 forecast output tests.
- `tests/test_t186_v2b_retrain.py` — model_version tracking through the v1→v2 retrain (`v2-065b9510`, ADR-0031).

## Model version currently in production

`v2-065b9510` (ADR-0031, SESSION 73) — confirmed via `grep -rn "model_version" src/prediction_market_bot/c3_forecasting/`.

## Status

**OPERATIONALLY DEMONSTRATED** — C3 forecasting has been live in production for 5+ weeks; the schema/bounds/traceability contract is enforced by the tests above, all passing as of the 2026-07-06 full-suite run (2375 passed / 6 skipped / 1 pre-existing unrelated failure — see FR-01/EVIDENCE.md for detail).
