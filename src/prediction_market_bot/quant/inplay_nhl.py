"""W103.3 (B-046): NHL in-play score math - goals as independent Poisson arrivals with state-dependent rates.

MODEL. Over the remaining regulation time tau (minutes) the home and away goal counts are independent Poisson with
means  L_h = lam_h * W_h / 60  and  L_a = lam_a * W_a / 60,  where lam are the pre-game even-strength-equivalent
goals per 60 (from the pre-game line / rating) and W is the state-weighted exposure: a state with multipliers
(m_h, m_a) (power play, empty net) applies for `window` minutes (a penalty's expected REMAINING sojourn,
E[D^2]/(2 E[D]) = 1.0 min for a 2-minute minor seen at a random instant; an empty net persists to the end of
regulation), even-strength rates apply for the rest. The score difference at the end of regulation is then
(score_h - score_a) + Skellam(L_h, L_a).

SETTLEMENT IS EXACT (99.1): a regulation tie goes to 5-minute 3v3 sudden-death overtime, with
P(home scores first) = lam'_h/(lam'_h + lam'_a) * (1 - exp(-5 (lam'_h + lam'_a)/60)), lam' = ot_mult * lam; a game still
tied after overtime goes to a shootout decided with probability p_so_home for the home team (0.5 by default). So
P(home wins the game) = P(reg win) + P(reg tie) * (P_ot_home + (1 - P_ot_end) * p_so_home), and the 3-way regulation
probabilities (home / tie / away) and regulation totals are returned separately, because Kalshi products settle on
different definitions.

WHEN IT APPLIES: regular-season games, no playoffs (overtime there is sudden-death 5v5 with no shootout); goals
are conditionally independent given the state and rates (no score effects, momentum, or goalie-quality changes within
the game: SCORE EFFECTS ARE NOT MODELLED - the held-out run reports the residual instead); the state at the instant is
held for `window`, which is crude for a power play whose expiry time is unknown to a score-only snapshot.

Nothing here touches an order, a position, a stake, a ledger row or a live model.
"""
from __future__ import annotations

import math
from typing import Dict, Optional, Sequence, Tuple

import numpy as np

REG_MINUTES = 60.0
OT_MINUTES = 5.0
MAX_GOALS = 25

# state -> (home multiplier, away multiplier, window minutes or None = to end of regulation). Defaults are neutral
# placeholders that the run script overrides with multipliers fitted on training seasons only.
NEUTRAL: Dict[str, Tuple[float, float, Optional[float]]] = {
    "EV": (1.0, 1.0, None),
    "H_PP": (1.0, 1.0, 1.0),
    "A_PP": (1.0, 1.0, 1.0),
    "H_EN": (1.0, 1.0, None),  # home goalie pulled
    "A_EN": (1.0, 1.0, None),  # away goalie pulled
}


def classify_state(home_skaters: int, away_skaters: int, home_goalie: int, away_goalie: int) -> str:
    """Strength state from the skater/goalie counts in the event store. A pulled goalie (goalie == 0) dominates a power play."""
    if home_goalie == 0 and away_goalie != 0:
        return "H_EN"
    if away_goalie == 0 and home_goalie != 0:
        return "A_EN"
    if home_skaters > away_skaters:
        return "H_PP"
    if away_skaters > home_skaters:
        return "A_PP"
    return "EV"


def _poisson_pmf(mean: float, n: int = MAX_GOALS + 1) -> np.ndarray:
    if mean <= 0:
        out = np.zeros(n)
        out[0] = 1.0
        return out
    k = np.arange(n)
    lg = np.array([math.lgamma(i + 1) for i in k])
    return np.exp(-mean + k * math.log(mean) - lg)


def remaining_means(minutes_left: float, lam_h: float, lam_a: float, state: str = "EV",
                    states: Optional[Dict[str, Tuple[float, float, Optional[float]]]] = None) -> Tuple[float, float]:
    """(L_h, L_a): expected remaining regulation goals given the instant state."""
    st = (states or NEUTRAL).get(state, (1.0, 1.0, None))
    mh, ma, window = st
    w = minutes_left if window is None else min(window, minutes_left)
    wh = w * mh + (minutes_left - w)
    wa = w * ma + (minutes_left - w)
    return lam_h * wh / REG_MINUTES, lam_a * wa / REG_MINUTES


def skellam_pmf(l_h: float, l_a: float) -> Tuple[np.ndarray, np.ndarray]:
    """(diffs, probs) of Home - Away remaining goals by explicit convolution of two Poisson pmfs (truncated at MAX_GOALS)."""
    ph, pa = _poisson_pmf(l_h), _poisson_pmf(l_a)
    diffs = np.arange(-MAX_GOALS, MAX_GOALS + 1)
    probs = np.zeros(len(diffs))
    for i, a in enumerate(ph):
        for j, b in enumerate(pa):
            probs[i - j + MAX_GOALS] += a * b
    return diffs, probs


def p_ot_home(lam_h: float, lam_a: float, ot_mult: float = 1.0) -> Tuple[float, float]:
    """(P(home wins in OT), P(OT ends with a goal)) for 5-minute 3v3 sudden death, rates ot_mult * lam per 60."""
    rh, ra = ot_mult * lam_h, ot_mult * lam_a
    tot = rh + ra
    p_end = 1.0 - math.exp(-OT_MINUTES * tot / 60.0)
    return (rh / tot) * p_end, p_end


def outcome_probs(score_h: int, score_a: int, minutes_left: float, lam_h: float, lam_a: float, state: str = "EV",
                  states: Optional[Dict[str, Tuple[float, float, Optional[float]]]] = None, ot_mult: float = 1.0,
                  p_so_home: float = 0.5) -> Dict[str, float]:
    """Regulation 3-way, game-win (OT+SO exact) and regulation-total pmf summary at (score, time left, state)."""
    if minutes_left <= 0:
        l_h = l_a = 0.0
    else:
        l_h, l_a = remaining_means(minutes_left, lam_h, lam_a, state, states)
    diffs, probs = skellam_pmf(l_h, l_a)
    final = (score_h - score_a) + diffs
    p_reg_h = float(probs[final > 0].sum())
    p_reg_t = float(probs[final == 0].sum())
    p_reg_a = float(probs[final < 0].sum())
    p_oth, p_end = p_ot_home(lam_h, lam_a, ot_mult)
    p_game_h = p_reg_h + p_reg_t * (p_oth + (1.0 - p_end) * p_so_home)
    return {"reg_home": p_reg_h, "reg_tie": p_reg_t, "reg_away": p_reg_a, "game_home": p_game_h,
            "p_ot_end": p_end, "L_h": l_h, "L_a": l_a}


def p_total_over(score_h: int, score_a: int, minutes_left: float, lam_h: float, lam_a: float, line: float,
                 state: str = "EV", states: Optional[Dict[str, Tuple[float, float, Optional[float]]]] = None) -> float:
    """P(regulation total goals > line) for a half-point line: the remaining total is Poisson(L_h + L_a)."""
    l_h, l_a = remaining_means(max(minutes_left, 0.0), lam_h, lam_a, state, states) if minutes_left > 0 else (0.0, 0.0)
    need = line - (score_h + score_a)  # remaining goals must exceed `need`
    pm = _poisson_pmf(l_h + l_a, MAX_GOALS * 2 + 1)
    k = np.arange(len(pm))
    return float(pm[k > need].sum())


def brier(p: Sequence[float], y: Sequence[float]) -> float:
    p = np.asarray(p, dtype=float)
    y = np.asarray(y, dtype=float)
    return float(np.mean((p - y) ** 2))
