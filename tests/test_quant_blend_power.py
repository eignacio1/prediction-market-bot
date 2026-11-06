"""Known-answer tests for quant/blend_power.py (W105.1)."""
import math
import random

import pytest

from prediction_market_bot.quant import blend_power as bp


def _rows(n_games=60, k=3, seed=1):
    r = random.Random(seed)
    out = []
    for g in range(n_games):
        for j in range(k):
            pm = 0.2 + 0.6 * r.random()
            pe = min(0.98, max(0.02, pm + r.uniform(-0.15, 0.15)))
            out.append((g, pm, pe, 1.0 if r.random() < pm else 0.0))
    return out


def test_single_look_boundary_is_normal_quantile():
    assert bp.gs_boundaries([1.0], 0.05)[0] == pytest.approx(1.6449, abs=1e-3)


def test_null_crossing_equals_alpha_and_obf_shape():
    f = [0.5, 1.0]
    b = bp.gs_boundaries(f, 0.05, "obrien_fleming")
    assert sum(bp._cross_by_look(f, b, 0.0)) == pytest.approx(0.05, abs=1e-6)
    assert b[0] > b[1] > 1.6449 - 1e-6  # early look is far stricter, final is above the fixed-sample value


def test_pocock_is_flatter_than_obf():
    p = bp.gs_boundaries([0.5, 1.0], 0.05, "pocock")
    assert abs(p[0] - p[1]) < 0.05


def test_power_monotone_in_drift_and_matches_fixed_for_one_look():
    b = bp.gs_boundaries([1.0], 0.05)
    assert bp.gs_power([1.0], b, 0.0) == pytest.approx(0.05, abs=1e-3)
    assert bp.gs_power([1.0], b, 2.4865) == pytest.approx(0.80, abs=5e-3)  # 1.645 + 0.842
    assert bp.gs_power([1.0], b, 1.0) < bp.gs_power([1.0], b, 2.0)


def test_games_fixed_sample_formula():
    n = bp.games_fixed_sample(mu=0.1, sigma=1.0)
    assert n == pytest.approx(((1.6449 + 0.8416) / 0.1) ** 2, rel=1e-3)
    assert bp.games_fixed_sample(0.0, 1.0) == math.inf


def test_group_sequential_needs_more_games_than_fixed():
    r = bp.gs_games_needed(0.1, 1.0, [0.5, 1.0])
    assert 1.0 < r["inflation"] < 1.15


def test_score_z_known():
    assert bp.score_z([1.0, 1.0, 1.0, 3.0]) == pytest.approx(1.5 / (1.0 / 2.0), rel=1e-9)
    assert math.isnan(bp.score_z([1.0]))


def test_game_scores_excludes_extreme_pm_and_clusters():
    rows = [("a", 0.5, 0.6, 1), ("a", 0.5, 0.4, 0), ("b", 0.01, 0.5, 1)]
    g = bp.game_scores(rows)
    assert set(g) == {"a"} and g["a"][2] == 2


def test_type_one_error_near_nominal_known_answer():
    """Simulated set with truth = market (w = 0): rejection rate at one-sided 5% is ~5%."""
    rate = bp.simulate_power(_rows(), w=0.0, n_games=60, alpha=0.05, reps=600, seed=3)
    assert 0.02 <= rate <= 0.09


def test_power_rises_with_w_and_games():
    rows = _rows()
    lo = bp.simulate_power(rows, 0.5, 40, reps=300, seed=4)
    hi = bp.simulate_power(rows, 0.5, 400, reps=300, seed=4)
    assert hi > lo and hi > 0.5


def test_effect_positive_for_positive_w_zero_for_null():
    rows = _rows()
    assert bp.effect_and_sd(rows, 0.5, reps=100)["mu"] > 0
    e0 = bp.effect_and_sd(rows, 0.0, reps=300)
    assert abs(e0["mu"]) < 0.3 * e0["sigma"]


def test_w_score_estimate_recovers_truth():
    rows = _rows(n_games=400)
    r = random.Random(9)
    sim = []
    by = {}
    for c, pm, pe, _ in rows:
        by.setdefault(c, []).append((pm, pe))
    for c, lst in by.items():
        u = r.random()
        for pm, pe in lst:
            sim.append((c, pm, pe, 1.0 if u < pm + 0.5 * (pe - pm) else 0.0))
    est = bp.w_score_estimate(bp.game_scores(sim))
    assert 0.2 < est < 0.8


def test_holm_at_look():
    assert bp.holm_at_look([0.001, 0.2, 0.5], 0.03) == [True, False, False]
    assert bp.holm_at_look([0.2, 0.3], 0.05) == [False, False]
