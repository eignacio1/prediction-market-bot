"""W77.2: market-side tests -- OLS/bootstrap recovery, de-vig, power injection sanity (12_EXPLORATORY/nfl_engine/market_tests)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np

MT = Path(__file__).resolve().parent.parent / "12_EXPLORATORY" / "nfl_engine" / "market_tests"
sys.path.insert(0, str(MT.parent.parent))


def _load(name):
    sp = importlib.util.spec_from_file_location(name, MT / f"{name}.py")
    m = importlib.util.module_from_spec(sp); sys.modules[name] = m; sp.loader.exec_module(m)
    return m


def test_ols_boot_recovers_known_coefficient_and_ci_covers_it():
    cl = _load("closing_line"); rng = np.random.default_rng(1)
    X = rng.normal(size=(600, 2)); y = 1.0 + 0.8 * X[:, 0] + 0.5 * X[:, 1] + rng.normal(0, 0.5, 600)
    r = cl.boot(X, y, B=200)
    assert abs(r["coef"][0] - 0.8) < 0.1 and r["lo"][1] < 0.5 < r["hi"][1] and r["n"] == 600


def test_devig_sums_to_one_and_orders():
    cl = _load("closing_line")
    assert abs(cl.devig(-150, 130) + cl.devig(130, -150) - 1) < 1e-9
    assert cl.devig(-150, 130) > 0.5 > cl.devig(130, -150)


def test_injection_zero_shift_is_not_detected_and_big_shift_is():
    pw = _load("power"); pw.REPS, pw.B_IN = 40, 100
    rng = np.random.default_rng(2); mu = rng.normal(0, 4, 800)
    assert pw.inject(mu, np.zeros(800), 13.0, 0.0, rng)["p_beats"] <= 0.15
    assert pw.inject(mu, np.full(800, 6.0), 13.0, 0.0, rng)["p_beats"] >= 0.8
