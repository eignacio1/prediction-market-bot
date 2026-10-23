"""W86.3: the fill-chain estimator recovers a known transition matrix from simulated order lives."""
import importlib.util
from pathlib import Path

import numpy as np

_P = Path(__file__).resolve().parents[1] / "12_EXPLORATORY" / "fill_dtmc" / "dtmc.py"
_spec = importlib.util.spec_from_file_location("fill_dtmc_dtmc", _P)
dtmc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dtmc)

EDGES = [10.0, 60.0, 300.0, 1800.0]
P_F = [0.10, 0.08, 0.06, 0.04, 0.0]
P_C = [0.00, 0.30, 0.20, 0.30, 1.0]
P_ADV = [1 - f - c for f, c in zip(P_F, P_C)]


def test_recovers_known_matrix():
    lives = dtmc.simulate(P_ADV, P_F, P_C, EDGES, n=60000, seed=3)
    est = dtmc.estimate(lives, EDGES)
    assert np.allclose(est["to_F"][:4], P_F[:4], atol=0.01)
    assert np.allclose(est["to_C"][1:4], P_C[1:4], atol=0.015)
    assert np.allclose(est["advance"][:4], P_ADV[:4], atol=0.015)


def test_recovers_hitting_probability_and_time():
    # analytic P(fill) from the known chain
    surv, pf = 1.0, 0.0
    for k in range(5):
        pf += surv * P_F[k]
        surv *= P_ADV[k] if k < 4 else 0.0
    lives = dtmc.simulate(P_ADV, P_F, P_C, EDGES, n=60000, seed=4)
    s = dtmc.summarise(dtmc.estimate(lives, EDGES), EDGES)
    assert abs(s["p_fill"] - pf) < 0.01
    assert abs(s["p_fill"] + s["p_cancel"] - 1.0) < 1e-9


def test_censoring_does_not_bias_early_bins():
    lives = dtmc.simulate(P_ADV, P_F, P_C, EDGES, n=60000, seed=5, censor_rate=1.0)
    est = dtmc.estimate(lives, EDGES)
    assert abs(est["to_F"][0] - P_F[0]) < 0.02


def test_cluster_bootstrap_interval_covers_truth():
    groups = {}
    for g in range(40):
        groups["g%d" % g] = dtmc.simulate(P_ADV, P_F, P_C, EDGES, n=300, seed=100 + g)
    pf = 0.0
    surv = 1.0
    for k in range(5):
        pf += surv * P_F[k]
        surv *= P_ADV[k] if k < 4 else 0.0
    pt, lo, hi = dtmc.cluster_bootstrap(groups, EDGES, lambda s: s["p_fill"], reps=200)
    assert lo <= pf <= hi
