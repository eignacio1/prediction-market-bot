"""Tests for run_exp015.py — T3 Analytical Simulation."""
import numpy as np
import pytest

from prediction_market_bot.run_exp015 import (
    simulate_t3_signal,
    compute_outcome_ev,
    run_monte_carlo,
    MOMENTUM_THRESHOLD,
    CONFIRM_MULTIPLIER,
    FADE_MULTIPLIER,
    T1_KELLY,
    T3_KELLY,
    MEASURED_VIG,
    MIP,
    EV_RATIO_GATE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _bet(direction="YES", edge=0.05, y_target=1, p_estimate=0.55):
    return {
        "player_name": "Test Player",
        "p_estimate":  p_estimate,
        "mid_price":   MIP,
        "edge":        edge,
        "direction":   direction,
        "y_target":    y_target,
    }


class _ConstantRng:
    """Mock RNG that always returns a fixed drift value."""
    def __init__(self, val: float):
        self._val = val

    def normal(self, *_args, **_kwargs):
        return self._val


class _ArrayRng:
    """Mock RNG that cycles through a list of values row-by-row."""
    def __init__(self, rows: np.ndarray):
        self._rows = rows
        self._idx  = 0

    def normal(self, loc, scale, size=None):
        if size is None:
            val = float(self._rows[self._idx])
            self._idx += 1
            return val
        result = self._rows[self._idx: self._idx + size[0]]
        self._idx += size[0]
        return result


# ---------------------------------------------------------------------------
# TestSimulateT3Signal
# ---------------------------------------------------------------------------

class TestSimulateT3Signal:
    def test_yes_positive_drift_above_threshold_confirm(self):
        rng = _ConstantRng(MOMENTUM_THRESHOLD + 0.001)
        assert simulate_t3_signal(_bet("YES"), 0.01, rng) == "CONFIRM"

    def test_no_negative_drift_below_threshold_confirm(self):
        rng = _ConstantRng(-MOMENTUM_THRESHOLD - 0.001)
        assert simulate_t3_signal(_bet("NO"), 0.01, rng) == "CONFIRM"

    def test_yes_negative_drift_below_threshold_fade(self):
        rng = _ConstantRng(-MOMENTUM_THRESHOLD - 0.001)
        assert simulate_t3_signal(_bet("YES"), 0.01, rng) == "FADE"

    def test_no_positive_drift_above_threshold_fade(self):
        rng = _ConstantRng(MOMENTUM_THRESHOLD + 0.001)
        assert simulate_t3_signal(_bet("NO"), 0.01, rng) == "FADE"

    def test_small_drift_neutral(self):
        rng = _ConstantRng(MOMENTUM_THRESHOLD / 2)
        assert simulate_t3_signal(_bet("YES"), 0.01, rng) == "NEUTRAL"

    def test_zero_drift_neutral(self):
        rng = _ConstantRng(0.0)
        assert simulate_t3_signal(_bet("YES"), 0.01, rng) == "NEUTRAL"


# ---------------------------------------------------------------------------
# TestComputeOutcomeEv
# ---------------------------------------------------------------------------

class TestComputeOutcomeEv:
    def test_confirm_kelly_applied_is_t3_kelly(self):
        r = compute_outcome_ev(_bet(), "CONFIRM")
        assert r["kelly_applied"] == pytest.approx(T3_KELLY)

    def test_confirm_edge_applied_uses_multiplier(self):
        edge = 0.05
        r = compute_outcome_ev(_bet(edge=edge), "CONFIRM")
        assert r["edge_applied"] == pytest.approx(edge * CONFIRM_MULTIPLIER, abs=1e-6)

    def test_confirm_position_size_ratio_vs_t1_baseline(self):
        r = compute_outcome_ev(_bet(), "CONFIRM")
        # ADR-0048 (2026-07-29) zeroed T1_KELLY; ratio-to-baseline is undefined
        # (0.0) rather than the historical 0.46 while T1 sizing is zero.
        expected = (
            0.0 if T1_KELLY == 0.0
            else round((T3_KELLY * CONFIRM_MULTIPLIER) / T1_KELLY, 4)
        )
        assert r["position_size_ratio"] == pytest.approx(expected, abs=1e-4)

    def test_fade_kelly_and_size_ratio_are_zero(self):
        r = compute_outcome_ev(_bet(), "FADE")
        assert r["kelly_applied"] == 0.0
        assert r["position_size_ratio"] == 0.0
        assert r["expected_value"] == 0.0
        assert r["outcome_pnl"] == 0.0

    def test_neutral_kelly_is_t1_kelly(self):
        r = compute_outcome_ev(_bet(), "NEUTRAL")
        assert r["kelly_applied"] == pytest.approx(T1_KELLY)
        assert r["position_size_ratio"] == pytest.approx(1.0)

    def test_yes_win_pnl_is_positive(self):
        # YES bet wins when y_target == 1
        r = compute_outcome_ev(_bet(direction="YES", y_target=1), "NEUTRAL")
        assert r["outcome_pnl"] > 0.0

    def test_yes_loss_pnl_is_negative(self):
        r = compute_outcome_ev(_bet(direction="YES", y_target=0), "NEUTRAL")
        assert r["outcome_pnl"] < 0.0


# ---------------------------------------------------------------------------
# TestRunMonteCarlo
# ---------------------------------------------------------------------------

class TestRunMonteCarlo:
    def _bets(self, n=20):
        bets = []
        for i in range(n):
            direction = "YES" if i % 2 == 0 else "NO"
            y_target  = 1 if i % 3 == 0 else 0
            bets.append(_bet(direction=direction, y_target=y_target, edge=0.04))
        return bets

    def test_signal_rates_sum_to_one(self):
        bets = self._bets()
        rng  = np.random.default_rng(42)
        r    = run_monte_carlo(bets, drift_std=0.020, n_sims=500, rng=rng)
        total = r["confirm_rate"] + r["fade_rate"] + r["neutral_rate"]
        assert total == pytest.approx(1.0, abs=1e-6)

    def test_deterministic_with_seed(self):
        bets = self._bets()
        r1   = run_monte_carlo(bets, drift_std=0.020, n_sims=200, rng=np.random.default_rng(0))
        r2   = run_monte_carlo(bets, drift_std=0.020, n_sims=200, rng=np.random.default_rng(0))
        assert r1["ev_ratio"] == pytest.approx(r2["ev_ratio"])

    def test_ev_ratio_in_plausible_range(self):
        bets = self._bets()
        rng  = np.random.default_rng(42)
        r    = run_monte_carlo(bets, drift_std=0.020, n_sims=500, rng=rng)
        assert 0.0 <= r["ev_ratio"] <= 2.0

    def test_higher_drift_more_confirm_fade(self):
        bets  = self._bets()
        r_low  = run_monte_carlo(bets, drift_std=0.005, n_sims=1000, rng=np.random.default_rng(1))
        r_high = run_monte_carlo(bets, drift_std=0.050, n_sims=1000, rng=np.random.default_rng(1))
        assert r_high["confirm_rate"] + r_high["fade_rate"] > \
               r_low["confirm_rate"]  + r_low["fade_rate"]


# ---------------------------------------------------------------------------
# TestEvFormula
# ---------------------------------------------------------------------------

class TestEvFormula:
    def _bets(self, n=30):
        return [_bet(direction="YES", edge=0.05, y_target=1) for _ in range(n)]

    def test_zero_drift_all_neutral_ev_ratio_one(self):
        # With drift_std ≈ 0, virtually all bets are NEUTRAL → T1 Kelly → EV ratio ≈ 1.0
        bets = self._bets()
        # Use tiny drift so all bets are NEUTRAL
        rng  = np.random.default_rng(42)
        r    = run_monte_carlo(bets, drift_std=1e-9, n_sims=100, rng=rng)
        assert r["neutral_rate"] == pytest.approx(1.0, abs=0.01)
        assert r["ev_ratio"] == pytest.approx(1.0, abs=0.05)

    def test_confirm_size_ratio_matches_formula(self):
        # position_size_ratio for CONFIRM = (T3_KELLY × CONFIRM_MULTIPLIER) / T1_KELLY
        r = compute_outcome_ev(_bet(direction="YES", edge=0.10), "CONFIRM")
        expected = (T3_KELLY * CONFIRM_MULTIPLIER) / T1_KELLY
        assert r["position_size_ratio"] == pytest.approx(expected, abs=1e-4)

    def test_ev_ratio_gate_constant_is_90_percent(self):
        assert EV_RATIO_GATE == 0.90
