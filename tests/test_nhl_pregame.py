"""NHL pregame model (T-607 / EXP-036 D2). Synthetic fixtures only; no network."""
import json
from datetime import datetime, timedelta, timezone

import pytest

from prediction_market_bot.c2_feature_store.nhl_features import NhlFeatureStore
from prediction_market_bot.c3_forecasting import nhl_pregame as m

N = len(m.GLM_FEATURES)


def params(c=0.1, scale=1.0, pa=0.0, pb=1.0):
    return {"glm": {"mu": [0.0] * N, "sd": [1.0] * N, "coef": [0.0] * N, "intercept": 1.1},
            "bivariate_c": c, "tiebreak": {"a": 0.0, "b": 0.5},
            "calibration": {"total_scale": scale, "platt_a": pa, "platt_b": pb}}


def mk(i, day, home, away, hs, as_, hid=1, aid=2):
    t = datetime(2025, 10, day, 23, tzinfo=timezone.utc)
    return {"game_id": i, "start_time_utc": t.isoformat(), "home": home, "away": away,
            "home_score_ex_so": hs, "away_score_ex_so": as_, "home_sog": 30, "away_sog": 28,
            "home_pp_goals": 1, "away_pp_goals": 0, "home_pim": 4, "away_pim": 6,
            "home_starter_id": hid, "away_starter_id": aid, "home_goalies_used": [hid],
            "away_goalies_used": [aid], "home_goalie_sa": 28, "home_goalie_saves": 26,
            "away_goalie_sa": 30, "away_goalie_saves": 27}


def sched(i, day, home, away, state="FUT", sstate="OK"):
    t = datetime(2025, 10, day, 23, tzinfo=timezone.utc)
    return {"game_id": i, "game_date": f"2025-10-{day:02d}", "start_time_utc": t.isoformat(),
            "home": home, "away": away, "state": state, "schedule_state": sstate}


def forecaster(games, schedule):
    return m.NhlPregameForecaster(m.NhlGoalsModel(params()), "sha", NhlFeatureStore(games), schedule)


HIST = [mk(1, 1, "AAA", "BBB", 4, 1), mk(2, 3, "BBB", "AAA", 2, 3)]
AS_OF = datetime(2025, 10, 8, 12, tzinfo=timezone.utc)
ROW = NhlFeatureStore(HIST).game_features("AAA", "BBB", datetime(2025, 10, 9, 23, tzinfo=timezone.utc), AS_OF)


def test_ladder_coherent_and_monotone():
    lad = m.NhlGoalsModel(params()).ladder(ROW)
    assert abs(m.joint_pmf(3.1, 2.9, 0.1).sum() - 1) < 1e-9
    for side in ("home", "away"):
        assert lad.p_win_by_over(side, 2.5) <= lad.p_win_by_over(side, 1.5) <= lad.p_team_win(side)
    ts = [lad.p_total_over(k + 0.5) for k in range(3, 10)]
    assert all(a >= b for a, b in zip(ts, ts[1:]))
    assert abs(lad.p_team_win("home") + lad.p_team_win("away") - 1) < 1e-9


def test_ot_so_total_counts_winner_goal():
    lad = m.Ladder(m.joint_pmf(0.5, 0.5, 0.0), 0.5)
    J = lad.J
    # a 0-0 regulation tie settles 1-0 (total 1), so it counts as over 0.5 but not over 1.5
    assert lad.p_total_over(0.5) == pytest.approx(1.0)
    expect = sum(J[x, y] for x in range(J.shape[0]) for y in range(J.shape[1]) if x + y + (x == y) > 1.5)
    assert lad.p_total_over(1.5) == pytest.approx(expect)


def test_puck_line_ignores_tiebreak_wins():
    lad_a = m.Ladder(m.joint_pmf(3, 3, 0.1), 0.1)
    lad_b = m.Ladder(m.joint_pmf(3, 3, 0.1), 0.9)
    assert lad_a.p_win_by_over("home", 1.5) == pytest.approx(lad_b.p_win_by_over("home", 1.5))
    assert lad_a.p_team_win("home") < lad_b.p_team_win("home")


def test_platt_moves_moneyline_and_stays_coherent():
    base = m.NhlGoalsModel(params()).ladder(ROW)
    tilt = m.NhlGoalsModel(params(pa=0.4)).ladder(ROW)
    assert tilt.p_team_win("home") > base.p_team_win("home")
    assert tilt.p_win_by_over("home", 1.5) > base.p_win_by_over("home", 1.5)


def test_total_scale_raises_totals():
    lo = m.NhlGoalsModel(params(scale=0.9)).ladder(ROW).p_total_over(5.5)
    hi = m.NhlGoalsModel(params(scale=1.1)).ladder(ROW).p_total_over(5.5)
    assert hi > lo


def test_parse_ticker_three_series():
    g = m.parse_ticker("KXNHLGAME-26OCT04VGKVAN-VAN")
    assert g["market_type"] == "NHL_MONEYLINE" and g["team"] == "VAN" and g["home"] == "VAN"
    s = m.parse_ticker("KXNHLSPREAD-26OCT04VGKVAN-VGK3")
    assert s["strike"] == 2.5 and s["team"] == "VGK"
    t = m.parse_ticker("KXNHLTOTAL-26OCT04VGKVAN-9")
    assert t["strike"] == 8.5
    assert m.parse_ticker("KXNHLTOTAL-26XXX04VGKVAN-9") is None
    assert m.parse_ticker("garbage") is None


def test_forecast_valid_and_strictly_inside_unit_interval():
    f = forecaster(HIST, [sched(10, 9, "AAA", "BBB")])
    r = f.forecast("KXNHLGAME-25OCT09BBBAAA-AAA", AS_OF)
    assert r.sport == "NHL" and 0 < r.p_yes < 1 and r.as_of_utc == AS_OF
    r2 = f.forecast("KXNHLTOTAL-25OCT09BBBAAA-6", AS_OF)
    assert 0 < r2.p_yes < 1


def test_forecast_none_cases():
    f = forecaster(HIST, [sched(10, 9, "AAA", "BBB"), sched(11, 9, "CCC", "DDD", "PPD", "PPD")])
    assert f.forecast("KXNHLGAME-25OCT09BBBAAA-AAA", datetime(2025, 10, 9, 23, tzinfo=timezone.utc)) is None
    assert f.forecast("KXNHLGAME-25OCT09BBBAAA-AAA", datetime(2025, 10, 10, tzinfo=timezone.utc)) is None
    assert f.forecast("KXNHLGAME-25OCT09DDDCCC-CCC", AS_OF) is None  # postponed
    assert f.forecast("KXNHLGAME-25OCT09ZZZYYY-ZZZ", AS_OF) is None  # unknown game
    assert f.forecast("KXNHLGAME-25OCT09BBBAAA-ZZZ", AS_OF) is None  # team not in game
    assert f.forecast("nonsense", AS_OF) is None


def test_cutoff_future_games_cannot_change_forecast():
    """Cutoff test: results timestamped after as_of_utc must not move the forecast; a leak would."""
    sc = [sched(10, 9, "AAA", "BBB")]
    base = forecaster(HIST + [mk(3, 12, "AAA", "CCC", 1, 0)], sc)
    leak = forecaster(HIST + [mk(3, 12, "AAA", "CCC", 9, 9)], sc)  # after as_of
    for tk in ("KXNHLGAME-25OCT09BBBAAA-AAA", "KXNHLTOTAL-25OCT09BBBAAA-6"):
        a, b = base.forecast(tk, AS_OF), leak.forecast(tk, AS_OF)
        assert a.p_yes == b.p_yes and a.feature_row_sha256 == b.feature_row_sha256
    # and a game that tipped off inside RESULT_LAG of as_of is likewise invisible
    edge = HIST + [mk(4, 8, "AAA", "BBB", 7, 0)]  # starts Oct 8 23:00, after as_of 12:00
    assert forecaster(edge, sc).forecast("KXNHLGAME-25OCT09BBBAAA-AAA", AS_OF).feature_row_sha256 == \
        forecaster(HIST, sc).forecast("KXNHLGAME-25OCT09BBBAAA-AAA", AS_OF).feature_row_sha256


def test_artifact_hash_roundtrip_and_tamper(tmp_path):
    p = params()
    p["sha256"] = m.artifact_sha256(p)
    f = tmp_path / "a.json"
    f.write_text(json.dumps(p))
    _, sha = m.load_model(f)
    assert sha == p["sha256"]
    p["bivariate_c"] = 0.2
    f.write_text(json.dumps(p))
    with pytest.raises(Exception):
        m.load_model(f)


def test_forecast_has_no_trading_imports():
    src = open(m.__file__).read()
    assert "paper_trader" not in src and "kalshi_client" not in src and "submit_order" not in src
