"""W116.2 C1: placement policy behind ARM_PLACEMENT_POLICY (default OFF). Known answers."""
from types import SimpleNamespace

import pytest

from prediction_market_bot.c5_execution.placement import policy as plc
from prediction_market_bot.decision_trees import arm_orders as ao
from tests.test_arm_orders import env, go, row  # noqa: F401  (fixture reuse)

T = {"cells": {"RIDE": {"best": "cross", "supported": True}, "RIDE|L1": {"best": "rest_inside", "supported": True},
               "FADE": {"best": "no_place", "supported": True}, "MOMENTUM": {"best": "cross", "supported": False}}}


def test_off_is_todays_touch():
    for v in (None, "", "off", "yes", "raised"):
        p = plc.place("RIDE", "L1", "yes", 0.40, 0.45, v, table=T)
        assert (p.option, p.price_yes, p.reason) == ("rest_touch", 0.40, "switch_off")


def test_prices_in_yes_frame():
    assert plc.price_for("rest_touch", "no", 0.40, 0.45) == 0.45
    assert plc.price_for("cross", "yes", 0.40, 0.45) == 0.45 and plc.price_for("cross", "no", 0.40, 0.45) == 0.40
    assert plc.price_for("rest_inside", "yes", 0.40, 0.45) == 0.41 and plc.price_for("rest_inside", "no", 0.40, 0.45) == 0.44
    assert plc.price_for("rest_inside", "yes", 0.40, 0.41) is None


def test_table_leaf_beats_arm_and_unsupported_stays_touch():
    assert plc.place("RIDE", "L1", "yes", 0.40, 0.45, "on", table=T).option == "rest_inside"
    assert plc.place("RIDE", "L9", "yes", 0.40, 0.45, "on", table=T).option == "cross"
    assert plc.place("MOMENTUM", None, "yes", 0.40, 0.45, "on", table=T).reason == "default_rest_touch"
    p = plc.place("RIDE", "L1", "yes", 0.40, 0.41, "on", table=T)
    assert (p.option, p.reason) == ("rest_touch", "inside_not_room")
    assert plc.place("RIDE", "L1", "yes", 0.40, 0.45, "on", table_path="/nonexistent.json").reason == "no_table"


def _book(monkeypatch):
    meta = {"yes_bid": 0.69, "yes_ask": 0.73}
    monkeypatch.setattr(ao.pol, "decide", lambda c, t, d, mid, rid: SimpleNamespace(action="SUBMIT", mid_price=0.69, reason="ok", meta=meta))


def test_act_off_unchanged(env, monkeypatch):  # noqa: F811
    _book(monkeypatch)
    r = go(env, row())
    assert r["placement"] == "rest_touch" and r["price_yes"] == 0.69 and "placement_reason" not in r


def test_act_on_uses_table_and_no_place_skips(env, monkeypatch, tmp_path):  # noqa: F811
    _book(monkeypatch)
    env.sw[plc.SWITCH_ENV] = "on"
    monkeypatch.setattr(plc, "load_table", lambda path=None: T)
    r = go(env, row())
    assert r["placement"] == "rest_inside" and r["price_yes"] == pytest.approx(0.70) and r["placement_reason"] == "table:RIDE|L1"
    s = ao.act(row("FADE", "no"), env.client, log=tmp_path / "f.jsonl")
    assert s["event"] == ao.SKIP_EVENT and "placement_no_place" in str(s)


def test_table_from_clustered_needs_interval_above_zero_and_games():
    from prediction_market_bot.c5_execution.placement import policy as pp
    mk = lambda lo, g: {"cross": {"net": 0.1}, "cross_minus_rest": {"n": 100, "n_games": g, "ci": [lo, 0.3]}}
    t = pp.table_from_clustered({"FADE": mk(-0.03, 20), "RIDE": mk(0.01, 5), "MOMENTUM": mk(0.01, 21)})
    assert list(t["cells"]) == ["MOMENTUM"]  # FADE interval includes 0; RIDE has too few games


def test_frozen_table_file_loads_and_is_all_rest_touch():
    from prediction_market_bot.c5_execution.placement import policy as pp
    t = pp.load_table()
    assert t is not None and t["cells"] == {}
    assert pp.place("FADE", None, "yes", 0.40, 0.44, switch_value="on").option == "rest_touch"
