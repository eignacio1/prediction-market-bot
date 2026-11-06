"""W105.5 / B-054: turn a router Route into a DEMO order, or into a logged paper-only row. DEMO ONLY.

A Route becomes a demo order only when ALL hold, checked in this order (first failure is the logged reason):
  1. the tree is RIDE and a ride_cells.toml cell backs it with status HELD_OUT or FORWARD_PASSED
     (FADE / MOMENTUM_* carry no cell status, so they log a paper row and never order);
  2. the host is the Kalshi DEMO host (demo_host_ok, fails closed) -- production Kalshi / real funds: never;
  3. the kill switch is clear (global + band ``ride_board``);
  4. the exposure gate for book RIDE_BOARD is clear (ENFORCING, W89);
  5. the per-event cap (_HARD_LIMITS max_single_event_exposure_usd) and the daily breaker pass;
  6. kelly_fraction is 0: the stake is the ADR-0050 flat measurement stake, never a Kelly output.
IN_SAMPLE cells get a paper-only row (the evidence is not out-of-sample, so no order).

Own book name RIDE_BOARD / band ``ride_board`` so fills never mix with other books. The order goes through the existing
KalshiMarketClient.submit_order unchanged (it re-checks kill switch and exposure gate itself). Nothing here edits
ride_cells.toml. Never raises into the runner: every failure is a logged skip.

Data epoch (GG-1771/GG-1784): NO-side demo fills before 2026-11-06T01:03:42Z were mirror-priced; any fill or P&L reader
of this book reports pre-epoch YES-only and post-epoch all sides.
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from prediction_market_bot.c4_risk_engine import exposure_gate as xg
from prediction_market_bot.c4_risk_engine.risk import _HARD_LIMITS, MAX_DAILY_LOSS_PCT
from prediction_market_bot.c5_execution import kill_switch_state as ksw
from prediction_market_bot.decision_trees import ride
from prediction_market_bot.decision_trees.router import RIDE, Route, Situation

BOOK = "RIDE_BOARD"
BAND = "ride_board"
KELLY_FRACTION = 0.0  # ADR-0048: flat demo stake only
NOTIONAL_USD = 1000.0  # denominator for the daily breaker (ledger-less book, same convention as SHADOW)
LOG_REL = Path("logs/ride_board/orders.jsonl")


def log_path() -> Path:
    return Path(os.environ.get("RIDE_BOARD_ORDER_LOG") or LOG_REL)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def append(row: dict) -> None:
    p = log_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as fh:
        fh.write(json.dumps({"ts": _now(), **row}, sort_keys=True) + "\n")


def _rows(p: Optional[Path] = None) -> list:
    out = []
    try:
        for line in (p or log_path()).read_text().splitlines():
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    except FileNotFoundError:
        pass
    return out


def placed(rows: list) -> list:
    return [r for r in rows if r.get("event") == "ride_order" and r.get("ok") and r.get("order_id")]


def book_state(p: Optional[Path] = None, notional: float = NOTIONAL_USD) -> dict:
    """Portfolio-shaped state for the exposure gate: every placed ride order counts as open stake (no ledger)."""
    pos = [{"kalshi_ticker": r.get("ticker"), "size_usd": float(r.get("stake_usd") or 0.0), "status": "OPEN"}
           for r in placed(_rows(p))]
    return {"initial_bankroll_usd": notional, "total_realized_pnl": 0.0, "open_positions": pos}


def feed_exposure_gate(p: Optional[Path] = None) -> None:
    """Report this book's placed stake to the exposure gate. Never raises; a failure marks the book failed."""
    try:
        xg.record_book(BOOK, book_state(p), xg.load_settled()[0])
    except Exception as e:  # noqa: BLE001
        try:
            xg.mark_feed_failed(BOOK, repr(e)[:200])
        except Exception:  # noqa: BLE001
            pass


def event_stake(rows: list, event: str) -> float:
    return sum(float(r.get("stake_usd") or 0.0) for r in placed(rows) if r.get("event_ticker") == event)


def day_stake(rows: list, day: str) -> float:
    return sum(float(r.get("stake_usd") or 0.0) for r in placed(rows) if str(r.get("ts", ""))[:10] == day)


def cell_for(s: Situation, route: Route, table: Any) -> Optional[ride.RideCell]:
    """The ride_cells.toml cell behind a RIDE route (same lookup the router used). None if there is none."""
    if route.tree != RIDE or s.mid is None:
        return None
    book = ("tight", "all") if (s.half_spread is not None and s.half_spread <= 0.01) else ("wide", "all")
    d = ride.decide(s.family, s.tier, s.mid, s.half_spread, table, book)
    return d.cell


def skip_reason(s: Situation, route: Route, cell: Optional[ride.RideCell], rows: list, stake_usd: float,
                host_ok: Callable[[], bool], now: Optional[datetime] = None) -> Optional[str]:
    """First reason this route must NOT become a demo order; None = clear to place. Pure given its inputs."""
    if route.tree != RIDE:
        return "paper_only:no_cell_status_for_" + route.tree.lower()
    if cell is None:
        return "paper_only:no_cell"
    if cell.status not in ride.RIDEABLE:
        return "paper_only:cell_" + str(cell.status).lower()
    if not host_ok():
        return "production_host_refused"
    halted = ksw.halt_reason(band_name=BAND)
    if halted:
        return "kill_switch:" + halted
    g = xg.gate_for_order(BAND)
    if g:
        return "exposure_gate:" + g
    cap = float(_HARD_LIMITS["max_single_event_exposure_usd"])
    if event_stake(rows, s.event) + stake_usd > cap:
        return "per_event_cap"
    day = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%d")
    if day_stake(rows, day) + stake_usd > MAX_DAILY_LOSS_PCT * NOTIONAL_USD:
        return "daily_breaker"
    return None


def flat_stake(entry_price: float) -> float:
    from prediction_market_bot.run_t4_mlb_live import measurement_stake_and_stratum  # lazy: heavy module
    return float(measurement_stake_and_stratum(entry_price)[0])


def maybe_order(s: Situation, route: Route, table: Any, client: Any, *,
                host_ok: Optional[Callable[[], bool]] = None,
                stake_fn: Callable[[float], float] = flat_stake,
                now: Optional[datetime] = None, schedule_cancel: bool = True) -> dict:
    """Decide and (if clear) place ONE demo order. Always appends exactly one row to orders.jsonl. Returns that row."""
    if host_ok is None:
        from prediction_market_bot.c5_execution.shadow_flat_stake import demo_host_ok as host_ok  # type: ignore
    base = {"book": BOOK, "ticker": s.ticker, "event_ticker": s.event, "family": s.family, "tier": s.tier,
            "route": route.tree, "side": route.side, "reasons": list(route.reasons), "kelly_fraction": KELLY_FRACTION}
    try:
        cell = cell_for(s, route, table)
        if cell is not None:
            base.update(cell_status=cell.status, cell_bucket=cell.bucket, cell_book=cell.book)
        if route.side not in ("yes", "no") or s.mid is None:
            row = {**base, "event": "ride_skip", "ok": False, "reason": "no_side_or_mid"}
            append(row)
            return row
        entry = s.yes_ask if route.side == "yes" else 1.0 - float(s.yes_bid)
        stake = float(stake_fn(float(entry)))
        why = skip_reason(s, route, cell, _rows(), stake, host_ok, now)
        if why:
            row = {**base, "event": "ride_paper" if why.startswith("paper_only") else "ride_skip", "ok": False,
                   "reason": why, "stake_usd": stake}
            append(row)
            return row
        rid = f"{s.ticker}|{route.tree}|{route.side}|{(now or datetime.now(timezone.utc)).strftime('%Y-%m-%d')}"
        # submit_order buys YES at mid_price, NO at 1 - mid_price (YES-frame price in, GG-1771 epoch semantics).
        order = client.submit_order(ticker=s.ticker, side=route.side, size_usd=stake, mid_price=float(s.mid),
                                    band=BAND, client_order_id=str(uuid.uuid5(uuid.NAMESPACE_URL, "ride-board/" + rid)))
        row = {**base, "event": "ride_order", "ok": bool(order.ok), "order_id": order.order_id, "stake_usd": stake,
               "price_yes": float(s.mid), "error": order.error}
        append(row)
        if order.ok and order.order_id and schedule_cancel:
            from prediction_market_bot.c5_execution import demo_fill_policy as pol
            pol.schedule_cancel(client, order.order_id, rid, s.ticker)
        feed_exposure_gate()
        return row
    except Exception as e:  # noqa: BLE001 -- a failed order step is a logged skip, never a crash
        row = {**base, "event": "ride_skip", "ok": False, "reason": "exception:" + repr(e)[:160]}
        try:
            append(row)
        except Exception:  # noqa: BLE001
            pass
        return row


def sweep_cancels(client: Any, enabled: bool = True, wait: bool = False) -> int:
    """The runner is short-lived, so schedule_cancel's daemon timer dies with it. Finish the job here: optionally wait out
    the cancel delay, then cancel every overdue scheduled order (durable pending records). Never raises. Returns count."""
    if not enabled or client is None:
        return 0
    try:
        import time
        from prediction_market_bot.c5_execution import demo_fill_policy as pol
        if wait:
            time.sleep(pol._float_env(pol.CANCEL_AFTER_ENV, pol.DEFAULT_CANCEL_AFTER_S) + 1.0)
        return int(pol.sweep_overdue(client))
    except Exception:  # noqa: BLE001
        return 0
