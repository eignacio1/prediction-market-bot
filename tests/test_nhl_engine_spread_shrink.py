"""W101.1 B-029: known-answer tests for the spread-shrink pieces."""
import numpy as np

from prediction_market_bot.nhl_engine import spread_shrink as S


def test_ols_slope_known_answer():
    p = np.array([1.0, 2.0, 3.0, 4.0])
    assert abs(S.ols_slope(p, 2 * p + 5) - 2.0) < 1e-12
    assert abs(S.ols_slope(p, 0.5 * p) - 0.5) < 1e-12
    assert S.ols_slope(np.ones(4), p) == 0.0


def test_shrink_identity_and_collapse():
    lh, la = np.array([3.0, 2.0]), np.array([3.0, 4.0])
    h, a = S.shrink_rates(lh, la, 6.0, 1.0)
    assert np.allclose(h, lh) and np.allclose(a, la)
    h, a = S.shrink_rates(lh, la, 6.0, 0.0)
    assert np.allclose(h + a, 6.0)
    assert np.allclose(h / (h + a), lh / (lh + la))  # home share kept


def test_shrink_moves_halfway():
    h, a = S.shrink_rates(np.array([4.0]), np.array([4.0]), 6.0, 0.5)   # T=8 -> 7
    assert abs((h + a)[0] - 7.0) < 1e-12 and abs(h[0] - 3.5) < 1e-12
