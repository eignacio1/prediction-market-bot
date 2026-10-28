"""W89.5: known-answer tests for the PAM-role-vs-points-prop-price cross (EXPLORATORY)."""
import importlib.util
import math
import sys
from pathlib import Path

D = Path(__file__).resolve().parents[1] / "12_EXPLORATORY/nba_pam_mass_tier"
sys.path[:0] = [str(D), str(D.parent), str(D.parents[1] / "src")]


def _load(name):
    spec = importlib.util.spec_from_file_location(name, D / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


cx, jn = _load("w89_cross"), _load("w89_join")


def _row(candles, tip="2026-10-22T23:00:00Z"):
    return {"candles": candles, "tip_utc": tip}


def test_anchor_first_skips_wide_quotes():
    cx.ANCHOR_MODE = "first"
    r = _row([[1, 0.0, 0.99, 0.5, 1], [2, 0.30, 0.34, 0.3, 1], [3, 0.40, 0.42, 0.4, 1]])
    ts, mid = cx.anchor(r)
    assert ts == 2 and abs(mid - 0.32) < 1e-9


def test_anchor_last_pretip_ignores_post_tip():
    tip = cx._tip(_row([]))
    r = _row([[tip - 60, 0.30, 0.34, 0.3, 1], [tip - 10, 0.40, 0.44, 0.4, 1], [tip + 60, 0.60, 0.62, 0.6, 1]])
    cx.ANCHOR_MODE = "last_pretip"
    try:
        ts, mid = cx.anchor(r)
        assert ts == tip - 10 and abs(mid - 0.42) < 1e-9
        assert cx.anchor(_row([[tip + 5, 0.60, 0.62, 0.6, 1]])) is None
    finally:
        cx.ANCHOR_MODE = "first"


def test_fit_logit_recovers_known_slope():
    xs = [-2 + 4 * i / 399 for i in range(400)]
    ys = [1 if (i * 0.6180339887) % 1 < 1 / (1 + math.exp(-1.5 * x)) else 0 for i, x in enumerate(xs)]
    w = cx.fit_logit([[1, x] for x in xs], ys, l2=0.01)
    assert abs(w[1] - 1.5) < 0.35 and abs(w[0]) < 0.35


def test_two_sided_p_null_is_large_and_shifted_is_small():
    null = {g: [(-1) ** (g + i) * 0.5 for i in range(4)] for g in range(30)}
    shifted = {g: [0.3 + (-1) ** i * 0.05 for i in range(4)] for g in range(30)}
    assert cx.two_sided_p(null, b=500) > 0.5
    assert cx.two_sided_p(shifted, b=500) < 0.01


def test_norm_matches_suffix_and_accent_variants():
    assert jn.norm("Jaren Jackson Jr.") == jn.norm("Jaren Jackson")
    assert jn.norm("Nikola Jokić") == jn.norm("Nikola Jokic")


def test_parse_event():
    d, a, h = jn.parse_event("KXNBAPTS-26OCT26MEMUTA")
    assert (str(d), a, h) == ("2026-10-26", "MEM", "UTA") and jn.parse_event("KXNBAPTS-bad") is None
