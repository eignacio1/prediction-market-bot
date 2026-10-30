"""Known-answer tests for engine_v3 (W96.1)."""
import numpy as np

from prediction_market_bot.nba_engine import engine_v2 as V, engine_v3 as V3


def test_centered_margin_shift_recovered_and_missing_is_neutral():
    rng = np.random.default_rng(11)
    n = 60000
    x = 5.0 + rng.standard_normal(n)  # deliberately uncentred
    h = 110 + 2.0 * (x - 5.0) + 10 * rng.standard_normal(n)
    a = 108 + 10 * rng.standard_normal(n)
    p, c = V3.fit(np.full(n, 110.0), np.full(n, 108.0), h, a, {"d_lineup_net": x}, ["d_lineup_net"])
    assert abs(p.shift_margin["d_lineup_net"] - 2.0) < 0.15
    m_miss, _ = V3.game_means(p, c, 110.0, 108.0, {})
    m_mean, _ = V3.game_means(p, c, 110.0, 108.0, {"d_lineup_net": 5.0})
    m_nan, _ = V3.game_means(p, c, 110.0, 108.0, {"d_lineup_net": float("nan")})
    assert abs(m_miss - m_mean) < 0.05 and m_miss == m_nan
    m_hi, _ = V3.game_means(p, c, 110.0, 108.0, {"d_lineup_net": 6.0})
    assert abs((m_hi - m_mean) - p.shift_margin["d_lineup_net"]) < 1e-9


def test_total_factor_routes_to_total_only():
    rng = np.random.default_rng(12)
    n = 60000
    s = rng.standard_normal(n)
    h = 110 + 1.5 * s + 10 * rng.standard_normal(n)
    a = 108 + 1.5 * s + 10 * rng.standard_normal(n)
    p, c = V3.fit(np.full(n, 110.0), np.full(n, 108.0), h, a, {"s_exp_missing": s}, ["s_exp_missing"])
    assert "s_exp_missing" in p.shift_total and not p.shift_margin
    assert abs(p.shift_total["s_exp_missing"] - 3.0) < 0.3


def test_no_factors_equals_v2_core():
    rng = np.random.default_rng(13)
    n = 5000
    h, a = 110 + 10 * rng.standard_normal(n), 108 + 10 * rng.standard_normal(n)
    p3, _ = V3.fit(np.full(n, 110.0), np.full(n, 108.0), h, a, {}, [])
    p2 = V.fit_params(np.full(n, 110.0), np.full(n, 108.0), h, a)
    assert p3 == p2
