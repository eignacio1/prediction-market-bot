"""W100.2: EXP-042 cell 10 is RETIRED in the ride table and the router never rides it; cells 9 and 11 are untouched."""
from prediction_market_bot.decision_trees import ride


def _cell(t, fam, tier, bkt, book):
    return t.lookup(fam, tier, bkt, book)


def test_cell10_retired_and_others_untouched():
    t = ride.load()
    c10 = _cell(t, "KXMLBTOTAL", "T0-2h", "85-90c", "wide")
    assert c10 is not None and c10.status == "RETIRED"
    assert _cell(t, "KXMLBF5", "T2-6h", "10-15c", "all").status == ride.IN_SAMPLE  # cell 9
    assert _cell(t, "KXMLBF7", "T0-2h", "40-45c", "wide").status == ride.IN_SAMPLE  # cell 11
    assert "RETIRED" not in ride.RIDEABLE


def test_router_returns_none_for_retired_cell():
    t = ride.load()
    d = ride.decide("KXMLBTOTAL", "T0-2h", 0.87, 0.03, t, book_classes=("wide", "all"))
    assert d.action == ride.NONE
    assert "status_RETIRED" in d.reason
