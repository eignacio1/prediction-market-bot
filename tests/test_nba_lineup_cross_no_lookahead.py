"""W81.2: the lineup-cross event builder uses only games strictly before G for roles, rotation and baselines."""
import importlib.util
from pathlib import Path

import pandas as pd

P = Path(__file__).resolve().parents[1] / "12_EXPLORATORY/20261020_nba_lineup_cross/lineup_cross.py"
spec = importlib.util.spec_from_file_location("lineup_cross", P)
lc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lc)


def _frames(pts_last=20, future_pts=10):
    pb, tg = [], []
    for g in range(14):
        gid = f"g{g:02d}"
        tg.append(dict(team_tricode="AAA", season=2020, game_id=gid, tg=g, o_team_tricode="BBB",
                       game_date=f"2020-01-{g+1:02d}", opp_def_pa30=100.0, opp_pace30=95.0))
        for pid in (1, 2, 3, 4, 5, 6):
            out = pid == 1 and g == 11  # star (highest FGA) injured in game 11
            pts = 10 if g < 11 else (pts_last if g == 11 and pid == 2 else future_pts if g > 11 else 10)
            pb.append(dict(team_tricode="AAA", season=2020, game_id=gid, person_id=pid,
                           played=not out, inj_dnp=out, **{"min": 0.0 if out else 30.0},
                           points=0 if out else pts, field_goals_attempted=0 if out else 20 - pid))
    return pd.DataFrame(pb), pd.DataFrame(tg)


def test_baseline_ignores_own_and_future_games():
    ev1 = lc.build_events(*_frames(pts_last=20, future_pts=10))
    ev2 = lc.build_events(*_frames(pts_last=20, future_pts=99))
    a = ev1[(ev1.game_id == "g11") & (ev1.b == 2)].iloc[0]
    b = ev2[(ev2.game_id == "g11") & (ev2.b == 2)].iloc[0]
    assert a.kind == "single" and a.role == "creator"
    assert a.d_pts == 10 == b.d_pts  # 20 actual - 10 trailing mean; independent of games after G
    ev3 = lc.build_events(*_frames(pts_last=50, future_pts=10))
    c = ev3[(ev3.game_id == "g11") & (ev3.b == 2)].iloc[0]
    assert c.d_pts == 40  # G's own points move the effect one-for-one, not the baseline
