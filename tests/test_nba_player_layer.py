"""Known-answer tests for the NBA engine player layer (W96.1 Part C)."""
import numpy as np

from prediction_market_bot.nba_engine import player_layer as PL


def test_known_shares_recovered_and_sum_constraint_holds():
    rng = np.random.default_rng(5)
    shares = PL.shares_from_means([22.0, 18.0, 15.0, 10.0, 5.0], rest_share=0.20)
    assert abs(shares.sum() - 1.0) < 1e-12 and abs(shares[-1] - 0.20) < 1e-12
    T = np.full(20000, 112)
    d = PL.draw_split(T, shares, conc=400.0, rng=rng)
    assert (d.sum(axis=1) == T).all()                       # players + rest add up to the team, every draw
    assert np.abs(d.mean(axis=0) / 112 - shares).max() < 0.004


def test_concentration_recovered():
    rng = np.random.default_rng(6)
    shares = PL.shares_from_means([20.0, 15.0, 10.0], rest_share=0.3)
    T = rng.integers(95, 130, size=40000)
    d = PL.draw_split(T, shares, conc=120.0, rng=rng)
    y = d[:, 0]
    c = PL.fit_concentration(y, T, np.full(len(T), shares[0]))
    assert 85.0 < c < 170.0
