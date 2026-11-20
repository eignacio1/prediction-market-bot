"""W122.4 Part A: the whole MLB board from ONE joint run grid (moneyline, run-line ladder, total ladder, team totals).

Applies: `model_lineup.RunModel` (negative-binomial runs, independent home/away) priced into every ladder rung the Kalshi
MLB series list. Rung units (the Kalshi suffix k): KXMLBTOTAL k = total >= k; KXMLBSPREAD k = team wins by >= k runs
(k=2 is the -1.5 run line); KXMLBTEAMTOTAL k = that team scores >= k. Moneyline splits extra innings evenly.
Does not apply: within-game state, weather, umpire; home/away run correlation (independence stated, not corrected).
Inputs are point-in-time only if the design frame is: this module never reads outcomes except to attach them.
"""
from __future__ import annotations

from typing import Dict, Iterable

import numpy as np
import pandas as pd

from prediction_market_bot.mlb_engine.model_lineup import KMAX, RunModel, _pmf

TOTAL_RUNGS = tuple(range(3, 17))
SPREAD_RUNGS = tuple(range(1, 8))
TEAM_RUNGS = tuple(range(1, 13))


def joint_grid(model: RunModel, d: pd.DataFrame):
    """(game_pk index, home pmf, away pmf, joint n x (KMAX+1) x (KMAX+1)) for games with both team rows."""
    d = d.copy()
    d["lam"] = model.lam(d)
    h = d[d.team_side == "home"].set_index("game_pk")
    a = d[d.team_side == "away"].set_index("game_pk")
    ix = h.index.intersection(a.index)
    ph, pa = _pmf(h.loc[ix, "lam"].to_numpy(), model.k), _pmf(a.loc[ix, "lam"].to_numpy(), model.k)
    ph, pa = ph / ph.sum(1, keepdims=True), pa / pa.sum(1, keepdims=True)
    return ix, h, a, ph, pa, ph[:, :, None] * pa[:, None, :]


def price_board(model: RunModel, d: pd.DataFrame) -> pd.DataFrame:
    """One row per game: p_home_ml; ge_total_k; home_by_ge_k / away_by_ge_k; home_runs_ge_k / away_runs_ge_k; outcomes."""
    ix, h, a, ph, pa, joint = joint_grid(model, d)
    hh, aa = np.meshgrid(np.arange(KMAX + 1), np.arange(KMAX + 1), indexing="ij")
    margin, tot = hh - aa, hh + aa
    out: Dict[str, np.ndarray] = {
        "game_pk": np.asarray(ix), "game_date": h.loc[ix, "game_date"].to_numpy(),
        "p_home_ml": (joint * (margin > 0)).sum((1, 2)) + 0.5 * (joint * (margin == 0)).sum((1, 2)),
        "home_runs": h.loc[ix, "runs"].to_numpy(), "away_runs": a.loc[ix, "runs"].to_numpy()}
    for k in TOTAL_RUNGS:
        out[f"ge_total_{k}"] = (joint * (tot >= k)).sum((1, 2))
    for k in SPREAD_RUNGS:
        out[f"home_by_ge_{k}"] = (joint * (margin >= k)).sum((1, 2))
        out[f"away_by_ge_{k}"] = (joint * (-margin >= k)).sum((1, 2))
    cum_h, cum_a = ph[:, ::-1].cumsum(1)[:, ::-1], pa[:, ::-1].cumsum(1)[:, ::-1]  # P(runs >= k)
    for k in TEAM_RUNGS:
        out[f"home_runs_ge_{k}"], out[f"away_runs_ge_{k}"] = cum_h[:, k], cum_a[:, k]
    return pd.DataFrame(out)


def realized(board: pd.DataFrame, family: str, side: str, k: int) -> np.ndarray:
    """0/1 outcome of one rung, from the attached runs. family: moneyline|total|spread|team_total; side: home|away."""
    hr, ar = board.home_runs.to_numpy(), board.away_runs.to_numpy()
    if family == "moneyline":
        return ((hr > ar) if side == "home" else (ar > hr)).astype(float)
    if family == "total":
        return ((hr + ar) >= k).astype(float)
    if family == "spread":
        return (((hr - ar) if side == "home" else (ar - hr)) >= k).astype(float)
    return ((hr if side == "home" else ar) >= k).astype(float)


def column(family: str, side: str, k: int) -> str:
    return {"moneyline": "p_home_ml" if side == "home" else None,
            "total": f"ge_total_{k}", "spread": f"{side}_by_ge_{k}", "team_total": f"{side}_runs_ge_{k}"}[family]


def rungs(family: str) -> Iterable[int]:
    return {"total": TOTAL_RUNGS, "spread": SPREAD_RUNGS, "team_total": TEAM_RUNGS, "moneyline": (0,)}[family]
