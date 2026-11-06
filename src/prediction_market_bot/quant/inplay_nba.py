"""W103.3 (B-046): NBA in-play score math - the margin as a drifting Brownian motion (Stern 1994 family).

MODEL. Home-minus-away margin X(t) over a 48-minute regulation game moves as dX = d dt + s dW, where the drift
d = M / 48 per minute is set by the pre-game expected final margin M (home minus away; the pre-game spread, sign
flipped: a line of home -4.5 means M = +4.5) and s^2 is the variance of the margin per minute. At (margin x, tau
minutes left) the final regulation margin is Normal(x + M tau / 48, s^2 tau). The total points process has the same
form with drift T / 48 per minute (T = the pre-game expected total) and its own variance per minute.

WHEN IT APPLIES: a game in regulation with a pre-game expected margin / total and a known score and clock; the
margin increments over the remaining time are roughly independent of the path so far (no momentum, no mean reversion),
the variance per minute is constant over the remaining time, and the drift is the pre-game line spread evenly over the
48 minutes. It does NOT apply in overtime, and it ignores late-game structure (intentional fouling when trailing,
garbage-time substitution, timeouts): s^2 is one pooled number, so calibration near tau -> 0 is where it is weakest.
Margins are integers; a half-point strike needs no correction, a moneyline treats a regulation tie as an overtime coin
toss (0.5 plus an optional overtime edge from the sign of the drift is NOT modelled: the tie mass is tiny).

Nothing here touches an order, a position, a stake, a ledger row or a live model.
"""
from __future__ import annotations

import math
from typing import Optional, Sequence, Tuple

import numpy as np

REG_MINUTES = 48.0
_SQRT2 = math.sqrt(2.0)


def _phi(z: float) -> float:
    """Standard normal CDF."""
    return 0.5 * (1.0 + math.erf(z / _SQRT2))


def expected_final(current: float, minutes_left: float, pregame_full: float) -> float:
    """Expected final value of a process with drift pregame_full / 48 per minute, now at `current`."""
    return current + pregame_full * (minutes_left / REG_MINUTES)


def p_margin_gt(margin: float, minutes_left: float, pregame_margin: float, sigma2_pm: float, threshold: float) -> float:
    """P(final regulation home margin > threshold).

    `threshold` is the strike on the margin: 0.0 for 'home wins in regulation by any amount' ... but use
    p_home_win for the moneyline, which splits the tie. For a half-point strike (4.5 = 'wins by 5 or more')
    this is the exact lattice answer under the normal approximation. At minutes_left == 0 the answer is 0/1.
    """
    if minutes_left <= 0.0:
        return 1.0 if margin > threshold else 0.0
    mu = expected_final(margin, minutes_left, pregame_margin)
    sd = math.sqrt(sigma2_pm * minutes_left)
    return 1.0 - _phi((threshold - mu) / sd)


def p_home_win(margin: float, minutes_left: float, pregame_margin: float, sigma2_pm: float) -> float:
    """P(home team wins the game, overtime included). A regulation tie goes to overtime and is split 50/50.

    Lattice form: P(X >= 1) + 0.5 P(X == 0), with X integer approximated by the normal on [x - .5, x + .5].
    """
    if minutes_left <= 0.0:
        if margin > 0:
            return 1.0
        return 0.5 if margin == 0 else 0.0
    mu = expected_final(margin, minutes_left, pregame_margin)
    sd = math.sqrt(sigma2_pm * minutes_left)
    p_hi = 1.0 - _phi((0.5 - mu) / sd)                      # X >= 1
    p_tie = _phi((0.5 - mu) / sd) - _phi((-0.5 - mu) / sd)   # X == 0
    return p_hi + 0.5 * p_tie


def p_total_gt(total_so_far: float, minutes_left: float, pregame_total: float, sigma2_pm: float, line: float) -> float:
    """P(regulation total points > line) for a half-point line. Total, not margin: sigma2_pm is the TOTAL's variance per minute."""
    if minutes_left <= 0.0:
        return 1.0 if total_so_far > line else 0.0
    mu = expected_final(total_so_far, minutes_left, pregame_total)
    sd = math.sqrt(sigma2_pm * minutes_left)
    return 1.0 - _phi((line - mu) / sd)


def estimate_sigma2(final_minus_now: Sequence[float], minutes_left: Sequence[float], pregame_full: Sequence[float]) -> float:
    """Variance per minute from checkpoints. Residual r = (final - now) - pregame_full * tau / 48; E[r^2] = s^2 tau, so
    the estimate is mean(r^2 / tau) over checkpoints with tau > 0 (training seasons only: pass nothing from held-out)."""
    a = np.asarray(final_minus_now, dtype=float)
    tau = np.asarray(minutes_left, dtype=float)
    m = np.asarray(pregame_full, dtype=float)
    keep = tau > 0
    if not keep.any():
        raise ValueError("no checkpoint with minutes_left > 0")
    r = a[keep] - m[keep] * tau[keep] / REG_MINUTES
    return float(np.mean(r * r / tau[keep]))


def simulate_margin_win(margin: float, minutes_left: float, pregame_margin: float, sigma2_pm: float,
                        n: int = 200_000, steps: int = 240, seed: int = 0) -> float:
    """Monte Carlo of the same model by explicit small steps (an independent check of the closed form, tie = 0.5).

    Steps are Gaussian increments; the final margin is rounded to the integer lattice before settling, so the tie
    mass is the same quantity the closed form integrates over [-0.5, 0.5]."""
    rng = np.random.default_rng(seed)
    dt = minutes_left / steps
    drift = pregame_margin / REG_MINUTES * dt
    inc = rng.normal(drift, math.sqrt(sigma2_pm * dt), size=(n, steps)).sum(axis=1)
    final = np.rint(margin + inc)
    return float(np.mean((final > 0) + 0.5 * (final == 0)))


def brier(p: Sequence[float], y: Sequence[float]) -> float:
    p = np.asarray(p, dtype=float)
    y = np.asarray(y, dtype=float)
    return float(np.mean((p - y) ** 2))


def calibration_bins(p: Sequence[float], y: Sequence[float], edges: Sequence[float] = (0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1.0001)
                     ) -> Tuple[Tuple[float, float, float, int], ...]:
    """(mean predicted, observed rate, ... n) per probability bin: (lo, mean_p, rate, n)."""
    p = np.asarray(p, dtype=float)
    y = np.asarray(y, dtype=float)
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (p >= lo) & (p < hi)
        if m.any():
            out.append((float(lo), float(p[m].mean()), float(y[m].mean()), int(m.sum())))
    return tuple(out)


def bootstrap_ci(values: Sequence[float], b: int = 2000, seed: int = 20261105, alpha: float = 0.05
                 ) -> Tuple[float, float, float]:
    """(mean, lo, hi) percentile bootstrap over the given per-game values."""
    v = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(v), size=(b, len(v)))
    means = v[idx].mean(axis=1)
    return float(v.mean()), float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))
