"""W116.2 Part B known answers for c5_execution.placement.model: fill rate, the adverse-selection term, and the option choice."""
import math

from prediction_market_bot.c5_execution.placement import model as pm


def _rec(arm, filled, won, price=0.5, placement="rest_touch", spread=0.02, series="KXNBAGAME", sport="nba"):
    return {"arm": arm, "sport": sport, "placement": placement, "price": price, "filled": filled, "won": won,
            "spread": spread, "depth": None, "hours": 2.0, "series": series}


def test_wilson_known_values():
    lo, hi = pm.wilson(5, 10)
    assert math.isclose(lo, 0.2366, abs_tol=1e-4) and math.isclose(hi, 0.7634, abs_tol=1e-4)
    assert pm.wilson(0, 0) == (None, None)
    assert pm.wilson(0, 20)[0] == 0.0


def test_fill_table_counts():
    rs = [_rec("RIDE", i < 12, True) for i in range(40)] + [_rec("FADE", i < 1, False) for i in range(10)]
    t = pm.fill_table(rs)
    assert t["RIDE"] == {"n": 40, "fills": 12, "p_fill": 0.3, **{k: t["RIDE"][k] for k in ("lo", "hi")}}
    assert t["FADE"]["fills"] == 1 and t["FADE"]["p_fill"] == 0.1


def test_planted_adverse_selection_is_recovered():
    # 50 fills winning 20/50 at 0.5 (edge -0.1) vs 50 non-fills winning 35/50 (edge +0.2): selection = -0.3 exactly
    rs = [_rec("MOM", True, i < 20) for i in range(50)] + [_rec("MOM", False, i < 35) for i in range(50)]
    s = pm.selection_table(rs)["MOM"]
    assert s["win_filled"] == 0.4 and s["win_unfilled"] == 0.7
    assert s["edge_filled"] == -0.1 and s["edge_unfilled"] == 0.2 and s["selection"] == -0.3
    assert s["selection_ci"][1] < 0 and s["supported"]


def test_no_selection_when_fills_are_a_random_subset():
    rs = [_rec("RIDE", i % 2 == 0, (i // 2) % 5 < 3) for i in range(200)]
    s = pm.selection_table(rs)["RIDE"]
    assert s["selection"] == 0.0 and s["selection_ci"][0] < 0 < s["selection_ci"][1]


def test_option_choice_rest_touch_wins_when_fills_are_good_and_crossing_pays_the_spread():
    # price 0.5, every order wins 55% -> rest_touch per order = P(fill) * (0.55 - 0.5 - 0 maker fee) = 0.5 * 0.05 = 0.025
    rs = [_rec("RIDE", i % 2 == 0, (i // 2) % 20 < 11) for i in range(400)]
    o = pm.option_table(rs)["RIDE"]
    assert math.isclose(o["rest_touch"]["net"], 0.025, abs_tol=1e-4)
    # cross buys at 0.52 and pays the taker fee: 0.55 - 0.52 - fee_rate(0.52, taker)
    from prediction_market_bot.quant import money
    assert math.isclose(o["cross"]["net"], 0.55 - 0.52 - money.fee_rate("KXNBAGAME", 0.52, "taker"), abs_tol=1e-4)
    assert o["best"] == "rest_touch" and o["no_place"]["net"] == 0.0


def test_option_choice_is_no_place_when_every_option_loses():
    rs = [_rec("FADE", i % 2 == 0, i % 10 < 3) for i in range(200)]  # win 30% at 0.5
    o = pm.option_table(rs)["FADE"]
    assert o["rest_touch"]["net"] < 0 and o["cross"]["net"] < 0 and o["best"] == "no_place"


def test_unsupported_cell_has_no_choice():
    rs = [_rec("POT", i < 3, True, price=0.1) for i in range(10)]
    o = pm.option_table(rs)["POT"]
    assert o["best"] is None and not o["rest_touch"]["supported"]
