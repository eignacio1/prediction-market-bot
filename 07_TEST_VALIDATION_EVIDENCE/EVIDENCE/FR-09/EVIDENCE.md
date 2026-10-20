# FR-09 Evidence — Risk Limit Enforcement

> **Record as of 2026-07-06** — a frozen, dated record, not a living document. It is not kept in step with the system; see `00_ADMIN/DOC_REGISTRY.toml`.


**Requirement:** (a) Order rejected when position would exceed max single-event limit; (b) Kill switch triggered automatically when daily loss limit breached (simulated); (c) Risk check runs before every order attempt; (d) Override path requires ADR evidence.

**Populated:** 2026-07-06 (GG-075 remediation).

## Test evidence

- `tests/test_c4_risk.py` — `_HARD_LIMITS` enforcement (`max_single_event_exposure_usd=500.0`, `max_drawdown_pct=0.20`).
- `tests/test_t156_daily_loss.py` — `MAX_DAILY_LOSS_PCT=0.15` auto-trigger (ADR-0012).
- `tests/test_t161_budget_credit.py`, `tests/test_t164_order_throttle.py` — per-band budget and throttle enforcement.
- `tests/test_t159_portfolio_invariants.py` — no-bypass-path / invariant checks across the portfolio.

## Known open question (not a test-coverage gap — a sufficiency-at-cadence question)

**GG-071 (RESOLVED via ADR-0040, 2026-07-04):** enforcement mechanics are correct and tested; the open question was whether the *values* were calibrated for real compounding cadence. A forward Monte Carlo found T1 MLB's real win rate produced material drawdown-breach probability under the pre-ADR-0040 `kelly_fraction=0.10`; ADR-0040 de-rated it to 0.061, reducing 1yr breach probability to ~5.6% (operator-selected target). This is a monitored risk (re-run `scripts/mc_forward_projection.py` if win rate/cadence/kelly_fraction shift materially), not an open enforcement defect.

## Status

**OPERATIONALLY DEMONSTRATED** — C4 risk engine enforces `_HARD_LIMITS` on every live paper order across both MLB and NBA ledgers. All limits still require formal ADR revision at G6 when live bankroll is set (open obligation, logged 2026-05-29, unchanged).
