"""Money: ONE net-edge and ONE fill-priced P&L definition (Kalshi taker, fee k007 = 0.07*q*(1-q), ADR-0016)."""
from __future__ import annotations

K007 = 0.07


def fee_k007(q: float) -> float:
    """Per-contract taker fee at entry price q in dollars. Applies to taker fills; maker/rebate schedules differ."""
    return K007 * q * (1.0 - q)


def net_edge(p_yes: float, yes_bid: float, yes_ask: float) -> dict:
    """Model-expected net edge per contract at entry. YES is bought at the ask, NO at 1 - yes_bid.
    Returns {'yes', 'no', 'side', 'edge'} with edge = the better side. Applies when a two-sided quote exists;
    with a one-sided or crossed book the caller must not call this."""
    q_no = 1.0 - yes_bid
    ey = p_yes - yes_ask - fee_k007(yes_ask)
    en = (1.0 - p_yes) - q_no - fee_k007(q_no)
    return {"yes": ey, "no": en, "side": "yes" if ey >= en else "no", "edge": max(ey, en)}


def fill_pnl(side: str, fill_price_yes: float, y: float) -> float:
    """Realised P&L per contract net of fee. `fill_price_yes` is the YES-contract price paid for side='yes',
    or the YES-equivalent price (1 - NO price paid) for side='no'. y is the YES outcome (0, 0.5 push, 1)."""
    if side == "yes":
        return y - fill_price_yes - fee_k007(fill_price_yes)
    q = 1.0 - fill_price_yes
    return (1.0 - y) - q - fee_k007(q)
