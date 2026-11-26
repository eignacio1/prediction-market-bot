"""W129.7: in-play pricer invariants (EXP-NHLINPLAY-001). Pure functions, no network."""
from prediction_market_bot.c3_forecasting.nhl_inplay import price_state, price_ticker


def _st(sh, sa, ml, strength="EV", ptype="REG"):
    return {"score_h": sh, "score_a": sa, "minutes_left_reg": ml, "strength": strength, "period_type": ptype}


def test_even_game_is_near_half_and_leader_late_is_near_one():
    even = price_state(3.0, 3.0, _st(0, 0, 60.0))
    assert abs(even["game_home"] - 0.5) < 0.05
    late = price_state(3.0, 3.0, _st(3, 0, 2.0))
    assert late["game_home"] > 0.99


def test_power_play_and_empty_net_move_price_the_right_way():
    base = price_state(3.0, 3.0, _st(1, 1, 10.0))["game_home"]
    assert price_state(3.0, 3.0, _st(1, 1, 10.0, "H_PP"))["game_home"] > base
    assert price_state(3.0, 3.0, _st(1, 1, 10.0, "A_PP"))["game_home"] < base


def test_abstains_in_ot_so_and_on_incomplete_state():
    assert price_state(3.0, 3.0, _st(2, 2, 0.0, ptype="OT")) is None
    assert price_state(3.0, 3.0, _st(2, 2, None)) is None
    assert price_state(3.0, 3.0, _st(2, 2, 10.0, strength=None)) is None


def test_total_over_is_one_when_line_already_cleared_and_monotone_in_time():
    t = "KXNHLTOTAL-26NOV25WPGBOS-5"
    done = price_ticker(t, 3.0, 3.0, _st(4, 3, 20.0))
    assert done is not None and done[0] > 0.99
    early = price_ticker(t, 3.0, 3.0, _st(0, 0, 55.0))[0]
    later = price_ticker(t, 3.0, 3.0, _st(0, 0, 10.0))[0]
    assert later < early


def test_probabilities_stay_in_open_unit_interval():
    p = price_ticker("KXNHLGAME-26NOV25WPGBOS-BOS", 3.0, 3.0, _st(5, 0, 0.5))[0]
    assert 0.0 < p < 1.0
