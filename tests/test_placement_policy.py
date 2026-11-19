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
    # W119.3: inside = the mid when the spread is 2+ ticks, snapped toward our own touch (YES down, NO up); under 2 ticks: None
    assert plc.price_for("rest_inside", "yes", 0.40, 0.45) == 0.42 and plc.price_for("rest_inside", "no", 0.40, 0.45) == 0.43
    assert plc.price_for("rest_inside", "yes", 0.40, 0.42) == 0.41 and plc.price_for("rest_inside", "no", 0.40, 0.42) == 0.41
    assert plc.price_for("rest_inside", "yes", 0.40, 0.43) == 0.41 and plc.price_for("rest_inside", "no", 0.40, 0.43) == 0.42
    assert plc.price_for("rest_inside", "yes", 0.40, 0.44) == plc.price_for("rest_inside", "no", 0.40, 0.44) == 0.42
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
    assert r["placement"] == "rest_inside" and r["price_yes"] == pytest.approx(0.71) and r["placement_reason"] == "table:RIDE|L1"
    s = ao.act(row("FADE", "no"), env.client, log=tmp_path / "f.jsonl")
    assert s["event"] == ao.SKIP_EVENT and "placement_no_place" in str(s)


def test_table_from_clustered_needs_interval_above_zero_and_games():
    from prediction_market_bot.c5_execution.placement import policy as pp
    mk = lambda lo, g: {"cross": {"net": 0.1}, "cross_minus_rest": {"n": 100, "n_games": g, "ci": [lo, 0.3]}}
    t = pp.table_from_clustered({"FADE": mk(-0.03, 20), "RIDE": mk(0.01, 5), "MOMENTUM": mk(0.01, 21)})
    assert list(t["cells"]) == ["MOMENTUM"]  # FADE interval includes 0; RIDE has too few games


def test_frozen_table_file_loads_and_without_a_key_is_all_rest_touch():
    from prediction_market_bot.c5_execution.placement import policy as pp
    t = pp.load_table()
    assert t is not None and set(t["cells"]) == {"FADE"}      # W119.3: the one forward-test cell; W117.1 fit named none
    assert pp.place("FADE", None, "yes", 0.40, 0.44, switch_value="on").option == "rest_touch"  # no order_key: not applied


# ---- W119.3: FADE forward test (share of orders inside the spread, the rest the concurrent rest_touch control) ----
TF = {"cells": {"FADE": {"best": "rest_inside", "supported": True, "share": 0.5, "forward_test": True}}}


def test_shared_cell_splits_deterministically_and_keeps_a_control():
    got = [plc.place("FADE", None, "yes", 0.40, 0.44, "on", table=TF, order_key=f"k{i}") for i in range(400)]
    inside = [p for p in got if p.option == "rest_inside"]
    ctl = [p for p in got if p.option == "rest_touch"]
    assert 140 < len(inside) < 260 and len(inside) + len(ctl) == 400
    assert {p.reason for p in inside} == {"table:FADE"} and {p.reason for p in ctl} == {"control:FADE"}
    assert all(p.price_yes == 0.42 for p in inside) and all(p.price_yes == 0.40 for p in ctl)
    again = plc.place("FADE", None, "yes", 0.40, 0.44, "on", table=TF, order_key="k7")
    assert again.option == got[7].option                     # same key, same side of the split
    assert plc.place("FADE", None, "yes", 0.40, 0.44, "on", table=TF).reason == "control:FADE"  # no key: never applied


def test_shipped_table_names_fade_inside_and_nothing_else():
    t = plc.load_table()
    assert set(t["cells"]) == {"FADE"} and t["cells"]["FADE"]["best"] == "rest_inside" and t["cells"]["FADE"]["share"] == 0.5
    assert plc.place("RIDE", None, "yes", 0.40, 0.44, "on", table=t).option == "rest_touch"
    assert plc.place("MOMENTUM", None, "yes", 0.40, 0.44, "on", table=t).option == "rest_touch"


def test_gg1943_never_cancelled_control_is_not_rest_inside_evidence():
    from prediction_market_bot.c5_execution.placement import model as pm
    base = dict(arm="FADE", sport="nba", series="KXNBAGAME", price=0.40, spread=0.02, filled=True, won=True, ticker="KXNBAGAME-26NOV18AABB-A")
    arm = [{**base, "placement": "rest_inside", "order_id": f"a{i}"} for i in range(35)] + \
          [{**base, "placement": "rest_inside", "order_id": f"u{i}", "filled": False} for i in range(35)]
    ctl = [{**base, "placement": "rest_inside", "order_id": f"c{i}", "cancel_rule": "never"} for i in range(200)]
    only = pm.option_table(arm, ("arm",))["FADE"]["rest_inside"]
    mixed = pm.option_table(arm + ctl, ("arm",))["FADE"]["rest_inside"]
    assert mixed["n"] == only["n"] == 70 and mixed["net"] == only["net"] and only["supported"]
    assert pm.option_table(ctl, ("arm",))["FADE"]["rest_inside"]["n"] == 0
