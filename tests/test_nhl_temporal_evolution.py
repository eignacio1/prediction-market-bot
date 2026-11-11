"""W109.2 -- NHL temporal evolution (wrapper over the tested NFL generics): known answers on a planted drift."""
import numpy as np
import pandas as pd

from prediction_market_bot.nhl_engine import granularity_index as gi, temporal_evolution as te


def _tg(drift=0.0, team_effect=0.0, seed=0, teams=24, seasons=(2021, 2022, 2023), games=82):
    rng = np.random.default_rng(seed)
    rows = []
    for s in seasons:
        for t in range(teams):
            lvl = rng.normal(0, 1) * team_effect
            for g in range(1, games + 1):
                rows.append({"team": t, "season": s, "game_no": g, "gf": 3.0 + lvl + drift * (g - 41) + rng.normal(0, 1.5),
                             "ga": 3.0, "total": 6.0, "b2b": 0, "game_id": 0, "is_home": 0, "opp": 0, "start": 0, "rest": 2.0})
    return pd.DataFrame(rows)


def test_long_table_contract():
    d = te.team_game_long(_tg(games=10, teams=2, seasons=(2021,)), "gf")
    assert list(d.columns) == ["team", "season", "week", "v"] and len(d) == 20 and d["week"].min() == 1


def test_within_season_slope_recovers_planted_drift():
    r = te.within_season_slope(te.team_game_long(_tg(drift=0.01), "gf"))
    assert abs(r["slope_per_week"] - 0.01) < 0.003 and r["lo"] < 0.01 < r["hi"]
    null = te.within_season_slope(te.team_game_long(_tg(drift=0.0), "gf"))
    assert null["lo"] < 0 < null["hi"]


def test_nhl_blend_weight_prefers_this_season_when_teams_persist():
    # persistent team level inside a season but independent across seasons -> prior-season weight ~ 0, in-season > 0
    rng = np.random.default_rng(3)
    rows = []
    for s in range(2019, 2025):
        for t in range(30):
            lvl = rng.normal(0, 0.6)
            for g in range(1, 83):
                rows.append({"team": t, "season": s, "week": g, "v": 3.0 + lvl + rng.normal(0, 1.2)})
    out = te.nhl_blend_weight(pd.DataFrame(rows), n_boot=100)
    assert [o["weeks"] for o in out] == ["10-25", "26-50", "51-82"]
    late = out[-1]
    assert late["w_in_season"] > 0.4 and abs(late["w_prev_season"]) < 0.15
    assert out[0]["w_in_season"] <= late["w_in_season"] + 0.2


def test_asof_ew_is_point_in_time():
    v = [1.0, 2.0, 3.0, 4.0]
    a = te.asof_ew(v, 5.0)
    assert np.isnan(a[0]) and a[1] == 1.0
    v2 = v[:3] + [99.0]
    assert np.allclose(a[:3], te.asof_ew(v2, 5.0)[:3], equal_nan=True)


def test_reliability_gap_zero_for_stationary_teams():
    r = te.reliability_gap(te.team_game_long(_tg(team_effect=0.6, seed=2), "gf"), n_boot=200)
    assert r["r_odd_even"] > 0.2 and r["lo"] < 0.05 and abs(r["gap"]) < 0.25
