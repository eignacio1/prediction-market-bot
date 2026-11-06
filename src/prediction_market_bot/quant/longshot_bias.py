"""W105.6 pot-of-gold measurement: favourite-longshot routes, net of Kalshi's exact fee and the quoted spread.

Three routes, defined on the LISTED YES contract's mid price p (the market as Kalshi lists it):
  FADE_LONGSHOT  p in 1-15c  -> buy NO at 1 - yes_bid   (the longshot YES is overpriced; take the favourite NO)
  TAKE_FAVOURITE p in 85-99c -> buy YES at yes_ask      (the listed favourite is underpriced)
  BUY_LONGSHOT   p in 1-15c  -> buy YES at yes_ask; p in 85-99c -> buy NO at 1 - yes_bid
                 (only where a cell shows the longshot cheap, i.e. it settles ABOVE its price)
FADE_LONGSHOT on a longshot market and TAKE_FAVOURITE on the mirror favourite market are the same bias seen from the two
listings of one event; they are kept as separate routes because the listed contract differs (a player-prop "3+ hits" is
only ever listed as the longshot; a moneyline lists both teams).

Pure functions: no I/O, nothing here sizes, places or logs. When it applies: a two-sided, pre-start, priced market.
"""
from __future__ import annotations

import math
import random
from collections import defaultdict
from statistics import NormalDist
from typing import Iterable, Optional, Sequence

from prediction_market_bot.quant.inference import cluster_bootstrap
from prediction_market_bot.quant.money import fee_rate

FADE_LONGSHOT, TAKE_FAVOURITE, BUY_LONGSHOT = "FADE_LONGSHOT", "TAKE_FAVOURITE", "BUY_LONGSHOT"
ROUTES = (FADE_LONGSHOT, TAKE_FAVOURITE, BUY_LONGSHOT)
LOW_BUCKETS = ("1-5c", "5-10c", "10-15c")
HIGH_BUCKETS = ("85-90c", "90-95c", "95-99c")
BUCKETS = LOW_BUCKETS + HIGH_BUCKETS
_EDGES = {"1-5c": (0.01, 0.05), "5-10c": (0.05, 0.10), "10-15c": (0.10, 0.15),
          "85-90c": (0.85, 0.90), "90-95c": (0.90, 0.95), "95-99c": (0.95, 0.99)}
_N = NormalDist()


def pot_bucket(p: float) -> Optional[str]:
    """Bucket label for a YES mid, or None when p is outside the six pot-of-gold buckets (15-85c, <1c, >=99c)."""
    for label, (lo, hi) in _EDGES.items():
        if lo <= p < hi:
            return label
    return None


def route_side(route: str, p: float) -> Optional[str]:
    """Which side a route buys at listed YES mid p: 'yes' | 'no', or None when the route does not apply at p."""
    b = pot_bucket(p)
    if b is None:
        return None
    low = b in LOW_BUCKETS
    if route == FADE_LONGSHOT:
        return "no" if low else None
    if route == TAKE_FAVOURITE:
        return None if low else "yes"
    if route == BUY_LONGSHOT:
        return "yes" if low else "no"
    raise ValueError(route)


def net_per_contract(series: str, side: str, y: float, yes_bid: float, yes_ask: float) -> float:
    """Realised net P&L per contract for one entry at the quote: YES at the ask, NO at 1 - bid, minus the exact taker
    fee for `series` (pre-live phase). y is the YES outcome (1/0). The spread is paid by entering at the quote."""
    if side == "yes":
        return y - yes_ask - fee_rate(series, yes_ask)
    q = 1.0 - yes_bid
    return (1.0 - y) - q - fee_rate(series, q)


def split_games(game_dates: dict, frac: float = 0.7) -> set:
    """Earlier `frac` of games (by game date, then id) -> the fit set; the rest are held out. game_dates: {game: date}."""
    order = sorted(game_dates, key=lambda g: (str(game_dates[g]), g))
    k = int(math.ceil(frac * len(order)))
    return set(order[:k])


def evaluate_cell(rows: Sequence[dict], side: str, boot: int = 1000, seed: int = 20261105) -> dict:
    """rows: dicts with game, series, y, bid, ask, p. Mean net per contract for `side` with a game-clustered bootstrap
    interval, the settle-rate gap (settled - price on the YES contract), and a one-sided cluster-robust p for net > 0.
    Applies with >= ~15 games; below that the interval undercovers and the caller must treat the cell as thin."""
    by_game = defaultdict(list)
    for r in rows:
        by_game[r["game"]].append(net_per_contract(r["series"], side, r["y"], r["bid"], r["ask"]))
    n = sum(len(v) for v in by_game.values())
    g = len(by_game)
    if n == 0:
        return {"n": 0, "games": 0}
    mean, lo, hi = cluster_bootstrap(by_game, b=boot, seed=seed)
    mu = mean
    s2 = sum((sum(x - mu for x in v)) ** 2 for v in by_game.values())
    se = math.sqrt(s2) / n
    p_one = 1.0 - _N.cdf(mu / se) if se > 0 and g >= 2 else (0.0 if mu > 0 and g >= 2 else 1.0)
    pbar = sum(r["p"] for r in rows) / len(rows)
    f = sum(r["y"] for r in rows) / len(rows)
    return {"n": n, "games": g, "net_mean": mean, "net_lo": lo, "net_hi": hi, "p_one": p_one,
            "pbar": pbar, "settled": f, "gap": f - pbar}


def simulate_market(n: int, bias: float, seed: int, lo: float = 0.01, hi: float = 0.15, half_spread: float = 0.005,
                    series: str = "KXNHLGAME") -> list:
    """Planted-bias market for the known-answer test. Each game lists one longshot YES at price p ~ U(lo, hi); its true
    probability is max(p - bias, 0.001) (bias > 0: longshot OVERpriced; bias < 0: UNDERpriced; 0: calibrated)."""
    rng = random.Random(seed)
    out = []
    for i in range(n):
        p = rng.uniform(lo, hi)
        q = min(max(p - bias, 0.001), 0.999)
        out.append({"game": f"G{i}", "series": series, "p": p, "bid": p - half_spread, "ask": p + half_spread,
                    "y": 1.0 if rng.random() < q else 0.0})
    return out


def holm_one_sided(pvals: Sequence[float], alpha: float = 0.05) -> list:
    """Holm step-down across one-sided p-values -> list of bool (rejected). Local so the module has no extra imports."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    rej = [False] * m
    for rank, i in enumerate(order):
        if pvals[i] <= alpha / (m - rank):
            rej[i] = True
        else:
            break
    return rej
