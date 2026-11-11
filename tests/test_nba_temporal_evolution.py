"""Known-answer tests for the NBA temporal-evolution scaffold (W109.1 Part B)."""
import numpy as np
import pandas as pd

from prediction_market_bot.nba_engine import temporal_evolution as te


def _league(*, seasons=8, teams=30, games=82, noise=1.0, talent_sd=0.5, league_slope=0.0, reset=False, seed=1):
    rng = np.random.default_rng(seed)
    talent = rng.normal(0, talent_sd, teams)
    rows = []
    for s in range(2016, 2016 + seasons):
        if reset:
            talent = rng.normal(0, talent_sd, teams)
        for g in range(1, games + 1):
            for t in range(teams):
                rows.append((t, s, g, talent[t] + league_slope * g + rng.normal(0, noise)))
    return pd.DataFrame(rows, columns=["team", "season", "week", "v"])


def test_team_game_long_numbers_games_by_date_per_team():
    g = pd.DataFrame({"season": [1, 1, 1], "date": pd.to_datetime(["2020-01-03", "2020-01-01", "2020-01-02"]),
                      "home": ["A", "A", "B"], "away": ["B", "C", "C"], "h": [1.0, 2.0, 3.0], "a": [4.0, 5.0, 6.0]})
    long = te.team_game_long(g, "h", "a")
    a = long[long.team == "A"].sort_values("week")
    assert list(a.week) == [1, 2] and list(a.v) == [2.0, 1.0]       # A's 01-01 game (v=2) precedes its 01-03 game (v=1)
    assert long.groupby("team").week.max().to_dict() == {"A": 2, "B": 2, "C": 2}


def test_asof_is_point_in_time():
    y = [1.0, 2.0, 3.0, 4.0]
    assert np.allclose(te.asof_ew(y, 2)[:3], te.asof_ew([1.0, 2.0, 3.0, 999.0], 2)[:3], equal_nan=True)
    assert np.isnan(te.asof_ew(y, 2)[0])


def test_in_season_league_drift_is_tracked_per_game():
    d = te.within_season_slope(_league(league_slope=0.01, seed=2), n_boot=300)
    assert d["lo"] < 0.01 < d["hi"] and d["lo"] > 0
    flat = te.within_season_slope(_league(league_slope=0.0, seed=3), n_boot=300)
    assert flat["lo"] < 0 < flat["hi"]


def test_blend_weight_releases_the_prior_when_talent_is_stable_and_not_when_it_resets():
    stable = te.blend_weight_by_game(_league(seed=4, reset=False), n_boot=60)
    reset = te.blend_weight_by_game(_league(seed=5, reset=True), n_boot=60)
    assert [r["games"] for r in stable] == ["5-20", "21-50", "51-82"]
    assert all(r["w_prev_season"] > 0.2 for r in stable)            # last season's level carries information
    assert all(abs(r["w_prev_season"]) < 0.2 for r in reset)        # a reset talent pool makes it carry none
