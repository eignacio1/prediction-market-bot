"""W126.2 / EXP-047-C2: stat-specific absorption. Known answers, no network."""
from datetime import datetime, timezone

import numpy as np

from prediction_market_bot.nba_engine import usage_redistribution as U
from prediction_market_bot.pregame_shadow import nba_engine_props_c1_forecaster as C1
from prediction_market_bot.pregame_shadow import nba_engine_props_c2_forecaster as C2
from prediction_market_bot.pregame_shadow import nba_engine_props_forecaster as F
from tests.test_nba_engine_props_shadow import _store

NOW = datetime(2026, 11, 9, 12, tzinfo=timezone.utc)
TIPS = {("2026-11-09", frozenset(("NOP", "GSW"))): datetime(2026, 11, 9, 23, 0, tzinfo=timezone.utc)}


def _mk(cls, out, **kw):
    games, pl = F.parse_box(_store())
    if cls is C2.NBAEnginePropsC2:
        return cls(games, pl, TIPS, lambda p, t: out, C2.parse_attempts(_store()), **kw)
    return cls(games, pl, TIPS, lambda p, t: out) if cls is not F.NBAEngineProps else cls(games, pl, TIPS)


def test_lambda_one_is_c1_rule_to_the_bit_and_zero_drops():
    w, p = [40.0, 30.0, 20.0, 10.0], [0.0, 1.0, 1.0, 1.0]
    assert U.absorb(w, p, 1.0) == U.redistribute(w, p)
    assert U.absorb(w, p, 0.0) == [0.0, 30.0, 20.0, 10.0]
    h = U.absorb(w, p, 0.5)
    assert abs(sum(h) - (60.0 + 0.5 * 40.0)) < 1e-9                       # active total = W_act + lam * vacated


def test_nobody_out_unchanged_to_the_bit():
    w = [31.7, 12.3, 5.5]
    assert U.absorb(w, [1.0, 1.0, 1.0], 0.4) == w
    assert U.absorb_threes([5.0, 3.0, 2.0], w, [1.0, 1.0, 1.0], 0.4) == w


def test_threes_convert_extra_attempts_at_own_make_rate():
    att, mk = [8.0, 6.0, 4.0], [3.2, 2.4, 1.0]        # make rates .4 .4 .25
    r = U.absorb_threes(att, mk, [0.0, 1.0, 1.0], 1.0)
    f = 18.0 / 10.0
    assert r[0] == 0.0 and np.allclose(r[1:], [2.4 * f, 1.0 * f])
    assert np.allclose(U.absorb_threes(att, mk, [0.0, 1.0, 1.0], 0.0)[1:], [2.4, 1.0])


def test_forecaster_nobody_out_equals_exp047_and_hash_differs():
    base, c2 = _mk(F.NBAEngineProps, set()), _mk(C2.NBAEnginePropsC2, set())
    for stat in ("PTS", "REB", "AST", "3PT"):
        for n in (2, 4, 8):
            t = f"KXNBA{stat}-26NOV09NOPGSW-NOPDQUEENA22-{n}"
            a, b = base.forecast(t, NOW), c2.forecast(t, NOW)
            assert a.p_yes == b.p_yes and b.model_sha256 == C2.MODEL_SHA256
    assert len({C2.MODEL_SHA256, C1.MODEL_SHA256, F.MODEL_SHA256}) == 3 and C2.MODEL_ID != C1.MODEL_ID


def test_points_equal_c1_and_lambda_zero_rebounds_below_c1():
    c1, c2, c20 = (_mk(C1.NBAEnginePropsC1, {"DudA QueenA"}), _mk(C2.NBAEnginePropsC2, {"DudA QueenA"}),
                   _mk(C2.NBAEnginePropsC2, {"DudA QueenA"}, lam={"rebounds": 0.0, "assists": 0.0, "threes": 0.0}))
    for n in (6, 10, 14):
        t = f"KXNBAPTS-26NOV09NOPGSW-NOPDQUEENB22-{n}"
        assert c2.forecast(t, NOW).p_yes == c1.forecast(t, NOW).p_yes
    ros, p = c20.roster("NOP", "2026-11-09"), {"team": "NOP", "game_date": "2026-11-09"}
    c1._out = c2._out = c20._out = frozenset(C2.norm_name(x) for x in ("DudA QueenA",))
    s0, s2, s1 = (sum(x._mu(ros, p)["rebounds"]) for x in (c20, c2, c1))
    assert s0 < s1 + 1e-9 and abs(s2 - s1) < 1e-9                    # default lambda 1.0 == C1; lambda 0 absorbs nothing
    assert s0 < sum(r[2]["rebounds"] for r in ros)


def test_out_on_other_team_untouched():
    base, c2 = _mk(F.NBAEngineProps, set()), _mk(C2.NBAEnginePropsC2, {"GuyA CurryA"})
    t = "KXNBAREB-26NOV09NOPGSW-NOPDQUEENB22-6"
    assert base.forecast(t, NOW).p_yes == c2.forecast(t, NOW).p_yes
