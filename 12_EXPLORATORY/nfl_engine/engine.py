"""EXPLORATORY -- NFL engine scaffold: possession-level Monte Carlo + pricing (W73.3, ADR-0073 stage 1). Not a verdict.

One simulation per game -> integer (home, away) scores + drive events; every market is a pure function of the sample.
Design and frozen parameters: PLAN.md / 02_ARCHITECTURE_DESIGN/NFL_ENGINE/INTERFACE.md. numpy only; no I/O.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

N0 = 11.0                      # mean possessions per team (fixed a priori)
TEAM_SD = 1.0                  # independent per-team possession noise (fixed a priori)
TD_MIX = (0.93, 0.04, 0.03)    # TD worth 7 / 6 / 8 (fixed a priori); mean 6.99
TD_MEAN = 6.99
P_TD_CAP = 0.55


@dataclass
class GameSample:
    home_pts: np.ndarray
    away_pts: np.ndarray
    td_h: np.ndarray
    td_a: np.ndarray
    fg_h: np.ndarray
    fg_a: np.ndarray
    n_poss_h: np.ndarray
    n_poss_a: np.ndarray
    went_ot: np.ndarray
    provenance: dict = field(default_factory=dict)

    @property
    def margin(self):
        return self.home_pts - self.away_pts

    @property
    def total(self):
        return self.home_pts + self.away_pts


def _rates(mu, r):
    p_td = np.minimum((mu / N0) / (TD_MEAN + 3.0 * r), P_TD_CAP)
    p_td = max(float(p_td), 1e-6)
    p_fg = min(r * p_td, 0.95 - p_td)
    return p_td, p_fg


def _team_regulation(rng, n_poss, p_td, p_fg):
    n_td = rng.binomial(n_poss, p_td)
    n_fg = rng.binomial(n_poss - n_td, p_fg / (1.0 - p_td))
    n6 = rng.binomial(n_td, TD_MIX[1])
    n8 = rng.binomial(n_td - n6, TD_MIX[2] / (1.0 - TD_MIX[1]))
    return 7 * n_td - n6 + n8 + 3 * n_fg, n_td, n_fg


def _one_possession(rng, k, p_td, p_fg):
    u = rng.random(k)
    return np.where(u < p_td, 7, np.where(u < p_td + p_fg, 3, 0))


def _overtime(rng, ph, pa, pts_h, pts_a):
    """Tied after regulation: one possession each; if still level, up to 2 alternating sudden-death possessions each; else tie."""
    tie = np.flatnonzero(pts_h == pts_a)
    if tie.size == 0:
        return np.zeros(len(pts_h), bool)
    h1, a1 = _one_possession(rng, tie.size, *ph), _one_possession(rng, tie.size, *pa)
    pts_h[tie] += h1
    pts_a[tie] += a1
    live = tie[h1 == a1]
    for _ in range(2):
        if live.size == 0:
            break
        h, a = _one_possession(rng, live.size, *ph), _one_possession(rng, live.size, *pa)
        pts_h[live] += h
        still = h == 0
        a = np.where(still, a, 0)
        pts_a[live] += a
        live = live[still & (a == 0)]
    went = np.zeros(len(pts_h), bool)
    went[tie] = True
    return went


def simulate(mu_h, mu_a, n, seed, r, s_n, delta=0.0, ot=True, provenance=None) -> GameSample:
    """n joint draws. mu_* = mean points (incl. OT) from the rating layer; delta = league OT add-on removed from regulation."""
    rng = np.random.default_rng(seed)
    pace = s_n * rng.standard_normal(n)
    nh = np.clip(np.rint(N0 + pace + TEAM_SD * rng.standard_normal(n)), 6, 22).astype(np.int64)
    na = np.clip(np.rint(N0 + pace + TEAM_SD * rng.standard_normal(n)), 6, 22).astype(np.int64)
    ph = _rates(max(mu_h - delta / 2.0, 1.0), r)
    pa = _rates(max(mu_a - delta / 2.0, 1.0), r)
    pts_h, td_h, fg_h = _team_regulation(rng, nh, *ph)
    pts_a, td_a, fg_a = _team_regulation(rng, na, *pa)
    pts_h, pts_a = pts_h.astype(np.int64), pts_a.astype(np.int64)
    went = _overtime(rng, ph, pa, pts_h, pts_a) if ot else np.zeros(n, bool)
    return GameSample(pts_h, pts_a, td_h, td_a, fg_h, fg_a, nh, na, went,
                      dict(provenance or {}, n=n, seed=seed, r=r, s_n=s_n, delta=delta, ot=ot, model="nfl_engine_v0_possession_mc"))


# ---- pricing: pure functions of one sample ---------------------------------------------------------------
def p_moneyline_home(s):
    m = s.margin
    return float((m > 0).mean() + 0.5 * (m == 0).mean())


def p_spread_home_covers(s, k):
    return float((s.margin > k).mean())


def p_total_over(s, k):
    return float((s.total > k).mean())


def p_team_total_over(s, home: bool, k):
    return float(((s.home_pts if home else s.away_pts) > k).mean())


def p_joint(s, event_a, event_b):
    return float((event_a(s) & event_b(s)).mean())


def ot_delta(mu=22.75, n=400_000, seed=20261014, r=0.6, s_n=1.0):
    """League OT add-on to the mean total (PLAN s1): sim with vs without OT at league-average means."""
    a = simulate(mu, mu, n, seed, r, s_n, ot=True)
    b = simulate(mu, mu, n, seed, r, s_n, ot=False)
    return float(a.total.mean() - b.total.mean())
