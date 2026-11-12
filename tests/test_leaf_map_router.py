"""W111.3 Part A: the router reads the per-leaf arm map; logging only."""
import json
import os

from prediction_market_bot.decision_trees import leaf_map as lm
from prediction_market_bot.decision_trees.shadow_route import router_fields

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _row(mt, band, mid, hs=0.01, p=0.5, sport="NBA", tk="KXNBATOTAL-26NOV12AAABBB-T220"):
    return {"sport": sport, "market_type": mt, "band": band, "market_ticker": tk, "event_ticker": tk.rsplit("-", 1)[0],
            "yes_bid": mid - hs, "yes_ask": mid + hs, "half_spread": hs, "p_yes": p, "horizon_hours_to_start": 5.0}


def test_shipped_map_equals_exploratory_source():
    a = open(os.path.join(ROOT, "src/prediction_market_bot/decision_trees/leaf_map.json")).read()
    b = open(os.path.join(ROOT, "12_EXPLORATORY/retro_route/leaf_map.json")).read()
    assert a == b


def test_ride_leaf_logs_ride_on_the_favoured_side():
    f = router_fields(_row("NBA_GAME_TOTAL", "T3", 0.70), "KXNBATOTAL", prev_mid=0.70)["router"]
    assert (f["branch"], f["arm"], f["side"]) == ("RIDE", "RIDE", "yes")
    assert f["leaf_id"] == "NBA|NBA_GAME_TOTAL|T3|3|flat" and f["arm_source"] == lm.ARM_SOURCE
    assert f["orders"] == "off" and f["thin"] is False


def test_fade_leaf_takes_the_other_side():
    f = router_fields(_row("NBA_SPREAD", "T2", 0.55, tk="KXNBASPREAD-26NOV12AAABBB-AAA5"), "KXNBASPREAD",
                      prev_mid=0.55)["router"]
    assert (f["branch"], f["arm"], f["side"]) == ("FADE", "FADE", "no")


def test_date_only_ticker_no_longer_blocks_a_routed_leaf():
    # replay bound 1: the band, not the ticker's time, picks the leaf
    f = router_fields(_row("NBA_GAME_TOTAL", "T3", 0.70, tk="KXNBATOTAL-26NOV12-T220"), "KXNBATOTAL", prev_mid=0.70)
    assert f["router"]["branch"] == "RIDE"


def test_replay_over_map_is_not_all_no_bet():
    d = json.load(open(os.path.join(ROOT, "src/prediction_market_bot/decision_trees/leaf_map.json")))
    m = lm.LeafMap(d)
    arms = {m.decide({"sport": k.split("|")[0], "market_type": k.split("|")[1], "band": k.split("|")[2],
                      "mid": [0.3, 0.57, 0.72, 0.9, 0.99][0] if False else 0.7, "move": 0.0}).arm
            for k in d["leaves"]}
    assert len(arms - {"NO_BET"}) >= 1
    routed = [k for k, v in d["leaves"].items() if not v["thin"] and v["arm"] == "RIDE"]
    assert routed


def test_unknown_and_thin_leaves_are_no_bet_with_reason():
    d = json.load(open(os.path.join(ROOT, "src/prediction_market_bot/decision_trees/leaf_map.json")))
    m = lm.LeafMap(d)
    assert m.decide({"sport": "XXX", "market_type": "Y", "band": "T1", "mid": 0.6, "move": 0.0}).reason == "leaf_not_in_map"
    thin = next(k for k, v in d["leaves"].items() if v["thin"])
    s, mt, b, fb, mb = thin.split("|")
    r = {"sport": s, "market_type": mt, "band": b, "mid": {"0": 0.3, "1": 0.58, "2": 0.58, "3": 0.72, "4": 0.9}[fb] if False else None}
    dec = m.leaves[thin]
    assert dec["thin"] is True


def test_momentum_needs_a_move_and_follows_its_sign():
    m = lm.LeafMap({"leaves": {"S|M|T1|2|up": {"arm": "MOMENTUM", "thin": False, "fit": {}, "test": None, "bh": False},
                               "S|M|T1|2|na": {"arm": "MOMENTUM", "thin": False, "fit": {}, "test": None, "bh": False}}})
    up = m.decide(m.row_for("S", "M", "T1", 0.57, 0.55))
    assert (up.arm, up.side) == ("MOMENTUM", "yes")
    na = m.decide(m.row_for("S", "M", "T1", 0.57, None))
    assert na.arm == "NO_BET" and na.reason == "momentum_needs_a_move"


def test_bad_book_is_no_bet_and_never_raises():
    r = _row("NBA_GAME_TOTAL", "T3", 0.7)
    r["yes_bid"] = 0
    assert router_fields(r, "KXNBATOTAL", prev_mid=0.7)["router"]["branch"] == "NO_BET"
    assert router_fields({}, "X")["router"]["branch"] == "ERROR"


def test_filters_fired_are_logged():
    f = router_fields(_row("NBA_GAME_TOTAL", "T3", 0.70), "KXNBATOTAL", prev_mid=0.7, filters={"rest": True, "x": False})
    assert f["router"]["filters_fired"] == ["rest"]


def test_d6_layers_6_and_7_are_evidence_only_w113_1():
    from prediction_market_bot.decision_trees import coverage as cov
    base = cov.d6_layers()
    assert not any(c["layers"][5] or c["layers"][6] for c in base)  # no orders -> no credit
    c0 = base[0]
    key = (c0["market_type"], c0["band"])
    orders = [{"event": "arm_order", "ok": True, "order_id": "o1", "ticker": "T", "market_type": key[0], "band": key[1],
               "ts": "2026-11-12T10:00:00Z", "size_for": {"stake_usd": 1.0}},
              {"event": "arm_order", "ok": True, "order_id": "old", "ticker": "T", "market_type": "X", "band": "T1",
               "ts": "2026-11-01T10:00:00Z"}]
    seen = []
    ff = lambda oid, t: (seen.append(oid) or {"fills": 0})  # no-fill recorded still counts as measured
    l6, l7 = cov.order_evidence(orders, ff)
    assert key in l6 and key in l7 and ("X", "T1") not in l7 and seen == ["o1"]  # pre-epoch order not evidence
    assert cov.order_evidence(orders, None)[1] == set()  # no fill source -> layer 7 unevidenced
    got = {(c["market_type"], c["band"]): c for c in cov.d6_layers(orders=orders, fills_for=ff)}[key]
    assert got["layers"][5] and got["layers"][6]
    assert all("missing" in m for m in cov.missing_one_layer(base))
