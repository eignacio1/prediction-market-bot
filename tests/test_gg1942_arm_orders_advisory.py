"""GG-1942: ARM_ORDERS is an advisory book in the exposure gate."""
from prediction_market_bot.c4_risk_engine import exposure_gate as xg
from prediction_market_bot.decision_trees import arm_orders


def _state(stake):
    return {"positions": [{"ticker": "KXT-1", "size_usd": stake, "entry_price": 0.5}], "cash": 1000.0,
            "initial_capital": 1000.0}


def test_arm_book_name_is_registered_advisory():
    assert arm_orders.BOOK in xg.BOOKS and xg.BOOKS[arm_orders.BOOK]["advisory"] is True


def test_large_arm_book_does_not_breach(tmp_path, monkeypatch):
    monkeypatch.setenv(xg.MODE_ENV, "enforce")
    st = xg.record_book(arm_orders.BOOK, _state(400.0), (), logs_dir=tmp_path)
    assert st["books"][arm_orders.BOOK]["advisory"] is True
    assert st["breaches"] == []


def test_arm_orders_band_does_not_steal_the_shadow_order_path():
    assert xg.book_for_band(arm_orders.KILL_BAND) == "SHADOW"
