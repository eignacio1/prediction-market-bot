"""W99.3 (GG-1630): top-3 reasons for the NBA player-points arms (EXP-039, EXP-040) -- logging only.

The price is ridge mean -> negative binomial -> Platt, which is not linear in the inputs, so the reason for a feature is
a COUNTERFACTUAL: re-price the same ticker with that ONE input at its training mean and report how far the probability
moved toward YES, in percentage points. Known-answer: for a model with one feature that moves p from p0 to p1 at its
mean, the reason is (p0 - p1) * 100 points. Any failure -> None (the caller logs a reasons_note); never raises.
"""
from __future__ import annotations

from typing import Callable, Optional

from prediction_market_bot.nba_engine.why import top_reasons
from prediction_market_bot.pregame_shadow.reasons import TOP_K, plain_name


def counterfactual_reasons(feats: dict, names: list, means: list, price: Callable[[dict], float],
                           k: int = TOP_K) -> Optional[tuple]:
    try:
        base = price(feats)
        cfs = []
        for n, mu in zip(names, means):
            if feats.get(n) is None or feats[n] == mu:
                continue
            cfs.append((plain_name(n), feats[n], price({**feats, n: mu})))
        got = top_reasons(base, cfs, k)
        return tuple(got) if got else None
    except Exception:  # noqa: BLE001 - logging only
        return None
