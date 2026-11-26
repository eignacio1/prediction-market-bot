"""W129.6 (Part B): NFL in-play price - the pre-game line updated by game state (arithmetic band first).

MODEL. Same family as ``inplay_nba`` (Stern 1974/1994): home-minus-away margin as a drifting Brownian motion over 60
regulation minutes. Drift = pre-game expected margin M / 60 per minute (M = the pre-game spread sign-flipped: home -14.5
means M = +14.5); variance per minute s2 is ONE pooled number fitted on TRAINING games only (never the scored ones).
Final regulation margin at (margin x, tau minutes left) is Normal(x + M tau/60 + EP_poss, s2 tau) where EP_poss is the
expected points of the CURRENT drive (possession x field position), the one NFL-specific term the NBA model lacks.
Totals use the same form with drift T/60 and the same drive term (the drive adds to the total whoever holds the ball).

EP_poss is a FIXED table (``EP_BY_YARDS_TO_GOAL``), not fitted here: a coarse piecewise-linear curve of published
expected-points values (Carter-Machol / nflfastR family), declared before any outcome was read. It is applied only on a
live down (down >= 1) with time left. A tuned curve would be a different, separately pre-registered test.

BANDS. ARITH is the model above in near-certain states (it is a threshold-approaching arithmetic problem: how many
possessions are left versus how far behind). FLOW (context multipliers: timeouts, two-minute drill, blowout clock-killing)
is a second mode registered behind it: ``flow_adjustment`` is the identity until its own pre-registered split exists, so
the FLOW cells log the same price with ``mode="flow_identity"`` and carry no extra claim.

DOES NOT APPLY in overtime (returns None: no price is logged for OT). Ignores: two-point tries, late-game clock
management beyond the pooled variance, weather. Margins are integers; a half-point strike needs no correction; a
regulation tie is split 50/50 for the moneyline (tie mass is small and OT is not modelled).

Nothing here touches an order, a position, a stake, a ledger row or a live model.
"""
from __future__ import annotations

import math
from typing import Optional, Sequence

from prediction_market_bot.quant.inplay_nba import _phi, bootstrap_ci, brier  # noqa: F401 - re-exported helpers

REG_MINUTES = 60.0

# (yards_to_goal, expected points of the drive for the team with the ball). First-and-ten values, linear between knots.
EP_BY_YARDS_TO_GOAL = ((1, 6.3), (10, 4.7), (20, 3.9), (35, 2.9), (50, 1.9), (65, 1.1), (80, 0.4), (99, -0.2))


def drive_ep(yards_to_goal: Optional[float], down: int) -> float:
    """Expected points of the current drive for the offense; 0 when there is no live down."""
    if yards_to_goal is None or down < 1:
        return 0.0
    y = min(max(float(yards_to_goal), 1.0), 99.0)
    for (y0, e0), (y1, e1) in zip(EP_BY_YARDS_TO_GOAL, EP_BY_YARDS_TO_GOAL[1:]):
        if y <= y1:
            return e0 + (e1 - e0) * (y - y0) / (y1 - y0)
    return EP_BY_YARDS_TO_GOAL[-1][1]


def _poss_sign(possession: str) -> int:
    return {"home": 1, "away": -1}.get(possession, 0)


def margin_mean(margin: float, secs_left: float, pregame_margin: float, possession: str, yards_to_goal: Optional[float],
                down: int) -> float:
    tau = secs_left / 60.0
    return margin + pregame_margin * (tau / REG_MINUTES) + _poss_sign(possession) * drive_ep(yards_to_goal, down)


def p_margin_gt(margin: float, secs_left: float, pregame_margin: float, sigma2_pm: float, threshold: float,
                possession: str = "", yards_to_goal: Optional[float] = None, down: int = 0) -> float:
    """P(final home-minus-away margin > threshold) in regulation. secs_left = 0 -> the margin is final."""
    mu = margin_mean(margin, secs_left, pregame_margin, possession, yards_to_goal, down)
    var = sigma2_pm * (secs_left / 60.0)
    if var <= 1e-12:
        return 1.0 if margin > threshold else (0.5 if margin == threshold else 0.0)
    return _phi((mu - threshold) / math.sqrt(var))


def p_home_win(margin: float, secs_left: float, pregame_margin: float, sigma2_pm: float, possession: str = "",
               yards_to_goal: Optional[float] = None, down: int = 0) -> float:
    """Regulation tie split 50/50: P(margin > 0) with a continuity correction at 0."""
    return p_margin_gt(margin, secs_left, pregame_margin, sigma2_pm, 0.0, possession, yards_to_goal, down)


def p_total_gt(total_so_far: float, secs_left: float, pregame_total: float, sigma2_total_pm: float, line: float,
               yards_to_goal: Optional[float] = None, down: int = 0) -> float:
    tau = secs_left / 60.0
    mu = total_so_far + pregame_total * (tau / REG_MINUTES) + (drive_ep(yards_to_goal, down) if tau > 0 else 0.0)
    var = sigma2_total_pm * tau
    if var <= 1e-12:
        return 1.0 if total_so_far > line else 0.0
    return 1.0 - _phi((line - mu) / math.sqrt(var))


def estimate_sigma2(final_minus_expected: Sequence[float], minutes_left: Sequence[float], weighted: bool = True) -> float:
    """Pooled variance per minute. weighted=True (v2): sum(r^2) / sum(tau). weighted=False (v1, first look): mean(r^2 / tau),
    which the near-zero-tau states dominate (their residual is drive-outcome noise, not Brownian), inflating s2 ~2.5x."""
    pairs = [(r, m) for r, m in zip(final_minus_expected, minutes_left) if m > 0]
    if not pairs:
        return float("nan")
    if weighted:
        return sum(r * r for r, _ in pairs) / sum(m for _, m in pairs)
    return sum(r * r / m for r, m in pairs) / len(pairs)


def flow_adjustment(p: float, mode: str = "flow_identity") -> float:
    """FLOW band hook: identity until its own pre-registered split exists (see module docstring)."""
    return p
