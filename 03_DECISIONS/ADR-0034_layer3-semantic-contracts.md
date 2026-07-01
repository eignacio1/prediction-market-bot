# ADR-0034 — Layer 3 Semantic Contracts: `c7_semantic_contracts.py`

**Status:** ACCEPTED — DS sign-off Earl Ignacio 2026-06-29 SESSION 100
**Date:** 2026-06-29
**Gate:** GG-051 resolution; active paper trading (MLB)
**Supersedes:** Nothing (new governance tier — not a revision of existing ADR)
**Amends:** ADR-0001 (Compass OS governance framework — adds Layer 3 to the three-layer model)
**Resolves:** GG-051

---

## Context

The governance framework entering SESSION 100 had two operational layers:

**Layer 1 — Architecture integrity (gate reviews):**
Verified at G0–G9 that components were built as designed. Does not run at runtime.

**Layer 2 — Operational health (C7 monitor.py):**
Verified per monitoring cycle that Brier/ECE drift was within bounds and P&L loss
hadn't triggered the kill switch. Ran on resolved forecasts.

Two independent silent failures exposed the structural gap:

**GG-049 (T1 MLB dark 2 days):**
T1 MLB placed 0 bets across June 27–28 (2 full game days). Root cause: a naming
convention mismatch in the Kalshi ticker date parser silently prevented all
player-to-market matching. The pipeline ran successfully (no exceptions, no errors),
fetched active MLB games, found live Kalshi markets — and then matched zero players.
Layer 1 did not catch it (the architecture was correct). Layer 2 did not catch it
(no resolved forecasts → no Brier drift → no alert). The fix was adding an operational
heartbeat to the session-start protocol — a human check at session open, not a
machine assertion at pipeline execution.

**GG-050 (T4 MLB re-betting 17.5×):**
`fired_tickers` was initialized inside `_run_cycle()`, resetting every 90-second
evaluation cycle. The intent was per-game dedup. The effect was per-cycle dedup.
73 independent markets received an average of 17.5 positions each (n=1274 total).
EXP-T4-01 produced a false DIRECTIONAL_POSITIVE verdict on contaminated data.
Layer 1 did not catch it (the logic appeared correct in unit tests). Layer 2 did
not catch it (individual positions appeared valid; the structural re-betting was
invisible to Brier/ECE monitoring).

**Common root cause:** No governance layer asked "Is what is currently running
doing what it was designed to do?"

---

## Decision

Adopt a Layer 3 governance tier: **Semantic Behavioral Contracts**.

Layer 3 formally states the behavioral intent of each pipeline stage and each
execution band, then verifies it at runtime. Violations emit to C6 and surface
in C7's health snapshot (C8 dashboard).

The module is `src/prediction_market_bot/c7_monitoring/semantic_contracts.py`.

---

## Contract Architecture

**PIPELINE_FLOOR contracts (C1→C2 boundary):**
Verify that data retrieved from C1 successfully mapped to model-ready players in C2.
The invariant: if games_fetched > 0, matched_players must be > 0.
Raised as `SemanticFloorViolation` (exception) → pipeline must halt.

**EVALUATION_GATE contracts (T4 pre-evaluation):**
Verify data window coherence before evaluate_forecast() is called.
Checks: market has live quotes, MIP in (0,1), player in live boxscore, game in progress,
elapsed_min < regulation, h_needed ≤ ab_remaining.
Returns False (ContaminationGuard.is_clean()) → evaluation skipped, cycle continues.

**BAND_INVARIANT contracts (per-band structural properties):**
Verify that each band is doing what its mathematical model is supposed to do.
T1 MLB: ba_l10 in [0.05, 0.60], threshold in [1,3], p_estimate in [0.05, 0.95].
T4-PROJ: lambda_prior not equal to fallback default (20.0).
T4-FLOW: score_differential in [-60, 60].
T4-ARITH: h_needed achievable given ab_remaining.
Returns ContractViolation → logged to C6 as WARNING; evaluation continues flagged.

**CORR_DOWNWARD contract (ADR-0029 Principle 6):**
T4-CORR overlay must only reduce position sizes, never increase them.
Raised as `T4CorrDownwardViolation` → caller must trigger kill switch.

---

## Throughput guarantee

All contracts are O(1) per evaluation (no I/O, no aggregation across players).
The ContaminationGuard processes one ticker in approximately 10 operations.
At ~1,000 evaluations/game (CLAUDE.md Hard Rule 9), Layer 3 adds < 1ms overhead
per cycle. The module does not compromise throughput design.

---

## Integration

Three call sites. Integration patches in `09_INTEGRATION_PATCHES/SEMANTIC_CONTRACTS_INTEGRATION.md`.

1. **PIPE-05** (run_mlb_paper_trade.py): SemanticFloorGuard.assert_floor() after data load.
2. **T4 MLB** (run_t4_mlb_live.py): ContaminationGuard.is_clean() in _run_cycle() inner loop.
3. **C7 monitor** (monitor.py): SemanticContractMonitor on SystemMonitor; health state in get_health_snapshot().

---

## Audit events

| Event | Severity | Trigger |
|-------|----------|---------|
| `semantic_floor_violation` | CRITICAL | Pipeline floor: games_fetched>0 AND matched_players=0 |
| `contamination_halt` | WARNING | T4 evaluation: data window incoherent |
| `semantic_contract_breach` | WARNING | Band invariant violated |
| `semantic_corr_downward_violation` | CRITICAL | T4-CORR overlay increased a position size |
| `semantic_health_snapshot` | INFO | Periodic session summary (sampled) |

---

## What this does not change

- C4 hard limits (ADR-0012, ADR-0026) — unchanged
- Kill switch SLA ≤60s (NFR-03) — unchanged
- Frozen model policy — unchanged
- No automated retraining — unchanged
- Paper trading mode — unchanged
- No live capital implications (G6 gate unchanged)

---

## Open obligations

- Integration patches must be applied and tested before the next MLB game day.
- BandInvariantChecker checks for T4-NBA sub-bands (T4-EVENT, T4-BOUNDARY, T4-LINEUP)
  are stubbed pending T4-NBA re-activation post-off-season.
- T4-CORR downward violation patch (Step 2.3) is marked Phase 8 gated — do not activate
  until T4-CORR sub-band is unfrozen per ADR-0029.
