"""W128.2 / D-07: one player-mean function. The same player-game gives the same mean in props, combos and the joint draw."""
from datetime import datetime, timezone

import numpy as np

from prediction_market_bot.nba_engine import joint as J
from prediction_market_bot.nba_engine import player_means as PM
from prediction_market_bot.pregame_shadow import nba_engine_props_c1_forecaster as C1
from prediction_market_bot.pregame_shadow import nba_engine_props_c2_forecaster as C2
from prediction_market_bot.pregame_shadow import nba_engine_props_forecaster as F
from tests.test_nba_engine_props_shadow import _store

NOW = datetime(2026, 11, 9, 12, tzinfo=timezone.utc)
TIPS = {("2026-11-09", frozenset(("NOP", "GSW"))): datetime(2026, 11, 9, 23, 0, tzinfo=timezone.utc)}
P = {"game_date": "2026-11-09", "home": "GSW", "away": "NOP"}


def _fc(out):
    games, pl = F.parse_box(_store())
    return C2.NBAEnginePropsC2(games, pl, TIPS, lambda p, t: out, C2.parse_attempts(_store()))


def test_frozen_hashes_unchanged():
    assert len({C2.MODEL_SHA256, C1.MODEL_SHA256, F.MODEL_SHA256}) == 3
    assert C2.MODEL_ID == "nba_engine_v2_props_c2_w126_2"
    assert C2.LAMBDA == {"rebounds": 0.26, "assists": 0.31, "threes": 0.27}


def test_nobody_out_returns_base_unchanged():
    base = {s: [20.0, 10.0, 5.0] for s in J.STATS}
    assert PM.c2_means(base, [1.0, 1.0, 1.0], None, C2.LAMBDA) is base


def test_team_means_equals_c2_means_and_props_mu():
    fc = _fc({"DudA QueenA"})
    ros, mu = fc.team_means("NOP", "2026-11-09", P, NOW)
    assert mu == fc._mu(ros, {"team": "NOP", "game_date": "2026-11-09"})
    i = [n for _, n, _ in ros].index("DudA QueenA")
    assert all(mu[s][i] == 0.0 for s in ("points", "rebounds", "assists", "threes"))
    assert sum(mu["points"]) > 0


def test_nobody_out_team_means_equal_trailing_means():
    fc = _fc(set())
    ros, mu = fc.team_means("NOP", "2026-11-09", P, NOW)
    base = fc.roster("NOP", "2026-11-09")
    assert base is not None and len(mu["points"]) == len(ros)


def test_joint_roster_mu_is_team_means(monkeypatch):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    import nba_combo_shadow as W
    fc = _fc({"DudA QueenA"})
    seen = {}
    real = J.JointRoster

    def spy(names, minutes, mu, pts):
        seen.setdefault("mu", []).append(mu)
        return real(names, minutes, mu, pts)

    monkeypatch.setattr(W.J, "JointRoster", spy)
    monkeypatch.setattr(fc, "_game_draws", lambda p: (np.full(200, 110.0) + np.arange(200) % 7, np.full(200, 105.0) + np.arange(200) % 5))
    W.game_draws(fc, "26NOV09NOPGSW", 200, NOW)
    _, expect = fc.team_means("NOP", "2026-11-09", P, NOW)
    assert seen["mu"] and any(m == {s: list(expect[s]) for s in J.STATS} for m in seen["mu"])


def test_combo_rows_carry_means_sha():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    import nba_combo_shadow as W
    assert W.PLAYER_MEANS_SHA256 == C2.MODEL_SHA256 and W.MODEL_ID.endswith("w128_2")
