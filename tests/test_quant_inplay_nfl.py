"""W129.6 Part B: known answers for the NFL in-play pricer (arithmetic band)."""
import math

from prediction_market_bot.quant import inplay_nfl as m


def test_final_margin_is_deterministic():
    assert m.p_home_win(3, 0, 7.0, 3.3) == 1.0
    assert m.p_home_win(-3, 0, 7.0, 3.3) == 0.0
    assert m.p_home_win(0, 0, 7.0, 3.3) == 0.5


def test_pick_em_symmetry():
    p = m.p_home_win(0, 1800, 0.0, 3.3)
    assert abs(p - 0.5) < 1e-9
    a = m.p_home_win(6, 900, 0.0, 3.3)
    b = m.p_home_win(-6, 900, 0.0, 3.3)
    assert abs(a + b - 1.0) < 1e-9


def test_pregame_price_matches_spread_arithmetic():
    # kickoff: home -7 -> P(home wins) = Phi(7 / sqrt(s2*60))
    s2 = 3.3
    want = m._phi(7.0 / math.sqrt(s2 * 60))
    assert abs(m.p_home_win(0, 3600, 7.0, s2) - want) < 1e-9


def test_drive_ep_sign_and_monotone():
    assert m.drive_ep(5, 1) > m.drive_ep(50, 1) > m.drive_ep(95, 1)
    assert m.drive_ep(50, 0) == 0.0 and m.drive_ep(None, 1) == 0.0
    base = m.p_home_win(0, 600, 0.0, 3.3)
    assert m.p_home_win(0, 600, 0.0, 3.3, "home", 10, 1) > base
    assert m.p_home_win(0, 600, 0.0, 3.3, "away", 10, 1) < base


def test_total_and_spread_thresholds():
    assert m.p_total_gt(50, 0, 45.0, 3.2, 49.5) == 1.0
    assert m.p_total_gt(40, 0, 45.0, 3.2, 40.5) == 0.0
    assert m.p_margin_gt(10, 0, 0.0, 3.3, 9.5) == 1.0


def test_sigma2_estimators():
    r, t = [6.0, 6.0], [10.0, 0.5]
    assert abs(m.estimate_sigma2(r, t, weighted=True) - 72 / 10.5) < 1e-9
    assert m.estimate_sigma2(r, t, weighted=False) > m.estimate_sigma2(r, t, weighted=True)
    assert math.isnan(m.estimate_sigma2([1.0], [0.0]))


def test_flow_is_identity():
    assert m.flow_adjustment(0.37) == 0.37
