# FR-05 Evidence — Kill Switch (≤60 seconds, all components)

**Requirement:** (a) Manual kill-switch trigger halts all processes within ≤60 seconds (timed); (b) Auto-trigger fires on daily loss limit breach (simulated); (c) Log entry created on every activation; (d) System does not resume without explicit operator restart.

**Populated:** 2026-07-06 (GG-075 remediation) — this is the clearest case in the whole evidence-trail gap: a real, passing drill result existed in prose (MEMORY_BANK.md, DECISION_LOG.md) for weeks but was never copied into the folder this document's own design pointed at.

## Drill record (real, previously undocumented here)

- **Drill ID:** KS-C8D7D90AF942
- **Result:** PASSED — halt completed in **0.340ms**, well under the ≤60s (NFR-03) requirement.
- **Approval:** APR-0013
- **Task:** T-051 (✅), recorded in `11_MEMORY_HANDOFF/MEMORY_BANK.md:769`.
- **Gate:** G5 (kill switch drill required before any live inference or capital use, per TEST_STRATEGY.md L4).

## Test evidence (auto-trigger + logging + no-auto-resume)

- `tests/test_c7_monitor.py` — kill switch mechanics, auto-trigger on limit breach.
- `tests/test_t156_daily_loss.py` — `MAX_DAILY_LOSS_PCT` (0.15) circuit breaker.
- `tests/test_t159_portfolio_invariants.py` — post-halt invariant checks.
- `tests/test_run_t4_mlb_live.py`, `tests/test_t4_live_runner.py` — T4-specific halt/contamination-guard behavior (`CONTAMINATION_HALT`, `game_state_fresh` checks).

## Status

**MET.** Manual drill passed at G5 with a real timed result (0.340ms << 60s). Auto-trigger, logging, and no-auto-resume are covered by the passing unit/integration tests above. This file closes the specific procedural gap GG-075 flagged for FR-05/NFR-03: the drill result now lives in the folder the design specifies, not only in narrative logs.
