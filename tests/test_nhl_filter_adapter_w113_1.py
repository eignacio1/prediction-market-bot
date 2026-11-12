"""W113.1 Part B: the NHL per-row filter adapter and the NHL rows of the filter-split table.
Applies when: a shadow row on KXNHLGAME / KXNHLSPREAD / KXNHLTOTAL needs its eight filter leaves point-in-time.
Doesn't: it does not choose arms; kept splits come only from the scored table (kept = held-out games >= 10 and net > 0).
Measured (14-day replay 2026-10-30..11-12, 3,147 NHL decisions): 401 NO_BET -> RIDE after kept splits; 1 of 20 kept
leaves survives BH (KXNHLGAME deployment@side away_edge, held-out +0.133, 19 games).
"""
import json
from pathlib import Path

from prediction_market_bot.decision_trees import filter_supply as fs

SPLITS = Path(fs.__file__).with_name("filter_splits.json")


def test_nhl_game_id_known_answers():
    look = {("2027-04-10", "LAK", "VGK"): 7, ("2026-11-12", "NJD", "TBL"): 9}
    assert fs.nhl_game_id("KXNHLGAME-27APR10LAKVGK", look) == 7
    assert fs.nhl_game_id("KXNHLSPREAD-26NOV12NJTB", look) == 9  # two-letter Kalshi codes alias to store codes
    assert fs.nhl_game_id("KXNHLGAME-27APR10ZZZYYY", look) is None
    assert fs.nhl_game_id("garbage", look) is None


def test_adapter_reasons(monkeypatch):
    monkeypatch.setattr(fs, "nhl_filters_for_row", lambda row: None)
    assert fs.nhl_adapter({"event_ticker": "x"})[1] == "filters_unavailable:nhl_game_not_in_store"
    monkeypatch.setattr(fs, "nhl_filters_for_row", lambda row: {"rest@side": "even_rest"})
    assert fs.nhl_adapter({"event_ticker": "x"}) == ({"rest@side": "even_rest"}, None)


def test_nhl_splits_follow_keep_rule():
    nhl = [s for s in json.loads(SPLITS.read_text())["splits"] if s["sport"] == "NHL"]
    assert nhl and {s["series"] for s in nhl} == {"KXNHLGAME", "KXNHLSPREAD", "KXNHLTOTAL"}
    for s in nhl:
        ok = s["arm"] != "NO_BET" and (s["test_games"] or 0) >= 10 and s["test_mean"] is not None and s["test_mean"] > 0
        assert s["kept"] == (ok and s["why"] == "kept")
    assert sum(s["kept"] for s in nhl if s["bh"]) == 1
