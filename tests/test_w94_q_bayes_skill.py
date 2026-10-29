"""W94.Q Part C: known-answer tests for the Bayesian skill weight."""
import math
import random

from prediction_market_bot.quant import bayes_skill as bs

BK = 0.20


def _games(n, true_adv, sd, rng):
    return {str(i): [rng.gauss(true_adv, sd)] for i in range(n)}


def test_conjugate_known_answer():
    # prior N(0, .005^2); data mean .01, se .005 -> equal precision -> posterior mean .005, sd .005/sqrt2.
    p = bs.posterior_from_summary(0.01, 0.005, 100, BK)
    assert math.isclose(p.mean, 0.005, rel_tol=1e-9)
    assert math.isclose(p.sd, 0.005 / math.sqrt(2), rel_tol=1e-9)
    assert math.isclose(p.weight, 0.005 / BK, rel_tol=1e-9)


def test_no_data_returns_prior_zero_weight():
    p = bs.posterior({}, BK)
    assert p.n == 0 and p.weight == 0.0 and p.mean == 0.0 and p.p_positive == 0.5


def test_small_true_advantage_earns_weight_as_n_grows():
    w = []
    for n in (100, 1000, 20000):
        w.append(sum(bs.posterior(_games(n, 0.01, 0.10, random.Random(k)), BK).weight for k in range(30)) / 30)
    assert w[0] < w[1] < w[2]
    assert w[2] > 0.04  # truth is .01/.20 = .05; the posterior approaches it


def test_null_model_weight_stays_near_zero_and_does_not_drift_up():
    for n in (200, 2000, 20000):
        ws = [bs.posterior(_games(n, 0.0, 0.10, random.Random(s)), BK).weight for s in range(40)]
        assert sum(ws) / len(ws) < 0.02
        if n == 20000:
            assert max(ws) < 0.03


def test_game_clustering_does_not_inflate_n():
    p = bs.posterior({"a": [0.01] * 50, "b": [0.03] * 50, "c": [0.02] * 50}, BK)
    assert p.n == 3


def test_forward_update_equals_pooled_when_prior_is_batch_posterior():
    rng = random.Random(7)
    a, b = _games(500, 0.01, 0.1, rng), {f"f{i}": v for i, v in enumerate(_games(500, 0.01, 0.1, rng).values())}
    u = bs.update(bs.posterior(a, BK), b, BK)
    assert u.n == 1000 and u.sd < bs.posterior(a, BK).sd


def test_n_for_weight_closed_form_inverts_the_posterior():
    n = bs.n_for_weight(0.01, 0.10, BK, 0.03)
    se = 0.10 / math.sqrt(n)
    p = bs.posterior_from_summary(0.01, se, int(n), BK)
    assert math.isclose(p.weight, 0.03, rel_tol=1e-6)
    assert bs.n_for_weight(0.004, 0.10, BK, 0.03) is None  # ceiling 0.004/0.20 = 0.02 < 0.03
