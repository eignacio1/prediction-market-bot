"""W87.1 Part B: the 86.2/86.3 helpers now live in quant/. Known-answer tests run against the core directly, and
the 12_EXPLORATORY wrappers must expose the very same functions."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

from prediction_market_bot.quant import coherence as C
from prediction_market_bot.quant import dtmc as D
from prediction_market_bot.quant import ladder as L

ROOT = Path(__file__).resolve().parents[1] / "12_EXPLORATORY"


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_parse_ticker_known_answer():
    assert L.parse_ticker("KXNFLSPREAD-26OCT04DENSF-SF8") == ("KXNFLSPREAD-26OCT04DENSF", "SF", 7.5)
    assert L.parse_ticker("KXNFLTOTAL-26OCT04DENSF-44") == ("KXNFLTOTAL-26OCT04DENSF", "", 43.5)
    with pytest.raises(ValueError):
        L.parse_ticker("nodash")


def test_fit_normal_recovers_planted_mu_sigma():
    mu, sg = 3.0, 12.0
    xs = [k - 0.5 for k in range(-10, 17)]
    pts = [(x, float(1 - L.norm.cdf((x - mu) / sg))) for x in xs]
    f = L.fit_normal(pts)
    assert abs(f["mu"] - mu) < 1e-6 and abs(f["sigma"] - sg) < 1e-6
    assert L.fit_normal(pts[:2]) is None


def test_decompose_pure_center_shift():
    x = np.arange(-9.5, 10.5)
    fm, fk = {"mu": 2.0, "sigma": 10.0}, {"mu": 0.0, "sigma": 10.0}
    d = L.decompose(x, L.surv_normal(x, 2.0, 10.0), L.surv_normal(x, 0.0, 10.0), fm, fk)
    assert np.allclose(d["width"], 0.0, atol=1e-12) and np.allclose(d["center"], d["delta_fit"], atol=1e-12)


def test_keynum_pmf_sums_to_one_and_boosts_3():
    p = L.keynum_pmf(0.0, 13.0, 1.5, 1.0)
    assert abs(p.sum() - 1.0) < 1e-12
    assert p[3 + 70] > L.keynum_pmf(0.0, 13.0, 1.0, 1.0)[3 + 70]


def test_coherence_fee_and_planted_monotonic_violation():
    assert C.fee(0.5) == 0.07 * 0.25
    rows = [{"ticker": "KXNFLTOTAL-X-40", "bid": 0.40, "ask": 0.42},
            {"ticker": "KXNFLTOTAL-X-45", "bid": 0.55, "ask": 0.57}]  # hi strike bid 0.55 > lo ask 0.42
    v = C.monotonic("X", "", rows)
    assert len(v) == 1 and abs(v[0]["gross"] - 0.13) < 1e-12


def test_dtmc_estimate_known_answer():
    e = D.estimate([(5, "F"), (5, "C"), (15, "F"), (20, "O")], [10.0])
    assert np.allclose(e["advance"], [0.5, 0.0]) and np.allclose(e["to_F"], [0.25, 1.0])
    assert np.allclose(e["to_C"], [0.25, 0.0]) and np.allclose(e["at_risk"], [4.0, 1.5])


@pytest.mark.parametrize("rel,core,names", [
    ("ladder_implied/ladder.py", L, ["parse_ticker", "survival_points", "fit_normal", "fit_keynum", "decompose"]),
    ("ladder_implied/coherence.py", C, ["monotonic", "exclusive_set", "dominates", "sized"]),
    ("fill_dtmc/dtmc.py", D, ["estimate", "bin_of", "summarise", "cluster_bootstrap"]),
])
def test_exploratory_wrappers_are_the_core_functions(rel, core, names):
    w = _load(rel, "w87_wrap_" + rel.replace("/", "_").replace(".py", ""))
    for n in names:
        assert getattr(w, n) is getattr(core, n)
