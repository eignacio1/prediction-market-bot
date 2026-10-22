"""Point-in-time + fit checks for the EXPLORATORY NHL factor builder (W84.3). Synthetic data; no store needed."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "12_EXPLORATORY" / "nhl_engine"))
import factors as F  # noqa: E402
import run_w84_3 as R  # noqa: E402


def _tg(n=40):
    rng = np.random.default_rng(0)
    return pd.DataFrame({"team": ["A"] * n, "game_id": range(n), "xg_5v5": rng.random(n), "a_xg_5v5": rng.random(n),
                         "xg_pp": rng.random(n), "a_xg_pp": rng.random(n), "spp": 120.0, "spk": 120.0, "s5v5": 3000.0})


def test_rolling_excludes_current_game():
    a = F.rolling(_tg()); b = _tg(); b.loc[30, ["xg_5v5", "a_xg_5v5", "xg_pp", "a_xg_pp"]] = 99.0
    b = F.rolling(b)
    assert a.loc[30, "xg_share5"] == b.loc[30, "xg_share5"]      # game 30's own result does not enter its own row
    assert a.loc[31, "xg_share5"] != b.loc[31, "xg_share5"]      # but enters the next one


def test_rolling_unchanged_by_future_rows():
    full = F.rolling(_tg()); head = F.rolling(_tg().iloc[:25])
    assert np.allclose(full.loc[:24, "st_net60"].fillna(-1), head["st_net60"].fillna(-1))


def test_fit_lr_recovers_sign():
    rng = np.random.default_rng(1); X = rng.normal(size=(4000, 1)); y = (rng.random(4000) < 1 / (1 + np.exp(-1.5 * X[:, 0]))).astype(float)
    b = R.fit_lr(X, y); assert 1.2 < b[1] < 1.8
