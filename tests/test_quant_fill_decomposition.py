"""Known-answer tests: synthetic fixtures with a set true split."""
import math

from prediction_market_bot.quant.fill_decomposition import cluster_bootstrap, decompose


def _rows(spec):
    """spec: list of (arm, game, stratum, win, price, count)."""
    out = []
    for arm, g, s, w, p, k in spec:
        out += [(arm, g, s, w - p)] * k
    return out


def test_all_placement():
    # same strata, same mix; treatment pays 0.05 less in each.
    spec = []
    for i, w in enumerate([1.0, 0.0, 1.0, 0.0]):
        spec.append(("control", f"g{i}", f"s{i}", w, 0.50, 10))
        spec.append(("treatment", f"g{i}", f"s{i}", w, 0.45, 10))
    d = decompose(_rows(spec))
    assert math.isclose(d["total"], 0.05)
    assert math.isclose(d["placement"], 0.05)
    assert math.isclose(d["selection"], 0.0, abs_tol=1e-12)
    assert math.isclose(d["unmatched"], 0.0, abs_tol=1e-12)


def test_all_selection():
    # same price in each stratum in both arms; treatment fills only the winner
    # stratum heavily, control fills both equally.
    spec = [
        ("control", "g0", "win", 1.0, 0.50, 10),
        ("control", "g1", "lose", 0.0, 0.50, 10),
        ("treatment", "g0", "win", 1.0, 0.50, 20),
        ("treatment", "g1", "lose", 0.0, 0.50, 0),
    ]
    d = decompose(_rows(spec))
    # mean_T = +0.5, mean_C = 0.0
    assert math.isclose(d["total"], 0.5)
    assert math.isclose(d["placement"], 0.0, abs_tol=1e-12)
    assert math.isclose(d["selection"], 0.5)
    assert math.isclose(d["unmatched"], 0.0, abs_tol=1e-12)


def test_half_half_and_identity():
    spec = [
        ("control", "g0", "win", 1.0, 0.50, 10),
        ("control", "g1", "lose", 0.0, 0.50, 10),
        ("treatment", "g0", "win", 1.0, 0.40, 20),  # placement +0.10 on win stratum
    ]
    d = decompose(_rows(spec))
    # mean_T = 0.6, mean_C = 0.0; control on win stratum = 0.5 -> placement 0.1, selection 0.5
    assert math.isclose(d["placement"], 0.1)
    assert math.isclose(d["selection"], 0.5)
    assert math.isclose(d["total"], d["placement"] + d["selection"] + d["unmatched"])


def test_unmatched_and_skipped():
    spec = [
        ("control", "g0", "a", 1.0, 0.5, 5),
        ("control", "g1", "c", 0.0, 0.4, 5),   # control-only: skipped by waiting
        ("treatment", "g0", "a", 1.0, 0.5, 5),
        ("treatment", "g2", "b", 1.0, 0.3, 5),  # treatment-only
    ]
    d = decompose(_rows(spec))
    assert math.isclose(d["skipped_control"], -0.4)
    assert math.isclose(d["total"], d["placement"] + d["selection"] + d["unmatched"])
    assert d["n_skipped_control"] == 5


def test_bootstrap_recovers_point_inside_interval():
    spec = []
    for i in range(30):
        w = float(i % 2)
        spec.append(("control", f"g{i}", f"s{i}", w, 0.50, 4))
        spec.append(("treatment", f"g{i}", f"s{i}", w, 0.45, 4))
    rows = _rows(spec)
    b = cluster_bootstrap(rows, reps=200, seed=1)
    lo, hi = b["placement"]
    assert math.isclose(lo, 0.05) and math.isclose(hi, 0.05)  # zero variance
    assert b["games"] == 30
