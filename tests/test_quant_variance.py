"""W124.1 variance tools: known-answer tests (planted effects, closed forms)."""
import math
import random

import pytest

from prediction_market_bot.quant import variance as V


def test_clustered_mean_known_answer():
    # two games, rows (1, 3) and (5, 7): mean 4; cluster sums of (y - 4) are -4 and +4
    # se = sqrt(G/(G-1) * (16 + 16)) / 4 = sqrt(64) / 4 = 2
    r = V.clustered_mean([1, 3, 5, 7], ["a", "a", "b", "b"])
    assert r["mean"] == 4 and r["se"] == pytest.approx(2.0) and r["n_clusters"] == 2
    # iid rows each their own cluster: CR1 se -> sd / sqrt(n)
    rng = random.Random(1)
    y = [rng.gauss(0, 1) for _ in range(4000)]
    r = V.clustered_mean(y, list(range(4000)))
    assert abs(r["se"] - 1 / math.sqrt(4000)) < 0.003


def test_clustered_se_is_wider_than_naive_when_rows_share_a_game():
    rng = random.Random(2)
    y, g = [], []
    for i in range(200):
        u = rng.gauss(0, 1)
        for _ in range(10):
            y.append(u + rng.gauss(0, 0.3)); g.append(i)
    r = V.clustered_mean(y, g)
    naive = (sum((v - r["mean"]) ** 2 for v in y) / (len(y) - 1)) ** 0.5 / math.sqrt(len(y))
    assert r["se"] > 2.5 * naive


def test_icc_and_design_effect_planted():
    rng = random.Random(3)
    y, g = [], []
    for i in range(1500):  # between sd 1, within sd 1 -> icc 0.5
        u = rng.gauss(0, 1)
        for _ in range(8):
            y.append(u + rng.gauss(0, 1)); g.append(i)
    d = V.design_effect(y, g)
    assert abs(d["icc"] - 0.5) < 0.03
    assert abs(d["deff"] - (1 + 7 * 0.5)) < 0.3
    assert d["n_games"] == 1500 and abs(d["n_eff_rows"] - len(y) / d["deff"]) < 1e-9
    # independent rows: icc ~ 0, deff ~ 1
    y2 = [rng.gauss(0, 1) for _ in range(8000)]
    g2 = [i // 8 for i in range(8000)]
    assert V.design_effect(y2, g2)["deff"] < 1.15
    assert V.icc([1.0], ["a"]) == 0.0


def test_mde_and_games_needed_closed_form():
    z = 1.6448536269514722 + 0.8416212335729143
    assert abs(V.mde_clustered(0.5, 100, 1, 0.0) - z * 0.5 / 10) < 1e-9
    # 10 rows / game, icc 0.5: deff 5.5
    assert abs(V.mde_clustered(0.5, 100, 10, 0.5) - z * 0.5 * math.sqrt(5.5 / 1000)) < 1e-9
    # icc 1: extra rows buy nothing -> same MDE as one row per game
    assert abs(V.mde_clustered(0.5, 100, 10, 1.0) - V.mde_clustered(0.5, 100, 1, 0.0)) < 1e-9
    # round trip
    e = V.mde_clustered(0.5, 400, 6, 0.2)
    assert abs(V.games_needed(0.5, 6, 0.2, e) - 400) < 1e-6
    # two-sided needs more games
    assert V.games_needed(0.5, 1, 0, 0.02, two_sided=True) > V.games_needed(0.5, 1, 0, 0.02)
    assert math.isnan(V.mde_clustered(0.5, 0, 1, 0))


def test_clv_both_sides():
    assert V.clv(0.40, 0.46, "yes") == pytest.approx(0.06)
    # bought NO at 0.55 (so YES mid was 0.45); close YES mid 0.40 -> NO worth 0.60
    assert V.clv(0.55, 0.40, "NO") == pytest.approx(0.05)
    # a NO bought and a YES bought at complementary prices are mirror images
    assert V.clv(0.55, 0.40, "no") == pytest.approx(-V.clv(0.45, 0.40, "yes"))
    with pytest.raises(ValueError):
        V.clv(0.5, 0.5, "maybe")


def test_control_variate_planted():
    rng = random.Random(4)
    n = 6000
    x = [rng.gauss(0, 1) for _ in range(n)]
    y = [0.30 + 2.0 * a + rng.gauss(0, 0.5) for a in x]
    g = [i // 3 for i in range(n)]  # 3 rows per game; rows independent so clustering is harmless
    fit = [i < 2000 for i in range(n)]
    r = V.control_variate(y, x, g, fit, x_mean=0.0)
    assert abs(r["theta"] - 2.0) < 0.05
    assert abs(r["adjusted"]["mean"] - 0.30) < 0.03
    # variance reduction = rho^2 = 4 / 4.25
    assert abs(r["variance_reduction"] - 4.0 / 4.25) < 0.03
    assert r["adjusted"]["hi"] - r["adjusted"]["lo"] < 0.3 * (r["raw"]["hi"] - r["raw"]["lo"])
    # no relationship -> no reduction, theta near zero
    y0 = [0.3 + rng.gauss(0, 0.5) for _ in range(n)]
    r0 = V.control_variate(y0, x, g, fit, x_mean=0.0)
    assert abs(r0["variance_reduction"]) < 0.02


def test_control_variate_theta_uses_fit_rows_only():
    # judged rows carry a different slope; theta must still be the fit slope
    x = [float(i % 7) for i in range(300)]
    y = [2.0 * a if i < 150 else -5.0 * a for i, a in enumerate(x)]
    r = V.control_variate(y, x, list(range(300)), [i < 150 for i in range(300)], x_mean=3.0)
    assert abs(r["theta"] - 2.0) < 1e-9


def test_paired_within_cluster_beats_unpaired():
    rng = random.Random(5)
    rows = []
    for i in range(400):
        u = rng.gauss(0, 1)  # shared game effect
        rows.append((i, u + 0.10 + rng.gauss(0, 0.2), u + rng.gauss(0, 0.2)))
    r = V.paired_within_cluster(rows)
    assert abs(r["mean_diff"] - 0.10) < 0.04
    assert r["lo"] > 0 > r["unpaired_lo"]  # paired excludes zero, unpaired cannot see it
    assert r["variance_reduction"] > 0.9 and r["n_games"] == 400


def test_partial_pool_homogeneous_and_heterogeneous():
    rng = random.Random(6)
    k, se = 30, 0.10
    # homogeneous: all true means 0.2
    cells = {i: (0.2 + rng.gauss(0, se), se) for i in range(k)}
    r = V.partial_pool(cells)
    assert r["tau"] < 0.06 and abs(r["mu"] - 0.2) < 0.05
    assert all(abs(c["shrunk"] - r["mu"]) < abs(c["raw"] - r["mu"]) + 1e-12 for c in r["cells"])
    assert sum(c["B"] for c in r["cells"]) / k > 0.7
    # heterogeneous: true sd 0.5
    cells = {i: (rng.gauss(0, 0.5) + rng.gauss(0, se), se) for i in range(k)}
    r = V.partial_pool(cells)
    assert 0.35 < r["tau"] < 0.7
    assert sum(c["B"] for c in r["cells"]) / k < 0.1
    # a noisy outlier cell is pulled in more than a precise one
    r = V.partial_pool({"a": (0.0, 0.05), "b": (0.0, 0.05), "c": (0.0, 0.05), "noisy": (0.9, 0.5), "precise": (0.9, 0.02)})
    byc = {c["cell"]: c for c in r["cells"]}
    assert byc["noisy"]["B"] > byc["precise"]["B"]
    assert byc["noisy"]["shrunk"] < 0.9
    with pytest.raises(ValueError):
        V.partial_pool({"a": (0.1, 0.1)})
