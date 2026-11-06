"""Net-of-cost ride / fade trade evaluation on a quoted price archive (W105.4, B-053).

A *quote series* is a time-sorted list of (t_seconds, yes_bid, yes_ask) for ONE market; bid/ask may be None when the
snapshot had no two-sided quote. A trade is entered by crossing the spread at the event snapshot and left either by
selling back into the bid ~60 min later (second taker fee) or by holding to a settlement proxy (one fee).
Everything is read-only analytics: no order, model or ledger is touched.

Sign convention: P&L is per contract, dollars, net of exact Kalshi taker fees (quant.money.fee). FADE = the side
against the move, FOLLOW = the side with it.
"""
from __future__ import annotations

import bisect
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Sequence, Tuple

from .money import fee

Quote = Tuple[float, Optional[float], Optional[float]]


def valid(bid: Optional[float], ask: Optional[float]) -> bool:
    """A tradable two-sided quote: 0 < bid < ask < 1."""
    return bid is not None and ask is not None and 0.0 < bid < ask < 1.0


def phase_for(t: float, event_date) -> str:
    """'live' on the ticker date or the day after (UTC), else 'prelive'. Live multiplier >= prelive, so this errs conservative.
    event_date None -> 'live' (conservative)."""
    if event_date is None:
        return "live"
    d = datetime.fromtimestamp(t, timezone.utc).date()
    return "live" if event_date <= d <= event_date + timedelta(days=1) else "prelive"


def quote_at(q: Sequence[Quote], t_target: float, tol_s: float) -> Optional[Quote]:
    """First snapshot at or after t_target within tol_s (no interpolation); None if none."""
    ts = [x[0] for x in q]
    j = bisect.bisect_left(ts, t_target)
    return q[j] if j < len(ts) and ts[j] - t_target <= tol_s else None


def net_pnl(series: str, move_sign: float, rule: str, entry: Quote, exit_q: Optional[Quote],
            settle_y: Optional[float], event_date) -> Optional[Dict[str, float]]:
    """Net P&L per contract for one event under `rule` ('FADE'|'FOLLOW').

    move_sign +1 = price rose. FADE after a rise buys NO; FOLLOW after a rise buys YES (and mirror for falls).
    Entry: YES at yes_ask, NO at 1 - yes_bid. Exit: YES sold at yes_bid, NO sold at 1 - yes_ask. Returns
    {'half_spread','entry','net60','netset'} (net60 / netset may be absent when that exit is unavailable), or None
    if the entry snapshot has no valid quote."""
    if rule not in ("FADE", "FOLLOW"):
        raise ValueError(rule)
    t0, b0, a0 = entry
    if not valid(b0, a0):
        return None
    buy_yes = (move_sign > 0) == (rule == "FOLLOW")
    entry_px = a0 if buy_yes else 1.0 - b0
    ph0 = phase_for(t0, event_date)
    f_in = fee(series, entry_px, 1, "taker", ph0)
    out: Dict[str, float] = {"half_spread": (a0 - b0) / 2.0, "entry": entry_px}
    if exit_q is not None and valid(exit_q[1], exit_q[2]):
        exit_px = exit_q[1] if buy_yes else 1.0 - exit_q[2]
        f_out = fee(series, exit_px, 1, "taker", phase_for(exit_q[0], event_date))
        out["net60"] = exit_px - entry_px - f_in - f_out
    if settle_y is not None:
        payoff = settle_y if buy_yes else 1.0 - settle_y
        out["netset"] = payoff - entry_px - f_in
    return out


def split_games(first_seen: Dict[str, float], fit_frac: float = 0.7) -> Tuple[set, set]:
    """Earlier fit_frac of games (by first snapshot time, ties by name) = fit; the rest = held out."""
    order = sorted(first_seen, key=lambda g: (first_seen[g], g))
    k = int(len(order) * fit_frac)
    return set(order[:k]), set(order[k:])
