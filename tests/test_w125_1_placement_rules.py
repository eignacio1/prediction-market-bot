"""W125.1 Part B: known answers for the measured placement rules. The default switch changes nothing."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from prediction_market_bot.c5_execution.placement import policy as pol  # noqa: E402

RULES = {"rules": {
    "FADE|moneyline|<1h|1c": {"option": "no_place", "reason": "cross -4.1c [-6.0,-2.2], 31 games", "n_games": 31},
    "RIDE|total|*|*": {"option": "cross", "reason": "cross-rest +1.2c [0.3,2.1]", "n_games": 40},
    "RIDE|spread|1-6h|3-5c": {"option": "rest_inside", "reason": "x", "n_games": 12},        # too few games
    "MOMENTUM|spread|1-6h|2c": {"option": "cross", "n_games": 50},                           # no measured reason
}}
TABLE = {"cells": {"FADE": {"best": "rest_inside", "supported": True, "share": 0.5}}}


def go(arm, side="yes", fam="total", h="1-6h", sp="2c", sw="rules", order_key="k", table=None, rules=RULES, bid=0.40, ask=0.42):
    return pol.place_rules(arm, None, side, bid, ask, fam, h, sp, sw, TABLE if table is None else table, rules, order_key)


def test_default_and_unset_are_todays_touch():
    for sw in ("current", "", None, "off", "garbage"):
        p = pol.place_rules("RIDE", None, "yes", 0.40, 0.42, "total", "1-6h", "2c", sw, {"cells": {}}, RULES, "k")
        assert (p.option, p.price_yes) == ("rest_touch", 0.40), sw


def test_on_is_the_existing_table_path():
    a = pol.place_rules("FADE", None, "yes", 0.40, 0.44, "moneyline", "<1h", "1c", "on", TABLE, RULES, "k")
    b = pol.place("FADE", None, "yes", 0.40, 0.44, "on", TABLE, None, "k")
    assert a == b


def test_rule_cross_prices_the_far_touch_both_sides():
    assert go("RIDE") .option == "cross" and go("RIDE").price_yes == 0.42
    n = go("RIDE", side="no")
    assert n.option == "cross" and n.price_yes == 0.40


def test_rule_no_place_and_wildcards():
    p = go("FADE", fam="moneyline", h="<1h", sp="1c", table={"cells": {}})
    assert p.option == "no_place" and p.price_yes is None
    assert go("RIDE", fam="total", h="24h+", sp="6c+").reason == "rule:RIDE|total|*|*"


def test_rule_needs_games_and_a_measured_reason():
    assert go("RIDE", fam="spread", sp="3-5c").option == "rest_touch"
    assert go("MOMENTUM", fam="spread", sp="2c").option == "rest_touch"


def test_w119_3_cell_keeps_its_assignment_over_rules():
    seen = set()
    for i in range(200):
        p = go("FADE", fam="moneyline", h="<1h", sp="1c", order_key=f"o{i}", bid=0.40, ask=0.44)
        seen.add((p.option, p.reason.split(":")[0]))
    assert seen == {("rest_inside", "table"), ("rest_touch", "control")}      # never no_place: the frozen test wins


def test_missing_rules_file_is_touch():
    assert go("RIDE", rules=None).option in ("cross", "rest_touch")   # None loads the shipped (empty) file, so touch
    assert pol.place_rules("RIDE", None, "yes", .4, .42, "total", "1-6h", "2c", "rules", {"cells": {}}, None, "k").option == "rest_touch"
    assert pol.rule_choice("RIDE", "total", "1-6h", "2c", None) == ("rest_touch", "no_rules")


def test_shipped_rules_file_is_empty_until_a_measured_commit():
    r = pol.load_rules()
    assert r is not None and r["rules"] == {}
