"""Known-answer tests for quant/inplay_nba.py (W103.3 / B-046)."""
import math

import numpy as np
import pytest

from prediction_market_bot.quant import inplay_nba as q


def test_symmetric_zero_drift_is_half():
    assert q.p_home_win(0.0, 30.0, 0.0, 4.8) == pytest.approx(0.5, abs=1e-12)


def test_zero_drift_closed_form_phi():
    # margin +6, 12 min left, s2=4: P(X>=1)+.5P(X==0) with X~N(6, 48) on the lattice
    sd = math.sqrt(4.0 * 12.0)
    expect = 1 - q._phi((0.5 - 6) / sd) - 0.5 * (q._phi((0.5 - 6) / sd) - q._phi((-0.5 - 6) / sd)) + 0.0
    # = P(X>=1) + .5 P(X==0)
    p_hi = 1 - q._phi((0.5 - 6) / sd)
    p_tie = q._phi((0.5 - 6) / sd) - q._phi((-0.5 - 6) / sd)
    assert q.p_home_win(6.0, 12.0, 0.0, 4.0) == pytest.approx(p_hi + 0.5 * p_tie, abs=1e-12)
    assert expect is not None


def test_antisymmetry():
    a = q.p_home_win(5.0, 20.0, 3.0, 4.8)
    b = q.p_home_win(-5.0, 20.0, -3.0, 4.8)
    assert a + b == pytest.approx(1.0, abs=1e-12)


def test_terminal_conditions():
    assert q.p_home_win(3.0, 0.0, 5.0, 4.8) == 1.0
    assert q.p_home_win(-3.0, 0.0, 5.0, 4.8) == 0.0
    assert q.p_home_win(0.0, 0.0, 5.0, 4.8) == 0.5
    assert q.p_margin_gt(5.0, 0.0, 0.0, 4.8, 4.5) == 1.0
    assert q.p_total_gt(220.0, 0.0, 220.0, 8.0, 219.5) == 1.0


def test_pregame_drift_is_spread_over_48():
    # 48 min left, margin 0: win prob equals Phi-lattice of N(M, s2*48)
    M, s2 = 4.0, 4.8
    sd = math.sqrt(s2 * 48)
    p_hi = 1 - q._phi((0.5 - M) / sd)
    p_tie = q._phi((0.5 - M) / sd) - q._phi((-0.5 - M) / sd)
    assert q.p_home_win(0.0, 48.0, M, s2) == pytest.approx(p_hi + 0.5 * p_tie, abs=1e-12)
    assert q.expected_final(10.0, 24.0, 6.0) == pytest.approx(13.0)


def test_monotone_in_margin_and_time():
    ps = [q.p_home_win(x, 12.0, 2.0, 4.8) for x in range(-10, 11)]
    assert all(b >= a for a, b in zip(ps, ps[1:]))
    # a lead is safer with less time left
    assert q.p_home_win(8.0, 5.0, 0.0, 4.8) > q.p_home_win(8.0, 30.0, 0.0, 4.8)


def test_simulation_matches_closed_form():
    for x, t, M in [(0.0, 48.0, 3.0), (6.0, 24.0, -2.0), (-4.0, 12.0, 5.0)]:
        sim = q.simulate_margin_win(x, t, M, 4.8, n=200_000, seed=1)
        assert sim == pytest.approx(q.p_home_win(x, t, M, 4.8), abs=0.004)


def test_total_over_symmetric():
    # expected total on the line exactly: P(over a half-point line just below the mean) ~ 0.5
    assert q.p_total_gt(0.0, 48.0, 220.0, 8.0, 220.0) == pytest.approx(0.5, abs=1e-12)


def test_estimate_sigma2_recovers_truth():
    rng = np.random.default_rng(7)
    tau = np.full(20000, 24.0)
    M = rng.normal(2, 4, 20000)
    fut = M * tau / 48 + rng.normal(0, np.sqrt(4.8 * tau))
    assert q.estimate_sigma2(fut, tau, M) == pytest.approx(4.8, rel=0.03)


def test_brier_and_bins_and_ci():
    assert q.brier([1.0, 0.0], [1, 0]) == 0.0
    bins = q.calibration_bins([0.05, 0.06, 0.95], [0, 0, 1])
    assert sum(b[3] for b in bins) == 3
    m, lo, hi = q.bootstrap_ci([0.1, 0.2, 0.3, 0.4])
    assert lo <= m <= hi
