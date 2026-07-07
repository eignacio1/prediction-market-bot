# FR-07 Evidence — Simulated Order Placement (Paper Trading)

**Requirement:** (a) Paper trading mode records hypothetical orders with all fields; (b) No real orders submitted (API call log shows zero submissions); (c) Simulated PnL calculated correctly on resolution.

**Populated:** 2026-07-06 (GG-075 remediation).

## Test evidence

- `tests/test_paper_trader.py` — order recording, PnL calculation on settlement.
- `tests/test_t174_pnl_reconciliation.py` — PnL correctness under reconciliation.
- `tests/test_run_mlb_paper_trade.py`, `tests/test_run_resolve.py`, `tests/test_t187e_mlb_resolve.py` — MLB-specific open/resolve cycle.

## Live production evidence (dual-ledger, ADR-0035/ADR-0037)

- PaperTrader running continuously since 2026-05-29 (T-060).
- **MLB (ACTIVE):** 99+ resolved paper positions as of 2026-07-05 session-end (G6 count+sign criterion met; EXP-017 sample-adequacy at Tier 1, see FR-03/EVIDENCE.md).
- **NBA (DARK/FROZEN):** 158 resolved, frozen historical baseline (GG-034/GG-037-adjudicated), -24.9% drawdown — not a live risk signal, per `feedback_portfolio_ledger_delineation` convention.
- No real venue orders: confirmed architecturally — `VenueAdapter` paper mode never calls a live order-submission endpoint; live capital gating (`BOT_C4_ACTIVE`-style + G6 gate flag) blocks the live path entirely pre-G6.

## Status

**MET, live in production.** Both ledgers have run continuously for 5+ weeks with correct PnL settlement on every resolved position.
