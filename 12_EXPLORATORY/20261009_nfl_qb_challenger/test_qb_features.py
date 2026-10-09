"""Look-ahead and equivalence tests for qb_features (W64.1). Synthetic data + (optional) real-data equivalence."""
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "src"))
from qb_features import ChallengerFeatures, shrunk_mean  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nfl_pregame_features import NFLPregameFeatureBuilder  # noqa: E402


def synth(n_weeks=12, seed=0, poison_from=None):
    """Two teams A,B playing each other weekly; QB 'q1' for A all along except a 'q2' start at the last week."""
    rng = np.random.default_rng(seed)
    sch, ts = [], []
    for w in range(1, n_weeks + 1):
        gd = (pd.Timestamp("2024-09-01") + pd.Timedelta(days=7 * w)).strftime("%Y-%m-%d")
        gid = f"g{w}"
        ea, eb = rng.normal(0.05, 0.2), rng.normal(-0.02, 0.2)
        if poison_from is not None and w >= poison_from:
            ea, eb = 50.0, -50.0  # absurd future values: must never reach an earlier game's features
        sch.append(dict(game_id=gid, season=2024, game_type="REG", week=w, gameday=gd, home_team="A", away_team="B",
                        home_score=24.0, away_score=20.0, home_rest=7, away_rest=7,
                        home_qb_id="q2" if w == n_weeks else "q1", away_qb_id="r1"))
        ts += [dict(season=2024, week=w, season_type="REG", game_id=gid, team="A", opponent_team="B", off_epa=ea),
               dict(season=2024, week=w, season_type="REG", game_id=gid, team="B", opponent_team="A", off_epa=eb)]
    s = pd.DataFrame(sch)
    return pd.DataFrame(ts), s, s


def test_k0_reproduces_frozen_builder():
    ts, s, e = synth()
    cf, fb = ChallengerFeatures(ts, s, e), NFLPregameFeatureBuilder(ts, s)
    for w in range(5, 13):
        d = pd.to_datetime(s.gameday[w - 1]).date()
        f = fb.row("A", "B", datetime(d.year, d.month, d.day, tzinfo=timezone.utc), 7, 7)["features"]
        r = cf.team_rates("A", d, 0.0)
        assert r["off_epa"] == pytest.approx(f["off_epa_h"], abs=1e-12)
        assert r["def_epa"] == pytest.approx(f["def_epa_h"], abs=1e-12)
        assert r["pf"] == pytest.approx(f["pf_h"], abs=1e-12) and r["pa"] == pytest.approx(f["pa_h"], abs=1e-12)


def test_future_rows_never_affect_earlier_game():
    ts0, s, e = synth(poison_from=None)
    ts1, _, _ = synth(poison_from=9)
    a, b = ChallengerFeatures(ts0, s, e), ChallengerFeatures(ts1, s, e)
    d = pd.to_datetime(s.gameday[7]).date()  # game 8: weeks >= 9 differ between the two worlds
    assert a.team_rates("A", d, 2.0) == b.team_rates("A", d, 2.0)
    qa, qb = a.projected_starter("A", d), b.projected_starter("A", d)
    assert a.qb_epa(qa, d) == b.qb_epa(qb, d)


def test_projected_starter_ignores_current_game_starter():
    ts, s, e = synth()
    cf = ChallengerFeatures(ts, s, e)
    d = pd.to_datetime(s.gameday[11]).date()  # last game: actual starter is q2, projection must still be q1
    assert cf.projected_starter("A", d) == "q1"
    # and the q2 start (on date d) is excluded from q2's own history at d
    assert cf.qb_epa("q2", d) == pytest.approx(cf._lm_epa.before(d))


def test_strictly_before_same_day_excluded():
    ts, s, e = synth()
    cf = ChallengerFeatures(ts, s, e)
    d = pd.to_datetime(s.gameday[6]).date()
    n_before = len([x for x in cf._qb_hist["q1"] if x[0] < d])
    assert n_before == 6


def test_shrink_limits():
    v = [0.1, 0.3]
    assert shrunk_mean(v, 0.85, 0.0, 9.9) == pytest.approx((0.1 * 0.85 + 0.3) / 1.85)
    assert shrunk_mean(v, 0.85, 1e9, 0.25) == pytest.approx(0.25, abs=1e-6)
    assert shrunk_mean([], 0.85, 2.0, 0.07) == pytest.approx(0.07)


def test_qb_shrinkage_toward_league_for_new_qb():
    ts, s, e = synth()
    cf = ChallengerFeatures(ts, s, e)
    d = pd.to_datetime(s.gameday[11]).date()
    mu = cf._lm_epa.before(d)
    assert cf.qb_epa(None, d) == pytest.approx(mu)
    assert cf.qb_epa("never_seen", d) == pytest.approx(mu)
    q1 = cf.qb_epa("q1", d)
    xs = [x[1] for x in cf._qb_hist["q1"] if x[0] < d][-16:]
    assert q1 == pytest.approx((sum(xs) + 6.0 * mu) / (len(xs) + 6.0))
