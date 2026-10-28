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


# ---- Exact Kalshi fee (W92.2). fee_k007 above is unchanged; it equals the exact taker fee only where the multiplier is 1.
import json as _json
import os as _os
from decimal import ROUND_CEILING as _CEIL, Decimal as _D

_FEE_TABLE_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "kalshi_fees.json")
_FEE_TABLE: dict = {}


def _load_fee_table() -> dict:
    if not _FEE_TABLE:
        with open(_FEE_TABLE_PATH) as fh:
            doc = _json.load(fh)
        by_series = {}
        for g in doc["groups"]:  # later groups override earlier ones
            for s in g["series"]:
                by_series[s] = {"taker": g["taker"], "maker": g["maker"], "source": g["source"]}
        _FEE_TABLE.update({"coef": doc["coefficients"], "defaults": doc["defaults"], "series": by_series})
    return _FEE_TABLE


def fee_multiplier(series: str, side: str = "taker", phase: str = "prelive") -> float:
    """Series multiplier M for side (taker|maker) and phase (prelive|live). Unlisted series: taker 1, maker 0.
    `series` may be a full ticker; the part before the first '-' is used."""
    if side not in ("taker", "maker") or phase not in ("prelive", "live"):
        raise ValueError(f"side={side!r} phase={phase!r}")
    t = _load_fee_table()
    row = t["series"].get(series.split("-")[0], t["defaults"])
    return float(row[side][0 if phase == "prelive" else 1])


def fee_rate(series: str, price: float, side: str = "taker", phase: str = "prelive") -> float:
    """Unrounded per-contract fee in dollars: M * coef * P * (1-P). Use for analytics on per-contract P&L; fee() is the order-level charge."""
    t = _load_fee_table()
    return fee_multiplier(series, side, phase) * t["coef"][side] * price * (1.0 - price)


def fee(series: str, price: float, contracts: int, side: str = "taker", phase: str = "prelive") -> float:
    """Kalshi fee in dollars for one matched order: round-up(M * coef * C * P * (1-P)) to a centicent ($0.0001), the
    definition in the July 2026 schedule. Decimal arithmetic so an exact tie does not round up through float noise.
    The schedule's printed examples are cent-rounded displays; this follows the definition sentence."""
    t = _load_fee_table()
    p = _D(repr(price))
    raw = _D(repr(fee_multiplier(series, side, phase))) * _D(repr(t["coef"][side])) * _D(contracts) * p * (1 - p)
    return float((raw * 10000).to_integral_value(rounding=_CEIL) / 10000)
