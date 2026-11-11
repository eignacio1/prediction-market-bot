"""NHL decision tree by horizon (W109.2): how deep the board engine's conditioning goes, as a function of time to puck drop.

Doctrine (ADR-0068): the longer the horizon, the deeper the tree. The engine's rate model is a Poisson GLM on
``model.FEATS``; a "tree" here is the nested conditioning ladder over those same fitted coefficients:

  depth 0  league base + home ice                      (feature set: home)
  depth 1  + matchup cross (log expected xG)           (+ lx)
  depth 2  + rest state (own / opponent back-to-back)  (+ b2b_own, b2b_opp)
  depth 3  + goalie proxy (previous starter, GG-1010)  (+ gs_own, gs_opp)   == ``Fitted.rates`` exactly

A level that is not conditioned on has its feature replaced by the TRAINING-set mean of that feature (not zero), so a
truncated tree prices the average case for what it ignores. A level the horizon cannot reach is not guessed.

When it applies: pre-game and early-game pricing from the fitted board engine. When it does not: in-play after the first
period is better served by remaining-time arithmetic (``late_game``); the depth map below only says how much conditioning
a horizon is entitled to, it does not claim the shallow depths are faster here -- they are not, so a shallow depth in this
module is a documented fallback for missing inputs, not an optimisation.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .model import FEATS, Fitted, side_rows

# nested feature sets by depth
DEPTH_FEATS = {
    0: ("home",),
    1: ("home", "lx"),
    2: ("home", "lx", "b2b_own", "b2b_opp"),
    3: ("home", "lx", "b2b_own", "b2b_opp", "gs_own", "gs_opp"),
}
MAX_DEPTH = 3


def depth_for_horizon(hours_to_start: float) -> int:
    """Horizon -> permitted depth. >= 12h: full tree (rest and goalie proxy are knowable); 3h..12h: through rest state
    (the goalie is typically confirmed late); 0.5h..3h: matchup cross only; inside 30 minutes or in play: base."""
    h = float(hours_to_start)
    if h >= 12.0:
        return 3
    if h >= 3.0:
        return 2
    if h >= 0.5:
        return 1
    return 0


def training_means(fr: pd.DataFrame) -> dict:
    """Mean of each model feature on the TRAINING rows (the neutral value a dropped level is replaced by)."""
    x = side_rows(fr)
    return {f: float(x[f].mean()) for f in FEATS}


def rates_at_depth(m: Fitted, fr: pd.DataFrame, depth: int, means: dict) -> tuple:
    """(lam_h, lam_a) at a given depth. ``depth`` 3 equals ``m.rates(fr)``."""
    if depth not in DEPTH_FEATS:
        raise ValueError(f"depth must be one of {sorted(DEPTH_FEATS)}")
    x = side_rows(fr)
    keep = set(DEPTH_FEATS[depth])
    cols = []
    for f in FEATS:
        cols.append(x[f].to_numpy() if f in keep else np.full(len(x), means[f]))
    lam = np.exp(np.column_stack([np.ones(len(x))] + cols) @ m.coef)
    n = len(fr)
    return lam[:n], lam[n:]


def route(m: Fitted, fr: pd.DataFrame, hours_to_start: float, means: dict) -> tuple:
    """Pick the depth the horizon permits and return (depth, lam_h, lam_a)."""
    d = depth_for_horizon(hours_to_start)
    lh, la = rates_at_depth(m, fr, d, means)
    return d, lh, la
