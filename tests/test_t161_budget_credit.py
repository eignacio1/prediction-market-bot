"""
Tests: T-161 / ADR-0022 — T4 band budget realized-value credit (GG-023 fix)
============================================================================
The G4 defect: t4_deployed_usd incremented on every entry fire and never
decremented on exit. Budget pinned at 100% by Q2 while 29 exits freed
economic capital; fired=0 for the entire second half.

ADR-0022 semantics (realized-value credit, capped at budget):
    deployed = open T4 exposure + realized T4 losses this game
    - Winning exit credits entry cost only (capacity never exceeds the
      authorized band budget — wins do not expand risk authorization)
    - Losing exit credits entry cost + pnl (losses permanently consume
      budget → the band's aggregate net loss is bounded by t4_band_budget)
    - Ledger is reconstructable from portfolio state after a process
      restart (G4: T4 process died mid-game)
"""

import pytest

from prediction_market_bot.run_t4_live import (
    _exit_budget_credit,
    _reconstruct_t4_ledger,
)


# ---------------------------------------------------------------------------
# _exit_budget_credit — per-exit arithmetic
# ---------------------------------------------------------------------------

class TestExitBudgetCredit:
    def test_winning_exit_credits_entry_cost_only(self):
        # $50 entry, +$12 pnl → credit exactly $50; the win does not create
        # capacity above the original budget.
        assert _exit_budget_credit(50.0, 12.0) == pytest.approx(50.0)

    def test_losing_exit_credits_realized_value(self):
        # $50 entry, -$20 pnl → only $30 of capital actually came back.
        assert _exit_budget_credit(50.0, -20.0) == pytest.approx(30.0)

    def test_breakeven_exit_credits_entry_cost(self):
        assert _exit_budget_credit(50.0, 0.0) == pytest.approx(50.0)

    def test_total_loss_credits_zero(self):
        # Position went to zero: nothing comes back, budget stays consumed.
        assert _exit_budget_credit(50.0, -50.0) == pytest.approx(0.0)

    def test_aggregate_net_loss_bounded_by_budget(self):
        """
        Structural property: under any sequence of entry/exit pairs the
        ledger admits, cumulative realized losses cannot exceed the budget.
        Simulates a high-churn game (the GG-023 regime) with every exit
        losing 40% of entry cost.
        """
        budget = 500.0
        deployed = 0.0
        total_loss = 0.0
        entry = 25.0
        for _ in range(200):  # far more attempts than budget/entry
            if deployed + entry > budget:
                continue  # BAND_BUDGET_EXHAUSTED path
            deployed += entry
            pnl = -0.4 * entry
            total_loss += -pnl
            deployed = max(0.0, deployed - _exit_budget_credit(entry, pnl))
        assert total_loss <= budget + 1e-9

    def test_winning_churn_recycles_capacity_without_expansion(self):
        """
        All-winning churn: deployed always returns exactly to zero after
        each round trip — capacity recycles (the G4 starvation is gone)
        but never exceeds the budget (no martingale expansion).
        """
        budget = 500.0
        deployed = 0.0
        fired = 0
        entry = 25.0
        for _ in range(100):
            assert deployed + entry <= budget  # never starved
            deployed += entry
            fired += 1
            deployed = max(0.0, deployed - _exit_budget_credit(entry, +10.0))
            assert deployed == pytest.approx(0.0)
        assert fired == 100  # old monotonic counter would have stopped at 20


# ---------------------------------------------------------------------------
# _reconstruct_t4_ledger — restart safety
# ---------------------------------------------------------------------------

def _pos(size, game_date="2026-06-12", pool_isolated=True, **kw):
    return {"size_usd": size, "game_date": game_date,
            "pool_isolated": pool_isolated, **kw}


class TestReconstructLedger:
    GAME = "2026-06-12"

    def test_empty_portfolio_is_zero(self):
        assert _reconstruct_t4_ledger(
            {"open_positions": [], "closed_positions": []}, self.GAME
        ) == 0.0

    def test_open_exposure_counted(self):
        pf = {
            "open_positions": [_pos(25.0), _pos(40.0)],
            "closed_positions": [],
        }
        assert _reconstruct_t4_ledger(pf, self.GAME) == pytest.approx(65.0)

    def test_realized_losses_counted_wins_do_not_offset(self):
        # One -$20 loss and one +$50 win: deployed = 20, not max(0, -30).
        # Per-exit semantics — a win restores its own entry cost only.
        pf = {
            "open_positions": [],
            "closed_positions": [
                _pos(50.0, status="EXITED", exit_pnl=-20.0),
                _pos(50.0, status="EXITED", exit_pnl=50.0),
            ],
        }
        assert _reconstruct_t4_ledger(pf, self.GAME) == pytest.approx(20.0)

    def test_non_t4_positions_excluded(self):
        # T1 positions (pool_isolated=False) must not consume T4 budget.
        pf = {
            "open_positions": [_pos(100.0, pool_isolated=False), _pos(25.0)],
            "closed_positions": [
                _pos(50.0, pool_isolated=False, status="EXITED", exit_pnl=-50.0),
            ],
        }
        assert _reconstruct_t4_ledger(pf, self.GAME) == pytest.approx(25.0)

    def test_other_game_dates_excluded(self):
        pf = {
            "open_positions": [_pos(25.0, game_date="2026-06-10")],
            "closed_positions": [
                _pos(50.0, game_date="2026-06-10", status="EXITED", exit_pnl=-30.0),
            ],
        }
        assert _reconstruct_t4_ledger(pf, self.GAME) == 0.0

    def test_resolved_positions_excluded(self):
        # Positions closed by end-of-game resolution (not early exit) are
        # settled outside the in-game ledger.
        pf = {
            "open_positions": [],
            "closed_positions": [
                _pos(50.0, status="RESOLVED", exit_pnl=-50.0),
            ],
        }
        assert _reconstruct_t4_ledger(pf, self.GAME) == 0.0

    def test_restart_equivalence_with_incremental_ledger(self):
        """
        The reconstructed ledger must equal the value the incremental
        per-cycle arithmetic would have reached — restart is lossless.
        """
        budget_entries = [(30.0, -10.0), (25.0, +5.0), (40.0, None), (20.0, -20.0)]
        # Incremental path
        deployed = 0.0
        for size, pnl in budget_entries:
            deployed += size
            if pnl is not None:
                deployed = max(0.0, deployed - _exit_budget_credit(size, pnl))
        # Portfolio state after the same history
        pf = {
            "open_positions": [_pos(40.0)],
            "closed_positions": [
                _pos(30.0, status="EXITED", exit_pnl=-10.0),
                _pos(25.0, status="EXITED", exit_pnl=5.0),
                _pos(20.0, status="EXITED", exit_pnl=-20.0),
            ],
        }
        assert _reconstruct_t4_ledger(pf, self.GAME) == pytest.approx(deployed)
