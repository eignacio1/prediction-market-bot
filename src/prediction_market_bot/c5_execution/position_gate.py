"""W85.2: the operator-accepted position gate (2026-10-21). PURE, UNWIRED, NOT IMPORTED BY ANY RUNNER.

The rule: one position per market per band; the model is pulled toward the market by its measured
skill; an order goes in only when what is left clears the fee plus the model's measured error; a
game's ladder counts as one exposure.

No I/O, no clock, no environment. Nothing here places, sizes or cancels an order. Wiring is a later
wave and needs its own decision (ADR-0072 addendum, DRAFT).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class Candidate:
    """One evaluation row the gate may keep. ``ts`` orders rows; any sortable value works."""
    ts: str
    market_ticker: str
    band: str
    game: str
    family: str
    p_model: float
    mid: float
    yes_bid: float
    yes_ask: float
    fee: float
    stake: float = 1.0


def skill_weight(brier_model: Optional[float], brier_market: Optional[float]) -> float:
    """Weight on the model, in [0, 1]: its held-out Brier skill against the MARKET (1 - Bm/Bk).

    No market-referenced Brier, or a model no better than the market, means 0: the market's price."""
    if brier_model is None or brier_market is None or brier_market <= 0:
        return 0.0
    return min(1.0, max(0.0, 1.0 - brier_model / brier_market))


def shrink(p_model: float, mid: float, weight: float) -> float:
    """Pull the model toward the market: mid + w * (p_model - mid). w=0 returns the market's mid."""
    w = min(1.0, max(0.0, weight))
    return mid + w * (p_model - mid)


def net_edge(side: str, p_adj: float, yes_bid: float, yes_ask: float, fee: float) -> float:
    """Edge after crossing the spread and paying the fee. YES buys at the ask; NO buys at 1 - bid."""
    if side == "yes":
        return p_adj - yes_ask - fee
    if side == "no":
        return yes_bid - p_adj - fee
    raise ValueError("side must be 'yes' or 'no'")


def error_bar(disagreements: Sequence[float]) -> float:
    """Spread (sample sd) of model-minus-market disagreement on held-out data. Fewer than 2 points:
    no measured error, so +inf (nothing clears an unmeasured bar)."""
    n = len(disagreements)
    if n < 2:
        return math.inf
    m = sum(disagreements) / n
    return math.sqrt(sum((d - m) ** 2 for d in disagreements) / (n - 1))


def best_side(c: Candidate, weight: float) -> Tuple[str, float]:
    """The side with the larger post-shrink net edge, and that edge."""
    p = shrink(c.p_model, c.mid, weight)
    ey = net_edge("yes", p, c.yes_bid, c.yes_ask, c.fee)
    en = net_edge("no", p, c.yes_bid, c.yes_ask, c.fee)
    return ("yes", ey) if ey >= en else ("no", en)


def clears(c: Candidate, weight: float, bar: float) -> Optional[str]:
    """The side to take if what is left after shrink clears the error bar (which already sits above
    the fee-inclusive net edge), else None."""
    side, edge = best_side(c, weight)
    return side if edge > bar else None


def ladder_key(c: Candidate, side: str) -> Tuple[str, str, str]:
    """A game's ladder: one game, one market family, one side."""
    return (c.game, c.family, side)


def select(candidates: Iterable[Candidate], weight: float, bar: float) -> List[Tuple[Candidate, str]]:
    """One position per (market, band): the first qualifying row by ``ts``. Returns (row, side)."""
    kept: Dict[Tuple[str, str], Tuple[Candidate, str]] = {}
    for c in sorted(candidates, key=lambda x: x.ts):
        key = (c.market_ticker, c.band)
        if key in kept:
            continue
        side = clears(c, weight, bar)
        if side is not None:
            kept[key] = (c, side)
    return list(kept.values())


def ladder_exposures(kept: Iterable[Tuple[Candidate, str]]) -> Dict[Tuple[str, str, str], float]:
    """Exposure per ladder. Strikes of one curve are one view of one distribution, so a ladder carries
    the LARGEST single stake in it, not the sum."""
    out: Dict[Tuple[str, str, str], float] = {}
    for c, side in kept:
        k = ladder_key(c, side)
        out[k] = max(out.get(k, 0.0), c.stake)
    return out
