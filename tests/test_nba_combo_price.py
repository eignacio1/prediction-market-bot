"""W126.4 Part B known-answer tests: Kalshi combo legs -> engine draws -> joint."""
import numpy as np

from prediction_market_bot.nba_engine.combo_price import parse_leg, price_kalshi_combo
from prediction_market_bot.nba_engine.sgp_price import GameDraws

G = "26NOV24BOSWAS"      # BOS away, WAS home


def _g(n=40000, seed=1):
    r = np.random.default_rng(seed)
    z = r.integers(0, 2, n)                       # common cause for the same player's points and threes
    pts = 10 + 10 * z + r.integers(0, 3, n)
    thr = 1 + 2 * z + r.integers(0, 2, n)
    home, away = 100 + r.integers(0, 20, n), 100 + r.integers(0, 20, n)
    return GameDraws(home, away, {("away", "JTATUM", "points"): pts, ("away", "JTATUM", "threes"): thr,
                                  ("home", "ADAVIS", "rebounds"): r.integers(0, 14, n)})


def test_parse_leg_conventions():
    assert parse_leg(f"KXNBATOTAL-{G}-219", "no").yes is False
    assert (parse_leg(f"KXNBATOTAL-{G}-219", "yes").kind, parse_leg(f"KXNBATOTAL-{G}-219", "yes").line) == ("total", 219.0)
    s = parse_leg(f"KXNBASPREAD-{G}-WAS7", "yes")
    assert (s.kind, s.side, s.line) == ("spread", "home", 7.0)
    p = parse_leg(f"KXNBAPTS-{G}-BOSJTATUM0-25", "yes")
    assert (p.kind, p.side, p.stat, p.player, p.line) == ("player", "away", "points", "JTATUM", 25.0)
    assert parse_leg(f"KXNBAPTSPROT-{G}-BOSJTATUM0-20", "yes").reason == "prot_variant_undefined"
    assert parse_leg(f"KXNBASTL-{G}-BOSJTATUM0-2", "yes").reason == "steals_not_modelled"


def test_independent_legs_reduce_to_product():
    g = _g()
    r = price_kalshi_combo(g, [(f"KXNBAGAME-{G}-WAS", "yes"), (f"KXNBATOTAL-{G}-215", "yes"), (f"KXNBAREB-{G}-WASADAVIS23-7", "yes")])
    assert r["p_all"] is not None and abs(r["p_all"] - r["p_naive"]) < 0.01 and abs(r["lift"] - 1) < 0.05 and not r["flags"]


def test_positively_correlated_pair_prices_above_product_and_is_flagged():
    g = _g()
    r = price_kalshi_combo(g, [(f"KXNBAPTS-{G}-BOSJTATUM0-18", "yes"), (f"KXNBA3PT-{G}-BOSJTATUM0-3", "yes")])
    assert r["p_all"] > r["p_naive"] * 1.3 and "same_player_cross_stat" in r["flags"]


def test_no_side_is_the_complement_and_unpriced_leg_blocks_p_all():
    g = _g()
    y = price_kalshi_combo(g, [(f"KXNBATOTAL-{G}-215", "yes"), (f"KXNBAGAME-{G}-WAS", "yes")])
    n = price_kalshi_combo(g, [(f"KXNBATOTAL-{G}-215", "no"), (f"KXNBAGAME-{G}-WAS", "yes")])
    ml = price_kalshi_combo(g, [(f"KXNBAGAME-{G}-WAS", "yes")])
    assert abs(y["p_all"] + n["p_all"] - ml["p_priced_subset"]) < 1e-9
    u = price_kalshi_combo(g, [(f"KXNBAGAME-{G}-WAS", "yes"), (f"KXNBASTL-{G}-BOSJTATUM0-2", "yes")])
    assert u["p_all"] is None and u["legs_unpriced"][0]["reason"] == "steals_not_modelled" and u["p_priced_subset"] == ml["p_priced_subset"]
