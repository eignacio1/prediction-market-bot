"""W105.5 / B-054: route -> DEMO order for the ride/fade board. DEMO ONLY, flat stake, kelly 0.

A decision is turned into one of three actions:
  ORDER  the route is RIDE / FADE / MOMENTUM_* on a cell whose ride_cells.toml status is HELD_OUT or
         FORWARD_PASSED, and every gate below is clear -> one flat demo order (book RIDE_BOARD).
  PAPER  the cell is IN_SAMPLE (or the route has no table cell) -> logged, no order.
  SKIP   a gate refused (switch off, production host, kill switch, per-event cap, daily breaker, cash).

Gates, in order: switch RIDE_BOARD_ORDERS == "on" (anything else is OFF) -> demo host -> NFR-03 kill switch
(global + band "ride_board") -> per-event cap (c4 _HARD_LIMITS) -> daily breaker (c4 MAX_DAILY_LOSS_PCT of the
book notional, measured on the book's own placed stake: ledger-less, so the stake IS the exposure) -> cash.
The exposure gate (W87.2) is fed after every order and still runs inside KalshiMarketClient.submit_order.
Production Kalshi or real funds: never.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from prediction_market_bot.c4_risk_engine import exposure_gate as xg
from prediction_market_bot.c4_risk_engine import risk
from prediction_market_bot.c5_execution import demo_fill_policy as pol
from prediction_market_bot.c5_execution import kill_switch_state as ksw
from prediction_market_bot.c5_execution.shadow_flat_stake import demo_host_ok
from prediction_market_bot.decision_trees import ride

BOOK = "RIDE_BOARD"
KILL_BAND = "ride_board"
SWITCH_ENV = "RIDE_BOARD_ORDERS"
ORDER_EVENT = "ride_order"
NOTIONAL_USD = xg.SHADOW_NOTIONAL_USD
ORDERABLE = ride.RIDEABLE  # HELD_OUT, FORWARD_PASSED
ORDER = "ORDER"
PAPER = "PAPER"
SKIP = "SKIP"


def order_log_path() -> Path:
    return pol.log_path().parent / "ride_board" / "orders.jsonl"


def is_enabled() -> bool:
    return pol.switch_value(SWITCH_ENV) == "on"


def _read(path: Path) -> list:
    out = []
    try:
        for line in path.read_text().splitlines():
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    except FileNotFoundError:
        pass
    return out


def append_order_log(entry: dict, path: Optional[Path] = None) -> None:
    p = path or order_log_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    entry = {"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "book": BOOK, **entry}
    with open(p, "a") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")


def _placed(path: Optional[Path] = None) -> list:
    return [e for e in _read(path or order_log_path()) if e.get("event") == ORDER_EVENT and e.get("ok")]


def event_exposure_usd(event: str, path: Optional[Path] = None) -> float:
    return sum(float(e.get("stake_usd") or 0.0) for e in _placed(path) if e.get("event_ticker") == event)


def day_exposure_usd(day: str, path: Optional[Path] = None) -> float:
    return sum(float(e.get("stake_usd") or 0.0) for e in _placed(path) if str(e.get("ts", "")).startswith(day))


def cap_reason(event: str, stake: float, day: str, path: Optional[Path] = None) -> Optional[str]:
    """Per-event cap and daily breaker, both from c4's own constants."""
    if event_exposure_usd(event, path) + stake > risk._HARD_LIMITS["max_single_event_exposure_usd"]:
        return "per_event_cap"
    if day_exposure_usd(day, path) + stake > NOTIONAL_USD * risk.MAX_DAILY_LOSS_PCT:
        return "daily_breaker"
    return None


def classify(route: Any, cell: Any) -> str:
    """ORDER-eligible vs PAPER, before any gate. NO_BET never reaches here."""
    if cell is None or getattr(cell, "status", None) not in ORDERABLE:
        return PAPER
    return ORDER


def feed_exposure_gate(path: Optional[Path] = None) -> None:
    try:
        xg.record_book(BOOK, xg.shadow_state(path or order_log_path(), NOTIONAL_USD, ORDER_EVENT), xg.load_settled()[0])
    except Exception as e:  # noqa: BLE001
        try:
            xg.mark_feed_failed(BOOK, repr(e)[:200])
        except Exception:  # noqa: BLE001
            pass


def _default_stake(entry: float) -> float:
    from prediction_market_bot.run_t4_mlb_live import measurement_stake_and_stratum
    return measurement_stake_and_stratum(entry)[0]


def act(d: dict, client: Any, stake_fn: Optional[Callable[[float], float]] = None, log: Optional[Path] = None,
        now: Optional[datetime] = None) -> dict:
    """d = the decision row: ticker, event_ticker, route, side, cell_status (None if no cell), yes_bid, yes_ask,
    decision_id. Returns {"action", "reason", ...}. Never raises on a refusal; every outcome is logged."""
    now = now or datetime.now(timezone.utc)
    rid, ticker = d["decision_id"], d["ticker"]

    class _Cell:
        status = d.get("cell_status")
    kind = classify(d["route"], _Cell if d.get("cell_status") else None)
    base = {"decision_id": rid, "ticker": ticker, "event_ticker": d.get("event_ticker"), "route": d["route"],
            "side": d["side"]}

    def out(action, reason, **kw):
        row = {"event": "ride_decision_action", "action": action, "reason": reason, **base, **kw}
        append_order_log(row, log)
        return row

    if kind == PAPER:
        return out(PAPER, "cell_" + str(d.get("cell_status") or "none"))
    if not is_enabled():
        return out(SKIP, "switch_off")
    if not demo_host_ok():
        return out(SKIP, "production_host_refused")
    halted = ksw.halt_reason(band_name=KILL_BAND)
    if halted:
        return out(SKIP, "kill_switch_halted", meta=halted)
    side = d["side"]
    ask, bid = d["yes_ask"], d["yes_bid"]
    # Limit price in the YES frame: buy YES at the ask; buy NO at the NO ask = 1 - yes_bid, i.e. YES-frame price yes_bid.
    price_yes = float(ask) if side == "yes" else float(bid)
    entry = price_yes if side == "yes" else 1.0 - price_yes
    stake = float((stake_fn or _default_stake)(entry))
    why = cap_reason(d.get("event_ticker") or ticker, stake, now.strftime("%Y-%m-%d"), log)
    if why:
        return out(SKIP, why, stake_usd=stake)
    why = pol.listing_skip_reason(client, ticker) or pol.cash_skip_reason(client, stake)
    if why:
        return out(SKIP, why, stake_usd=stake)
    order = client.submit_order(ticker=ticker, side=side, size_usd=stake, mid_price=price_yes, band=KILL_BAND,
                                client_order_id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"ride-board/{rid}")))
    row = {"event": ORDER_EVENT, "ok": order.ok, "order_id": order.order_id, "stake_usd": stake,
           "price_yes": price_yes, "entry_price": entry, "error": order.error, **base}
    if not order.ok:
        row.update(pol.refusal_context(client, None))
    append_order_log(row, log)
    if order.ok and order.order_id:
        pol.schedule_cancel(client, order.order_id, rid, ticker)
    feed_exposure_gate(log)
    return {"action": ORDER, "reason": "placed" if order.ok else "refused", "ok": order.ok, "order_id": order.order_id,
            "price_yes": price_yes, "entry_price": entry, "stake_usd": stake}
