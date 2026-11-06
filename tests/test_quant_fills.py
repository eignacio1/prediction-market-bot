"""Known-answer tests for quant/fills.py (W104.1, B-048).

Simulated order flow with PLANTED structure: fills depend on distance from mid and depth (not on
noise); informed fills lose after the fill (negative markout) only where the planted feature says so;
and a planted selection effect makes fills win more/less than non-fills so gap_explained must
recover how much is covariate-driven.
"""
import numpy as np

from prediction_market_bot.quant import fills


def _flow(n=20000, seed=3):
    rng = np.random.default_rng(seed)
    dist = rng.uniform(0, 4, n)          # cents from mid; further = harder to fill
    depth = rng.normal(0, 1, n)          # standardised queue depth ahead
    noise = rng.normal(0, 1, n)          # planted irrelevant feature
    return rng, dist, depth, noise


def test_logit_recovers_planted_coefficients_and_ignores_noise():
    rng, dist, depth, noise = _flow()
    true = np.array([0.5, -1.0, -0.6, 0.0])
    X = fills.add_const(np.column_stack([dist, depth, noise]))
    y = (rng.random(len(dist)) < 1 / (1 + np.exp(-(X @ true)))).astype(float)
    f = fills.fit_logit(X, y)
    assert f["converged"]
    assert np.all(np.abs(f["beta"] - true) < 4 * f["se"] + 0.02)
    assert abs(f["beta"][3]) < 3 * f["se"][3]            # noise feature not significant
    p = fills.predict_logit(f, X)
    assert fills.calibration(p, y)["ece"] < 0.02


def test_hazard_with_censoring_recovers_feature_effect():
    rng, dist, depth, _ = _flow(n=8000, seed=5)
    edges = [5, 15, 30, 60]
    base = np.array([-2.8, -2.6, -2.5, -2.4])
    beta = -0.8  # further from mid -> lower hazard
    dur, filled = [], []
    cancel = 60.0                                          # bot cancels at 60s: right-censoring
    for d in dist:
        lo, t, hit = 0.0, None, False
        for a, b in zip(base, edges):
            h = 1 / (1 + np.exp(-(a + beta * d)))
            if rng.random() < h:
                t, hit = rng.uniform(lo, b), True
                break
            lo = b
        dur.append(t if hit else cancel)
        filled.append(hit)
    h = fills.fit_hazard(dur, filled, dist[:, None], edges)
    assert abs(h["beta"][0] - beta) < 4 * h["se"][0] + 0.02
    near = fills.hazard_fill_by(h, np.array([0.5]), 60)
    far = fills.hazard_fill_by(h, np.array([3.5]), 60)
    assert near > far


def test_person_period_censors_correctly():
    oi, ii, ev = fills.person_period([3.0, 20.0, 60.0], [True, True, False], [5, 15, 30, 60])
    # order0 fills in interval 0; order1 fills in interval 2 (rows 0,1,2); order2 censored after 4 intervals
    assert list(ev[oi == 0]) == [1]
    assert list(ev[oi == 1]) == [0, 0, 1]
    assert list(ev[oi == 2]) == [0, 0, 0, 0]


def test_ols_cluster_recovers_planted_markout_driver():
    rng = np.random.default_rng(9)
    n, G = 6000, 300
    game = rng.integers(0, G, n)
    shock = rng.normal(0, 1.0, G)[game]                    # shared within game
    thin = rng.normal(0, 1, n)                             # planted: thin book -> informed -> negative markout
    noise = rng.normal(0, 1, n)
    y = -0.8 * thin + 0.0 * noise + shock + rng.normal(0, 1, n)
    r = fills.ols_cluster(fills.add_const(np.column_stack([thin, noise])), y, game)
    assert abs(r["beta"][1] + 0.8) < 3 * r["se"][1] + 0.02
    assert abs(r["beta"][2]) < 3 * r["se"][2]
    assert r["clusters"] == G


def test_gap_explained_recovers_covariate_share():
    rng = np.random.default_rng(21)
    n = 40000
    x = rng.normal(0, 1, n)
    p_fill = 1 / (1 + np.exp(-(-0.3 + 1.2 * x)))
    filled = rng.random(n) < p_fill
    # win depends on covariate x (selection on observables) and, for fills only, on a hidden term.
    base_win = 1 / (1 + np.exp(-(0.0 + 0.8 * x)))
    win = (rng.random(n) < np.clip(base_win + np.where(filled, -0.05, 0.0), 0.01, 0.99)).astype(float)
    r = fills.gap_explained(win, filled, p_fill)
    # raw gap is positive purely from x; adjusted gap should be ~ -0.05 (the planted hidden effect)
    assert r["raw"] > 0.10
    assert abs(r["adjusted"] - (-0.05)) < 0.02
    assert r["share_explained"] > 1.0                      # covariates explain more than the whole gap


def test_gap_explained_zero_when_fills_are_random():
    rng = np.random.default_rng(2)
    n = 20000
    x = rng.normal(0, 1, n)
    filled = rng.random(n) < 0.4                           # fills independent of everything
    win = (rng.random(n) < 1 / (1 + np.exp(-0.8 * x))).astype(float)
    p = np.full(n, 0.4)
    r = fills.gap_explained(win, filled, p)
    assert abs(r["raw"]) < 0.02 and abs(r["adjusted"]) < 0.02


def test_gap_explained_bootstrap_interval_covers_estimate():
    rng = np.random.default_rng(4)
    n = 6000
    game = rng.integers(0, 150, n)
    x = rng.normal(0, 1, n)
    p_fill = 1 / (1 + np.exp(-(0.2 + 1.0 * x)))
    filled = rng.random(n) < p_fill
    win = (rng.random(n) < 1 / (1 + np.exp(-0.7 * x))).astype(float)
    r = fills.gap_explained(win, filled, p_fill, clusters=game, reps=200)
    lo, hi = r["adjusted_ci90"]
    assert lo <= r["adjusted"] <= hi
    assert r["clusters"] == 150
