"""NBA engine v3 (W96.1): v2's closed-form pricing plus pre-tip availability and lineup shifts.

v3 adds nothing to v2's pricing math; it is v2 with named factors fed through ``engine_v2.fit_params`` / ``game_means``.
What is new is the factor contract: every factor is centred on its TRAINING mean (so a missing value is the neutral value, not a
spurious level shift) and carries the side convention used to build it. Officials are deliberately absent: the crew is not known
before the price (GG-1390), so it cannot be a pricing input.

When it applies: a factor is carried only if it improved held-out Brier for some family over v2 (study_v3.py, results_W96_1.md).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

import numpy as np

from . import engine_v2 as V

# name -> (target, game-level column, how the column is built)
FACTORS: Dict[str, Tuple[str, str, str]] = {
    "d_exp_missing": ("margin", "d_exp_missing", "home - away expected missing rotation-minute share (statuses at tip_earliest)"),
    "s_exp_missing": ("total", "s_exp_missing", "home + away expected missing rotation-minute share"),
    "d_lineup_net": ("margin", "d_lineup_net", "home - away rotation-weighted prior-game player net rating"),
    "s_lineup_net": ("total", "s_lineup_net", "home + away rotation-weighted prior-game player net rating"),
}


@dataclass(frozen=True)
class Centers:
    mean: Dict[str, float]

    def apply(self, x: Dict[str, float]) -> Dict[str, float]:
        """Centre raw factor values; absent / non-finite values become 0.0 (the training mean)."""
        out = {}
        for f, mu in self.mean.items():
            v = x.get(f)
            out[f] = float(v) - mu if v is not None and np.isfinite(v) else 0.0
        return out


def fit_centers(columns: Dict[str, np.ndarray]) -> Centers:
    """Training means per factor, ignoring non-finite entries."""
    return Centers({f: float(np.nanmean(np.asarray(v, float))) for f, v in columns.items()})


def split_targets(names: Iterable[str]) -> Tuple[list, list]:
    names = list(names)
    return [f for f in names if FACTORS[f][0] == "margin"], [f for f in names if FACTORS[f][0] == "total"]


def fit(mu_h, mu_a, home_pts, away_pts, columns: Dict[str, np.ndarray], names: Iterable[str]):
    """Fit v2 parameters with the chosen v3 factors on TRAINING games; returns (params, centers)."""
    names = list(names)
    centers = fit_centers({f: columns[f] for f in names})
    cen = {f: np.where(np.isfinite(columns[f]), np.asarray(columns[f], float) - centers.mean[f], 0.0) for f in names}
    mf, tf = split_targets(names)
    return V.fit_params(mu_h, mu_a, home_pts, away_pts, cen, mf, tf), centers


def game_means(p: V.V2Params, centers: Centers, mu_h: float, mu_a: float, x: Dict[str, float]) -> Tuple[float, float]:
    return V.game_means(p, mu_h, mu_a, centers.apply(x))
