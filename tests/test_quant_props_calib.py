from prediction_market_bot.quant.money import fee_k007
from prediction_market_bot.quant.props_calib import (holdout_cell, net_pnl_side, pick_side, simulate_market,
                                                     time_split)


def test_net_pnl_exact():
    assert abs(net_pnl_side("yes", 1.0, 0.48, 0.52) - (1 - 0.52 - fee_k007(0.52))) < 1e-12
    assert abs(net_pnl_side("no", 0.0, 0.48, 0.52) - (1 - 0.52 - fee_k007(0.52))) < 1e-12


def test_time_split_never_splits_a_game():
    rows = simulate_market(100, 3, 0.0)
    fit, hold = time_split(rows, 0.7)
    assert {r["game"] for r in fit}.isdisjoint({r["game"] for r in hold})
    assert len({r["game"] for r in fit}) == 70
    assert max(r["ts"] for r in fit) < min(r["ts"] for r in hold)


def test_known_answer_no_bias_is_negative_net():
    rows = simulate_market(600, 5, 0.0, seed=3)
    fit, hold = time_split(rows)
    c = holdout_cell(fit, hold)
    assert c["net"] < 0 and c["hi"] < 0.01  # spread + fee make a fair market lose


def test_known_answer_planted_edge_recovered():
    rows = simulate_market(600, 5, 0.10, seed=4)  # YES under-priced by 10c
    fit, hold = time_split(rows)
    assert pick_side(fit) == "yes"
    c = holdout_cell(fit, hold)
    assert 0.04 < c["net"] < 0.09 and c["lo"] > 0 and c["p_pos"] < 0.01
