"""W88.1 quant-bar test: known-answer recovery on simulated heavy-tailed losses."""
import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "12_EXPLORATORY" / "tails_evt"))
import gpd  # noqa: E402


def _sim(n, xi=0.3, sigma=1.0, seed=1):
    rng = np.random.default_rng(seed)
    return stats.genpareto.rvs(xi, scale=sigma, size=n, random_state=rng)


def test_return_level_recovers_known_gpd():
    # exact GPD(xi=.3, s=1): 1-in-1000 level is s/xi*((1000)^xi - 1); threshold q=.75 keeps the GPD form.
    x = _sim(20000)
    f = gpd.fit_pot(x, q=0.75)
    truth = (1.0 / 0.3) * ((1000.0) ** 0.3 - 1.0)
    assert f["status"] == "OK"
    assert abs(gpd.return_level(f, 1000) / truth - 1) < 0.2
    assert abs(f["xi"] - 0.3) < 0.07


def test_normal_underestimates_heavy_tail():
    x = _sim(20000, xi=0.4)
    f = gpd.fit_pot(x)
    assert gpd.return_level(f, 1000) > 1.5 * gpd.normal_level(x, 1000)


def test_too_few_exceedances_refuses():
    f = gpd.fit_pot(_sim(40), q=0.75)
    assert f["status"] == "TOO_FEW" and gpd.return_level(f, 100) is None


def test_max_drawdown_known_path():
    p = np.array([[1.0, -2.0, -3.0, 4.0, -1.0]])
    assert gpd.max_drawdown(p)[0] == 5.0


def test_bootstrap_interval_brackets_truth():
    x = _sim(3000, seed=7)
    ci, fail = gpd.cluster_bootstrap_levels(x, ms=(100,), n_boot=300)
    truth = (1.0 / 0.3) * ((100.0) ** 0.3 - 1.0)
    assert ci[100] is not None and ci[100][0] < truth < ci[100][1] and fail < 0.1


def test_sample_tail_model_keeps_tail_probability():
    """Smoothed bootstrap must not inflate P(loss > u): known answer is n_exc / n (here ~25%)."""
    rng = np.random.default_rng(3)
    x = rng.pareto(3.0, 4000)
    f = gpd.fit_pot(x)
    d = gpd.sample_tail_model(x, f, 200000, rng)
    assert abs((d > f["u"]).mean() - f["n_exc"] / f["n"]) < 0.01
