"""W106.2 (B-057) cost-wall helpers. NEW functions only; money.py is untouched.

All amounts are dollars per ONE contract on a $1 payout. Fee rule and table come from money.fee / kalshi_fees.json
(Kalshi fee schedule: PDF 2026-07-07 and web page read 2026-10-27, undated).

When it applies: pricing a single round of crossing the book (taker) or resting (maker) on a binary contract.
When it does not: it is not a model of fill probability, queue position or size impact; markout is passed in, not predicted.
"""
from __future__ import annotations

from .money import fee


def fee_per_contract(series: str, price: float, side: str = "taker", phase: str = "prelive") -> float:
    """Exact schedule fee for one contract (100-lot fee / 100, so centicent rounding is amortised like a real order)."""
    return fee(series, price, 100, side, phase) / 100.0


def taker_entry_cost(series: str, mid: float, half_spread: float, phase: str = "prelive") -> float:
    """Cost of buying at the ask versus the mid: half-spread plus the taker fee at the price actually paid."""
    return half_spread + fee_per_contract(series, min(max(mid + half_spread, 0.01), 0.99), "taker", phase)


def taker_round_trip_cost(series: str, mid: float, half_spread: float, phase: str = "prelive") -> float:
    """Cross in and cross out before settlement: two half-spreads and two taker fees (entry at ask, exit at bid)."""
    ask = min(mid + half_spread, 0.99)
    bid = max(mid - half_spread, 0.01)
    return 2 * half_spread + fee_per_contract(series, ask, "taker", phase) + fee_per_contract(series, bid, "taker", phase)


def maker_entry_cost(series: str, fill_price: float, markout: float, phase: str = "prelive") -> float:
    """Cost of a resting fill versus the mid one minute later: maker fee plus adverse markout (markout > 0 means the
    mid moved against us, so pass -1 * the signed 'held-side mid minus fill price' figure)."""
    return fee_per_contract(series, fill_price, "maker", phase) + markout


def net_after_cost(gross: float, cost: float) -> float:
    return gross - cost


def k007_overstatement(series: str, price: float, phase: str = "prelive") -> float:
    """fee_k007 minus the exact taker fee per contract (positive = k007 overstates, as for MLB pre-game)."""
    from .money import fee_k007
    return fee_k007(price) - fee_per_contract(series, price, "taker", phase)
