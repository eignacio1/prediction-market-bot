"""Known-answer tests for ladder.py (quant-bar item 1)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ladder as L  # noqa: E402


def _margin_rows(mu, sigma, ks=range(1, 25), team_a="DEN", team_b="SF", half=0.01):
    """Synthetic two-team spread ladder from a known normal margin (A minus B)."""
    rows = []
    for k in ks:
        pa = 1 - L.norm.cdf((k - 0.5 - mu) / sigma)        # A wins by over k-0.5
        pb = L.norm.cdf((-(k - 0.5) - mu) / sigma)         # B wins by over k-0.5
        for team, p in ((team_a, pa), (team_b, pb)):
            rows.append({"ticker": f"KXNFLSPREAD-26OCT04{team_a}{team_b}-{team}{k}",
                         "bid": max(p - half, 0), "ask": min(p + half, 1)})
    return rows


def test_parse_ticker_strike_rule():
    assert L.parse_ticker("KXNFLSPREAD-26OCT04DENSF-SF8") == ("KXNFLSPREAD-26OCT04DENSF", "SF", 7.5)
    assert L.parse_ticker("KXNFLTOTAL-26OCT04DENSF-45") == ("KXNFLTOTAL-26OCT04DENSF", "", 44.5)


def test_parse_ts_five_digit_fraction():
    assert L.parse_ts("2026-10-05T22:59:41.34128Z").second == 41
    assert L.parse_ts("2026-10-05T22:59:41+00:00").tzinfo is not None


def test_margin_fit_recovers_known_mu_sigma():
    rows = _margin_rows(mu=-3.0, sigma=11.0)
    f = L.fit_normal(L.survival_points(rows, "margin"))
    assert abs(f["mu"] - (-3.0)) < 0.15 and abs(f["sigma"] - 11.0) < 0.3


def test_total_fit_recovers_known_mu_sigma():
    rows = []
    for k in range(30, 70):
        p = 1 - L.norm.cdf((k - 0.5 - 47.0) / 9.5)
        rows.append({"ticker": f"KXNFLTOTAL-26OCT04DENSF-{k}", "bid": p - .005, "ask": p + .005})
    f = L.fit_normal(L.survival_points(rows, "total"))
    assert abs(f["mu"] - 47.0) < 0.1 and abs(f["sigma"] - 9.5) < 0.2


def test_fit_rejects_too_few_points_and_flat_ladders():
    assert L.fit_normal([(1.5, 0.5), (2.5, 0.4)]) is None
    assert L.fit_normal([(1.5, 0.5), (2.5, 0.5), (3.5, 0.5), (4.5, 0.5)]) is None


def test_keynum_pmf_normalised_and_recovered():
    p = L.keynum_pmf(0, 13, 1.3, 1.2)
    assert abs(p.sum() - 1) < 1e-12
    # generate ladder from key-number pmf, recover mu/sigma at the true weights
    xs = [k - 0.5 for k in range(-20, 21)]
    S = L.surv_keynum(xs, 2.0, 12.0, 1.3, 1.2)
    pts = [(x, s) for x, s in zip(xs, S)]
    f = L.fit_keynum(pts, 1.3, 1.2)
    assert abs(f["mu"] - 2.0) < 0.1 and abs(f["sigma"] - 12.0) < 0.2 and f["sse"] < 1e-6
    # at the wrong (flat) weights the SSE must be strictly larger
    assert L.fit_keynum(pts, 1.0, 1.0)["sse"] > f["sse"]


def test_decompose_pure_width_and_pure_center():
    x = np.arange(-20.5, 21, 1.0)
    k = {"mu": 0.0, "sigma": 13.0}
    # pure width: same centre, model narrower
    m = {"mu": 0.0, "sigma": 10.0}
    d = L.decompose(x, L.surv_normal(x, **m), L.surv_normal(x, **k), m, k)
    assert np.allclose(d["center"], 0, atol=1e-12) and np.abs(d["width"]).max() > 0.01
    assert np.allclose(d["width"], d["delta_fit"]) and np.abs(d["residual"]).max() < 1e-12
    # pure centre: same width, model shifted
    m = {"mu": 3.0, "sigma": 13.0}
    d = L.decompose(x, L.surv_normal(x, **m), L.surv_normal(x, **k), m, k)
    assert np.allclose(d["width"], 0, atol=1e-12) and np.allclose(d["center"], d["delta_fit"])


def test_decompose_shapley_sums_to_fit_delta():
    x = np.arange(-20.5, 21, 1.0)
    m = {"mu": 2.0, "sigma": 9.0}; k = {"mu": -1.0, "sigma": 14.0}
    d = L.decompose(x, L.surv_normal(x, **m), L.surv_normal(x, **k), m, k)
    assert np.allclose(d["center"] + d["width"], d["delta_fit"])
