from prediction_market_bot.decision_trees.shadow_route import router_fields, tier_for_hours


def _row(**k):
    r = {"sport": "nba", "market_ticker": "KXNBAGAME-26NOV12LALBOS-LAL", "event_ticker": "KXNBAGAME-26NOV12LALBOS",
         "yes_bid": 0.48, "yes_ask": 0.52, "half_spread": 0.02, "p_yes": 0.55, "horizon_hours_to_start": 30.0, "band": "T1"}
    r.update(k)
    return r


def test_tiers():
    assert [tier_for_hours(x) for x in (30, 10, 3, 0.5)] == ["T>24h", "T6-24h", "T2-6h", "T0-2h"]
    assert tier_for_hours(0) is None and tier_for_hours(None) is None


def test_fields_shape_and_orders_off():
    r = router_fields(_row(), "KXNBAGAME")["router"]
    assert r["orders"] == "off" and r["depth"] == "deep" and r["branch"] in {"RIDE", "FADE", "POT_OF_GOLD", "NO_BET"} or r["branch"]
    assert router_fields(_row(band="T3"), "KXNBAGAME")["router"]["depth"] == "shallow"


def test_bad_book_is_no_bet_not_error():
    r = router_fields(_row(yes_bid=0.0), "KXNBAGAME")["router"]
    assert r["branch"] == "NO_BET" and "no_two_sided_book" in r["reason"]


def test_never_raises():
    assert router_fields({}, "X")["router"]["branch"] == "ERROR"
