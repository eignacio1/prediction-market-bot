"""W98.3 / GG-1580: top-3 reasons are exact ridge contributions, logging only."""
import math

from prediction_market_bot.pregame_shadow import reasons as R


def _art():
    names = ["h_pf10", "a_pf10", "h_rest"]
    m = {"mean": [100.0, 100.0, 2.0], "std": [10.0, 10.0, 1.0], "coef": [3.0, -2.0, 0.5], "intercept": 0.0}
    t = {"mean": [100.0, 100.0, 2.0], "std": [10.0, 10.0, 1.0], "coef": [4.0, 4.0, 0.0], "intercept": 220.0}
    return {"margin": m, "total": t, "platt": {"a": 0.5, "b": 0.0}}, names


def test_top3_ranked_by_size_and_sum_matches_model():
    art, names = _art()
    feats = {"h_pf10": 110.0, "a_pf10": 90.0, "h_rest": 3.0}
    out = R.ridge_reasons(art, names, feats, "NBA_MONEYLINE", subject_is_home=True)
    assert [r["factor"] for r in out][:2] == ["home team points scored per game, last 10",
                                             "away team points scored per game, last 10"]
    assert math.isclose(sum(r["pts"] for r in out), 0.5 * (3.0 + 2.0 + 0.5))  # a * sum(coef*z)
    assert out[0]["toward_yes"] == 1.5 and out[1]["toward_yes"] == 1.0


def test_away_subject_flips_sign_and_total_ignores_subject():
    art, names = _art()
    feats = {"h_pf10": 110.0, "a_pf10": 90.0, "h_rest": 3.0}
    away = R.ridge_reasons(art, names, feats, "NBA_SPREAD", subject_is_home=False)
    assert away[0]["toward_yes"] == -1.5 and away[0]["pts"] == 1.5
    tot = R.ridge_reasons(art, names, feats, "NBA_GAME_TOTAL")
    assert tot[0]["factor"].startswith("home team points") and tot[0]["toward_yes"] == 4.0


def test_failure_returns_none_not_exception():
    art, names = _art()
    assert R.ridge_reasons(art, names, {}, "NBA_MONEYLINE", subject_is_home=True) is None
    assert R.ridge_reasons(art, names, {"h_pf10": 1, "a_pf10": 1, "h_rest": 1}, "NBA_WEIRD") is None


def test_every_real_feature_has_plain_words():
    from prediction_market_bot.c1_signal_ingestion import mlb_game_pregame_features as M, nba_pregame_features as B
    from prediction_market_bot.c1_signal_ingestion import nfl_pregame_features as F
    for n in list(M.FEATURE_NAMES) + list(B.FEATURE_NAMES) + list(F.FEATURE_NAMES):
        assert "_" not in R.plain_name(n) or n.split("_")[0] in ("h", "a"), n
