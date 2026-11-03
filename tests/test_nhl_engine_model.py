import numpy as np
import pandas as pd

from prediction_market_bot.nhl_engine import goals, model


def _frame(n, rng):
    f = rng.normal(2.4, 0.3, n)
    d = {"game_id": np.arange(n), "sec5_h": 3000.0, "lg_f5_h": 2.4, "lg_pp_h": 7.0}
    for s in ("h", "a"):
        d[f"f5_{s}"] = f if s == "h" else rng.normal(2.4, 0.3, n)
        d[f"a5_{s}"] = 2.4; d[f"pp_{s}"] = 7.0; d[f"pk_{s}"] = 7.0; d[f"ppt_{s}"] = 300.0; d[f"sht_{s}"] = 300.0
        d[f"rest_{s}"] = 2.0; d[f"gs_{s}"] = 0.0
    return pd.DataFrame(d)


def test_fit_recovers_xg_slope_and_dispersion():
    rng = np.random.default_rng(1)
    fr = _frame(20000, rng)
    x = model.side_rows(fr)
    n = len(fr)
    lam = np.exp(0.9 * x["lx"].to_numpy() - 0.7 + 0.1 * x["home"].to_numpy())
    g = rng.gamma(10.0, 0.1, n)
    rh, ra = rng.poisson(lam[:n] * g), rng.poisson(lam[n:] * g)
    m = model.fit(fr, rh, ra, rng.random(n) < 0.5)
    assert abs(m.coef[1] - 0.9) < 0.1
    assert 6 < m.k < 16
    lh, la = m.rates(fr.iloc[:50])
    assert lh.shape == (50,) and (lh > 0).all()


def test_price_games_coherent():
    rng = np.random.default_rng(2)
    fr = _frame(400, rng)
    rh, ra = rng.poisson(2.8, 400), rng.poisson(2.6, 400)
    m = model.fit(fr, rh, ra, rng.random(400) < 0.5)
    b = model.price_games(m, fr.iloc[:3], n_sim=4000)[0]
    t = list(b["total_over"].values())
    assert all(t[i] >= t[i + 1] for i in range(len(t) - 1))
    assert 0 < b["moneyline_home"] < 1


def test_level_adjust_recovers_scale_and_is_point_in_time():
    rng = np.random.default_rng(3)
    n = 3000
    fr = pd.DataFrame({"start": pd.date_range("2024-10-01", periods=n, freq="3h")})
    lh = np.full(n, 3.0); la = np.full(n, 2.8)
    rh = rng.poisson(1.10 * lh); ra = rng.poisson(1.10 * la)          # truth runs 10% above the predicted level
    ah, aa = model.level_adjust(fr, lh, la, rh, ra)
    assert abs((ah[-500:] + aa[-500:]).mean() / (lh + la).mean() - 1.10) < 0.03
    assert ah[0] == lh[0]                                              # nothing is known at the first puck drop
    rh2 = rh.copy(); rh2[1500:] = 40                                   # corrupt outcomes from game 1500 on
    ah2, _ = model.level_adjust(fr, lh, la, rh2, ra)
    assert np.allclose(ah[:1501], ah2[:1501])                          # the rate at game 1500 never read game 1500's result
