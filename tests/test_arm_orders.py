"""W112.3 / B-083: arm -> demo order. Each arm's side, NO BET, kill switch, demo-only, dry run, tags."""
from types import SimpleNamespace

import pytest

from prediction_market_bot.c5_execution import shadow_flat_stake as sfs
from prediction_market_bot.decision_trees import arm_orders as ao


class FakeClient:
    def __init__(self):
        self.calls = []

    def submit_order(self, **kw):
        self.calls.append(kw)
        return SimpleNamespace(ok=True, order_id="oid-1", error=None)


def row(arm="RIDE", side="yes", mid=0.70, branch=None, leaf="L1"):
    return {"run_id": "r1", "market_ticker": "T1", "event_ticker": "EV1", "sport": "nfl", "market_type": "x",
            "band": "T1", "mid": mid, "yes_bid": mid - 0.01, "yes_ask": mid + 0.01,
            "router": {"branch": branch or arm, "arm": arm, "side": side, "leaf_id": leaf, "tier": "T2-6h",
                       "filters_fired": ["rest"], "reason": "leaf_arm:" + str(arm)}}


@pytest.fixture
def env(tmp_path, monkeypatch):
    sw = {"ARM_ORDERS": "on"}
    monkeypatch.setattr(ao.pol, "switch_value", lambda n: sw.get(n))
    monkeypatch.setattr(ao, "demo_host_ok", lambda: True)
    monkeypatch.setattr(ao.ksw, "halt_reason", lambda band_name=None: None)
    monkeypatch.setattr(ao.pol, "listing_skip_reason", lambda c, t: None)
    monkeypatch.setattr(ao.pol, "cash_skip_reason", lambda c, s: None)
    monkeypatch.setattr(ao.pol, "schedule_cancel", lambda *a, **k: None)
    monkeypatch.setattr(ao.pol, "decide", lambda c, t, d, mid, rid: SimpleNamespace(action="SUBMIT", mid_price=mid, reason="ok", meta={}))
    monkeypatch.setattr(ao, "feed_exposure_gate", lambda p=None: None)
    monkeypatch.setattr(ao, "size_for", lambda arm, cell, ctx: 1.0)
    return SimpleNamespace(log=tmp_path / "o.jsonl", client=FakeClient(), sw=sw)


def go(env, r):
    return ao.act(r, env.client, log=env.log)


def test_ride_backs_favourite(env):
    assert go(env, row("RIDE", "yes", 0.70))["event"] == ao.ORDER_EVENT
    assert env.client.calls[0]["side"] == "yes"
    env.client.calls.clear()
    go(env, row("RIDE", "no", 0.30))
    assert env.client.calls[0]["side"] == "no"


def test_fade_backs_other_side(env):
    go(env, row("FADE", "no", 0.70))
    assert env.client.calls[0]["side"] == "no"


def test_ride_fade_router_disagreement_skips(env):
    r = go(env, row("RIDE", "no", 0.70))
    assert r["event"] == ao.SKIP_EVENT and env.client.calls == []


def test_momentum_and_pot_of_gold_follow_router_side(env):
    go(env, row("MOMENTUM", "yes", 0.40, branch="MOMENTUM_FOLLOW"))
    go(env, row("POT_OF_GOLD", "no", 0.10, branch="POT_OF_GOLD"))
    assert [c["side"] for c in env.client.calls] == ["yes", "no"]


def test_no_bet_places_nothing(env):
    r = go(env, row(None, None, branch="NO_BET"))
    assert r["event"] == ao.SKIP_EVENT and r["reason"] == "no_bet" and env.client.calls == []


def test_kill_switch_stops_it(env, monkeypatch):
    monkeypatch.setattr(ao.ksw, "halt_reason", lambda band_name=None: "flag")
    assert go(env, row())["reason"] == "kill_switch_halted" and env.client.calls == []


def test_demo_only(env, monkeypatch):
    monkeypatch.setattr(ao, "demo_host_ok", lambda: False)
    assert go(env, row())["reason"] == "production_host_refused" and env.client.calls == []


def test_off_is_inert(env):
    env.sw["ARM_ORDERS"] = None
    assert go(env, row()) is None and env.client.calls == []


def test_dry_run_logs_would_order_only(env):
    env.sw["ARM_ORDERS"] = "dry"
    r = go(env, row())
    assert r["event"] == ao.WOULD_EVENT and env.client.calls == []


def test_tags(env):
    r = go(env, row("RIDE", "yes", 0.70, leaf="LEAF-7"))
    assert r["arm"] == "RIDE" and r["leaf_id"] == "LEAF-7"
    assert r["adr0072_assignment"] in ("treatment", "control")
    assert r["split_path"]["filters_fired"] == ["rest"]


def test_cap_blocks(env, monkeypatch):
    monkeypatch.setattr(ao, "size_for", lambda *a: 10_000.0)
    assert go(env, row())["reason"] in ("per_event_cap", "daily_breaker") and env.client.calls == []


def test_sizer_hook(env, monkeypatch):
    monkeypatch.undo()  # restore real size_for
    ao.SIZER = lambda arm, cell, ctx: 2.5
    try:
        assert ao.size_for("RIDE", None, {"entry": 0.5}) == 2.5
    finally:
        ao.SIZER = None


def test_maybe_place_on_routed_row_uses_arm_path_only(env, monkeypatch):
    monkeypatch.setattr(sfs, "is_enabled", lambda: True)
    monkeypatch.setattr(sfs, "demo_host_ok", lambda: True)
    monkeypatch.setattr(ao, "order_log_path", lambda: env.log)
    r = row("RIDE", "yes", 0.70)
    r.update(e_net_yes_k007=0.5, e_net_no_k007=0.1)
    sfs.maybe_place(r, env.client)
    assert len(env.client.calls) == 1 and env.client.calls[0]["side"] == "yes"
    assert env.client.calls[0]["client_order_id"] != ""
    env.client.calls.clear()
    nb = row(None, None, branch="NO_BET")
    nb.update(e_net_yes_k007=0.5, e_net_no_k007=0.1)
    assert sfs.maybe_place(nb, env.client) is None and env.client.calls == []
