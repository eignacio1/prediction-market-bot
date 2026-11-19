"""W119.1: goalie and special-teams classes. Point in time: the value stored for a game never uses a later game."""
import numpy as np
import pandas as pd

from prediction_market_bot.nhl_engine import factors_w112 as f


def _games(n):
    return pd.DataFrame({"game_id": [f"g{i}" for i in range(n)],
                         "start_time_utc": [f"2026-10-{i + 1:02d}T00:00:00+00:00" for i in range(n)],
                         "home_team_id": ["A"] * n, "away_team_id": ["B"] * n, "venue": ["x"] * n,
                         "game_type": [2] * n, "neutral_site": [False] * n})


def _box(n, sa=40, sv=36):
    rows = []
    for i in range(n):
        for t in ("A", "B"):
            rows.append(dict(game_id=f"g{i}", season=2026, team_id=t, player_id=f"G{t}", group="goalies", toi_s=3600,
                             pim=0, pp_goals=0, shots_against=sa, saves=sv, starter=True))
            rows.append(dict(game_id=f"g{i}", season=2026, team_id=t, player_id=f"S{t}", group="skaters", toi_s=1000,
                             pim=2 if t == "A" else 4, pp_goals=1 if t == "A" else 0, shots_against=np.nan, saves=np.nan,
                             starter=False))
    return pd.DataFrame(rows)


def test_goalie_nan_until_min_shots_then_shrunk():
    g = f.goalie_rolling(_box(4), _games(4)).sort_values("game_id")
    a = g[g.team_id == "A"].goalie_sv.tolist()
    assert np.isnan(a[0]) and np.isnan(a[1])          # 40, 80 shots < 100
    assert not np.isnan(a[2])                          # 120 shots
    assert abs(a[2] - 0.9) < 1e-9                      # league rate equals his rate, so shrinkage leaves 0.9


def test_goalie_no_leak_from_later_games():
    box = _box(5)
    base = f.goalie_rolling(box, _games(5)).set_index(["game_id", "team_id"]).goalie_sv
    box2 = box.copy(); box2.loc[box2.game_id == "g4", "saves"] = 0   # wreck the last game
    alt = f.goalie_rolling(box2, _games(5)).set_index(["game_id", "team_id"]).goalie_sv
    for gid in ("g0", "g1", "g2"):                                    # earlier rows do not move
        for t in ("A", "B"):
            a, b = base[(gid, t)], alt[(gid, t)]
            assert (np.isnan(a) and np.isnan(b)) or a == b


def test_special_teams_rolls_and_nan_before_five():
    s = f.special_teams_rolling(_box(8), _games(8)).sort_values("game_id")
    a = s[s.team_id == "A"]
    assert a.pp_for.isna().iloc[:4].all()
    last = a.iloc[-1]
    assert last.pp_for > 0 and last.pim_taken > 0
    b = s[s.team_id == "B"].iloc[-1]
    assert b.pp_for == 0 and b.pim_taken > last.pim_taken
