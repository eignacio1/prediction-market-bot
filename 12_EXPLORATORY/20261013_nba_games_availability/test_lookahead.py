"""W71.3 no-look-ahead tests (EXPLORATORY). Run before the fit is read: PYTHONPATH=src python3 -m pytest test_lookahead.py"""
import copy
import sys
from datetime import timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import games_features as G  # noqa: E402
from prediction_market_bot.c1_signal_ingestion import nba_ingest as N  # noqa: E402
from prediction_market_bot.c1_signal_ingestion import nba_player_ingest as P  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_player_features import PlayerFeatureBuilder  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_pregame_features import _dt, et_date, et_midnight_utc  # noqa: E402

W = G.W69
RAW_G = HERE.parents[1].parent / "nba_raw"
RAW_P = HERE.parents[1].parent / "_w65_data"


def test_snapshot_slot_at_least_4h_before_tip():
    start = _dt("2026-02-10T00:00:00Z")                    # 19:00 ET on Feb 9
    d = str(et_date(start))
    inj = {d: {"11:30": {"x y": "Out"}, "15:30": {"x y": "Available"}, "19:30": {"x y": "Out"}}}
    assert W.snapshot(inj, start) == inj[d]["11:30"]       # 15:30 is only 3.5h before tip
    early = _dt("2026-02-09T19:00:00Z")                    # 14:00 ET: nothing >=4h before
    inj2 = {str(et_date(early)): {"11:30": {"x y": "Out"}}}
    assert W.snapshot(inj2, early) is None


def test_future_injury_files_do_not_change_past_snapshot():
    start = _dt("2026-02-10T00:00:00Z")
    d = str(et_date(start))
    inj = {d: {"11:30": {"x y": "Out"}}}
    base = W.snapshot(inj, start)
    inj2 = copy.deepcopy(inj)
    inj2["2026-02-11"] = {"11:30": {"x y": "Available"}}
    inj2[d]["19:30"] = {"x y": "Available"}
    assert W.snapshot(inj2, start) == base


def _fb():
    games, stores = [], []
    for s in (2025, 2026):
        games += list(N.load_season(s, RAW_G)["games"].values())
        stores.append(P.load_players(s, RAW_P))
    return games, stores, PlayerFeatureBuilder(games, stores)


def test_own_box_score_does_not_move_features():
    games, stores, fb = _fb()
    rec = next(r for s in stores for g, r in s["games"].items() if len(r["rows"]) > 10 and g in {x["game_id"] for x in games if x["season"] == 2026})
    gid = next(g for s in stores for g, r in s["games"].items() if r is rec)
    g = next(x for x in games if x["game_id"] == gid)
    start = _dt(rec["start_time_utc"])
    inj = {str(et_date(start)): {"11:30": {}}}
    before = G.team_out_min(fb, inj, g, g["home"], start)
    stores2 = copy.deepcopy(stores)
    for s in stores2:
        if gid in s["games"]:
            for r in s["games"][gid]["rows"]:
                r["minutes"] = 99.0
    fb2 = PlayerFeatureBuilder(games, stores2)
    assert G.team_out_min(fb2, inj, g, g["home"], start) == before


def test_trailing_history_uses_only_prior_games():
    games, stores, fb = _fb()
    import bisect
    for pid, starts in list(fb._pstarts.items())[:200]:
        cutoff = starts[len(starts) // 2]
        j = bisect.bisect_left(starts, cutoff)
        assert all(t < cutoff for t, _, _ in fb._by_player[pid][:j])
