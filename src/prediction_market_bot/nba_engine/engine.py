"""Possession-pace Monte Carlo of the two scores; every market is a pure function of the sample (W93.3, ADR-0073).

Per game: P ~ N(mu_poss, s_p) shared possessions, e_h/e_a ~ N(0, s_e) points-per-100 noise, integer scores, ties broken by
overtime. Score correlation is an output (measured by ``score_corr``), not an input.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

OT_FRACTION = 5.0 / 48.0


@dataclass(frozen=True)
class GameSample:
    home_pts: np.ndarray
    away_pts: np.ndarray

    @property
    def margin(self) -> np.ndarray:
        return self.home_pts - self.away_pts

    @property
    def total(self) -> np.ndarray:
        return self.home_pts + self.away_pts


def simulate(mu_poss: float, ppp_h: float, ppp_a: float, hca: float, s_p: float, s_e: float, n: int = 20000,
             seed: int = 0) -> GameSample:
    """Joint sample of integer (home, away) scores. Same ``seed`` = common random numbers across games/parameters."""
    rng = np.random.default_rng(seed)
    z_p, z_h, z_a = rng.standard_normal(n), rng.standard_normal(n), rng.standard_normal(n)
    poss = np.maximum(mu_poss + s_p * z_p, 60.0)
    h = np.rint(poss * (ppp_h + s_e * z_h) / 100.0 + hca / 2.0)
    a = np.rint(poss * (ppp_a + s_e * z_a) / 100.0 - hca / 2.0)
    tied = np.flatnonzero(h == a)
    guard = 0
    while tied.size and guard < 20:
        guard += 1
        k = tied.size
        p_ot = np.maximum(mu_poss * OT_FRACTION + s_p * OT_FRACTION * rng.standard_normal(k), 3.0)
        h[tied] += np.rint(p_ot * (ppp_h + s_e * rng.standard_normal(k)) / 100.0)
        a[tied] += np.rint(p_ot * (ppp_a + s_e * rng.standard_normal(k)) / 100.0)
        tied = tied[h[tied] == a[tied]]
    h[tied] += 1.0  # vanishing-probability residual: break by one point so the ML is never a push
    return GameSample(h, a)


def p_moneyline_home(s: GameSample) -> float:
    return float(np.mean(s.margin > 0))


def p_margin_ge(s: GameSample, n: int) -> float:
    """P(home wins by >= n), n integer (Kalshi suffix N = strike N-0.5). n=1 is the moneyline."""
    return float(np.mean(s.margin >= n))


def p_away_margin_ge(s: GameSample, n: int) -> float:
    return float(np.mean(-s.margin >= n))


def p_total_ge(s: GameSample, n: int) -> float:
    return float(np.mean(s.total >= n))


def p_team_total_ge(s: GameSample, side: str, n: int) -> float:
    pts = s.home_pts if side == "home" else s.away_pts
    return float(np.mean(pts >= n))


def p_joint(s: GameSample, margin_ge: int, total_ge: int) -> float:
    """Parlay leg pair from the same draws: home wins by >= margin_ge AND total >= total_ge."""
    return float(np.mean((s.margin >= margin_ge) & (s.total >= total_ge)))


def score_corr(s: GameSample) -> float:
    return float(np.corrcoef(s.home_pts, s.away_pts)[0, 1])


def fit_shape(resid_margin: np.ndarray, resid_total: np.ndarray, mu_poss: float, mu_total: float) -> tuple:
    """Moment-match (s_p, s_e) from out-of-sample residual SDs by linearising pts = P*(ppp+e)/100.

    Var(margin) ~ 2*(mu_poss/100)^2 s_e^2 (home/away means equal to first order); Var(total) ~ (mu_total/mu_poss)^2 s_p^2
    + 2*(mu_poss/100)^2 s_e^2. Applies to residuals from a model whose means are out of sample."""
    v_m, v_t = float(np.var(resid_margin)), float(np.var(resid_total))
    s_e = np.sqrt(max(v_m, 1e-9) / (2.0 * (mu_poss / 100.0) ** 2))
    rest = v_t - 2.0 * (mu_poss / 100.0) ** 2 * s_e ** 2
    s_p = np.sqrt(max(rest, 1e-9)) * mu_poss / mu_total
    return float(s_p), float(s_e)
