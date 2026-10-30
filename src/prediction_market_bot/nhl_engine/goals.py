"""Team goals as a shared-factor count distribution, with Kalshi's overtime / shootout settlement (W97.4 Part B).

Regulation goals: H ~ Poisson(lam_h * G), A ~ Poisson(lam_a * G), G ~ Gamma(shape=k, scale=1/k) shared by both teams.
Marginals are negative binomial (variance lam + lam^2/k); the shared G gives a positive score correlation
corr = sqrt(lam_h*lam_a) * var(G) / sqrt((1+lam_h*var(G)) (1+lam_a*var(G)))-ish, measured, not assumed (``score_corr``).
k = inf is the independent Poisson. Which of the two fits is a measured choice (results_W97_4.md), not a default.

Settlement (Kalshi KXNHLGAME / SPREAD / TOTAL / TEAMTOTAL rules, read 2026-10-30): goals in regulation and overtime
count as normal; a shootout winner is credited ONE goal. So a regulation tie is always broken: the OT/SO winner ends
one goal ahead, the total is 2h+1, and the loser's team total is unchanged. The moneyline includes OT/SO.
Empty-net goals are inside the regulation counts (the dispersion k absorbs them); they are not modelled separately.

Applies to regular-season and playoff-regular-format games. Does not apply to playoff overtime (sudden-death 20-min
periods: a tie is broken by goals, not a single credited goal).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class GoalSample:
    home: np.ndarray   # final settled goals per simulation (OT/SO credit included)
    away: np.ndarray
    reg_home: np.ndarray
    reg_away: np.ndarray


def simulate(lam_h: float, lam_a: float, k: float = np.inf, p_home_ot: float = 0.5, n: int = 200000,
             seed: int = 0) -> GoalSample:
    rng = np.random.default_rng(seed)
    if np.isfinite(k):
        g = rng.gamma(k, 1.0 / k, size=n)
    else:
        g = np.ones(n)
    h = rng.poisson(lam_h * g)
    a = rng.poisson(lam_a * g)
    tie = h == a
    home_wins_ot = rng.random(n) < p_home_ot
    fh = h + (tie & home_wins_ot)
    fa = a + (tie & ~home_wins_ot)
    return GoalSample(fh, fa, h, a)


def p_moneyline_home(s: GoalSample) -> float:
    return float(np.mean(s.home > s.away))


def p_home_wins_by_over(s: GoalSample, strike: float) -> float:
    """P(home wins by over ``strike`` goals), strike = N-0.5 (Kalshi 'wins by over N-0.5 goals')."""
    return float(np.mean((s.home - s.away) > strike))


def p_away_wins_by_over(s: GoalSample, strike: float) -> float:
    return float(np.mean((s.away - s.home) > strike))


def p_total_over(s: GoalSample, strike: float) -> float:
    return float(np.mean((s.home + s.away) > strike))


def p_team_total_over(s: GoalSample, side: str, strike: float) -> float:
    x = s.home if side == "home" else s.away
    return float(np.mean(x > strike))


def score_corr(s: GoalSample) -> float:
    return float(np.corrcoef(s.reg_home, s.reg_away)[0, 1])


def price_board(s: GoalSample, spreads=(0.5, 1.5, 2.5, 3.5), totals=(3.5, 4.5, 5.5, 6.5, 7.5, 8.5),
                team_totals=(0.5, 1.5, 2.5, 3.5, 4.5, 5.5)) -> dict:
    """Every number is a sample frequency of the one joint distribution, so every ladder is coherent by construction."""
    return {
        "moneyline_home": p_moneyline_home(s),
        "home_wins_by_over": {x: p_home_wins_by_over(s, x) for x in spreads},
        "away_wins_by_over": {x: p_away_wins_by_over(s, x) for x in spreads},
        "total_over": {x: p_total_over(s, x) for x in totals},
        "home_goals_over": {x: p_team_total_over(s, "home", x) for x in team_totals},
        "away_goals_over": {x: p_team_total_over(s, "away", x) for x in team_totals},
        "score_corr": score_corr(s),
    }


def fit_dispersion(h: np.ndarray, a: np.ndarray, lam_h: np.ndarray, lam_a: np.ndarray) -> float:
    """Method-of-moments shared-factor shape k from regulation goals given per-game rates: Cov(H,A) = lam_h*lam_a*var(G),
    var(G) = 1/k. Returns np.inf when the covariance is not positive (the independent Poisson)."""
    resid = (h - lam_h) * (a - lam_a)
    denom = float(np.mean(lam_h * lam_a))
    v = float(np.mean(resid)) / denom if denom > 0 else 0.0
    return float(1.0 / v) if v > 1e-9 else float("inf")
