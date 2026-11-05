"""NHL engine, W101.1 Part C (B-029): shrink the predicted game-total rate toward the league mean.

Pre-registered in 12_EXPLORATORY/nhl_engine/NHL_TOTALS_CHALLENGER_PREREGISTRATION_2026-11-05.md (committed before any
challenger row). Held-out predictions were over-spread (slope of actual total on predicted total ~0.4-0.5). This module
replaces each game's total rate T = lam_h + lam_a by ``m + s * (T - m)`` and keeps the home share; the merged
``model.py`` / ``model_pit.py`` are untouched and are reused for fitting, level adjustment and pricing.

``s`` is estimated from TRAINING games only (2-fold cross-fit by game-date parity) and clipped to [S_MIN, S_MAX]; no
test-season outcome enters it.
"""
from __future__ import annotations

from typing import Tuple

import numpy as np
import pandas as pd

from . import model as _m
from . import model_pit as _pit

S_MIN, S_MAX = 0.3, 1.0


def ols_slope(pred: np.ndarray, actual: np.ndarray) -> float:
    """Slope of ``actual`` regressed on ``pred`` (with intercept). 0.0 when ``pred`` has no variance."""
    p = np.asarray(pred, float); a = np.asarray(actual, float)
    pc = p - p.mean()
    den = float((pc ** 2).sum())
    return float((pc * (a - a.mean())).sum() / den) if den > 0 else 0.0


def shrink_rates(lam_h: np.ndarray, lam_a: np.ndarray, m: float, s: float) -> Tuple[np.ndarray, np.ndarray]:
    """T' = m + s*(T-m), home share kept. s=1 returns the input; s=0 sets every game's total to m."""
    lh = np.asarray(lam_h, float); la = np.asarray(lam_a, float)
    t = lh + la
    share = lh / t
    t2 = m + s * (t - m)
    return t2 * share, t2 * (1.0 - share)


def crossfit_slope(tr: pd.DataFrame, fit_fn) -> Tuple[float, float, int]:
    """(s, m, n): s = clipped OLS slope of actual regulation total on predicted T over 2-fold out-of-fold predictions inside
    ``tr`` (fold = parity of the day number of the puck drop); m = mean of the full-fit predicted T on ``tr``."""
    day = pd.to_datetime(tr["start"]).dt.dayofyear.to_numpy() + 366 * pd.to_datetime(tr["start"]).dt.year.to_numpy()
    fold = (day % 2).astype(int)
    pred = np.full(len(tr), np.nan)
    for f in (0, 1):
        a, b = tr[fold != f].reset_index(drop=True), tr[fold == f]
        mod = fit_fn(a)
        lh, la = mod.rates(b.reset_index(drop=True))
        pred[(fold == f)] = lh + la
    act = (tr["reg_h"] + tr["reg_a"]).to_numpy(float)
    s = float(np.clip(ols_slope(pred, act), S_MIN, S_MAX))
    full = fit_fn(tr)
    lh, la = full.rates(tr)
    return s, float((lh + la).mean()), len(tr)


def fit_pit(tr: pd.DataFrame):
    return _pit.fit_pit(tr, tr["reg_h"].to_numpy(), tr["reg_a"].to_numpy(), (tr["home_score"] > tr["away_score"]).to_numpy())


def challenger_rates(te: pd.DataFrame, mod, m: float, s: float) -> Tuple[np.ndarray, np.ndarray]:
    """Shrink then the unchanged point-in-time ``level_adjust`` (so level stays handled by the merged mechanism)."""
    lh, la = shrink_rates(*mod.rates(te), m, s)
    return _m.level_adjust(te, lh, la, te["reg_h"].to_numpy(), te["reg_a"].to_numpy())
