"""NFL board v2 (W93.4): the whole board from the market's own line, with the shape learned from history.

One joint (home score, away score) distribution per game, built in two steps:

1. SHAPE. A kernel-weighted empirical distribution of past (margin, total) outcomes among games whose closing spread
   and total were close to this game's. Key numbers (3, 7, 10, ...), the margin-total correlation and overtime are in
   it because they are in the outcomes; nothing is assumed about them.
2. ANCHOR. An exponential tilt (a, b) on (margin, total) moves the distribution until the market's own main spread and
   total are its medians. The tilt keeps the support on the integers the game can actually end on, so the key-number
   spikes survive the move.

Every price comes off that one distribution: moneyline, any spread strike, any total strike, both team totals.
Ties in the library (rare) pay half on the moneyline.

When this applies: a market that quotes a main line (spread / total) and a ladder of strikes around it. When it does
not: it says nothing about WHERE the line should be (the centre is the market's); it prices the shape around it.
Nothing here touches an order, a position, a stake or a ledger row.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np
import pandas as pd
from statistics import NormalDist

_N = NormalDist()

# Bandwidths (points) of the kernel over the library's closing spread / total.
H_SPREAD = 1.75
H_TOTAL = 4.0
MIN_GAMES = 200


@dataclass(frozen=True)
class Library:
    """Past outcomes with the lines they closed at (rows are games)."""

    m: np.ndarray        # home margin (int)
    t: np.ndarray        # total points (int)
    line: np.ndarray     # closing spread, home-favoured positive (nflverse convention)
    tline: np.ndarray    # closing total
    season: np.ndarray

    def __len__(self) -> int:
        return len(self.m)


def build_library(sched: pd.DataFrame, before_season: Optional[int] = None, seasons: Optional[Sequence[int]] = None) -> Library:
    """Library from an nflverse schedule frame. Keeps finished games with both lines; ``before_season`` keeps seasons
    strictly earlier (rolling origin); ``seasons`` keeps exactly those."""
    d = sched[sched.home_score.notna() & sched.away_score.notna() & sched.spread_line.notna() & sched.total_line.notna()]
    if before_season is not None:
        d = d[d.season < before_season]
    if seasons is not None:
        d = d[d.season.isin(list(seasons))]
    m = (d.home_score - d.away_score).to_numpy(dtype=int)
    t = (d.home_score + d.away_score).to_numpy(dtype=int)
    return Library(m, t, d.spread_line.to_numpy(float), d.total_line.to_numpy(float), d.season.to_numpy(int))


@dataclass
class Board:
    """The joint distribution for one game: support points and their probabilities."""

    m: np.ndarray
    t: np.ndarray
    p: np.ndarray
    ess: float

    # ---- margin side (m = home - away) ----
    def p_margin_ge(self, k: int) -> float:
        """P(home margin >= k), k integer (k > 0: home wins by k or more; k <= 0 reads the away side)."""
        return float(self.p[self.m >= k].sum())

    def p_margin_eq(self, k: int) -> float:
        return float(self.p[self.m == k].sum())

    def p_abs_margin_eq(self, k: int) -> float:
        return float(self.p[np.abs(self.m) == k].sum())

    def p_home_win(self) -> float:
        return float(self.p[self.m > 0].sum() + 0.5 * self.p[self.m == 0].sum())

    # ---- total side ----
    def p_total_ge(self, k: int) -> float:
        return float(self.p[self.t >= k].sum())

    # ---- team totals (home = (t + m) / 2, away = (t - m) / 2) ----
    def p_team_ge(self, home: bool, k: int) -> float:
        pts = (self.t + self.m) // 2 if home else (self.t - self.m) // 2
        return float(self.p[pts >= k].sum())

    def mean_margin(self) -> float:
        return float((self.p * self.m).sum())

    def mean_total(self) -> float:
        return float((self.p * self.t).sum())


def _median_gap(m: np.ndarray, p: np.ndarray, line: float) -> float:
    """G(line) - 0.5 where G(L) = P(X > L) + 0.5 P(X = L), linearly interpolated between half-integers so it is
    continuous in L (a Kalshi ladder, which only quotes half-integer thresholds, is read the same way)."""
    lo = np.floor(line - 0.5) + 0.5   # half-integer at or below `line`
    hi = lo + 1.0
    g_lo = p[m > lo].sum()            # P(X > lo) = P(X >= lo + 0.5)
    g_hi = p[m > hi].sum()
    w = line - lo
    return float((1 - w) * g_lo + w * g_hi) - 0.5


def _tilt(w: np.ndarray, m: np.ndarray, t: np.ndarray, line: float, total: float, iters: int = 12) -> tuple[np.ndarray, float, float]:
    """Tilt (a, b): p ~ w exp(a*m + b*t) with median(margin) = line and median(total) = total (alternating bisection)."""
    a = b = 0.0
    z = np.zeros_like(w)

    def pmf(a_, b_):
        x = np.log(np.maximum(w, 1e-300)) + a_ * m + b_ * t
        x -= x.max()
        q = np.exp(x)
        return q / q.sum()

    for _ in range(iters):
        lo, hi = -1.0, 1.0
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if _median_gap(m, pmf(mid, b), line) < 0:
                lo = mid
            else:
                hi = mid
        a = 0.5 * (lo + hi)
        lo, hi = -1.0, 1.0
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if _median_gap(t, pmf(a, mid), total) < 0:
                lo = mid
            else:
                hi = mid
        b = 0.5 * (lo + hi)
    return pmf(a, b), a, b


def price_board(lib: Library, line: float, total: float, h_spread: float = H_SPREAD, h_total: float = H_TOTAL) -> Board:
    """Joint distribution for a game whose market main spread is ``line`` (home-favoured positive) and main total is
    ``total``. Support is the library's observed (margin, total) pairs, collapsed to unique points."""
    if len(lib) < MIN_GAMES:
        raise ValueError(f"library has {len(lib)} games, need at least {MIN_GAMES}")
    w = np.exp(-0.5 * ((lib.line - line) / h_spread) ** 2 - 0.5 * ((lib.tline - total) / h_total) ** 2)
    if w.sum() <= 0:
        raise ValueError("no library game within kernel reach of this line")
    ess = float(w.sum() ** 2 / (w ** 2).sum())
    # Unique (m, t) points so the tilt solve runs on the support, not on every game.
    pairs = np.stack([lib.m, lib.t], axis=1)
    uniq, inv = np.unique(pairs, axis=0, return_inverse=True)
    wu = np.bincount(inv.ravel(), weights=w, minlength=len(uniq))
    mu, tu = uniq[:, 0], uniq[:, 1]
    keep = wu > 1e-12
    p, _, _ = _tilt(wu[keep] / wu[keep].sum(), mu[keep].astype(float), tu[keep].astype(float), line, total)
    return Board(mu[keep], tu[keep].astype(int), p, ess)


def gaussian_ladder(line: float, sd: float, k: int, side: str = "margin") -> float:
    """Same-median Gaussian baseline for P(X >= k) with continuity correction (X integer). margin: mean = line."""
    return 1.0 - _N.cdf((k - 0.5 - line) / sd)


def key_number_counts(board_list: Sequence[Board], ks: Sequence[int]) -> dict[int, tuple[float, float]]:
    """Expected count and variance of games ending |margin| = k, summed over boards (Poisson-binomial)."""
    out = {}
    for k in ks:
        ps = np.array([b.p_abs_margin_eq(k) for b in board_list])
        out[k] = (float(ps.sum()), float((ps * (1 - ps)).sum()))
    return out
