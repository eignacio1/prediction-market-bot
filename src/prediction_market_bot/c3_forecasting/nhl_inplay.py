"""C3 -- NHL in-play pricer for the T4NHL-ARITH band (W129.7).

Prices the three NHL Kalshi families (game winner, puck line, game total) from the NHL engine's PRE-GAME goal rates
(lam_h, lam_a: ``NhlGoalsModel.raw_ladder``) updated by the live game state: score, regulation time left, strength
(even / power play / empty net). The score math is ``quant/inplay_nhl.py`` (W103.3); this module only fixes the
state multipliers and maps a Kalshi ticker onto an outcome.

STATE MULTIPLIERS (fitted on 2021-22..2024-25 only, ``12_EXPLORATORY/quant_w103_inplay/RESULT.md`` Part B): power
play 2.4x for the PP side / 0.35x for the short-handed side, window 1.0 min (expected remaining sojourn of a minor);
empty net 7.1x for the team that pulled its goalie / 2.7x for the other side, to end of regulation.

KNOWN LIMITS (stated, not hidden): score effects are not modelled; goals are Poisson so regulation ties and totals are
under-priced (W103.3: model 17-19% ties vs 24.8% actual); the PP window ignores the penalty timer even though the feed
carries it. Overtime and shootout states are not priced here (the arithmetic band is regulation); they abstain.
Evaluate-and-log only: no order or position imports.
"""
from __future__ import annotations

from typing import Optional

from prediction_market_bot.c3_forecasting.nhl_pregame import parse_ticker
from prediction_market_bot.quant import inplay_nhl as q

EPS = 0.001
STATES = {
    "EV": (1.0, 1.0, None),
    "H_PP": (2.4, 0.35, 1.0),
    "A_PP": (0.35, 2.4, 1.0),
    "H_EN": (7.1, 2.7, None),
    "A_EN": (2.7, 7.1, None),
}
P_SO_HOME = 0.508  # W103.3 training share


def price_state(lam_h: float, lam_a: float, state: dict) -> Optional[dict]:
    """Outcome summary at the state, or None when the state is outside the arithmetic band (OT/SO, incomplete)."""
    ml = state.get("minutes_left_reg")
    if ml is None or state.get("strength") is None or state.get("score_h") is None or state.get("score_a") is None:
        return None
    if state.get("period_type") != "REG":
        return None
    sh, sa = int(state["score_h"]), int(state["score_a"])
    out = q.outcome_probs(sh, sa, float(ml), lam_h, lam_a, state["strength"], STATES, p_so_home=P_SO_HOME)
    out["score_h"], out["score_a"], out["minutes_left"], out["strength"] = sh, sa, float(ml), state["strength"]
    out["lam_h"], out["lam_a"] = lam_h, lam_a
    return out


def p_win_by_over_reg(sh: int, sa: int, ml: float, lam_h: float, lam_a: float, strength: str, side: str,
                      strike: float) -> float:
    """P(side wins by MORE than ``strike`` goals) for strike >= 1.5: OT/SO wins are by exactly one goal, so only the
    regulation margin can clear 1.5; the regulation margin is score diff + Skellam of the remaining goals."""
    l_h, l_a = q.remaining_means(max(ml, 0.0), lam_h, lam_a, strength, STATES) if ml > 0 else (0.0, 0.0)
    diffs, probs = q.skellam_pmf(l_h, l_a)
    final = (sh - sa) + diffs
    if side == "away":
        final = -final
    return float(probs[final > strike].sum())


def price_ticker(ticker: str, lam_h: float, lam_a: float, state: dict) -> Optional[tuple[float, dict]]:
    """(p_yes, parsed ticker info) for a KXNHLGAME / SPREAD / TOTAL ticker at the live state, or None."""
    info = parse_ticker(ticker)
    st = price_state(lam_h, lam_a, state)
    if info is None or st is None:
        return None
    sh, sa, ml, strength = st["score_h"], st["score_a"], st["minutes_left"], st["strength"]
    if info["series"] == "GAME":
        side = "home" if info["team"] == info["home"] else "away" if info["team"] == info["away"] else None
        if side is None:
            return None
        p = st["game_home"] if side == "home" else 1.0 - st["game_home"]
    elif info["series"] == "SPREAD":
        side = "home" if info["team"] == info["home"] else "away" if info["team"] == info["away"] else None
        if side is None:
            return None
        k = float(info["strike"])
        if k < 1.0:
            p = st["game_home"] if side == "home" else 1.0 - st["game_home"]
        else:
            p = p_win_by_over_reg(sh, sa, ml, lam_h, lam_a, strength, side, k)
    else:
        p = q.p_total_over(sh, sa, ml, lam_h, lam_a, float(info["strike"]), strength, STATES)
    return min(max(p, EPS), 1 - EPS), info
