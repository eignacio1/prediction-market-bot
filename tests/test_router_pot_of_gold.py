"""W106.1 / B-056: POT_OF_GOLD branch, precedence (12_EXPLORATORY/pot_of_gold/ROUTER_PRECEDENCE.md), status gate."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "12_EXPLORATORY" / "longshot_bias"))

import run_ride_board as rr  # noqa: E402
from prediction_market_bot.decision_trees import longshot as L, ride  # noqa: E402
from prediction_market_bot.decision_trees.router import (  # noqa: E402
    FADE, MOMENTUM_FOLLOW, NO_BET, POT_OF_GOLD, RIDE, Evidence, MomentumCell, Situation, Skill, route)


def sit(bid=0.96, ask=0.98, **kw):
    d = dict(sport="mlb", family="KXMLBTOTAL", ticker="X", event="E", tier="T2-6h", yes_bid=bid, yes_ask=ask,
             half_spread=0.01)
    d.update(kw)
    return Situation(**d)


def lcell(status="HELD_OUT", side="yes", route_="TAKE_FAVOURITE", bucket="95-99c"):
    return L.LongshotCell(sport="MLB", family="KXMLBTOTAL", tier="T2-6h", bucket=bucket, book="all", route=route_,
                          side=side, status=status, net_lo=0.02)


def ev(*cells, **kw):
    return Evidence(longshot=L.Table(cells), **kw)


class RT:
    def __init__(self, *cells):
        self.c = {(x.family, x.tier, x.bucket, x.book): x for x in cells}

    def lookup(self, f, t, b, k, kind=None):
        return self.c.get((f, t, b, k))


RIDE_YES = ride.RideCell("KXMLBTOTAL", "T2-6h", "95-99c", "tight", "yes", 0.01)
RIDE_NO = ride.RideCell("KXMLBTOTAL", "T2-6h", "95-99c", "tight", "no", 0.01)
GOOD = {("mlb", "KXMLBTOTAL"): Skill(0.1, 0.002, 500)}


def test_each_branch_fires_on_a_fixture():
    r = route(sit(), ev(lcell()))
    assert (r.tree, r.side) == (POT_OF_GOLD, "yes") and r.cell.route == "TAKE_FAVOURITE"
    assert route(sit(), Evidence(ride=RT(RIDE_YES), longshot=L.Table([]))).tree == RIDE
    # FADE: model says YES is worth more than the 0.98 ask -> no edge at 0.97; use a cheap market instead
    f = route(sit(0.20, 0.22, model_p=0.50), Evidence(skill=GOOD, longshot=L.Table([])))
    assert f.tree == FADE
    m = route(sit(0.50, 0.52, move_1h=0.2), Evidence(momentum=[MomentumCell(MOMENTUM_FOLLOW, 0.1, 0.01)],
                                                      longshot=L.Table([])))
    assert m.tree == MOMENTUM_FOLLOW
    assert route(sit(), ev()).tree == NO_BET


def test_in_sample_and_other_statuses_never_route():
    for st in ("IN_SAMPLE", "FAILED", "UNTESTED"):
        r = route(sit(), ev(lcell(status=st)))
        assert r.tree == NO_BET and r.cell is None
    for st in ("HELD_OUT", "FORWARD_PASSED"):
        assert route(sit(), ev(lcell(status=st))).tree == POT_OF_GOLD


def test_precedence_opposite_sides_no_bet():
    r = route(sit(), Evidence(ride=RT(RIDE_NO), longshot=L.Table([lcell(side="yes")])))
    assert r.tree == NO_BET and "conflict" in r.reasons


def test_precedence_same_side_names_ride_then_pot_then_fade():
    r = route(sit(), Evidence(ride=RT(RIDE_YES), longshot=L.Table([lcell(side="yes")])))
    assert r.tree == RIDE and r.agreed and "pot_of_gold_agrees" in r.reasons
    r = route(sit(0.20, 0.22, model_p=0.50), Evidence(skill=GOOD, longshot=L.Table([L.LongshotCell(
        "MLB", "KXMLBTOTAL", "T2-6h", "15-20c", "all", "BUY_LONGSHOT", "yes", "HELD_OUT", 0.02)])))
    assert r.tree == FADE  # 15-20c is outside pot buckets: pot makes no claim


def test_shipped_table_routes_nothing_and_default_unchanged():
    assert route(sit(), Evidence()).tree == NO_BET


def test_runner_logs_pot_of_gold_and_gates_orders(tmp_path):
    from calib import tier
    mk = {"ticker": "A", "event_ticker": "KXMLBTOTAL-26NOV10X", "yes_bid_dollars": "0.96", "yes_ask_dollars": "0.98"}
    now = 1794000000.0
    for st, expect_cell in (("HELD_OUT", "HELD_OUT"), ("IN_SAMPLE", None)):
        d = tmp_path / st
        rr.run({"KXMLBTOTAL": [mk]}, now, ev(lcell(status=st)), lambda e, n: "T2-6h", d,
               archive_dir=tmp_path / "none", place=False)
        row = json.loads((d / "decisions.jsonl").read_text().splitlines()[0])
        assert (row["route"] == POT_OF_GOLD) is (st == "HELD_OUT")
        assert row["cell_status"] == expect_cell
