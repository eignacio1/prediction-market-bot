"""W106.4 Part B: run-expectancy model from the lineup-aware design, priced into moneyline / total / run line.

Applies: any feature list from `lineup_aware` (ablations share one code path); runs per team-game, gamma-Poisson
(negative binomial) with one dispersion fitted on TRAINING data only, independent home/away runs (the joint grid
gives ML, total and run line from one distribution). Does not apply: within-game state, weather, umpire, injuries;
independence ignores the small positive home/away run correlation (stated, not corrected).
"""
from __future__ import annotations

from typing import Dict, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy.stats import nbinom
from sklearn.linear_model import PoissonRegressor

KMAX = 30


class RunModel:
    def __init__(self, features: Sequence[str], alpha: float = 1e-3):
        self.features, self.alpha = list(features), alpha
        self.reg = PoissonRegressor(alpha=alpha, max_iter=1000)
        self.coef, self.intercept = np.zeros(len(self.features)), 0.0
        self.k = 1e6  # NB size; huge = Poisson

    def fit(self, tr: pd.DataFrame) -> "RunModel":
        x, y = tr[self.features].to_numpy(float), tr["runs"].to_numpy(float)
        self.reg.fit(x, y)
        self.coef, self.intercept = np.asarray(self.reg.coef_, float), float(self.reg.intercept_)
        mu = self.lam(tr)
        # method of moments for var = mu + mu^2/k  ->  k = sum(mu^2) / sum((y-mu)^2 - mu)
        excess = float(np.sum((y - mu) ** 2 - mu))
        self.k = float(np.sum(mu ** 2) / excess) if excess > 0 else 1e6
        return self

    def lam(self, d: pd.DataFrame) -> np.ndarray:
        return np.exp(d[self.features].to_numpy(float) @ self.coef + self.intercept)


def _pmf(lam: np.ndarray, k: float) -> np.ndarray:
    kk = np.arange(KMAX + 1)[None, :]
    return nbinom.pmf(kk, k, k / (k + lam[:, None]))


def price(model: RunModel, d: pd.DataFrame, total_line: float = 8.5) -> pd.DataFrame:
    """One row per game: p_home (ML), p_over (total_line), p_home_rl (home -1.5 covers), plus outcomes."""
    d = d.copy()
    d["lam"] = model.lam(d)
    h = d[d.team_side == "home"].set_index("game_pk")
    a = d[d.team_side == "away"].set_index("game_pk")
    ix = h.index.intersection(a.index)
    ph, pa = _pmf(h.loc[ix, "lam"].to_numpy(), model.k), _pmf(a.loc[ix, "lam"].to_numpy(), model.k)
    ph, pa = ph / ph.sum(1, keepdims=True), pa / pa.sum(1, keepdims=True)
    joint = ph[:, :, None] * pa[:, None, :]  # n x home runs x away runs
    hh, aa = np.meshgrid(np.arange(KMAX + 1), np.arange(KMAX + 1), indexing="ij")
    margin, tot = hh - aa, hh + aa
    win = (joint * (margin > 0)).sum((1, 2))
    tie = (joint * (margin == 0)).sum((1, 2))
    out = pd.DataFrame({"game_pk": ix, "game_date": h.loc[ix, "game_date"].to_numpy(),
                        "p_home": win + 0.5 * tie,  # extra innings split evenly
                        "p_over": (joint * (tot > total_line)).sum((1, 2)),
                        "p_home_rl": (joint * (margin >= 2)).sum((1, 2)),
                        "home_runs": h.loc[ix, "runs"].to_numpy(), "away_runs": a.loc[ix, "runs"].to_numpy()})
    out["home_win"] = (out.home_runs > out.away_runs).astype(float)
    out["over"] = ((out.home_runs + out.away_runs) > total_line).astype(float)
    out["home_rl"] = ((out.home_runs - out.away_runs) >= 2).astype(float)
    return out.reset_index(drop=True)


def logloss(p: np.ndarray, y: np.ndarray, eps: float = 1e-6) -> float:
    p = np.clip(p, eps, 1 - eps)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def brier(p: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean((p - y) ** 2))


def boot_gain(p_model: np.ndarray, p_base: np.ndarray, y: np.ndarray, kind: str = "brier", n: int = 2000,
              seed: int = 7) -> Tuple[float, float, float]:
    """Loss(base) - Loss(model), game-level bootstrap 95% interval; positive = model better."""
    if kind == "brier":
        e = (p_base - y) ** 2 - (p_model - y) ** 2
    else:
        pm, pb = np.clip(p_model, 1e-6, 1 - 1e-6), np.clip(p_base, 1e-6, 1 - 1e-6)
        e = -(y * np.log(pb) + (1 - y) * np.log(1 - pb)) + (y * np.log(pm) + (1 - y) * np.log(1 - pm))
    rng = np.random.default_rng(seed)
    bs = e[rng.integers(0, len(e), size=(n, len(e)))].mean(axis=1)
    return float(e.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def naive(train_y: np.ndarray, n: int) -> np.ndarray:
    return np.full(n, float(np.mean(train_y)))


def score(pr: pd.DataFrame, base: Dict[str, float]) -> Dict[str, dict]:
    """Brier / log loss vs the naive constant (train base rate) per market, with intervals."""
    res = {}
    for name, pc, yc in (("moneyline", "p_home", "home_win"), ("total", "p_over", "over"),
                         ("runline", "p_home_rl", "home_rl")):
        p, y = pr[pc].to_numpy(), pr[yc].to_numpy()
        nv = np.full(len(y), base[yc])
        res[name] = {"n": len(y), "brier": brier(p, y), "brier_naive": brier(nv, y), "logloss": logloss(p, y),
                     "logloss_naive": logloss(nv, y), "gain_brier": boot_gain(p, nv, y, "brier"),
                     "gain_logloss": boot_gain(p, nv, y, "logloss")}
    return res
