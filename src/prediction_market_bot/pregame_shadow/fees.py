"""Fee candidates for E_net at entry (EXP-037). Per-contract, taker, on entry price q.

k007  : 0.07 * q * (1-q)           (ADR-0016)
kmult : 0.07 * 0.5 * q * (1-q)     (series API fee_multiplier=0.5; coefficient INFERRED,
                                    not established from accessible docs -- EXP-035 D2(e), GG-332)
"""
from __future__ import annotations

from prediction_market_bot.quant import money as _Q  # noqa: E402

K007 = 0.07
KMULT = 0.035


def fee_k007(q: float) -> float:
    """Thin wrapper: the one definition lives in quant.money (W87.1, bit-equal on the frozen snapshot)."""
    return _Q.fee_k007(q)


def fee_kmult(q: float) -> float:
    return KMULT * q * (1.0 - q)


def e_net(p_yes: float, yes_bid: float, yes_ask: float, fee) -> tuple[float, float]:
    """(E_net buying YES at the ask, E_net buying NO at 1-yes_bid), per contract, $."""
    q_no = 1.0 - yes_bid
    return (p_yes - yes_ask - fee(yes_ask), (1.0 - p_yes) - q_no - fee(q_no))
