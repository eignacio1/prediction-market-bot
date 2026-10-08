"""W59.2 Part C (GG-499): one settled-row schema across NFL / NHL / MLB, normalised at read time, raw rows untouched."""
import copy

from prediction_market_bot.pregame_shadow import settled_schema as ss

NFL = {"market_ticker": "KXNFLGAME-A-DET", "band": "T1", "y": 1.0, "game_key": "KXNFLGAME-A", "p_clim": 0.5, "p_yes": 0.6}
MLB = {"market_ticker": "KXMLBGAME-B-LAD", "band": "T1", "y": 0.0, "game_key": "KXMLBGAME-B", "p_yes": 0.4}
NHL = {"run_id": "r1", "market_ticker": "KXNHLGAME-C-BOS", "band": "T1", "outcome": 1, "p_yes": 0.55, "mid": 0.5}
NHL_LEDGER = {"run_id": "r1", "market_ticker": "KXNHLGAME-C-BOS", "event_ticker": "KXNHLGAME-C", "p_yes": 0.55, "mid": 0.5,
              "yes_bid": 0.49, "yes_ask": 0.51}


def test_three_sports_normalise_to_y_and_game_key():
    n = [ss.normalize(NFL), ss.normalize(MLB), ss.normalize(NHL, NHL_LEDGER)]
    assert [r["y"] for r in n] == [1.0, 0.0, 1.0] and all(isinstance(r["y"], float) for r in n)
    assert [r["game_key"] for r in n] == ["KXNFLGAME-A", "KXMLBGAME-B", "KXNHLGAME-C"]
    assert n[1].get("p_clim") is None and n[2].get("p_clim") is None       # never invented
    assert n[2]["yes_bid"] == 0.49                                          # NHL quotes come from the joined ledger row


def test_raw_rows_are_not_mutated():
    before = [copy.deepcopy(r) for r in (NFL, MLB, NHL, NHL_LEDGER)]
    ss.normalize(NFL); ss.normalize(MLB); ss.normalize(NHL, NHL_LEDGER)
    assert [NFL, MLB, NHL, NHL_LEDGER] == before


def test_zero_and_half_are_settled_none_is_not():
    assert ss.settled_y({"y": 0.0}) == 0.0 and ss.settled_y({"outcome": 0}) == 0.0 and ss.settled_y({"y": 0.5}) == 0.5
    assert ss.settled_y({"y": None, "outcome": None}) is None and ss.settled_y({}) is None
    assert ss.normalize({"y": None, "game_key": "G"}) is None
    assert ss.normalize(NHL) is None                                        # NHL without its ledger row has no game id: not scorable
    assert ss.is_settled({"outcome": 0}) and not ss.is_settled({"market_ticker": "x"})
