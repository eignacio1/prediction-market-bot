"""W121.2 -- NBA prop splits (EXP-NBAPROPS-001): point-in-time rules, the props candidate, and v1 untouched."""
import json
from datetime import date

import pytest

from prediction_market_bot.decision_trees import leaf_map as lm
from prediction_market_bot.decision_trees import shadow_route as sr
from prediction_market_bot.decision_trees.filters import nba_props as NP
from prediction_market_bot.decision_trees.filters.nba_depth import PITViolation
from prediction_market_bot.quant import retro_route as rr

TK = "KXNBAREB-26NOV20NOPGSW-NOPDQUEEN22-10"


def _mid_for_bin(b):
    for i in range(50, 100):
        m = i / 100
        if rr._bin(m) == b:
            return m
    raise AssertionError(b)


def _row(mid, tk=TK, mt="NBA_PLAYER_REBOUNDS", band="T3"):
    return {"sport": "NBA", "market_type": mt, "band": band, "market_ticker": tk, "event_ticker": tk.rsplit("-", 2)[0],
            "yes_bid": round(mid - 0.01, 2), "yes_ask": round(mid + 0.01, 2), "half_spread": 0.01, "p_yes": 0.5,
            "horizon_hours_to_start": 0.5}


# --- point in time ---
def test_rest_uses_only_a_prior_date():
    assert NP.rest_leaf(date(2026, 11, 19), date(2026, 11, 20)) == "b2b"
    assert NP.rest_leaf(date(2026, 11, 17), date(2026, 11, 20)) == "rested"
    with pytest.raises(PITViolation):
        NP.rest_leaf(date(2026, 11, 20), date(2026, 11, 20))
    with pytest.raises(PITViolation):
        NP.rest_leaf(date(2026, 11, 21), date(2026, 11, 20))


def test_minutes_trend_needs_five_prior_games_and_reads_only_what_it_is_given():
    assert NP.minutes_trend([30, 30, 30, 30]) == "unknown"
    assert NP.minutes_trend([30] * 20) == "flat"
    assert NP.minutes_trend([30] * 20 + [40] * 10) == "up"
    assert NP.minutes_trend([30] * 20 + [20] * 10) == "down"


def test_supply_drops_same_day_and_later_games():
    games = {"g1": {"date": "2026-11-10", "home": "GSW", "away": "NOP"}, "g2": {"date": "2026-11-20", "home": "GSW", "away": "NOP"},
             "g3": {"date": "2026-11-22", "home": "GSW", "away": "LAL"}}
    pl = {("NOP", "Dalen Queen"): [("2026-11-%02d" % d, {"min": 30.0}) for d in range(1, 10)] + [("2026-11-20", {"min": 99.0}),
                                                                                                 ("2026-11-22", {"min": 99.0})]}
    prof = json.load(open("12_EXPLORATORY/nba_depth_splits/profiles.json"))
    leaves = NP.make_props_supply(games, pl, prof)({"market_ticker": TK, "ts_utc": "2026-11-20T23:00:00+00:00"})
    assert leaves["minutes_trend@player"] == "flat"      # the 99-minute game on/after the game day never entered
    assert leaves["rest@player"] == "rested"             # previous game is 11-10, not 11-20 or 11-22


def test_supply_never_raises():
    assert NP.make_props_supply({}, {}, {})({"market_ticker": "junk"}) is None


def test_prior_season_rule_is_enforced():
    prof = json.load(open("12_EXPLORATORY/nba_depth_splits/profiles.json"))
    kw = dict(team="NOP", opp="GSW", home="GSW", away="NOP", stat="points", prior_minutes=[], prev_game=None, game_day=date(2026, 11, 20))
    NP.prop_filters(prof=prof, row_season=int(prof["season"]) + 1, **kw)
    with pytest.raises(PITViolation):
        NP.prop_filters(prof=prof, row_season=int(prof["season"]), **kw)


# --- the candidate ---
def test_prop_candidate_applies_to_prop_rows_only_and_v1_is_identical(monkeypatch):
    monkeypatch.setenv("PM_CANDIDATE_ARMS", "off")
    off = sr.router_fields(_row(0.6), "KXNBAREB", prev_mid=0.6)["router"]
    monkeypatch.setenv("PM_CANDIDATE_ARMS", "on")
    on = sr.router_fields(_row(0.6), "KXNBAREB", prev_mid=0.6, props={"rest@player": "normal"})
    assert on["router"] == off
    assert "nba_props" in on["router_candidates"]
    game = sr.router_fields(_row(0.6, tk="KXNBATOTAL-26NOV20NOPGSW-T220", mt="NBA_GAME_TOTAL"), "KXNBATOTAL", prev_mid=0.6)
    assert "nba_props" not in game["router_candidates"]
    json.dumps(on)


def test_kept_split_moves_the_candidate_arm_and_logs_earned(monkeypatch):
    monkeypatch.setenv("PM_CANDIDATE_ARMS", "on")
    doc = json.load(open(lm.MAP_VERSIONS["nba_props"]))
    k = next(s for s in doc["splits"] if s["kept"] and s["earned"])
    sport, mt, band, favbin, mv = k["leaf"].split("|")
    row = _row(_mid_for_bin(int(favbin)), mt=mt, band=band)
    sr._cand_ev.cache_clear()
    sr._SEEN.clear()   # an earlier call in this process would otherwise supply a previous mid and change the move bin
    rec = sr.router_fields(row, "KXNBAREB", prev_mid=None, props={k["split"]: k["split_leaf"]})["router_candidates"]["nba_props"]
    assert rec["leaf_id"] == k["leaf"], rec
    assert rec["prop_split_applied"] and rec["arm"] != "ERROR"
    assert rec["prop_split_kept"] == [f"{k['split']}={k['split_leaf']}->{k['arm']}"]
    assert rec["prop_split_earned"] == [f"{k['split']}={k['split_leaf']}"]
    unfired = sr.router_fields(row, "KXNBAREB", prev_mid=None, props={k["split"]: "unknown"})["router_candidates"]["nba_props"]
    assert not unfired["prop_split_applied"]


def test_conflicting_kept_splits_change_nothing():
    ps = lm.PropSplits({"splits": [
        {"leaf": "L", "split": "a", "split_leaf": "x", "arm": "RIDE", "kept": True, "earned": False},
        {"leaf": "L", "split": "b", "split_leaf": "y", "arm": "FADE", "kept": True, "earned": True}]})
    r = ps.lookup("L", {"a": "x", "b": "y"})
    assert r["arm"] is None and r["conflict"]


def test_only_kept_entries_are_indexed_and_stumps_are_logged():
    ps = lm.PropSplits({"splits": [
        {"leaf": "L", "split": "a", "split_leaf": "x", "arm": "NO_BET", "kept": False, "earned": False}]})
    r = ps.lookup("L", {"a": "x"})
    assert r["arm"] is None and r["logged_only"] == ["a=x"]


def test_map_file_is_consistent_with_results():
    doc = json.load(open(lm.MAP_VERSIONS["nba_props"]))
    assert doc["n_kept"] == sum(s["kept"] for s in doc["splits"]) and doc["n_earned"] <= doc["n_kept"]
    assert all(s["kept"] is False or (s["arm"] != "NO_BET") for s in doc["splits"])
