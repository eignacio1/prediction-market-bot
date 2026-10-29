"""W94.Q known-answer tests: exact per-series fee vs fee_k007 in the recompute helpers."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "12_EXPLORATORY", "quant_w94"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "12_EXPLORATORY"))
import exact_fee_recompute as X  # noqa: E402

from prediction_market_bot.quant.money import fee_k007, fee_rate  # noqa: E402

GRID = [i / 100 for i in range(1, 100)]


@pytest.mark.parametrize("series", ["KXNFLGAME", "KXNFLSPREAD", "KXNFLTOTAL", "KXNBAGAME", "KXNHLGAME"])
def test_multiplier_one_series_equal_k007(series):
    for q in GRID:
        assert X.fee_x(series, q) == pytest.approx(fee_k007(q))


@pytest.mark.parametrize("series", ["KXMLBTOTAL", "KXMLBSPREAD", "KXMLBHIT", "KXMLBF5"])
def test_mlb_prelive_is_half_k007(series):
    for q in GRID:
        assert X.fee_x(series, q) == pytest.approx(0.5 * fee_k007(q))


def test_leg_net_known_answer():
    f = lambda q: 0.01  # noqa: E731
    assert X.leg_net("yes", 1.0, 0.40, 0.42, f) == pytest.approx(1 - 0.42 - 0.01)
    assert X.leg_net("no", 0.0, 0.40, 0.42, f) == pytest.approx(1 - 0.60 - 0.01)
    assert X.leg_net("no", 1.0, 0.40, 0.42, f) == pytest.approx(-0.60 - 0.01)


def test_exact_net_exceeds_k007_net_by_half_fee_for_mlb():
    q = 0.42
    old = X.leg_net("yes", 1.0, 0.40, q, lambda p: fee_k007(p))
    new = X.leg_net("yes", 1.0, 0.40, q, lambda p: X.fee_x("KXMLBTOTAL", p))
    assert new - old == pytest.approx(0.5 * fee_k007(q))


def test_status_change():
    assert X.status_change(0.01, -0.01).startswith("LOST")
    assert X.status_change(-0.01, 0.01).startswith("GAINED")
    assert X.status_change(0.01, 0.02).startswith("none")
