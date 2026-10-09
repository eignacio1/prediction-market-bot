"""GG-532 / W62.1: MLB event -> cache game matches on teams + ET game date, never on the ticker's HHMM."""
from datetime import datetime, timezone
from types import SimpleNamespace

import pandas as pd

from prediction_market_bot.pregame_shadow.mlb_forecaster import MLBScheduleIndex
from prediction_market_bot.pregame_shadow.mlb_settlement import final_games, find_final
from prediction_market_bot.pregame_shadow.runner import run_once


def _row(pk, home, away, start, status="Preview", hs=None, as_=None):
    return {"game_pk": pk, "game_type": "D", "season": 2026, "game_date": start[:10], "start_utc": start,
            "status": status, "home": home, "away": away, "home_score": hs, "away_score": as_,
            "home_sp": 1.0, "away_sp": 2.0}


def _idx(*rows):
    return MLBScheduleIndex(pd.DataFrame(list(rows)))


def test_ticker_time_not_cache_time_still_matches_and_uses_cache_time():
    # real 10-08 case: ticker said 17:00 ET (21:00Z), the cache (truth) says 20:00 ET
    idx = _idx(_row(1, "CLE", "CWS", "2026-10-09T00:00:00Z"))
    ko = idx.kickoff_for_event("KXMLBGAME-26OCT081700CWSCLE")
    assert ko == (datetime(2026, 10, 9, 0, tzinfo=timezone.utc), "stats_api_schedule")


def test_late_evening_game_matches_on_et_date_not_utc_date():
    idx = _idx(_row(1, "SD", "MIL", "2026-10-08T02:00:00Z"))           # 22:00 ET on 10-07
    assert idx.kickoff_for_event("KXMLBGAME-26OCT072200MILSD") is not None


def test_placeholder_row_skips_with_its_own_reason():
    idx = _idx(_row(1, "MIL", "LAD", "2026-10-11T07:33:00Z"))
    assert idx.kickoff_for_event("KXMLBGAME-26OCT112000LADMIL") is None
    assert idx.miss_reason_for_event("KXMLBGAME-26OCT112000LADMIL") == "schedule_placeholder"


def test_no_row_for_pair_and_date_is_no_kickoff():
    idx = _idx(_row(1, "MIL", "LAD", "2026-10-11T07:33:00Z"))
    assert idx.miss_reason_for_event("KXMLBGAME-26OCT122000LADMIL") == "no_kickoff"
    assert idx.miss_reason_for_event("KXMLBGAME-26OCT112000CWSCLE") == "no_kickoff"


def test_doubleheader_picks_nearest_start_to_ticker():
    idx = _idx(_row(1, "NYY", "TB", "2026-10-07T17:00:00Z"), _row(2, "NYY", "TB", "2026-10-07T23:00:00Z"))
    g1 = idx.kickoff_for_event("KXMLBGAME-26OCT071300TBNYY")            # 13:00 ET = 17:00Z
    g2 = idx.kickoff_for_event("KXMLBGAME-26OCT071900TBNYY")            # 19:00 ET = 23:00Z
    assert g1[0].hour == 17 and g2[0].hour == 23


def test_equidistant_doubleheader_is_refused_not_guessed():
    idx = _idx(_row(1, "NYY", "TB", "2026-10-07T17:00:00Z"), _row(2, "NYY", "TB", "2026-10-07T21:00:00Z"))
    assert idx.kickoff_for_event("KXMLBGAME-26OCT071500TBNYY") is None  # 15:00 ET = 19:00Z, equidistant from 17Z and 21Z


def test_settlement_finds_final_despite_ticker_time_mismatch():
    fin = final_games(pd.DataFrame([_row(1, "CLE", "CWS", "2026-10-09T00:00:00Z", "Final", 4, 2)]))
    parsed = {"home": "CLE", "away": "CWS", "start_utc": datetime(2026, 10, 8, 21, tzinfo=timezone.utc)}
    assert find_final(fin, parsed) == (4.0, 2.0)


def _run(idx, now, ticker="KXMLBGAME-26OCT081700CWSCLE"):
    mkt = {"ticker": ticker + "-CLE", "event_ticker": ticker, "yes_bid_dollars": "0.40", "yes_ask_dollars": "0.44"}
    fc = SimpleNamespace(forecast=lambda t, n: SimpleNamespace(
        sport="MLB", p_yes=0.5, model_id="m", model_sha256="s", feature_row_sha256="f"))
    return run_once(forecaster=fc, cells=[("MLB_MONEYLINE", "KXMLBGAME")], list_markets=lambda s: (True, [mkt]),
                    kickoff_for=idx.kickoff_for_event, kickoff_miss_reason=idx.miss_reason_for_event,
                    ledger_dir=__import__("pathlib").Path(__import__("tempfile").mkdtemp()), run_id="r",
                    now_utc=now, code_sha="x")


def test_runner_writes_pregame_with_cache_time_and_never_after_start():
    idx = _idx(_row(1, "CLE", "CWS", "2026-10-09T00:00:00Z"))
    ok = _run(idx, datetime(2026, 10, 8, 20, 0, tzinfo=timezone.utc))        # 4h before the cache start -> T2
    assert ok["written"] == {"MLB_MONEYLINE:T2": 1}
    started = _run(idx, datetime(2026, 10, 9, 0, 30, tzinfo=timezone.utc))   # game has begun
    assert started["written"] == {}
    placeholder = _run(_idx(_row(1, "CLE", "CWS", "2026-10-08T07:33:00Z")), datetime(2026, 10, 8, 20, tzinfo=timezone.utc))
    assert placeholder["skipped"] == {"MLB_MONEYLINE:schedule_placeholder": 1}
