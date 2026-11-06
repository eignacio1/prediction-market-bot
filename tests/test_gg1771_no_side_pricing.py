"""GG-1771 / GG-1770 (W103.4): NO orders are priced in the v2 YES frame; lookup_fill reads action=sell.

Kalshi v2 /portfolio/events/orders: side "bid" = buy YES at ``price``; side "ask" = sell YES at
``price`` == buy NO at ``1 - price``. Before the fix ``submit_order`` posted ``1 - mid`` for NO, so a NO
order meant to cost ``1 - mid`` was placed at a NO cost of ``mid`` (mirror-priced).
"""
import importlib.util
import sys
from pathlib import Path

import pytest

from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient


@pytest.fixture(autouse=True)
def _gate_log_mode(monkeypatch):
    monkeypatch.setenv("EXPOSURE_GATE_MODE", "log")


def _client_capturing():
    client = KalshiMarketClient(api_key_id="x" * 12, private_key="dummy-not-real-key")
    sent = {}

    def fake_post(path, body):
        sent.update(body)
        return True, {"order": {"order_id": "oid-1", "status": "resting"}}

    client._post = fake_post  # type: ignore[method-assign]
    return client, sent


def test_no_order_posts_yes_frame_price_so_no_cost_is_one_minus_mid():
    """The block's reproduction: side="no" at mid_yes 0.395 must cost 0.605 on the NO side."""
    client, sent = _client_capturing()
    order = client.submit_order("KXNHLGAME-26NOV03ANAVAN-VAN", "no", 10.0, 0.395)
    assert order.ok
    assert sent["side"] == "ask"
    posted_yes = float(sent["price"])
    assert abs(posted_yes - 0.395) <= 0.005 + 1e-9, f"YES-frame price should be ~0.395, got {posted_yes}"
    assert abs((1.0 - posted_yes) - 0.605) <= 0.005 + 1e-9  # intended NO cost
    assert order.actual_cost_usd == pytest.approx(order.contracts * (1.0 - posted_yes), abs=1e-3)


def test_yes_order_posts_mid_unchanged():
    client, sent = _client_capturing()
    client.submit_order("KXNHLGAME-26NOV03ANAVAN-VAN", "yes", 10.0, 0.395)
    assert sent["side"] == "bid"
    assert abs(float(sent["price"]) - 0.395) <= 0.005 + 1e-9


@pytest.mark.parametrize("mid", [0.01, 0.07, 0.25, 0.395, 0.50, 0.605, 0.83, 0.97, 0.99])
@pytest.mark.parametrize("side", ["yes", "no"])
def test_every_order_path_round_trips_intended_cost(side, mid):
    """GG-1771 guard: intended own-side cost == own-side price implied by the posted YES-frame price."""
    client, sent = _client_capturing()
    order = client.submit_order("KXMLBGAME-26NOV03AAABBB-AAA", side, 25.0, mid)
    assert order.ok
    posted_yes = float(sent["price"])
    implied_cost = posted_yes if side == "yes" else 1.0 - posted_yes
    intended_cost = mid if side == "yes" else 1.0 - mid
    assert abs(implied_cost - intended_cost) <= 0.005 + 1e-9
    # the reported per-contract own-side cost agrees with the posted price
    assert order.yes_price_cents / 100.0 == pytest.approx(implied_cost, abs=1e-9)


# --- GG-1770: lookup_fill ---------------------------------------------------------------------
def _report_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "demo_fill_forward_report.py"
    spec = importlib.util.spec_from_file_location("demo_fill_forward_report_t", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class _FakeClient:
    def __init__(self, order, result):
        self._order, self._result = order, result

    def _get(self, path, authenticated=False):
        if path.startswith("/portfolio/orders/"):
            return True, {"order": self._order}
        return True, {"market": {"result": self._result, "status": "finalized"}}


def _no_fill_order():
    # shape recorded in GG-1770: order placed as side="no" comes back as action=sell, side=yes
    return {"status": "executed", "action": "sell", "side": "yes", "fill_count_fp": "10.00",
            "yes_price_dollars": "0.60", "no_price_dollars": "0.40",
            "maker_fill_cost_dollars": "4.00", "taker_fill_cost_dollars": "0"}


@pytest.mark.parametrize("result,won", [("no", True), ("yes", False)])
def test_lookup_fill_no_buy_via_sell_action(result, won):
    mod = _report_module()
    rec = mod.lookup_fill(_FakeClient(_no_fill_order(), result), "oid", "T", {})
    assert rec["side"] == "no"
    assert rec["price"] == pytest.approx(0.40)
    assert rec["won"] is won


def test_lookup_fill_plain_yes_buy_unchanged():
    mod = _report_module()
    order = {"status": "executed", "action": "buy", "side": "yes", "fill_count_fp": "5.00",
             "maker_fill_cost_dollars": "2.00"}
    rec = mod.lookup_fill(_FakeClient(order, "yes"), "oid2", "T", {})
    assert rec["side"] == "yes" and rec["won"] is True
