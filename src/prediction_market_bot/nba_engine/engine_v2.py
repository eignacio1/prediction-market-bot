"""NBA engine v2 (W94.1 Part C): v1's team means, plus an estimated score correlation, optional factor shifts and a
train-only calibration step. v1 (``engine.py``) is untouched and stays as pinned in EXP-044.

Model: home/away points ~ bivariate normal around mean margin m and mean total t. With residual variances Vm (margin) and
Vt (total) measured out of sample: per-team variance = (Vt + Vm) / 4 and score correlation rho = (Vt - Vm) / (Vt + Vm) -
rho is estimated, not assumed (v1 over-states it by ~0.06-0.09). Factors shift m and/or t by coefficients fit on training
seasons only. A per-family logistic (Platt) step is fit on training-season predictions only.

Every probability has a closed form (continuity-corrected at n - 0.5); ``simulate`` draws the same joint for parlays.
Nothing here touches an order, a position, a stake or a ledger row.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from statistics import NormalDist
from typing import Dict, Iterable, Tuple

import numpy as np

ND = NormalDist()
FAMILIES = ("ml", "spread", "total", "team_total")


@dataclass(frozen=True)
class V2Params:
    hca: float
    tbias: float
    sd_margin: float
    sd_total: float
    shift_margin: Dict[str, float] = field(default_factory=dict)   # factor -> points of margin per unit
    shift_total: Dict[str, float] = field(default_factory=dict)    # factor -> points of total per unit
    platt: Dict[str, Tuple[float, float]] = field(default_factory=dict)  # family -> (intercept, slope) on logit p

    @property
    def sd_team(self) -> float:
        return float(np.sqrt((self.sd_margin ** 2 + self.sd_total ** 2) / 4.0))

    @property
    def rho(self) -> float:
        vm, vt = self.sd_margin ** 2, self.sd_total ** 2
        return float((vt - vm) / (vt + vm))


def _ols(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    beta, *_ = np.linalg.lstsq(np.column_stack([np.ones(len(X)), X]), y, rcond=None)
    return beta


def fit_params(mu_h, mu_a, home_pts, away_pts, factors: Dict[str, np.ndarray] = None,
               margin_factors: Iterable[str] = (), total_factors: Iterable[str] = ()) -> V2Params:
    """Fit hca/level, factor shifts and residual SDs on TRAINING games only (arrays aligned by game)."""
    factors = factors or {}
    mu_h, mu_a = np.asarray(mu_h, float), np.asarray(mu_a, float)
    rm = (np.asarray(home_pts, float) - np.asarray(away_pts, float)) - (mu_h - mu_a)
    rt = (np.asarray(home_pts, float) + np.asarray(away_pts, float)) - (mu_h + mu_a)
    mf, tf = list(margin_factors), list(total_factors)
    sm, st = {}, {}
    if mf:
        b = _ols(np.column_stack([factors[f] for f in mf]), rm)
        sm, hca = dict(zip(mf, map(float, b[1:]))), float(b[0])
        rm = rm - np.column_stack([factors[f] for f in mf]) @ b[1:]
    else:
        hca = float(rm.mean())
    if tf:
        b = _ols(np.column_stack([factors[f] for f in tf]), rt)
        st, tbias = dict(zip(tf, map(float, b[1:]))), float(b[0])
        rt = rt - np.column_stack([factors[f] for f in tf]) @ b[1:]
    else:
        tbias = float(rt.mean())
    return V2Params(hca=hca, tbias=tbias, sd_margin=float(np.std(rm - rm.mean())), sd_total=float(np.std(rt - rt.mean())),
                    shift_margin=sm, shift_total=st)


def game_means(p: V2Params, mu_h: float, mu_a: float, x: Dict[str, float] = None) -> Tuple[float, float]:
    """(mean margin, mean total) for one game; ``x`` maps factor name -> value (missing factor = no shift)."""
    x = x or {}
    m = (mu_h - mu_a) + p.hca + sum(c * x.get(f, 0.0) for f, c in p.shift_margin.items())
    t = (mu_h + mu_a) + p.tbias + sum(c * x.get(f, 0.0) for f, c in p.shift_total.items())
    return float(m), float(t)


def _surv(mean: float, sd: float, n: int, margin: bool = False) -> float:
    """P(X >= n) for integer X with continuity correction. A margin of exactly 0 goes to overtime and splits evenly, so the
    "wins" boundary (n = 1) sits at 0, not 0.5."""
    cut = 0.0 if (margin and n == 1) else n - 0.5
    return 1.0 - ND.cdf((cut - mean) / sd)


def raw_prob(p: V2Params, family: str, m: float, t: float, n: int) -> float:
    """P(event) before the calibration step. ml: home wins (n ignored); spread: home margin >= n; total: total >= n;
    team_total: the HOME team's points >= n (the away team is the same call with m negated)."""
    if family == "ml":
        return _surv(m, p.sd_margin, 1, True)
    if family == "spread":
        return _surv(m, p.sd_margin, n, True)
    if family == "total":
        return _surv(t, p.sd_total, n)
    if family == "team_total":
        return _surv((t + m) / 2.0, p.sd_team, n)
    raise ValueError(family)


def logit(q: float) -> float:
    q = min(max(q, 1e-4), 1 - 1e-4)
    return float(np.log(q / (1 - q)))


def calibrated(p: V2Params, family: str, raw: float) -> float:
    a, b = p.platt.get(family, (0.0, 1.0))
    return float(1.0 / (1.0 + np.exp(-(a + b * logit(raw)))))


def fit_platt(raw: np.ndarray, y: np.ndarray, iters: int = 30) -> Tuple[float, float]:
    """Logistic recalibration (intercept, slope on logit raw) by Newton, on training predictions only."""
    x = np.log(np.clip(raw, 1e-4, 1 - 1e-4) / (1 - np.clip(raw, 1e-4, 1 - 1e-4)))
    X = np.column_stack([np.ones_like(x), x])
    b = np.array([0.0, 1.0])
    for _ in range(iters):
        mu = 1 / (1 + np.exp(-X @ b))
        W = mu * (1 - mu)
        b = b + np.linalg.solve(X.T @ (X * W[:, None]) + 1e-9 * np.eye(2), X.T @ (y - mu))
    return float(b[0]), float(b[1])


def with_platt(p: V2Params, platt: Dict[str, Tuple[float, float]]) -> V2Params:
    return V2Params(p.hca, p.tbias, p.sd_margin, p.sd_total, p.shift_margin, p.shift_total, dict(platt))


def simulate(p: V2Params, m: float, t: float, n: int = 20000, seed: int = 0):
    """Joint (home, away) points draws from the same bivariate normal, continuous (so P(margin >= k) matches the closed
    form at k - 0.5 after rounding). Returns (home_pts, away_pts) arrays; ties are broken by a coin flip."""
    rng = np.random.default_rng(seed)
    z = rng.standard_normal((2, n))
    sd, rho = p.sd_team, p.rho
    e_h = sd * z[0]
    e_a = sd * (rho * z[0] + np.sqrt(max(1 - rho ** 2, 0.0)) * z[1])
    h = np.rint((t + m) / 2.0 + e_h)
    a = np.rint((t - m) / 2.0 + e_a)
    tied = h == a
    h[tied] += np.where(rng.random(int(tied.sum())) < 0.5, 1.0, 0.0)
    return h, a
