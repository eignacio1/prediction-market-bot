"""W109.2 -- NHL decision tree by horizon."""
import numpy as np
import pandas as pd
import pytest

from prediction_market_bot.nhl_engine import decision_tree as dt, model


def _frame(n, rng):
    d = {"game_id": np.arange(n), "sec5_h": 3000.0, "lg_f5_h": 2.4, "lg_pp_h": 7.0}
    for s in ("h", "a"):
        d[f"f5_{s}"] = rng.normal(2.4, 0.3, n)
        d[f"a5_{s}"] = 2.4; d[f"pp_{s}"] = 7.0; d[f"pk_{s}"] = 7.0; d[f"ppt_{s}"] = 300.0; d[f"sht_{s}"] = 300.0
        d[f"rest_{s}"] = rng.choice([1.0, 3.0], n); d[f"gs_{s}"] = rng.normal(0, 1, n)
    return pd.DataFrame(d)


def _fit(n=6000, seed=0, rest_eff=-0.15):
    rng = np.random.default_rng(seed)
    fr = _frame(n, rng)
    x = model.side_rows(fr)
    lam = np.exp(0.9 * x["lx"].to_numpy() - 0.6 + 0.1 * x["home"] + rest_eff * x["b2b_own"] - 0.08 * x["gs_opp"].to_numpy())
    rh, ra = rng.poisson(lam[:n]), rng.poisson(lam[n:])
    return fr, rh, ra, model.fit(fr, rh, ra, rng.random(n) < 0.5)


def test_depth_for_horizon_is_monotone_and_bounded():
    hs = [48, 24, 12, 11.9, 6, 3, 2.9, 1, 0.5, 0.49, 0]
    ds = [dt.depth_for_horizon(h) for h in hs]
    assert ds == sorted(ds, reverse=True) and set(ds) == {0, 1, 2, 3}
    assert dt.depth_for_horizon(24) == dt.MAX_DEPTH and dt.depth_for_horizon(0) == 0


def test_full_depth_equals_fitted_rates():
    fr, _, _, m = _fit()
    means = dt.training_means(fr)
    lh, la = dt.rates_at_depth(m, fr.iloc[:200], 3, means)
    mh, ma = m.rates(fr.iloc[:200])
    assert np.allclose(lh, mh) and np.allclose(la, ma)


def test_depth0_is_constant_per_side_and_home_ice_survives():
    fr, _, _, m = _fit()
    means = dt.training_means(fr)
    lh, la = dt.rates_at_depth(m, fr.iloc[:300], 0, means)
    assert np.ptp(lh) < 1e-12 and np.ptp(la) < 1e-12 and lh[0] > la[0]


def test_dropped_level_is_replaced_by_training_mean_not_zero():
    fr, _, _, m = _fit()
    means = dt.training_means(fr)
    sub = fr.iloc[:100]
    lh2, _ = dt.rates_at_depth(m, sub, 2, means)
    x = model.side_rows(sub)
    z = np.exp(m.coef[0] + sum(m.coef[1 + i] * (x[f].to_numpy()[:100] if f in dt.DEPTH_FEATS[2] else means[f])
                               for i, f in enumerate(model.FEATS)))
    assert np.allclose(lh2, z)


def test_known_answer_each_added_level_improves_poisson_loglik_when_truth_uses_it():
    fr, rh, ra, m = _fit(n=20000, seed=5)
    means = dt.training_means(fr)
    y = np.concatenate([rh, ra]).astype(float)
    ll = []
    for d in range(4):
        lh, la = dt.rates_at_depth(m, fr, d, means)
        lam = np.concatenate([lh, la])
        ll.append(float(np.sum(y * np.log(lam) - lam)))
    assert ll[0] < ll[1] < ll[2] < ll[3]


def test_route_and_bad_depth():
    fr, _, _, m = _fit(n=500)
    means = dt.training_means(fr)
    d, lh, la = dt.route(m, fr.iloc[:5], 20.0, means)
    assert d == 3 and lh.shape == (5,)
    assert dt.route(m, fr.iloc[:5], 1.0, means)[0] == 1
    with pytest.raises(ValueError):
        dt.rates_at_depth(m, fr.iloc[:5], 4, means)
