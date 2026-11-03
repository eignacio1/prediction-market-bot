"""NHL engine model layer (W97.4 Part B): point-in-time features -> expected regulation goals -> the priced board.

``fit`` takes ``game_features`` rows from EARLIER seasons than the ones it will price (walk-forward is the caller's job;
nothing here sees an outcome it is not handed). Poisson GLM on log expected xG (the matchup cross), home ice, rest and the
goalie proxy; the shared-factor dispersion k and the home OT/SO win share are fit on the same training rows.

Applies to regular-season games with a play-by-play. Does not apply to playoff overtime or to games whose starter is
known to differ from the previous game's (the goalie factor is a proxy, see ``inputs.GOALIE_STARTER_NOTE``).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import goals
from .inputs import expected_xg

FEATS = ["lx", "home", "b2b_own", "b2b_opp", "gs_own", "gs_opp"]


def side_rows(fr: pd.DataFrame) -> pd.DataFrame:
    """Stack the frame to one row per (game, side) with the model's features."""
    out = []
    recs = fr.to_dict("records")
    for side in ("h", "a"):
        o = "a" if side == "h" else "h"
        out.append(pd.DataFrame({
            "game_id": [r["game_id"] for r in recs],
            "lx": [np.log(max(expected_xg(r, side), 1e-3)) for r in recs],
            "home": 1.0 if side == "h" else 0.0,
            "b2b_own": [float(r[f"rest_{side}"] < 1.5) for r in recs],
            "b2b_opp": [float(r[f"rest_{o}"] < 1.5) for r in recs],
            "gs_own": [r[f"gs_{side}"] for r in recs],
            "gs_opp": [r[f"gs_{o}"] for r in recs],
        }))
    return pd.concat(out, ignore_index=True)


def poisson_irls(x: np.ndarray, y: np.ndarray, l2: float = 1e-3, iters: int = 50) -> np.ndarray:
    """Ridge Poisson regression with log link by IRLS; returns [intercept, coefs]. The intercept is not penalised."""
    X = np.column_stack([np.ones(len(x)), x])
    b = np.zeros(X.shape[1]); b[0] = np.log(max(y.mean(), 1e-6))
    pen = l2 * np.eye(len(b)); pen[0, 0] = 0.0
    for _ in range(iters):
        mu = np.exp(np.clip(X @ b, -20, 20))
        step = np.linalg.solve(X.T @ (X * mu[:, None]) + pen, X.T @ (y - mu) - pen @ b)
        b += step
        if np.abs(step).max() < 1e-9:
            break
    return b


@dataclass
class Fitted:
    coef: np.ndarray
    k: float
    p_home_ot: float
    tie_odds: float = 1.0

    def rates(self, fr: pd.DataFrame):
        x = side_rows(fr)
        lam = np.exp(np.column_stack([np.ones(len(x)), x[FEATS].to_numpy()]) @ self.coef)
        n = len(fr)
        return lam[:n], lam[n:]


def fit(fr: pd.DataFrame, reg_h: np.ndarray, reg_a: np.ndarray, home_won: np.ndarray, force_poisson: bool = False,
        alpha: float = 1e-3) -> Fitted:
    x = side_rows(fr)
    y = np.concatenate([reg_h, reg_a]).astype(float)
    coef = poisson_irls(x[FEATS].to_numpy(), y, alpha)
    lam = np.exp(np.column_stack([np.ones(len(x)), x[FEATS].to_numpy()]) @ coef)
    n = len(fr)
    k = np.inf if force_poisson else goals.fit_dispersion(reg_h, reg_a, lam[:n], lam[n:])
    tie = reg_h == reg_a
    p_ot = float(np.mean(home_won[tie])) if tie.any() else 0.5
    t0 = float(goals.poisson_tie_prob(lam[:n], lam[n:]).mean()); t1 = float(tie.mean())
    odds = (t1 / (1 - t1)) / (t0 / (1 - t0)) if 0 < t0 < 1 and 0 < t1 < 1 else 1.0
    return Fitted(coef, k, p_ot, odds)


def price_games(m: Fitted, fr: pd.DataFrame, n_sim: int = 20000, seed: int = 0, rates: tuple = None) -> list:
    """Price every game's board. ``rates`` = (lam_h, lam_a) overrides the fitted rates (e.g. after ``level_adjust``)."""
    lh, la = rates if rates is not None else m.rates(fr)
    return [goals.price_board(goals.simulate(float(h), float(a), m.k, m.p_home_ot, n_sim, seed + i, m.tie_odds))
            for i, (h, a) in enumerate(zip(lh, la))]


def level_adjust(fr: pd.DataFrame, lam_h: np.ndarray, lam_a: np.ndarray, reg_h: np.ndarray, reg_a: np.ndarray,
                 prior_games: float = 150.0) -> tuple:
    """Point-in-time league-level recalibration: scale each game's rates by (goals scored + prior*g) / (goals predicted
    + prior*g) over games with a STRICTLY EARLIER puck drop within ``fr``, so no outcome from the game's own start or
    later enters. ``g`` is the mean predicted goals per game; ``prior_games`` games of weight pull the ratio to 1.
    Applies when the feature level can drift between seasons (the out-of-time xG model is refit each season); it cannot
    fix a team-specific bias. ``fr`` needs a ``start`` column; ``reg_h``/``reg_a`` are the realized regulation goals,
    read only for games already finished by each puck drop."""
    st = pd.to_datetime(fr["start"]).to_numpy()
    d = pd.DataFrame({"st": st, "act": np.asarray(reg_h, float) + np.asarray(reg_a, float),
                      "prd": np.asarray(lam_h, float) + np.asarray(lam_a, float), "n": 1.0}).groupby("st").sum().sort_index()
    c = d.cumsum().shift(1).fillna(0.0)
    g = float(d["prd"].sum() / d["n"].sum())
    ratio = ((c["act"] + prior_games * g) / (c["prd"] + prior_games * g)).reindex(st).to_numpy()
    return np.asarray(lam_h) * ratio, np.asarray(lam_a) * ratio
