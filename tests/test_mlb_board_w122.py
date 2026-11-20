"""W122.4: the board pricer's ladders are coherent with one joint grid (monotone, margin/total identities)."""
import numpy as np
import pandas as pd

from prediction_market_bot.mlb_engine import board as bd
from prediction_market_bot.mlb_engine.model_lineup import RunModel


def _frame(n=40, seed=1):
    rng = np.random.default_rng(seed)
    rows = []
    for g in range(n):
        for side in ("home", "away"):
            rows.append({"game_pk": g, "game_date": pd.Timestamp("2026-05-01"), "team_side": side,
                         "is_home": float(side == "home"), "runs": float(rng.poisson(4.4))})
    return pd.DataFrame(rows)


def test_board_ladders_are_monotone_and_bounded():
    d = _frame()
    b = bd.price_board(RunModel(["is_home"]).fit(d), d)
    assert len(b) == 40
    for fam_cols in ([f"ge_total_{k}" for k in bd.TOTAL_RUNGS], [f"home_by_ge_{k}" for k in bd.SPREAD_RUNGS],
                     [f"home_runs_ge_{k}" for k in bd.TEAM_RUNGS]):
        m = b[fam_cols].to_numpy()
        assert (np.diff(m, axis=1) <= 1e-12).all() and (m >= 0).all() and (m <= 1).all()


def test_moneyline_and_spread_identities():
    d = _frame()
    b = bd.price_board(RunModel(["is_home"]).fit(d), d)
    # P(home by>=1) + P(away by>=1) + P(tie) = 1, and ML splits the tie evenly
    tie = 1 - b.home_by_ge_1 - b.away_by_ge_1
    assert (tie >= -1e-9).all()
    assert np.allclose(b.p_home_ml, b.home_by_ge_1 + 0.5 * tie, atol=1e-9)


def test_realized_units_match_ladder_units():
    b = pd.DataFrame({"home_runs": [5, 2], "away_runs": [3, 2]})
    assert bd.realized(b, "spread", "home", 2).tolist() == [1.0, 0.0]
    assert bd.realized(b, "total", "home", 7).tolist() == [1.0, 0.0]
    assert bd.realized(b, "team_total", "away", 3).tolist() == [1.0, 0.0]
    assert bd.column("spread", "away", 2) == "away_by_ge_2"
