"""W84.2: the PAM mass-tier point-in-time table uses only games strictly before each game (no look-ahead)."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

D = Path(__file__).resolve().parents[1] / "12_EXPLORATORY/nba_pam_mass_tier"
sys.path.insert(0, str(D))
spec = importlib.util.spec_from_file_location("mass_tier", D / "mass_tier.py")
mt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mt)


def _frame(own_pts=20, future_pts=10):
    rows = []
    for g in range(12):
        row = {c: 0.0 for c in mt.SUM_COLS}
        pts = own_pts if g == 6 else future_pts if g > 6 else 10
        row.update(g=1.0, min=30.0, fga=10.0, fgm=5.0, pts=float(pts), tm_min=240.0, tm_fga=90.0)
        row.update(season=2026, person_id=1, game_id=f"g{g:02d}", game_date=f"2026-01-{g + 1:02d}")
        rows.append(row)
    return pd.DataFrame(rows)


def _row(df, gid):
    return df[df.game_id == gid].iloc[0]


def test_pit_row_ignores_own_and_future_games():
    a = mt.pit_table(_frame(own_pts=20, future_pts=10), 2026)
    b = mt.pit_table(_frame(own_pts=99, future_pts=77), 2026)
    for col in ("gp", "mpg", "usg", "ts"):
        x, y = _row(a, "g06")[col], _row(b, "g06")[col]
        assert (np.isnan(x) and np.isnan(y)) or x == y


def test_first_game_has_no_prior_and_gp_counts_strictly_before():
    t = mt.pit_table(_frame(), 2026)
    assert t[t.game_id == "g00"].iloc[0].gp != t[t.game_id == "g00"].iloc[0].gp or t[t.game_id == "g00"].iloc[0].gp == 0
    assert _row(t, "g06").gp == 6
