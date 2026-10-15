"""GG-746 / W75.5: recurring ADR-0071 booking of OPEN paper positions from Kalshi's own settlement.

The retired NFL game-market book was booked once by hand (W58.1) and nothing ever booked it again, so four
positions whose games were still in the future that day stayed open past game end. This is the reusable sweep
(the one-time script now calls it). Each open position resolves to a typed result:

  settled / cancelled  -> booked via PaperTrader.settle_position_from_venue (cancelled at Kalshi's value,
                          flagged cancelled, excluded from G6 / calibration by existing consumers)
  NOT_FINAL            -> left open; the game is inside its scheduled-end window
  LOOKUP_FAILED        -> left open and returned in `alarms`: the venue state is unknown/errored, or the game
                          is past its scheduled end + grace with no settlement. Never read as "wait".
"""
from __future__ import annotations

import os
import time
from collections import Counter
from pathlib import Path
from typing import Callable, Optional

os.environ.setdefault("BOT_ENV", "paper")

from prediction_market_bot.c5_execution.paper_trader import PaperTrader
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from prediction_market_bot.pregame_shadow import settle_result as sr
from prediction_market_bot.run_resolve_mlb import (
    VENUE_CANCELLED,
    VENUE_NOT_FINAL,
    VENUE_SETTLED,
    _settlement_value,
    _venue_market_state,
)


def classify_position(p: dict, state: str, raw: dict, now=None) -> tuple[Optional[tuple], Optional[sr.SettleResult]]:
    """((result, value), None) when bookable, else (None, NOT_FINAL | LOOKUP_FAILED)."""
    if state == VENUE_SETTLED:
        return (str(raw["result"]).lower(), None), None
    if state == VENUE_CANCELLED:
        v = _settlement_value(raw)
        if v is None:
            return None, sr.lookup_failed("cancelled_no_value")
        return ("scalar", v), None
    gd = p.get("game_date")
    if state == VENUE_NOT_FINAL or not gd:
        if gd:
            return None, sr.missing_final(gd, now, what="venue_settlement")
        return None, sr.lookup_failed("no_game_date")
    return None, sr.lookup_failed(f"venue_state={state}")


def sweep_open_positions(portfolio: Path, audit: Path, apply: bool = False,
                         state_fn: Callable = _venue_market_state, now=None, pause_s: float = 0.15) -> dict:
    trader = PaperTrader(portfolio, AuditLogger(audit, min_severity="INFO"))
    before = trader.get_state()
    open_pos = [p for p in before["open_positions"] if p.get("status") == "OPEN"]
    cache: dict[str, tuple[str, dict]] = {}
    plan, waiting, alarms = [], [], []
    for p in open_pos:
        t = p.get("kalshi_ticker") or ""
        if t not in cache:
            cache[t] = state_fn(t)
            if pause_s:
                time.sleep(pause_s)
        state, raw = cache[t]
        book, res = classify_position(p, state, raw, now)
        if book is not None:
            plan.append((p, *book))
        elif res.status == sr.NOT_FINAL:
            waiting.append({"position_id": p["position_id"], "ticker": t, "reason": res.reason})
        else:
            alarms.append({"position_id": p["position_id"], "ticker": t,
                           "game_date": p.get("game_date"), "reason": res.reason})
    booked = 0
    if apply:
        for p, res, val in plan:
            ok, _ = trader.settle_position_from_venue(p["position_id"], res, val)
            booked += 1 if ok else 0
    after = trader.get_state()
    return {
        "applied": apply,
        "open_before": len(open_pos),
        "bookable": len(plan),
        "booked": booked,
        "not_final": waiting,
        "alarms": alarms,
        "venue_results": dict(Counter(r for _, r, _ in plan)),
        "cancelled": sum(1 for _, r, _ in plan if r == "scalar"),
        "bankroll_before": before["bankroll_usd"],
        "bankroll_after": after["bankroll_usd"],
        "realized_before": before["total_realized_pnl"],
        "realized_after": after["total_realized_pnl"],
        "closed_before": len(before["closed_positions"]),
        "closed_after": len(after["closed_positions"]),
        "open_after": len(after["open_positions"]),
    }
