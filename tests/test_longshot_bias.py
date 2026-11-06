"""W105.6: pot-of-gold measurement helpers. The known-answer test comes first: a planted bias must be recovered."""
import pytest

from prediction_market_bot.quant import longshot_bias as L
from prediction_market_bot.quant.money import fee_rate


def test_buckets_edges_and_gaps():
    assert L.pot_bucket(0.0099) is None and L.pot_bucket(0.01) == "1-5c"
    assert L.pot_bucket(0.05) == "5-10c" and L.pot_bucket(0.149) == "10-15c" and L.pot_bucket(0.15) is None
    assert L.pot_bucket(0.50) is None and L.pot_bucket(0.85) == "85-90c" and L.pot_bucket(0.989) == "95-99c"
    assert L.pot_bucket(0.99) is None


def test_route_sides():
    assert L.route_side(L.FADE_LONGSHOT, 0.08) == "no" and L.route_side(L.FADE_LONGSHOT, 0.92) is None
    assert L.route_side(L.TAKE_FAVOURITE, 0.92) == "yes" and L.route_side(L.TAKE_FAVOURITE, 0.08) is None
    assert L.route_side(L.BUY_LONGSHOT, 0.08) == "yes" and L.route_side(L.BUY_LONGSHOT, 0.92) == "no"
    assert L.route_side(L.FADE_LONGSHOT, 0.5) is None
    with pytest.raises(ValueError):
        L.route_side("NOPE", 0.08)


def test_net_per_contract_uses_quote_and_exact_fee():
    # NO bought at 1 - bid = 0.93, wins when y = 0: 1 - 0.93 - fee(0.93)
    got = L.net_per_contract("KXNHLGAME", "no", 0.0, 0.07, 0.09)
    assert got == pytest.approx(0.07 - fee_rate("KXNHLGAME", 0.93))
    # YES at ask 0.09 loses on y = 0
    assert L.net_per_contract("KXNHLGAME", "yes", 0.0, 0.07, 0.09) == pytest.approx(-0.09 - fee_rate("KXNHLGAME", 0.09))
    # MLB multiplier is lower than NHL's, so the same trade nets more
    assert L.net_per_contract("KXMLBGAME", "yes", 1.0, 0.9, 0.92) > L.net_per_contract("KXNHLGAME", "yes", 1.0, 0.9, 0.92)


def test_known_answer_planted_longshot_bias_recovered_sign_and_size():
    rows = L.simulate_market(6000, bias=0.04, seed=11)  # longshots overpriced by 4c
    ev = L.evaluate_cell(rows, "no")
    assert ev["gap"] == pytest.approx(-0.04, abs=0.012)  # sign negative: settles below price
    assert ev["net_mean"] > 0 and ev["p_one"] < 1e-3  # FADE earns net of fee + spread
    assert ev["net_lo"] > 0
    buy = L.evaluate_cell(rows, "yes")
    assert buy["net_hi"] < 0  # the mirror route loses


def test_known_answer_underpriced_longshot_flips_the_route():
    rows = L.simulate_market(6000, bias=-0.04, seed=12)  # longshots UNDERpriced by 4c
    ev_yes = L.evaluate_cell(rows, "yes")
    assert ev_yes["gap"] == pytest.approx(0.04, abs=0.012)
    assert ev_yes["net_lo"] > 0 and L.evaluate_cell(rows, "no")["net_hi"] < 0


def test_calibrated_market_is_not_flagged_and_false_positive_rate_is_bounded():
    hits = 0
    for s in range(40):
        ev = L.evaluate_cell(L.simulate_market(800, bias=0.0, seed=100 + s), "no", boot=200)
        hits += ev["p_one"] < 0.05
    assert hits <= 8  # one-sided alpha 0.05 over 40 reps; calibrated, and the spread+fee make net negative anyway
    assert L.evaluate_cell(L.simulate_market(3000, 0.0, 5), "no")["net_mean"] < 0


def test_split_is_time_ordered_and_70_30():
    gd = {f"G{i}": f"2026-10-{(i % 28) + 1:02d}" for i in range(100)}
    fit = L.split_games(gd, 0.7)
    assert len(fit) == 70
    assert max(gd[g] for g in fit) <= min(gd[g] for g in gd if g not in fit)


def test_holm():
    assert L.holm_one_sided([0.001, 0.2, 0.04]) == [True, False, False]
    assert L.holm_one_sided([0.004, 0.012, 0.02]) == [True, True, True]


def test_empty_and_single_game_cells_do_not_crash():
    assert L.evaluate_cell([], "no")["n"] == 0
    one = L.simulate_market(3, 0.0, 1)
    for r in one:
        r["game"] = "same"
    assert L.evaluate_cell(one, "no", boot=50)["games"] == 1
