"""Known-answer tests for 12_EXPLORATORY/edge_location/h2_timing/h2_timing.py (W123.2)."""
import importlib.util
import os
import random

_P = os.path.join(os.path.dirname(__file__), "..", "12_EXPLORATORY", "edge_location", "h2_timing", "h2_timing.py")
_spec = importlib.util.spec_from_file_location("h2_timing", _P)
h2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(h2)


def _planted(slope, n_games=300, per=2, seed=1):
    rng = random.Random(seed)
    rows = []
    for g in range(n_games):
        common = rng.gauss(0, 0.01)  # game-level shock shared by the markets of one game
        for _ in range(per):
            s = rng.gauss(0, 0.05)
            rows.append(("g%d" % g, [1.0, s], slope * s + common + rng.gauss(0, 0.02)))
    return rows


def test_planted_slope_recovered_and_covered():
    b, lo, hi, n, g = h2.ols_cluster(_planted(0.30), 1, random.Random(7), b=400)
    assert lo < 0.30 < hi
    assert abs(b - 0.30) < 0.08
    assert g == 300 and n == 600


def test_null_slope_interval_spans_zero():
    b, lo, hi, _, _ = h2.ols_cluster(_planted(0.0, seed=3), 1, random.Random(7), b=400)
    assert lo < 0.0 < hi


def test_cluster_mean_known():
    groups = {"a": [0.1, 0.1], "b": [0.3], "c": [0.2, 0.2, 0.2]}
    m, lo, hi, n, g = h2.cluster_boot_mean(groups, random.Random(1), b=300)
    assert abs(m - (0.2 + 0.3 + 0.6) / 6) < 1e-12
    assert (n, g) == (6, 3) and lo <= m <= hi


def test_solve_known_system():
    x = h2.solve([[2.0, 1.0], [1.0, 3.0]], [5.0, 10.0])
    assert abs(x[0] - 1.0) < 1e-9 and abs(x[1] - 3.0) < 1e-9
    assert h2.solve([[1.0, 2.0], [2.0, 4.0]], [1.0, 2.0]) is None


def test_ts_epoch_tolerant():
    a = h2.ts_epoch("2026-11-12T00:00:00Z")
    assert h2.ts_epoch("2026-11-12T00:00:00+00:00") == a
    assert abs(h2.ts_epoch("2026-11-12T00:00:00.5Z") - a - 0.5) < 1e-6
    assert abs(h2.ts_epoch("2026-11-12T00:00:00.12345+00:00") - a - 0.12345) < 1e-6
    assert h2.ts_epoch("") is None


def test_buckets_and_fee():
    assert [h2.bucket(x) for x in (0.5, 3, 12, 30, 60)] == ["<1h", "1-6h", "6-24h", "24-48h", "48h+"]
    assert abs(h2.fee(0.5) - 0.0175) < 1e-12
