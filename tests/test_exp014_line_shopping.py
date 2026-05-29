"""Tests for run_exp014.py — Line Shopping EV Simulation."""
import pytest
import numpy as np
import pandas as pd

from prediction_market_bot.run_exp014 import (
    simulate_vig_savings,
    estimate_lock_frequency,
    run_sensitivity_grid,
    EXP010_EV_PER_BET,
    EXP010_N_BETS,
    EXP010_VIG_KALSHI,
    EXP010_WIN_RATE,
    EXP010_BETS_YES,
    EXP010_BETS_NO,
    VIG_SAVINGS_SCENARIOS,
    ROUTING_FRACTION_SCENARIOS,
)


# ---------------------------------------------------------------------------
# TestSimulateVigSavings
# ---------------------------------------------------------------------------

class TestSimulateVigSavings:
    def test_zero_savings_equals_baseline(self):
        r = simulate_vig_savings(
            EXP010_EV_PER_BET, EXP010_VIG_KALSHI, 0.0, 1.0,
            EXP010_N_BETS, EXP010_WIN_RATE, EXP010_BETS_YES, EXP010_BETS_NO
        )
        assert r["ev_delta_per_bet"] == 0.0
        assert r["ev_per_bet_improved"] == pytest.approx(EXP010_EV_PER_BET, abs=1e-9)

    def test_higher_savings_higher_ev(self):
        r_small = simulate_vig_savings(
            EXP010_EV_PER_BET, EXP010_VIG_KALSHI, 0.005, 1.0,
            EXP010_N_BETS, EXP010_WIN_RATE, EXP010_BETS_YES, EXP010_BETS_NO
        )
        r_large = simulate_vig_savings(
            EXP010_EV_PER_BET, EXP010_VIG_KALSHI, 0.015, 1.0,
            EXP010_N_BETS, EXP010_WIN_RATE, EXP010_BETS_YES, EXP010_BETS_NO
        )
        assert r_large["ev_per_bet_improved"] > r_small["ev_per_bet_improved"]

    def test_partial_routing_scales_linearly(self):
        r_half = simulate_vig_savings(
            EXP010_EV_PER_BET, EXP010_VIG_KALSHI, 0.010, 0.50,
            EXP010_N_BETS, EXP010_WIN_RATE, EXP010_BETS_YES, EXP010_BETS_NO
        )
        r_full = simulate_vig_savings(
            EXP010_EV_PER_BET, EXP010_VIG_KALSHI, 0.010, 1.00,
            EXP010_N_BETS, EXP010_WIN_RATE, EXP010_BETS_YES, EXP010_BETS_NO
        )
        assert r_half["ev_delta_per_bet"] == pytest.approx(r_full["ev_delta_per_bet"] / 2, abs=1e-9)

    def test_annual_improvement_is_ev_delta_times_n_bets(self):
        r = simulate_vig_savings(
            EXP010_EV_PER_BET, EXP010_VIG_KALSHI, 0.010, 1.00,
            EXP010_N_BETS, EXP010_WIN_RATE, EXP010_BETS_YES, EXP010_BETS_NO
        )
        expected_annual = r["ev_delta_per_bet"] * EXP010_N_BETS
        assert r["annual_dollar_improvement"] == pytest.approx(expected_annual, abs=1e-4)

    def test_positive_ev_delta_for_nonzero_savings_and_routing(self):
        r = simulate_vig_savings(
            EXP010_EV_PER_BET, EXP010_VIG_KALSHI, 0.010, 0.50,
            EXP010_N_BETS, EXP010_WIN_RATE, EXP010_BETS_YES, EXP010_BETS_NO
        )
        assert r["ev_delta_per_bet"] > 0.0
        assert r["pct_improvement"] > 0.0


# ---------------------------------------------------------------------------
# TestEstimateLockFrequency
# ---------------------------------------------------------------------------

class TestEstimateLockFrequency:
    def test_zero_vig_diff_near_zero_frequency(self):
        # Equal vigs → locks require very large divergence; frequency must be very low
        r = estimate_lock_frequency(0.030, 0.030, n_simulations=50_000, seed=42)
        assert r["lock_frequency"] < 0.05

    def test_lock_frequency_in_unit_interval(self):
        r = estimate_lock_frequency(0.030, 0.020, n_simulations=50_000, seed=42)
        assert 0.0 <= r["lock_frequency"] <= 1.0

    def test_monotone_in_vig_savings(self):
        r_small = estimate_lock_frequency(0.030, 0.025, n_simulations=50_000, seed=42)
        r_large = estimate_lock_frequency(0.030, 0.015, n_simulations=50_000, seed=42)
        assert r_large["lock_frequency"] >= r_small["lock_frequency"]

    def test_deterministic_with_same_seed(self):
        r1 = estimate_lock_frequency(0.030, 0.020, n_simulations=10_000, seed=7)
        r2 = estimate_lock_frequency(0.030, 0.020, n_simulations=10_000, seed=7)
        assert r1["lock_frequency"] == r2["lock_frequency"]
        assert r1["avg_net_profit"] == r2["avg_net_profit"]


# ---------------------------------------------------------------------------
# TestSensitivityGrid
# ---------------------------------------------------------------------------

class TestSensitivityGrid:
    def _grid(self):
        return run_sensitivity_grid(
            EXP010_EV_PER_BET, EXP010_N_BETS, EXP010_VIG_KALSHI,
            EXP010_WIN_RATE, EXP010_BETS_YES, EXP010_BETS_NO,
            VIG_SAVINGS_SCENARIOS, ROUTING_FRACTION_SCENARIOS,
        )

    def test_correct_row_count(self):
        grid = self._grid()
        expected_rows = len(VIG_SAVINGS_SCENARIOS) * len(ROUTING_FRACTION_SCENARIOS)
        assert len(grid) == expected_rows

    def test_required_columns_present(self):
        grid = self._grid()
        required = {
            "vig_savings", "routing_fraction", "ev_per_bet_baseline",
            "ev_per_bet_improved", "ev_delta_per_bet",
            "annual_dollar_improvement", "pct_improvement",
        }
        assert required.issubset(set(grid.columns))

    def test_max_ev_at_max_params(self):
        grid = self._grid()
        max_vig  = max(VIG_SAVINGS_SCENARIOS)
        max_rf   = max(ROUTING_FRACTION_SCENARIOS)
        best_row = grid.loc[grid["ev_per_bet_improved"].idxmax()]
        assert best_row["vig_savings"] == max_vig
        assert best_row["routing_fraction"] == max_rf

    def test_all_pct_improvement_nonnegative(self):
        grid = self._grid()
        assert (grid["pct_improvement"] >= 0.0).all()
