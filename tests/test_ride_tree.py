import dataclasses

from prediction_market_bot.decision_trees import ride
from prediction_market_bot.decision_trees.ride import (
    FAILED, FORWARD_PASSED, HELD_OUT, IN_SAMPLE, LADDER, NONE, RIDE_NO, RIDE_YES, UNTESTED, RideCell, Table, decide)
from prediction_market_bot.decision_trees.router import RIDE, Evidence, Situation, route
from prediction_market_bot.quant.money import fee_k007

BASE = RideCell("KXMLBHIT", "T0-2h", "20-25c", "tight", "yes", 0.017, status=HELD_OUT, net_mean=0.044,
                max_half_spread=0.01)


def d(cell, price=0.22, hs=0.01, books=("tight", "all"), **kw):
    return decide(cell.family, cell.tier, price, hs, Table([cell]), books, **kw)


def test_cell_outside_table_is_none():
    assert d(BASE, price=0.50).action == NONE
    assert decide("KXNOPE", "T0-2h", 0.22, 0.01, Table([BASE]), ("tight",)).action == NONE
    assert decide("KXMLBHIT", "T0-2h", 0.22, 0.01, None).reason == "ride:no_table"


def test_only_held_out_or_forward_passed_ride():
    for st in (IN_SAMPLE, FAILED, UNTESTED):
        r = d(dataclasses.replace(BASE, status=st))
        assert r.action == NONE and r.reason == f"ride:status_{st}"
    for st in (HELD_OUT, FORWARD_PASSED):
        assert d(dataclasses.replace(BASE, status=st)).action == RIDE_YES


def test_held_out_returns_its_side_and_interval():
    r = d(BASE)
    assert (r.action, r.side, r.net_mean, r.net_lo) == (RIDE_YES, "yes", 0.044, 0.017)
    assert d(dataclasses.replace(BASE, side="no")).action == RIDE_NO


def test_nonpositive_lower_bound_is_none():
    assert d(dataclasses.replace(BASE, net_lo=0.0)).action == NONE
    assert d(dataclasses.replace(BASE, net_lo=-0.01)).action == NONE


def test_book_wider_than_cell_is_none():
    assert d(BASE, hs=0.01).action == RIDE_YES
    r = d(BASE, hs=0.02)
    assert r.action == NONE and r.reason == "ride:book_wider_than_cell"
    assert d(BASE, hs=None).action == NONE


def test_kind_filter():
    lad = dataclasses.replace(BASE, kind=LADDER)
    assert d(lad, kind=ride.CALIBRATION).action == NONE
    assert d(lad, kind=LADDER).action == RIDE_YES
    assert d(lad).action == RIDE_YES  # kind None = any


def test_bucket_edges():
    assert ride.bucket(0.22) == "20-25c" and ride.bucket(0.25) == "25-30c" and ride.bucket(0.995) == "99-100c"
    assert ride.bucket(0.03) == "1-5c"


def test_k007_at_the_quote():
    # the table's net is per contract after the fee; the fee is 0.07*q*(1-q), largest at q=0.5
    assert abs(fee_k007(0.5) - 0.0175) < 1e-12 and abs(fee_k007(0.22) - 0.07 * 0.22 * 0.78) < 1e-12


def test_shipped_table_routes_nothing_today():
    t = ride.load()
    cal = [c for c in t.c.values() if c.kind == "CALIBRATION"]
    lad = [c for c in t.c.values() if c.kind == LADDER]
    assert len(t) == 13 and len(cal) == 11 and all(c.status == IN_SAMPLE for c in cal)
    # W92.2: the two W91.2 ladder cells are HELD_OUT, keyed on the gap bin, which no price bucket can reach
    assert len(lad) == 2 and all(c.status == HELD_OUT and c.family == "KXMLBTOTAL" for c in lad)
    for c in cal:
        for tier_price in (0.225, 0.925, 0.075, 0.125, 0.425, 0.875, 0.175):
            r = decide(c.family, c.tier, tier_price, 0.005, t, (c.book, "all"))
            assert r.action == NONE
    s = Situation("mlb", "KXMLBHIT", "X", "E", "T0-2h", 0.21, 0.23, 0.01)
    assert route(s, Evidence(ride=t)).tree != RIDE


def test_router_routes_ride_once_cell_is_held_out():
    held = dataclasses.replace(next(c for c in ride.load().c.values() if c.family == "KXMLBHIT" and c.book == "tight"),
                               status=HELD_OUT)
    s = Situation("mlb", "KXMLBHIT", "X", "E", "T0-2h", 0.21, 0.23, 0.01)
    r = route(s, Evidence(ride=Table([held])))
    assert (r.tree, r.side) == (RIDE, "yes")
