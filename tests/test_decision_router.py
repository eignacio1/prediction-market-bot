from prediction_market_bot.decision_trees.router import (
    FADE, MOMENTUM_FOLLOW, NO_BET, RIDE, Evidence, MomentumCell, RideCell, Situation, Skill, route)


class T:
    def __init__(self, *cells):
        self.c = {(x.family, x.tier, x.bucket, x.book): x for x in cells}

    def lookup(self, f, t, b, k):
        return self.c.get((f, t, b, k))


def sit(**kw):
    d = dict(sport="mlb", family="KXMLBHIT", ticker="X", event="E", tier="T0-2h", yes_bid=0.21, yes_ask=0.23,
             half_spread=0.01)
    d.update(kw)
    return Situation(**d)


CELL = RideCell("KXMLBHIT", "T0-2h", "20-25c", "tight", "yes", 0.017)
GOOD = {("mlb", "KXMLBHIT"): Skill(0.1, 0.002, 500)}
ZERO = {("mlb", "KXMLBHIT"): Skill(0.0018, -0.003, 2037)}


def test_default_is_no_bet():
    assert route(sit(), Evidence()).tree == NO_BET


def test_ride_known_cell():
    r = route(sit(), Evidence(ride=T(CELL)))
    assert (r.tree, r.side) == (RIDE, "yes")


def test_ride_cell_with_nonpositive_lower_bound_gets_nothing():
    bad = RideCell("KXMLBHIT", "T0-2h", "20-25c", "tight", "yes", -0.001)
    assert route(sit(), Evidence(ride=T(bad))).tree == NO_BET


def test_fade_needs_measured_skill():
    assert route(sit(model_p=0.40), Evidence(skill=ZERO)).tree == NO_BET
    r = route(sit(model_p=0.40), Evidence(skill=GOOD))
    assert (r.tree, r.side) == (FADE, "yes")


def test_conflict_is_no_bet():
    r = route(sit(model_p=0.01), Evidence(skill=GOOD, ride=T(CELL)))
    assert r.tree == NO_BET and "conflict" in r.reasons


def test_agreement_routes_to_ride():
    r = route(sit(model_p=0.40), Evidence(skill=GOOD, ride=T(CELL)))
    assert r.tree == RIDE and r.agreed


def test_t3_fade_holds_fade_only():
    assert route(sit(model_p=0.40, t3="FADE"), Evidence(skill=GOOD)).tree == NO_BET
    assert route(sit(model_p=0.40, t3="CONFIRM"), Evidence(skill=GOOD)).tree == FADE
    assert route(sit(t3="FADE"), Evidence(ride=T(CELL))).tree == RIDE


def test_disqualifiers():
    for kw in (dict(yes_bid=None), dict(tier=None), dict(tier="D0"), dict(yes_bid=0.0, yes_ask=0.01)):
        assert route(sit(**kw), Evidence(ride=T(CELL))).tree == NO_BET


def test_momentum_only_with_table():
    assert route(sit(move_1h=0.06), Evidence()).tree == NO_BET
    ev = Evidence(momentum=[MomentumCell(MOMENTUM_FOLLOW, 0.05, 0.01)])
    r = route(sit(move_1h=0.06), ev)
    assert (r.tree, r.side) == (MOMENTUM_FOLLOW, "yes")


def test_no_tree_gets_traffic_without_measurement():
    """Invariant: with empty evidence every situation, however attractive, is NO_BET."""
    for bid in (0.05, 0.21, 0.5, 0.9):
        for mp in (None, 0.01, 0.99):
            assert route(sit(yes_bid=bid, yes_ask=bid + 0.02, model_p=mp, move_1h=0.2), Evidence()).tree == NO_BET
