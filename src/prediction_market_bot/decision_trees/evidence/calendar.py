"""Power calendar: at the current row rate, the week a leaf could first earn an arm under each router.

Deterministic expected path: assume the true net equals a stated value mu (the caller passes the current posterior mean,
or a family effect), every future week brings games_per_week games with the per-game variance seen so far, and each
week's mean equals mu. It answers "how long if the effect is real and this size", not "will it happen".
When it applies: a stable weekly game rate. When it doesn't: mu <= 0 (never earns: returned as None), or a season ending
inside the horizon (the caller caps weeks at the season).
"""
from __future__ import annotations

import math
from typing import Optional, Tuple

from prediction_market_bot.decision_trees.evidence.model import norm_cdf
from prediction_market_bot.decision_trees.evidence.sequential import log_e_increment

MAX_WEEKS = 104


def inv_norm(p: float) -> float:
    lo, hi = -10.0, 10.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if norm_cdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def weeks_to_cross(log_e_now: float, prior: Tuple[float, float], mu: float, var_game: float, games_per_week: float,
                   alpha: float = 0.10, min_inc_games: int = 5, max_weeks: int = MAX_WEEKS) -> Optional[int]:
    """Weeks until the node's e-process reaches 1/alpha (0 = already there)."""
    need = math.log(1.0 / alpha)
    if log_e_now >= need:
        return 0
    if mu <= 0 or games_per_week <= 0 or var_game <= 0:
        return None
    m, v = prior
    le, pending = log_e_now, 0.0
    for w in range(1, max_weeks + 1):
        pending += games_per_week
        if pending < min_inc_games:
            continue
        se2 = var_game / pending
        le += log_e_increment(mu, se2, m, v)
        p = 1.0 / v + 1.0 / se2
        m, v = (m / v + mu / se2) / p, 1.0 / p
        pending = 0.0
        if le >= need:
            return w
    return None


def weeks_to_bar(post: Tuple[float, float], mu: float, var_game: float, games_per_week: float, bar: float = 0.90,
                 max_weeks: int = MAX_WEEKS) -> Optional[int]:
    """Weeks until the leaf's own posterior has P(net > 0) >= bar (help from sibling leaves ignored: an upper bound)."""
    m, v = post
    if norm_cdf(m / math.sqrt(v)) >= bar:
        return 0
    if mu <= 0 or games_per_week <= 0 or var_game <= 0:
        return None
    for w in range(1, max_weeks + 1):
        info = w * games_per_week / var_game
        p = 1.0 / v + info
        if norm_cdf(((m / v + mu * info) / p) * math.sqrt(p)) >= bar:
            return w
    return None


def weeks_to_bh(games_now: float, rows_per_game: float, mu: float, var_game: float, games_per_week: float, m_tests: int,
                q: float = 0.10, fit_frac: float = 0.7, min_fit_rows: int = 60, min_fit_games: int = 20,
                min_test_games: int = 10, max_weeks: int = MAX_WEEKS) -> Optional[int]:
    """Weeks until a leaf judged alone (W110.5 rule: 70/30 split by game, thin below 60 fit rows / 20 fit games, 10 held-out
    games, Benjamini-Hochberg at q over m_tests leaves) could be the first rejection: z on the held-out 30% >= z(1 - q/m)."""
    if mu <= 0 or games_per_week <= 0 or var_game <= 0:
        return None
    z = inv_norm(1.0 - q / max(1, m_tests))
    for w in range(0, max_weeks + 1):
        g = games_now + w * games_per_week
        tg = (1.0 - fit_frac) * g
        if fit_frac * g < min_fit_games or fit_frac * g * rows_per_game < min_fit_rows or tg < min_test_games:
            continue
        if mu / math.sqrt(var_game / tg) >= z:
            return w
    return None
