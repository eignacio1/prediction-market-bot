"""W105.5 / B-054: route -> demo order gates. Fixture night: HELD_OUT fires, IN_SAMPLE logs only, gates block."""
from types import SimpleNamespace

import pytest

from prediction_market_bot.decision_trees import ride_orders as ro


class FakeClient:
    def __init__(self):
        self.calls = []

    def submit_order(self, **kw):
        self.calls.append(kw)
        return SimpleNamespace(ok=True, order_id="oid-1", error=None)


def row(status="HELD_OUT", side="no", yes_bid=0.40, yes_ask=0.44, event="EV1", rid="T1|1"):
    return {"decision_id": rid, "ticker": "T1", "event_ticker": event, "route": "RIDE", "side": side,
            "cell_status": status, "yes_bid": yes_bid, "yes_ask": yes_ask}


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(ro.pol, "switch_value", lambda name: "on")
    monkeypatch.setattr(ro, "demo_host_ok", lambda: True)
    monkeypatch.setattr(ro.ksw, "halt_reason", lambda band_name=None: None)
    monkeypatch.setattr(ro.pol, "listing_skip_reason", lambda c, t: None)
    monkeypatch.setattr(ro.pol, "cash_skip_reason", lambda c, s: None)
    monkeypatch.setattr(ro.pol, "schedule_cancel", lambda *a, **k: None)
    monkeypatch.setattr(ro, "feed_exposure_gate", lambda p=None: None)
    return SimpleNamespace(log=tmp_path / "orders.jsonl", client=FakeClient())


def go(env, d, stake=1.0):
    return ro.act(d, env.client, stake_fn=lambda e: stake, log=env.log)


def test_held_out_fires_one_demo_order_at_no_price(env):
    r = go(env, row("HELD_OUT", side="no", yes_bid=0.40, yes_ask=0.44))
    assert r["action"] == ro.ORDER and r["ok"]
    assert len(env.client.calls) == 1
    c = env.client.calls[0]
    assert c["side"] == "no" and c["mid_price"] == 0.40 and c["band"] == ro.KILL_BAND
    assert r["entry_price"] == pytest.approx(0.60)  # NO ask = 1 - yes_bid


def test_yes_buys_at_the_ask(env):
    r = go(env, row("FORWARD_PASSED", side="yes"))
    assert env.client.calls[0]["mid_price"] == 0.44 and r["entry_price"] == 0.44


def test_in_sample_logs_only(env):
    r = go(env, row("IN_SAMPLE"))
    assert r["action"] == ro.PAPER and env.client.calls == []


def test_no_cell_is_paper(env):
    assert go(env, row(None))["action"] == ro.PAPER and env.client.calls == []


def test_switch_off_by_default(env, monkeypatch):
    monkeypatch.setattr(ro.pol, "switch_value", lambda name: "off")
    r = go(env, row())
    assert (r["action"], r["reason"]) == (ro.SKIP, "switch_off") and env.client.calls == []


def test_production_host_refused(env, monkeypatch):
    monkeypatch.setattr(ro, "demo_host_ok", lambda: False)
    assert go(env, row())["reason"] == "production_host_refused" and env.client.calls == []


def test_kill_switch_blocks(env, monkeypatch):
    monkeypatch.setattr(ro.ksw, "halt_reason", lambda band_name=None: "global flag")
    assert go(env, row())["reason"] == "kill_switch_halted" and env.client.calls == []


def test_per_event_cap_blocks(env):
    # earlier days' stake on the same event (event cap 500 outlives the 150/day breaker)
    import json
    with open(env.log, "w") as fh:
        for i in range(5):
            fh.write(json.dumps({"event": ro.ORDER_EVENT, "ok": True, "event_ticker": "EV1", "stake_usd": 99.0,
                                 "ts": f"2026-11-0{i + 1}T12:00:00Z"}) + "\n")
    r = go(env, row(rid="b"), stake=10.0)  # 495 + 10 > 500
    assert r["reason"] == "per_event_cap" and env.client.calls == []


def test_daily_breaker_blocks(env):
    assert go(env, row(event="E1", rid="a"), stake=100.0)["action"] == ro.ORDER
    assert go(env, row(event="E2", rid="b"), stake=45.0)["action"] == ro.ORDER
    r = go(env, row(event="E3", rid="c"), stake=10.0)  # 155 > 15% of 1000
    assert r["reason"] == "daily_breaker" and len(env.client.calls) == 2


def test_listing_skip(env, monkeypatch):
    monkeypatch.setattr(ro.pol, "listing_skip_reason", lambda c, t: "not_open")
    assert go(env, row())["reason"] == "not_open" and env.client.calls == []


def test_client_order_id_is_deterministic(env):
    go(env, row(rid="same"))
    go(env, row(rid="same", event="EV2"))
    ids = [c["client_order_id"] for c in env.client.calls]
    assert ids[0] == ids[1]
