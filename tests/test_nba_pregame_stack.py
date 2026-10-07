import copy
from datetime import datetime, timedelta, timezone

import pytest

from prediction_market_bot.c1_signal_ingestion.nba_pregame_features import FEATURE_NAMES, NBAFeatureBuilder
from prediction_market_bot.pregame_shadow import nba_settlement as S
from prediction_market_bot.pregame_shadow.nba_forecaster import (
    NBAForecaster, NBAScheduleIndex, parse_market_ticker)
from prediction_market_bot.pregame_shadow.nba_model import NBAPregameModel, p_yes_for
from prediction_market_bot.pregame_shadow.nfl_model import canonical_sha

T0 = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)


def games(n=30):
    out = []
    for i in range(n):
        t = T0 + timedelta(days=2 * i, hours=1)
        out.append({"game_id": str(i), "start_time_utc": t.isoformat(), "season": 2026, "season_type": 2,
                    "state": "STATUS_FINAL", "completed": True, "neutral_site": False,
                    "home": "BOS" if i % 2 else "NYK", "away": "NYK" if i % 2 else "BOS",
                    "home_score": 100 + i, "away_score": 95})
    return out


def art():
    z = {"intercept": 5.0, "coef": [0.0] * len(FEATURE_NAMES), "mean": [0.0] * len(FEATURE_NAMES),
         "std": [1.0] * len(FEATURE_NAMES)}
    a = {"model_id": "t", "feature_names": FEATURE_NAMES, "margin": z, "total": {**z, "intercept": 220.0},
         "platt": {"a": 1.0, "b": 0.0}, "sigma_margin": 12.0, "sigma_total": 18.0, "rho": 0.0}
    a["sha256"] = canonical_sha(a)
    return a


def test_features_are_point_in_time():
    g = games()
    fb = NBAFeatureBuilder(g)
    target = g[20]
    start = datetime.fromisoformat(target["start_time_utc"])
    base = fb.row(target["home"], target["away"], start, start)
    mutated = copy.deepcopy(g)
    for x in mutated[20:]:
        x["home_score"], x["away_score"] = 999, 0          # outcomes at/after the game must not matter
    assert NBAFeatureBuilder(mutated).row(target["home"], target["away"], start, start)["sha256"] == base["sha256"]


def test_as_of_excludes_later_games():
    g = games()
    start = datetime.fromisoformat(g[20]["start_time_utc"])
    early = NBAFeatureBuilder(g).row("BOS", "NYK", start, start - timedelta(days=10))
    late = NBAFeatureBuilder(g).row("BOS", "NYK", start, start)
    assert early is None or early["sha256"] != late["sha256"]


def test_too_little_history_returns_none():
    g = games()
    start = datetime.fromisoformat(g[3]["start_time_utc"])
    assert NBAFeatureBuilder(g).row("BOS", "NYK", start, start) is None


def test_model_rejects_tampered_artifact():
    a = art()
    a["sigma_margin"] = 1.0
    with pytest.raises(ValueError):
        NBAPregameModel(a)


def test_coherence_and_no_ties():
    m = NBAPregameModel(art())
    f = {n: 0.0 for n in FEATURE_NAMES}
    ml_h = p_yes_for(m, f, "NBA_MONEYLINE", subject_is_home=True)
    ml_a = p_yes_for(m, f, "NBA_MONEYLINE", subject_is_home=False)
    assert abs(ml_h + ml_a - 1) < 1e-12
    s = [p_yes_for(m, f, "NBA_SPREAD", subject_is_home=True, strike=k) for k in (-5.5, 0.5, 5.5)]
    assert s[0] > s[1] > s[2]
    t = [p_yes_for(m, f, "NBA_GAME_TOTAL", strike=k) for k in (210.5, 220.5, 230.5)]
    assert t[0] > t[1] > t[2]
    h = p_yes_for(m, f, "NBA_TEAM_TOTAL", subject_is_home=True, strike=110.5)
    a = p_yes_for(m, f, "NBA_TEAM_TOTAL", subject_is_home=False, strike=110.5)
    assert h > a                                             # home favoured by +5 margin intercept


def test_parse_tickers():
    p = parse_market_ticker("KXNBASPREAD-26OCT06BKNCHA-BKN38")
    assert (p["away"], p["home"], p["subject"], p["strike"], p["game_date"]) == ("BKN", "CHA", "BKN", 37.5, "2026-10-06")
    assert parse_market_ticker("KXNBATOTAL-26OCT07MININD-256")["strike"] == 255.5
    assert parse_market_ticker("KXNBAGAME-26OCT13INDOKC-OKC")["subject"] == "OKC"
    assert parse_market_ticker("KXNBAGAME-26OCT13INDOKC-XXX") is None
    assert parse_market_ticker("KXNFLGAME-26OCT13INDOKC-OKC") is None


def test_forecaster_and_schedule():
    g = games()
    g[25]["completed"], g[25]["home_score"], g[25]["away_score"] = False, None, None
    idx = NBAScheduleIndex(g)
    fc = NBAForecaster(NBAPregameModel(art()), NBAFeatureBuilder(g), idx)
    start = datetime.fromisoformat(g[25]["start_time_utc"])
    d = start.astimezone(__import__("zoneinfo").ZoneInfo("America/New_York")).date()
    ev = f"KXNBAGAME-{d:%y}{d:%b}{d:%d}".upper() + "NYKBOS"        # i=25 odd: home BOS, away NYK
    tkr = ev + "-BOS"
    assert idx.kickoff_for_event(ev)[0] == start
    f = fc.forecast(tkr, start - timedelta(hours=1))
    assert f is not None and 0 < f.p_yes < 1 and f.sport == "NBA"
    assert fc.forecast("KXNBAGAME-26OCT13INDOKC-OKC", start) is None


def test_settlement():
    clim = {"home_win_rate": 0.58, "mean_margin": 2.0, "mean_total": 225.0, "sd_margin": 13.0, "sd_total": 20.0}
    row = lambda t: {"market_ticker": t, "market_type": None}
    # home CHA 110, away BKN 100
    j = lambda t: S.join_row(row(t), "CHA", "BKN", 110, 100, clim)
    assert j("KXNBAGAME-26OCT06BKNCHA-CHA")["y"] == 1.0
    assert j("KXNBAGAME-26OCT06BKNCHA-BKN")["y"] == 0.0
    assert j("KXNBASPREAD-26OCT06BKNCHA-CHA10")["y"] == 1.0   # wins by 10 > 9.5
    assert j("KXNBASPREAD-26OCT06BKNCHA-CHA11")["y"] == 0.0
    assert j("KXNBASPREAD-26OCT06BKNCHA-BKN11")["y"] == 0.0
    assert j("KXNBATOTAL-26OCT06BKNCHA-210")["y"] == 1.0      # 210 > 209.5
    assert j("KXNBATOTAL-26OCT06BKNCHA-211")["y"] == 0.0
    assert j("KXNBATEAMTOTAL-26OCT06BKNCHA-BKN100")["y"] == 1.0   # 100 > 99.5
    assert j("KXNBAGAME-26OCT06BKNCHA-CHA")["game_key"] == "2026-10-06:BKN@CHA"
