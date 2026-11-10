"""Weather-ladder calibration (W108.4, B-065). Research-only helpers; wired to nothing.

Kalshi daily-temperature ladders settle on an INTEGER reading. Strike semantics (read from rules_primary, 2026-11-10):
  floor-tail  (floor=f, cap None): YES iff T >= f+1      ("greater than f")
  cap-tail    (floor None, cap=c): YES iff T <= c-1      ("less than c")
  bucket      (floor=f, cap=c):    YES iff f <= T <= c
"""
from __future__ import annotations

import math
from typing import Optional, Sequence

from .money import fee_rate


def settle_yes(floor: Optional[float], cap: Optional[float], temp: float) -> int:
    """1 if the ladder strike resolves YES for integer reading `temp`. Applies to Kalshi daily-temperature series only."""
    if cap is None:
        return int(temp >= floor + 1)
    if floor is None:
        return int(temp <= cap - 1)
    return int(floor <= temp <= cap)


def _phi(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def strike_prob(mu: float, sigma: float, floor: Optional[float], cap: Optional[float]) -> float:
    """P(strike resolves YES) when the true reading's continuous version X ~ N(mu, sigma) is rounded to an integer.
    Applies when the forecast error is near-Gaussian and sigma > 0; tail asymmetry is not modelled."""
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    if cap is None:
        return 1.0 - _phi((floor + 0.5 - mu) / sigma)
    if floor is None:
        return _phi((cap - 0.5 - mu) / sigma)
    return _phi((cap + 0.5 - mu) / sigma) - _phi((floor - 0.5 - mu) / sigma)


def fit_error(fc: Sequence[float], actual: Sequence[float]) -> tuple:
    """(bias, sd) of actual - forecast, the sample sd with n-1. Fit on the training split only."""
    n = len(fc)
    if n < 3:
        raise ValueError("need >= 3 pairs")
    e = [a - f for f, a in zip(fc, actual)]
    b = sum(e) / n
    sd = math.sqrt(sum((x - b) ** 2 for x in e) / (n - 1))
    return b, sd


def trade_toward(p_model: float, price_yes: float, half_spread: float, series: str) -> dict:
    """Per-contract P&L of trading toward the model at a quoted-equivalent price, fee included, outcome not yet known.
    Buys YES at price+half_spread or NO at (1-price)+half_spread (taker). Returns side and expected net edge.
    Applies when price is a trade-print proxy and half_spread is an estimate; with a real two-sided quote use money.net_edge."""
    ya = min(0.99, price_yes + half_spread)
    na = min(0.99, (1.0 - price_yes) + half_spread)
    ey = p_model - ya - fee_rate(series, ya)
    en = (1.0 - p_model) - na - fee_rate(series, na)
    return {"side": "yes" if ey >= en else "no", "edge": max(ey, en), "ask_yes": ya, "ask_no": na}


def realised(side: str, entry_yes_ask: float, entry_no_ask: float, y: int, series: str) -> float:
    """Realised net P&L per contract for the side taken, y the YES outcome (0/1)."""
    if side == "yes":
        return y - entry_yes_ask - fee_rate(series, entry_yes_ask)
    return (1 - y) - entry_no_ask - fee_rate(series, entry_no_ask)
