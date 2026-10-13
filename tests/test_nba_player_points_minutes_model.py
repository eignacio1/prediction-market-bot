import json
from pathlib import Path

import pytest

from prediction_market_bot.pregame_shadow.nba_player_points_minutes_model import NBAPlayerPointsMinutesModel

ART = Path(__file__).resolve().parent.parent / "models" / "nba_player_points_minutes_v1.json"
FROZEN_SHA = "c47cbac7378f160f2ed1cd31807663193cd4ce92df5ed00da6ed253ec3548527"


def _feats(m, **kw):
    f = {n: 0.0 for n in m.names}
    f.update(pts10=18.0, pts30=17.0, min10=32.0, fga10=14.0, pts_season=17.5, gp_prior=40.0, home=1.0,
             rest=2.0, min30=31.0, min_rank=2.0, opp_def10=112.0)
    f.update(kw)
    return f


def test_sha_is_the_registered_one():
    assert NBAPlayerPointsMinutesModel.load(ART).sha256 == FROZEN_SHA


def test_tamper_refused(tmp_path):
    a = json.loads(ART.read_text()); a["dispersion_r"] = 9.9
    p = tmp_path / "x.json"; p.write_text(json.dumps(a))
    with pytest.raises(ValueError):
        NBAPlayerPointsMinutesModel.load(p)


def test_only_registered_strike():
    m = NBAPlayerPointsMinutesModel.load(ART)
    assert 0.0 < m.p_at_least(_feats(m), 15) < 1.0
    for k in (10, 20, 25):
        with pytest.raises(ValueError):
            m.p_at_least(_feats(m), k)


def test_more_points_history_raises_p():
    m = NBAPlayerPointsMinutesModel.load(ART)
    assert m.p_at_least(_feats(m, pts10=24.0, pts30=23.0), 15) > m.p_at_least(_feats(m, pts10=10.0, pts30=10.0), 15)
