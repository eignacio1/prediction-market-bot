"""Part C model: known-answer checks on win probability and Brier helpers."""
import numpy as np
import pandas as pd
import pytest

from prediction_market_bot.mlb_engine import model


def test_win_prob_symmetry_and_known_value():
    p = model._win_prob(np.array([4.0, 5.0]), np.array([4.0, 3.0]))
    assert p[0] == pytest.approx(0.5, abs=1e-9)  # equal rates -> exactly even (ties split)
    assert p[1] > 0.5
    # complement: swapping sides gives 1 - p
    assert model._win_prob(np.array([3.0]), np.array([5.0]))[0] == pytest.approx(1 - p[1], abs=1e-9)


def test_over_probability_matches_poisson_tail():
    games = pd.DataFrame({"game_pk": [1], "home_runs": [5], "away_runs": [4]})
    d = pd.DataFrame({"game_pk": [1, 1], "team_side": ["home", "away"],
                      "lineup_woba": [0.32, 0.32], "starter_woba_allowed": [0.32, 0.32], "is_home": [1.0, 0.0]})

    class M:  # constant 4.5 runs per side
        def predict(self, X):
            return np.full(len(X), 4.5)

    g = model.predict(M(), games, d, line=8.5)
    from scipy.stats import poisson
    assert g.loc[0, "p_over"] == pytest.approx(poisson.sf(8, 9.0))
    assert g.loc[0, "over"] == 1.0 and g.loc[0, "home_win"] == 1.0


def test_brier_and_bootstrap_sign():
    y = np.array([1.0, 0.0, 1.0, 0.0] * 50)
    good, bad = np.where(y == 1, 0.8, 0.2), np.full_like(y, 0.5)
    assert model.brier(bad, y) == pytest.approx(0.25)
    mean, lo, hi = model.boot_diff(good, bad, y)
    assert mean > 0 and lo > 0 and hi >= mean


def test_shrink_pulls_toward_mean():
    s = model._shrunk(pd.Series([0.0]), pd.Series([0.0]), 0.31)
    assert s.iloc[0] == pytest.approx(0.31)
    big = model._shrunk(pd.Series([40.0]), pd.Series([100.0]), 0.31)  # 0.40 observed over 100
    assert 0.31 < big.iloc[0] < 0.40
