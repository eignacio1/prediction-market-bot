"""Known-answer tests for quant/blend.py (W104.2 / B-049)."""
from __future__ import annotations

import math
import random

import pytest

from prediction_market_bot.quant import blend


def _sig(z: float) -> float:
    return 1 / (1 + math.exp(-z))


def _planted(n_games: int, seed: int, skill: bool):
    """A calibrated market sees signal a. With skill the truth is a+b and the model sees a+b; without it the truth is
    a and the model is independent noise. (A market that is itself over-dispersed would give a pure-noise model a
    small positive w by shrinking it toward the centre - see the module docstring.)"""
    rng = random.Random(seed)
    rows = []
    for g in range(n_games):
        a = rng.gauss(0, 1.0)
        b = rng.gauss(0, 0.8) if skill else 0.0
        pm = _sig(a)
        pe = _sig(a + b) if skill else _sig(rng.gauss(0, 1.0))
        y = 1.0 if rng.random() < _sig(a + b) else 0.0
        for _ in range(2):  # two rows per game cluster, same y
            rows.append((f"g{g}", pm, pe, y))
    return rows


def test_blend_prob_endpoints():
    for form in ("linear", "logit"):
        assert blend.blend_prob(0.3, 0.8, 0.0, form) == pytest.approx(0.3, abs=1e-6)
        assert blend.blend_prob(0.3, 0.8, 1.0, form) == pytest.approx(0.8, abs=1e-6)
    assert blend.blend_prob(0.4, 0.6, 0.5, "linear") == pytest.approx(0.5)
    with pytest.raises(ValueError):
        blend.blend_prob(0.4, 0.6, 0.5, "nope")


def test_model_equal_to_truth_gives_w_one():
    rng = random.Random(1)
    rows = []
    for g in range(400):
        p = rng.uniform(0.1, 0.9)
        y = 1.0 if rng.random() < p else 0.0
        rows.append((f"g{g}", 0.5, p, y))  # market uninformative, model is the truth
    assert blend.fit_w(rows, "linear") > 0.8


def test_planted_skill_recovers_positive_w():
    rows = _planted(600, 7, skill=True)
    for form in ("linear", "logit"):
        r = blend.blend_report(rows, form, b=200)
        assert r["w_hat"] > 0.2
        assert r["w_boot_ci"][0] > 0.0
        assert r["beats_market"] is True


def test_pure_noise_recovers_w_near_zero():
    rows = _planted(600, 11, skill=False)
    for form in ("linear", "logit"):
        r = blend.blend_report(rows, form, b=200)
        assert r["w_hat"] < 0.15
        assert r["beats_market"] is False


def test_model_identical_to_market_is_zero_gain():
    rng = random.Random(3)
    rows = [(f"g{i}", p, p, 1.0 if rng.random() < p else 0.0)
            for i, p in enumerate(rng.uniform(0.2, 0.8) for _ in range(200))]
    r = blend.blend_report(rows, "linear", b=100)
    assert r["oos_gain"] == pytest.approx(0.0, abs=1e-12)
    assert r["beats_market"] is False


def test_shrink_toward_zero():
    assert blend.shrink_toward_zero(0.0, 0.1) == 0.0
    assert blend.shrink_toward_zero(0.1, 0.2) == 0.0       # no larger than its noise
    assert blend.shrink_toward_zero(0.8, 0.01) == pytest.approx(0.8, abs=1e-3)


def test_cv_is_clustered_and_deterministic():
    rows = _planted(60, 5, skill=True)
    a, b = blend.cv_gain(rows, k=5), blend.cv_gain(rows, k=5)
    assert a["fold_w"] == b["fold_w"]
    assert set(a["gain_by_cluster"]) == {f"g{i}" for i in range(60)}


def test_too_few_games():
    assert blend.blend_report([("g0", 0.5, 0.6, 1.0)])["w_hat"] is None
    assert blend.fit_w([]) == 0.0
