import numpy as np
import pandas as pd
import pytest

from prediction_market_bot.mlb_engine import model_lineup as ml


def _d(lam_h, lam_a, hr=5, ar=3):
    return pd.DataFrame({"game_pk": [1, 1], "game_date": pd.to_datetime(["2025-05-01"] * 2),
                         "team_side": ["home", "away"], "runs": [hr, ar], "x": [lam_h, lam_a]})


def test_symmetric_teams_give_half_and_probabilities_are_coherent():
    m = ml.RunModel(["x"]); m.coef = np.array([0.0]); m.intercept = np.log(4.5); m.k = 1e6
    pr = ml.price(m, _d(0, 0))
    assert pr.p_home[0] == pytest.approx(0.5, abs=1e-6)
    assert 0 < pr.p_home_rl[0] < pr.p_home[0] < 1  # covering -1.5 is harder than winning


def test_poisson_total_known_answer():
    from scipy.stats import poisson
    m = ml.RunModel(["x"]); m.coef = np.array([0.0]); m.intercept = np.log(4.0); m.k = 1e6
    pr = ml.price(m, _d(0, 0), total_line=8.5)
    assert pr.p_over[0] == pytest.approx(poisson.sf(8, 8.0), abs=1e-5)  # sum of two Poisson(4) = Poisson(8)


def test_fit_recovers_dispersion_and_stronger_team_wins_more():
    rng = np.random.default_rng(1)
    n = 6000
    x = rng.normal(0, 0.3, n)
    mu = 4.5 * np.exp(x)
    y = rng.negative_binomial(8, 8 / (8 + mu))
    tr = pd.DataFrame({"x": x, "runs": y})
    m = ml.RunModel(["x"]).fit(tr)
    assert 5 < m.k < 13  # true size 8
    assert m.coef[0] == pytest.approx(1.0, abs=0.1)


def test_boot_gain_sign_and_naive():
    y = np.array([1.0, 0, 1, 0] * 200)
    good, flat = np.where(y == 1, 0.8, 0.2), np.full(len(y), 0.5)
    g, lo, hi = ml.boot_gain(good, flat, y)
    assert g > 0 and lo > 0
    assert ml.boot_gain(flat, good, y)[0] < 0
    assert ml.logloss(flat, y) == pytest.approx(np.log(2))
