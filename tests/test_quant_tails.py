"""Known-answer tests for quant/tails.py (W103.1, B-044)."""
import numpy as np
import pytest
from scipy import stats

from prediction_market_bot.quant import tails


def _gpd_sample(xi, sigma, n, seed):
    return stats.genpareto.rvs(xi, loc=0, scale=sigma, size=n, random_state=np.random.default_rng(seed))


def test_gpd_recovers_shape_and_quantile():
    # Known answer: GPD(xi=0.3, sigma=2) data with u=0 body; fit the whole sample above its own 0.5 quantile.
    x = _gpd_sample(0.3, 2.0, 6000, 1)
    f = tails.pot_fit(x, q=0.5)
    assert f["status"] == "OK"
    assert abs(f["xi"] - 0.3) < 0.08
    true99 = stats.genpareto.ppf(0.99, 0.3, scale=2.0)
    assert abs(tails.var(f, 0.99) - true99) / true99 < 0.12


def test_student_t_tail_index():
    # |t| with 4 df has tail index 1/4 -> xi = 0.25.
    x = np.abs(stats.t.rvs(4, size=8000, random_state=np.random.default_rng(2)))
    f = tails.pot_fit(x, q=0.9)
    assert f["status"] == "OK"
    assert abs(f["xi"] - 0.25) < 0.12
    true99 = stats.t.ppf(1 - 0.01 / 2, 4)
    assert abs(tails.var(f, 0.99) - true99) / true99 < 0.15


def test_light_tail_told_apart_from_heavy():
    rng = np.random.default_rng(3)
    light = np.abs(rng.normal(size=4000))
    heavy = np.abs(stats.t.rvs(3, size=4000, random_state=rng))
    cl, ch = tails.shape_ci(light, q=0.8, n_boot=200), tails.shape_ci(heavy, q=0.8, n_boot=200)
    assert cl["class"] == "light" and cl["hi"] < 0.1
    assert ch["class"] == "heavy" and ch["lo"] > 0.1


def test_too_few_is_not_forced():
    f = tails.pot_fit(np.arange(30.0))
    assert f["status"] == "TOO_FEW"
    assert tails.var(f, 0.99) is None
    assert tails.expected_shortfall(f, 0.99) is None
    assert tails.shape_ci(np.arange(30.0))["class"] == "too_few"
    assert tails.pot_fit([])["status"] == "TOO_FEW"


def test_expected_shortfall_known_answer():
    # Exponential (xi=0): ES_p = VaR_p + sigma.
    x = np.random.default_rng(4).exponential(3.0, 8000)
    f = tails.pot_fit(x, q=0.5)
    assert abs(tails.expected_shortfall(f, 0.99) - (3.0 * np.log(100) + 3.0)) < 1.0
    assert tails.var(f, 0.4) is None  # tail prob 0.6 >= exceedance prob 0.5: inside the body, refused


def test_choose_threshold_stable_on_gpd():
    x = np.abs(_gpd_sample(0.2, 1.0, 5000, 5))
    r = tails.choose_threshold(x)
    assert r["fit"]["status"] == "OK" and r["stable"]
    assert abs(r["fit"]["xi"] - 0.2) < 0.12


def test_mean_excess_linear_for_gpd():
    x = _gpd_sample(0.25, 1.0, 20000, 6)
    us = [0.5, 1.0, 2.0]
    e = tails.mean_excess(x, us)
    # GPD: e(u) = (sigma + xi*u)/(1-xi)
    for u, v in zip(us, e):
        assert abs(v - (1.0 + 0.25 * u) / 0.75) < 0.15
    assert tails.mean_excess([1.0], [5.0]) == [None]


def test_max_drawdown_exact():
    r = np.array([[-0.1, -0.1, 0.2, -0.05]])
    expect = 1 - 0.9 * 0.9  # 19% fall first, recovered peak not exceeded
    assert tails.max_drawdown_frac(r)[0] == pytest.approx(expect)
    assert tails.max_drawdown_frac(np.array([[0.1, 0.1]]))[0] == 0.0


def test_breach_zero_for_riskless_and_certain_for_ruinous():
    gain = np.full(50, 0.01)
    p = tails.breach_probability(gain, 0.05, 100, n_paths=2000, n_outer=20)
    assert p["drawdown_kill"]["p"] == 0.0 and p["daily_breaker"]["p"] == 0.0
    ruin = np.full(50, -1.0)
    p = tails.breach_probability(ruin, 0.5, 5, n_paths=2000, n_outer=20)
    assert p["drawdown_kill"]["p"] == 1.0 and p["daily_breaker"]["p"] == 1.0


def test_breach_rises_with_stake_and_horizon():
    rng = np.random.default_rng(7)
    d = rng.normal(0.0, 1.0, 120)
    kw = dict(n_paths=4000, n_outer=40)
    lo = tails.breach_probability(d, 0.02, 60, **kw)["drawdown_kill"]["p"]
    hi = tails.breach_probability(d, 0.08, 60, **kw)["drawdown_kill"]["p"]
    long_ = tails.breach_probability(d, 0.02, 240, **kw)["drawdown_kill"]["p"]
    assert hi > lo and long_ >= lo


def test_breach_known_answer_random_walk():
    # Symmetric +/-0.1 daily steps, 20% limit, horizon 50: breach prob is the exact random-walk-in-log-space value;
    # check the simulator against an independent brute-force over the same law.
    d = np.array([-1.0, 1.0] * 50)
    p = tails.breach_probability(d, 0.1, 50, n_paths=20000, n_outer=50)["drawdown_kill"]["p"]
    rng = np.random.default_rng(8)
    steps = rng.choice([-0.1, 0.1], size=(20000, 50))
    ref = float((tails.max_drawdown_frac(steps) >= 0.2).mean())
    assert abs(p - ref) < 0.03


def test_stake_for_breach_monotone_and_none_when_drifting_down():
    rng = np.random.default_rng(9)
    d = rng.normal(0.05, 1.0, 150)
    kw = dict(n_paths=3000, n_outer=30)
    s = tails.stake_for_breach(d, 60, target=0.05, **kw)
    assert s is not None and 0 < s < 0.5
    assert tails.breach_probability(d, s * 1.5, 60, **kw)["drawdown_kill"]["p"] >= \
        tails.breach_probability(d, s, 60, **kw)["drawdown_kill"]["p"]
    bad = np.full(40, -0.5)
    assert tails.stake_for_breach(bad, 60, target=0.05, lo=0.05, **kw) is None


def test_tail_smoothed_path_runs():
    x = np.abs(stats.t.rvs(3, size=300, random_state=np.random.default_rng(10)))
    f = tails.pot_fit(x, q=0.8)
    assert f["status"] == "OK"
    p = tails.breach_probability(-x, 0.05, 60, n_paths=2000, n_outer=20, tail_fit=f)
    assert 0.0 <= p["drawdown_kill"]["p"] <= 1.0
