"""Known-answer tests for the NFL temporal-evolution scaffold (W94.2 Part B)."""
import numpy as np
import pandas as pd

from prediction_market_bot.nfl_engine import temporal_evolution as te


def _league(*, seasons=10, teams=32, weeks=17, noise=1.0, talent_sd=0.5, league_slope=0.0,
            walk_sd=0.0, reset_each_season=False, seed=1) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    talent = rng.normal(0, talent_sd, teams)
    rows = []
    for s in range(2010, 2010 + seasons):
        if reset_each_season:
            talent = rng.normal(0, talent_sd, teams)
        cur = talent.copy()
        for w in range(1, weeks + 1):
            cur = cur + rng.normal(0, walk_sd, teams)
            for t in range(teams):
                rows.append((t, s, w, cur[t] + league_slope * w + rng.normal(0, noise)))
    return pd.DataFrame(rows, columns=["team", "season", "week", "v"])


def test_asof_ew_is_point_in_time_and_recovers_constant():
    x = [3.0, 3.0, 3.0, 3.0]
    out = te.asof_ew(x, halflife=2)
    assert np.isnan(out[0]) and np.allclose(out[1:], 3.0)
    y = [1.0, 2.0, 3.0, 4.0]
    base = te.asof_ew(y, halflife=2)
    y2 = [1.0, 2.0, 3.0, 999.0]                          # a future value must not move earlier outputs
    assert np.allclose(base[:4], te.asof_ew(y2, halflife=2)[:4], equal_nan=True)
    assert te.asof_ew(y, halflife=1)[3] > te.asof_ew(y, halflife=50)[3]   # short half-life leans on recent


def test_league_drift_is_tracked_and_stable_reads_stable():
    drift = te.within_season_slope(_league(league_slope=0.02, seed=2), n_boot=400)
    assert drift["lo"] < 0.02 < drift["hi"] and drift["lo"] > 0
    stable = te.within_season_slope(_league(league_slope=0.0, seed=3), n_boot=400)
    assert stable["lo"] < 0 < stable["hi"]


def test_team_drift_opens_the_reliability_gap_and_stable_does_not():
    drifting = te.reliability_gap(_league(walk_sd=0.35, noise=0.8, seed=4), n_boot=300)
    assert drifting["lo"] > 0 and drifting["r_odd_even"] > drifting["r_early_late"]
    stable = te.reliability_gap(_league(walk_sd=0.0, noise=0.8, seed=5), n_boot=300)
    assert stable["lo"] < 0 < stable["hi"]


def test_blend_weight_releases_prior_when_talent_resets():
    reset = te.blend_weight_by_week(_league(reset_each_season=True, talent_sd=0.8, noise=0.8, seed=6), n_boot=150)
    assert reset and all(abs(r["w_prev_season"]) < 0.1 for r in reset)
    assert all(r["w_in_season"] > 0.3 for r in reset)
    keep = te.blend_weight_by_week(_league(reset_each_season=False, talent_sd=0.8, noise=0.8, seed=7), n_boot=150)
    assert all(r["w_prev_season"] > 0.15 for r in keep)
