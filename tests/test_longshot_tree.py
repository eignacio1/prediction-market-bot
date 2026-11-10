from prediction_market_bot.decision_trees import longshot as T

C = lambda **k: T.LongshotCell(**{**dict(sport="MLB", family="KXMLBTOTAL", tier="T2-6h", bucket="95-99c", book="all",
                                         route="TAKE_FAVOURITE", side="yes", status="HELD_OUT", net_lo=0.02), **k})


def tab(*cells):
    return T.Table(cells)


def test_orders_only_for_held_out_or_forward_passed():
    for st, ok in (("HELD_OUT", True), ("FORWARD_PASSED", True), ("IN_SAMPLE", False), ("FAILED", False), ("UNTESTED", False)):
        d = T.decide("KXMLBTOTAL", "T2-6h", 0.97, 0.005, tab(C(status=st)))
        assert (d.action == "TAKE_FAVOURITE") is ok and (d.action == "NO_BET") is (not ok)


def test_no_cell_outside_buckets_and_nonpositive_lower_bound():
    assert T.decide("KXMLBTOTAL", "T2-6h", 0.50, 0.005, tab(C())).action == "NO_BET"
    assert T.decide("KXMLBTOTAL", "T6-24h", 0.97, 0.005, tab(C())).action == "NO_BET"
    assert T.decide("KXMLBTOTAL", "T2-6h", 0.97, 0.005, tab(C(net_lo=0.0))).action == "NO_BET"


def test_book_gate_and_side():
    c = C(book="tight", max_half_spread=0.01)
    assert T.decide("KXMLBTOTAL", "T2-6h", 0.97, 0.03, tab(c)).action == "NO_BET"  # wide book, tight-only cell
    d = T.decide("KXMLBTOTAL", "T2-6h", 0.97, 0.005, tab(c))
    assert d.action == "TAKE_FAVOURITE" and d.side == "yes"
    f = C(bucket="5-10c", route="FADE_LONGSHOT", side="no")
    assert T.decide("KXMLBTOTAL", "T2-6h", 0.07, 0.005, tab(f)).side == "no"


def test_shipped_table_loads_and_routes_nothing_today():
    t = T.load()
    assert len(t) > 0 and all(c.status == "IN_SAMPLE" for c in t._c.values())
    for c in t._c.values():
        lo = {"1-5c": 0.03, "5-10c": 0.07, "10-15c": 0.12, "85-90c": 0.87, "90-95c": 0.92, "95-99c": 0.97}[c.bucket]
        assert T.decide(c.family, c.tier, lo, 0.005, t).action == "NO_BET"
