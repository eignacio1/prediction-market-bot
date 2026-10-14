"""GG-666/W72.1: order-write path refuses a non-demo host without an accepted live-capital ADR."""
from unittest.mock import MagicMock, patch

import pytest

from prediction_market_bot.c5_execution import kalshi_client as kc


def _client():
    c = kc.KalshiMarketClient.__new__(kc.KalshiMarketClient)
    c._private_key = object()
    c._key_id = "k"
    c._session = MagicMock()
    return c


@pytest.mark.unit
def test_demo_host_allowed(monkeypatch):
    monkeypatch.setenv("BOT_ENV", "paper")
    assert kc._order_write_host_refusal() is None


@pytest.mark.unit
def test_live_host_refused_post_and_delete(monkeypatch):
    monkeypatch.setenv("BOT_ENV", "live")
    c = _client()
    ok, data = c._post("/portfolio/events/orders", {})
    assert not ok and data["error"] == "host_refused"
    ok, data = c._delete("/portfolio/events/orders/x")
    assert not ok and data["error"] == "host_refused"
    c._session.post.assert_not_called()
    c._session.delete.assert_not_called()


@pytest.mark.unit
def test_unrecognised_env_refused(monkeypatch):
    monkeypatch.setenv("BOT_ENV", "staging")
    assert kc._order_write_host_refusal() is not None


@pytest.mark.unit
def test_live_allowed_only_with_adr_and_matching_env(monkeypatch):
    monkeypatch.setenv("BOT_ENV", "live")
    monkeypatch.setenv("KALSHI_LIVE_CAPITAL_ADR", "ADR-9999")
    assert kc._order_write_host_refusal() is not None  # env alone is not enough
    with patch.object(kc, "LIVE_CAPITAL_ADR", "ADR-9999"):
        assert kc._order_write_host_refusal() is None
    assert kc.LIVE_CAPITAL_ADR is None  # none accepted today
