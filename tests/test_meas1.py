"""Known-answer tests for 12_EXPLORATORY/edge_location/meas_close/run_meas1.py (W124.2, H-MEAS-1)."""
import importlib.util
import os

import numpy as np

_P = os.path.join(os.path.dirname(__file__), "..", "12_EXPLORATORY", "edge_location", "meas_close", "run_meas1.py")
_spec = importlib.util.spec_from_file_location("run_meas1", _P)
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)


def _rows(games, per, true_fn, seed=3, pop="early"):
    rng = np.random.default_rng(seed)
    out = []
    for g in range(games):
        for k in range(per):
            c = float(rng.uniform(0.06, 0.94))
            y = float(rng.random() < true_fn(c))
            out.append(dict(t=f"t{g}_{k}", sport="NBA", fam="x", game=f"g{g}", pop=pop, c=c, y=y, cost=0.04, e6=None, e24=None))
    return out


def test_calibrated_close_is_licensed():
    v = m.verdict(_rows(2500, 6, lambda c: c), np.random.default_rng(1))
    assert v["verdict"] == "LICENSED" and v["slope_contains_1"] and abs(v["slope"] - 1) < 0.1


def test_calibrated_but_noisy_is_tagged_noise_limited_not_miscalibrated():
    v = m.verdict(_rows(400, 6, lambda c: c), np.random.default_rng(1))  # slope CI holds 1, bucket gap ~ the noise floor
    assert v["slope_contains_1"] and v["verdict"] == "NOT LICENSED" and v["tag"] == "noise_limited"


def test_planted_miscalibration_is_not_licensed():
    v = m.verdict(_rows(400, 6, lambda c: min(max(0.5 + 1.5 * (c - 0.5), 0.0), 1.0)), np.random.default_rng(1))
    assert v["verdict"] == "NOT LICENSED" and not v["slope_contains_1"] and v["slope"] > 1.3


def test_too_few_games_is_underpowered_with_n_needed():
    v = m.verdict(_rows(12, 20, lambda c: c), np.random.default_rng(1))
    assert v["verdict"] == "UNDERPOWERED" and v["games_needed"] > 0


def test_variance_ratio_is_settlement_over_clv_variance():
    rows = _rows(300, 4, lambda c: c)
    rng = np.random.default_rng(5)
    for r in rows:
        r["e6"] = r["c"] - float(rng.normal(0, 0.05))  # CLV = c - e6 has sd 0.05
    v = m.family_stats(rows, np.random.default_rng(2))["varratio_6h"]
    assert abs(v["sd_clv"] - 0.05) < 0.005 and 60 < v["ratio"] < 140  # ~ (0.5 sd of a y-e6)^2 / 0.0025
