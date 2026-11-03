import numpy as np, pandas as pd
from prediction_market_bot.nhl_engine import late_game as LG


def test_state_buckets():
    assert list(LG._state(np.array([-5, -2, -1, 0, 1, 2, 7]))) == [0, 0, 1, 2, 3, 4, 4]


def test_flat_multipliers_recover_base_poisson_total():
    # known answer: state rate = lam/lam_bar per minute with lam==lam_bar and early_scale 1 -> total ~ lam*(55+5)/60 each side
    base = np.full((2, 5), 1.0 / 60.0 * 60.0 / 60.0)  # goals per rate-weighted minute = lam_bar/60 with lam_bar=1 per game
    s = LG.simulate_v2(1.0, 1.0, base, 1.0, np.inf, 0.5, 200000, 1, 1.0, 1.0)
    assert abs(s.reg_home.mean() - (55 + 5) / 60) < 0.02 and abs(s.reg_away.mean() - (55 + 5) / 60) < 0.02


def test_fit_late_known_rate():
    n = 4000; rng = np.random.default_rng(0)
    tab = pd.DataFrame(dict(h_at5=0, a_at5=0, h_at2=0, a_at2=0, h_w1=rng.poisson(0.1 * 3, n), a_w1=rng.poisson(0.1 * 3, n),
                            h_w2=rng.poisson(0.3 * 2, n), a_w2=rng.poisson(0.3 * 2, n)))
    b = LG.fit_late(tab, np.ones(n), np.ones(n))
    assert abs(b[0, 2] - 0.1) < 0.01 and abs(b[1, 2] - 0.3) < 0.015


def test_early_scale_keeps_expected_goals():
    tab = pd.DataFrame(dict(h_all=[3] * 10, a_all=[3] * 10, h_w1=[0, 1] * 5, a_w1=[0] * 10, h_w2=[0] * 10, a_w2=[0] * 10))
    assert abs(LG.early_scale(tab) * 55 / 60 * 6 + 0.5 - 6) < 1e-9
