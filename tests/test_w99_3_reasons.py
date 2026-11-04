"""W99.3 / GG-1630: every arm says why. Known-answer tests for the counterfactual reasons; logging only."""
from datetime import datetime, timezone

import pandas as pd

from prediction_market_bot.c2_feature_store.nhl_features import NhlFeatureStore
from prediction_market_bot.c3_forecasting import nhl_pregame as m
from prediction_market_bot.nba_engine import engine_v2 as V, live_v2 as L2, why as W
from prediction_market_bot.pregame_shadow.point_reasons import counterfactual_reasons
from prediction_market_bot.pregame_shadow.reasons import TOP_K


def test_top_reasons_known_answer_is_exact_points_toward_yes():
    got = W.top_reasons(0.60, [("a", 1.0, 0.50), ("b", 2.0, 0.65), ("c", 3.0, 0.60), ("d", 4.0, 0.59), ("e", 5.0, None)])
    assert [r["factor"] for r in got] == ["a", "b", "d"] and len(got) == TOP_K
    assert got[0]["toward_yes"] == 10.0 and got[1]["toward_yes"] == -5.0 and got[2]["toward_yes"] == 1.0
    assert W.top_reasons(0.5, []) is None and W.top_reasons(0.5, [("x", 1, None)]) is None


def test_attach_never_raises_and_always_leaves_a_trace():
    ok = W.attach({"k": 1}, lambda: [{"factor": "f", "value": 1, "pts": 2, "toward_yes": 2}])
    assert ok["reasons"][0]["factor"] == "f" and "reasons_note" not in ok

    def boom():
        raise ValueError("bad")
    bad = W.attach({"k": 1}, boom)
    assert bad["reasons"] is None and "ValueError" in bad["reasons_note"] and bad["k"] == 1
    empty = W.attach({}, lambda: None)
    assert empty["reasons"] is None and empty["reasons_note"]


def test_points_reasons_known_answer_and_failure():
    # price depends on x only (y is inert): moving x from 5 to its mean 2 moves p by 0.3 -> 30 points
    price = lambda f: 0.2 + 0.1 * (f["x"] - 2) + 0.3 * 1.0 if f["x"] != 2 else 0.2 + 0.3 * 0  # noqa: E731
    r = counterfactual_reasons({"x": 5.0, "y": 7.0}, ["x", "y"], [2.0, 7.0], price)
    assert len(r) == 1 and abs(r[0]["toward_yes"] - (price({"x": 5.0, "y": 7.0}) - 0.2) * 100) < 1e-9
    assert counterfactual_reasons({"x": 1.0}, ["x"], [0.0], lambda f: 1 / 0) is None


NROW = len(m.GLM_FEATURES)


def _nhl_params(coef0=0.0):
    coef = [0.0] * NROW
    coef[0] = coef0
    return {"glm": {"mu": [0.0] * NROW, "sd": [1.0] * NROW, "coef": coef, "intercept": 1.1},
            "bivariate_c": 0.1, "tiebreak": {"a": 0.0, "b": 0.5},
            "calibration": {"total_scale": 1.0, "platt_a": 0.0, "platt_b": 1.0}}


def _game(i, day, home, away, hs, as_):
    t = datetime(2025, 10, day, 23, tzinfo=timezone.utc)
    return {"game_id": i, "start_time_utc": t.isoformat(), "home": home, "away": away, "home_score_ex_so": hs,
            "away_score_ex_so": as_, "home_sog": 30, "away_sog": 28, "home_pp_goals": 1, "away_pp_goals": 0,
            "home_pim": 4, "away_pim": 6, "home_starter_id": 1, "away_starter_id": 2, "home_goalies_used": [1],
            "away_goalies_used": [2], "home_goalie_sa": 28, "home_goalie_saves": 26, "away_goalie_sa": 30,
            "away_goalie_saves": 27}


def test_nhl_reasons_known_answer_only_the_weighted_input_matters():
    hist = [_game(1, 1, "AAA", "BBB", 4, 1), _game(2, 3, "BBB", "AAA", 2, 3)]
    sched = [{"game_id": 10, "game_date": "2025-10-09", "start_time_utc": datetime(2025, 10, 9, 23, tzinfo=timezone.utc).isoformat(),
              "home": "AAA", "away": "BBB", "state": "FUT", "schedule_state": "OK"}]
    f = m.NhlPregameForecaster(m.NhlGoalsModel(_nhl_params(0.3)), "sha", NhlFeatureStore(hist), sched)
    r = f.forecast("KXNHLGAME-25OCT09BBBAAA-AAA", datetime(2025, 10, 8, 12, tzinfo=timezone.utc))
    assert r.reasons and len(r.reasons) <= TOP_K
    top = r.reasons[0]
    assert "goals scored" in top["factor"] and top["factor"].startswith("home team")
    assert top["toward_yes"] > 0                       # home scoring above the mean pushes the home-win price up
    # the weight sits on "goals scored"; the away side's scoring pushes the other way, and nothing else has weight
    assert "away team goals scored" in r.reasons[1]["factor"] and r.reasons[1]["toward_yes"] < 0
    assert all(abs(x["toward_yes"]) < 1e-9 for x in r.reasons[2:])
    assert [abs(x["toward_yes"]) for x in r.reasons] == sorted((abs(x["toward_yes"]) for x in r.reasons), reverse=True)
    # a total on the same game gets reasons too
    t = f.forecast("KXNHLTOTAL-25OCT09BBBAAA-6", datetime(2025, 10, 8, 12, tzinfo=timezone.utc))
    assert t.reasons and t.reasons[0]["toward_yes"] > 0


def test_nhl_labels_are_plain_words():
    assert m._nhl_label("own_gf_ew", "h", "a") == "home team goals scored (recent, weighted)"
    assert m._nhl_label("opp_goalie_svp", "h", "a").startswith("away team starting goalie")
    assert "home-ice" in m._nhl_label("is_home", "h", "a")


def test_v2_rows_carry_reasons_with_known_direction(monkeypatch):
    rating = {"home": {"pace": 100.0, "ortg": 120.0, "drtg": 110.0, "n_prior": 20},
              "away": {"pace": 100.0, "ortg": 105.0, "drtg": 112.0, "n_prior": 20}}
    monkeypatch.setattr(L2.L, "team_rating", lambda tg, tid, season, cut: rating["home" if tid == 1 else "away"])
    monkeypatch.setattr(L2.L, "game_means", lambda h, a: {"mu_poss": (h["pace"] + a["pace"]) / 2,
                                                          "ppp_h": (h["ortg"] + a["drtg"]) / 2,
                                                          "ppp_a": (a["ortg"] + h["drtg"]) / 2})
    tg = pd.DataFrame({"season": [L2.L.SEASON - 1] * 4, "pace": [100.0] * 4, "ortg": [110.0] * 4, "drtg": [110.0] * 4})
    p = V.with_platt(V.V2Params(hca=2.0, tbias=0.0, sd_margin=14.0, sd_total=19.0),
                     {"ml": (0.0, 1.0), "spread": (0.0, 1.0), "total": (0.0, 1.0), "team_total": (0.0, 1.0)})
    parsed = dict(event_ticker="KXNBAGAME-26OCT28OKCDAL", game_date="2026-10-28", away="OKC", home="DAL", subject="DAL",
                  strike=None, market_type="NBA_MONEYLINE")
    now = datetime(2026, 10, 28, 12, tzinfo=timezone.utc)
    rows = L2.price_event_rows({"T1": {"yes_mid": 0.6, "run_ts": "t", "half_spread": 0.01}}, {"T1": parsed}, tg, {"DAL": 1, "OKC": 2},
                               p, now, now, "pid")
    r = rows[0]
    assert r["reasons"] and len(r["reasons"]) <= TOP_K
    top = r["reasons"][0]
    assert "home team offense" in top["factor"] and top["toward_yes"] > 0   # a 120 offense vs a 110 league average
    # the pipeline for an unpriceable counterfactual leaves a note instead of losing the row
    monkeypatch.setattr(L2.W, "league_means", lambda tg, season: (_ for _ in ()).throw(KeyError("x")))
    r2 = L2.price_event_rows({"T1": {"yes_mid": 0.6, "run_ts": "t"}}, {"T1": parsed}, tg, {"DAL": 1, "OKC": 2}, p, now, now, "pid")[0]
    assert r2["reasons"] is None and r2["reasons_note"]
