"""Known-answer tests for quant.ride_net (W105.4)."""
import math
from datetime import date, datetime, timezone

from prediction_market_bot.quant.money import fee
from prediction_market_bot.quant.ride_net import net_pnl, phase_for, quote_at, split_games, valid

T = datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc).timestamp()
D = date(2026, 11, 16)


def test_valid():
    assert valid(0.4, 0.5) and not valid(0.5, 0.5) and not valid(None, 0.5) and not valid(0.0, 0.5) and not valid(0.4, 1.0)


def test_phase():
    assert phase_for(T, D) == "live"
    assert phase_for(T - 3 * 86400, D) == "prelive"
    assert phase_for(T, None) == "live"


def test_fade_after_rise_buys_no_exit_known_answer():
    # rise -> FADE buys NO at 1-bid=0.60; exit sells NO at 1-ask(exit)=0.70
    r = net_pnl("KXNFLTOTAL", +1, "FADE", (T, 0.40, 0.42), (T + 3600, 0.28, 0.30), None, D)
    f_in = fee("KXNFLTOTAL", 0.60, 1, "taker", "live")
    f_out = fee("KXNFLTOTAL", 0.70, 1, "taker", "live")
    assert math.isclose(r["entry"], 0.60) and math.isclose(r["half_spread"], 0.01)
    assert math.isclose(r["net60"], 0.70 - 0.60 - f_in - f_out)
    assert "netset" not in r


def test_follow_after_rise_buys_yes_settle():
    r = net_pnl("KXNFLTOTAL", +1, "FOLLOW", (T, 0.40, 0.42), None, 1.0, D)
    assert math.isclose(r["entry"], 0.42)
    assert math.isclose(r["netset"], 1.0 - 0.42 - fee("KXNFLTOTAL", 0.42, 1, "taker", "live"))
    assert "net60" not in r


def test_fade_after_fall_buys_yes_loses_when_no():
    r = net_pnl("KXNFLTOTAL", -1, "FADE", (T, 0.40, 0.42), None, 0.0, D)
    assert r["netset"] < -0.42


def test_invalid_entry_drops_and_bad_exit_skips():
    assert net_pnl("KXNFLTOTAL", 1, "FADE", (T, None, 0.5), None, None, D) is None
    r = net_pnl("KXNFLTOTAL", 1, "FADE", (T, 0.4, 0.42), (T + 3600, 0.5, 0.5), None, D)
    assert "net60" not in r


def test_round_trip_is_negative_with_no_move():
    r = net_pnl("KXNFLTOTAL", 1, "FOLLOW", (T, 0.40, 0.42), (T + 3600, 0.40, 0.42), None, D)
    assert r["net60"] < -0.02  # pays the spread and two fees


def test_quote_at_and_split():
    q = [(0, 0.4, 0.5), (1000, 0.4, 0.5), (3600, 0.3, 0.4)]
    assert quote_at(q, 3500, 200)[0] == 3600 and quote_at(q, 2000, 200) is None
    fit, held = split_games({"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6, "g": 7, "h": 8, "i": 9, "j": 10})
    assert fit == set("abcdefg") and held == set("hij")
