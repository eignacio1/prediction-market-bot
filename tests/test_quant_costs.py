"""W106.2 known-answer tests. Published example: Kalshi schedule, 100 contracts at 50c taker = 0.07*100*0.25 = $1.75;
maker coef 0.0175 -> $0.4375 (centicent exact). Source: Kalshi fee schedule PDF 2026-07-07."""
import pytest

from prediction_market_bot.quant import costs as C


def test_taker_fee_published_example():
    assert C.fee_per_contract("KXNFLGAME", 0.50, "taker") == pytest.approx(0.0175)


def test_maker_fee_quarter_of_taker_where_listed():
    # KXNFLGAME maker is not in the table (known gap) -> use a series with a maker multiplier
    from prediction_market_bot.quant.money import fee_multiplier
    s = next(x for x in ("KXMLBGAME", "KXMLBTOTAL", "KXMLBHIT") if fee_multiplier(x, "maker", "live") > 0)
    assert C.fee_per_contract(s, 0.5, "maker", "live") == pytest.approx(C.fee_per_contract(s, 0.5, "taker", "live") / 4, rel=1e-6)


def test_mlb_prelive_half_of_nfl_at_same_price():
    assert C.fee_per_contract("KXMLBTOTAL", 0.40) == pytest.approx(0.5 * C.fee_per_contract("KXNFLTOTAL", 0.40))


def test_taker_entry_cost_known_answer():
    # mid .49 half-spread .01 -> pay .50: .01 + .0175
    assert C.taker_entry_cost("KXNFLGAME", 0.49, 0.01) == pytest.approx(0.0275)


def test_round_trip_is_two_legs():
    rt = C.taker_round_trip_cost("KXNFLGAME", 0.50, 0.01)
    legs = 0.02 + C.fee_per_contract("KXNFLGAME", 0.51) + C.fee_per_contract("KXNFLGAME", 0.49)
    assert rt == pytest.approx(legs)


def test_maker_entry_cost_adds_markout():
    assert C.maker_entry_cost("KXNFLGAME", 0.5, 0.0123) == pytest.approx(C.fee_per_contract("KXNFLGAME", 0.5, "maker") + 0.0123)


def test_k007_overstates_mlb_prelive_by_half():
    assert C.k007_overstatement("KXMLBTOTAL", 0.5) == pytest.approx(0.5 * 0.0175)
    assert C.k007_overstatement("KXNFLTOTAL", 0.5) == pytest.approx(0.0, abs=1e-9)
