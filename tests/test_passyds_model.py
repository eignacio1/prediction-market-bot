"""W82.1: KXNFLPASSYDS frozen strike model -- sha refusal, point-in-time features, cold start, QB out, monotone strikes, no network."""
import json
import shutil
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from prediction_market_bot.pregame_shadow import passyds_model as pm  # noqa: E402

NOW = datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc)


def _frames(n_games=5, qb="Drake Maye", team="NE", opp="CHI"):
    """n_games of one QB (all vs `opp`), each with a defense row; gamedays 2026-09-01 + 7d steps."""
    qrows, drows = [], []
    for i in range(n_games):
        day = pd.Timestamp("2026-09-01") + pd.Timedelta(days=7 * i)
        yds = 200 + 10 * i
        qrows.append(dict(player_id="p1", name_key=pm.norm_name(qb), team=team, opponent_team=opp, season=2026, week=i + 1,
                          game_id=f"g{i}", gameday=day, home=float(i % 2), passing_yards=yds, attempts=30))
        drows.append(dict(game_id=f"g{i}", opponent_team=opp, passing_yards=yds, gameday=day))
    return pd.DataFrame(qrows), pd.DataFrame(drows)


def _rt(qg, dg, inj=()):
    rt = pm.Runtime.__new__(pm.Runtime)
    rt.model, rt.sha = pm.load_frozen(ROOT / "models")
    rt.qg, rt.dg, rt.inj = qg, dg, list(inj)
    rt.sched = None
    return rt


def _mkt(strike=250):
    return {"event_ticker": "KXNFLPASSYDS-26OCT22NECHI", "no_sub_title": "Drake Maye: 250+", "floor_strike": strike}


def test_frozen_artifact_loads_and_matches_committed_sha():
    model, sha = pm.load_frozen(ROOT / "models")
    assert sha == (ROOT / "models" / "passyds_strike_v1.sha256").read_text().split()[0]
    assert sha.startswith("1053c843")
    assert model.sigma_c > 0


def test_sha_mismatch_refuses(tmp_path):
    for f in ("passyds_strike_v1.json", "passyds_strike_v1.sha256"):
        shutil.copy(ROOT / "models" / f, tmp_path / f)
    art = json.loads((tmp_path / "passyds_strike_v1.json").read_text())
    art["coef"]["intercept"] += 1.0
    (tmp_path / "passyds_strike_v1.json").write_text(json.dumps(art))
    with pytest.raises(RuntimeError, match="hash mismatch"):
        pm.load_frozen(tmp_path)


def test_features_are_point_in_time():
    qg, dg = _frames(5)
    when = pd.Timestamp("2026-09-15")  # games g0 (09-01), g1 (09-08) are before; g2 is ON the date and excluded
    f = pm.features_for(qg, dg, pm.norm_name("Drake Maye"), "CHI", 1.0, when, 230.0, 230.0)
    assert f is None  # only 2 prior starts < MIN_PRIOR_STARTS
    when = pd.Timestamp("2026-09-16")
    f = pm.features_for(qg, dg, pm.norm_name("Drake Maye"), "CHI", 1.0, when, 230.0, 230.0)
    assert f["n_prior_starts"] == 3 and f["qb_last_game"] == "2026-09-15"
    # a future game's yardage must not move the features
    qg2 = qg.copy()
    qg2.loc[qg2["gameday"] > when, "passing_yards"] = 999
    dg2 = dg.copy()
    dg2.loc[dg2["gameday"] > when, "passing_yards"] = 999
    f2 = pm.features_for(qg2, dg2, pm.norm_name("Drake Maye"), "CHI", 1.0, when, 230.0, 230.0)
    assert f2["qb_shrunk"] == f["qb_shrunk"] and f2["opp_dev"] == f["opp_dev"]


def test_cold_start_returns_no_forecast():
    qg, dg = _frames(2)
    out = _rt(qg, dg).fields(_mkt(), NOW)
    assert out["model_p"] is None and out["model_status"] == "cold_start"


def test_qb_out_returns_none():
    qg, dg = _frames(5)
    inj = [{"name": "Drake Maye", "status": "Out", "is_qb": True, "_captured_utc": "2026-10-22T10:00:00Z"}]
    out = _rt(qg, dg, inj).fields(_mkt(), NOW)
    assert out["model_p"] is None and out["model_status"] == "qb_unavailable"
    assert out["factor_as_of"]["injury_snapshot_utc"] == "2026-10-22T10:00:00Z"


def test_healthy_qb_gets_forecast_with_provenance():
    qg, dg = _frames(5)
    out = _rt(qg, dg).fields(_mkt(), NOW)
    assert out["model_status"] == "ok" and 0.0 <= out["model_p"] <= 1.0
    assert out["model_id"] == "passyds_strike_v1" and out["model_sha256"].startswith("1053c843")
    assert out["factor_as_of"]["features_before"] == "2026-10-22"


def test_p_ge_monotone_non_increasing_in_strike():
    model, _ = pm.load_frozen(ROOT / "models")
    f = {"qb_shrunk": 240.0, "opp_dev": 5.0, "home": 1.0}
    ps = [model.p_ge(f, s) for s in range(150, 420, 10)]
    assert all(a >= b for a, b in zip(ps, ps[1:])) and ps[0] > ps[-1]


def test_unparsed_market_is_null_not_error():
    qg, dg = _frames(5)
    out = _rt(qg, dg).fields({"event_ticker": "junk", "floor_strike": 250}, NOW)
    assert out["model_p"] is None and out["model_status"] == "unparsed_market"


def test_no_network_in_fields_path(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("network call in the model's fields path")
    monkeypatch.setattr(urllib.request, "urlopen", boom)
    qg, dg = _frames(5)
    assert _rt(qg, dg).fields(_mkt(), NOW)["model_status"] == "ok"


def test_hook_never_raises(monkeypatch):
    monkeypatch.setattr(pm, "_RT", None)

    def bad(*a, **k):
        raise OSError("down")
    monkeypatch.setattr(pm, "Runtime", bad)
    out = pm.model_fields(_mkt(), NOW, root=ROOT)
    assert out["model_p"] is None and out["model_status"].startswith("error:OSError")
