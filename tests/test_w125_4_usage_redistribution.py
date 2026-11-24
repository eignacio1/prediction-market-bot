"""W125.4 / EXP-047-C1: one usage-redistribution rule shared by the game-line and props paths. Known answers, no network."""
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from prediction_market_bot.nba_engine import factors_applied as FA
from prediction_market_bot.nba_engine import usage_redistribution as U
from prediction_market_bot.pregame_shadow import nba_engine_props_c1_forecaster as C1
from prediction_market_bot.pregame_shadow import nba_engine_props_forecaster as F
from tests.test_nba_engine_props_shadow import _store

NOW = datetime(2026, 11, 9, 12, tzinfo=timezone.utc)
TIP = datetime(2026, 11, 9, 23, 0, tzinfo=timezone.utc)
TIPS = {("2026-11-09", frozenset(("NOP", "GSW"))): TIP}


def _pair(out):
    games, pl = F.parse_box(_store())
    games2, pl2 = F.parse_box(_store())
    return F.NBAEngineProps(games, pl, TIPS), C1.NBAEnginePropsC1(games2, pl2, TIPS, lambda p, t: out)


def test_rule_known_answer_and_total_preserved():
    w = [40.0, 30.0, 20.0, 10.0]
    r = U.redistribute(w, [0.0, 1.0, 1.0, 1.0])
    assert r[0] == 0.0 and abs(sum(r) - 100.0) < 1e-9
    assert np.allclose(r[1:], [30 / 60 * 100, 20 / 60 * 100, 10 / 60 * 100])      # proportional to their own weight
    assert abs(U.absorption_factor(w, [0.0, 1, 1, 1]) - 1 / (1 - 0.4)) < 1e-12


def test_nobody_out_returns_input_bit_identical():
    w = [31.7, 12.3, 5.5]
    assert U.redistribute(w, [1.0, 1.0, 1.0]) == w


def test_game_path_unchanged_bit_identical():
    df = pd.DataFrame({"game_id": ["g"] * 3, "team_id": ["t"] * 3, "share": [0.4, 0.35, 0.25], "p_play": [0.25, 1.0, 0.5]})
    out = FA.usage_missing(df).iloc[0]
    assert out["usage_missing"] == 0.4 * (1.0 - 0.25) + 0.35 * (1.0 - 1.0) + 0.25 * (1.0 - 0.5)
    assert out["creator_out"] == 0.4 * (1.0 - 0.25)
    assert U.missing_usage(0.4, 0.25) == 0.4 * (1.0 - 0.25)


def test_nobody_out_leaves_exp047_unchanged_to_the_bit():
    base, c1 = _pair(set())
    for stat, ser in (("PTS", "points"), ("REB", "rebounds"), ("AST", "assists"), ("3PT", "threes")):
        for n in (2, 4, 8):
            t = f"KXNBA{stat}-26NOV09NOPGSW-NOPDQUEENA22-{n}"
            a, b = base.forecast(t, NOW), c1.forecast(t, NOW)
            assert a.p_yes == b.p_yes
            assert (b.model_id, b.model_sha256) != (a.model_id, a.model_sha256) and b.model_sha256 == C1.MODEL_SHA256


def test_planted_out_creator_shifts_teammates_up_and_total_stays():
    base, c1 = _pair({"DudA QueenA"})
    up = 0
    for n in (6, 10, 14):
        t = f"KXNBAPTS-26NOV09NOPGSW-NOPDQUEENB22-{n}"
        up += c1.forecast(t, NOW).p_yes > base.forecast(t, NOW).p_yes
    assert up == 3                                          # teammate points rise at every strike
    assert c1.forecast("KXNBAPTS-26NOV09NOPGSW-NOPDQUEENA22-6", NOW).p_yes < 0.01      # the Out player himself
    ros = c1.roster("NOP", "2026-11-09")
    mu = c1._mu(ros, {})
    assert abs(sum(mu["points"]) - sum(r[2]["points"] for r in ros)) < 1e-9


def test_out_on_other_team_does_not_touch_this_team_and_models_separate():
    base, c1 = _pair({"GuyA CurryA"})                     # a GSW player; ticker below is NOP
    t = "KXNBAPTS-26NOV09NOPGSW-NOPDQUEENB22-10"
    assert base.forecast(t, NOW).p_yes == c1.forecast(t, NOW).p_yes
    assert C1.MODEL_SHA256 != F.MODEL_SHA256 and C1.MODEL_ID != F.MODEL_ID
