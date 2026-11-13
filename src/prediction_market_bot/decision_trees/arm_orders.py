"""W112.3 / B-083 (D6 layer 7): the router's arm picks the side of the ADR-0072 demo forward test's orders.

DEMO ONLY, flat demo stake, kelly 0. Authorization: operator 2026-11-11 16:51 PT ("yes I approve"); recorded as
the superseding addendum ADR-0072-ADDENDUM-W112-3 (the frozen ADR-0072 file is not edited).

For a routed shadow row (row["router"] from shadow_route.router_fields):
  RIDE            backs the market's favoured side (mid >= 0.5 -> yes) at its price
  FADE            backs the other side
  MOMENTUM        backs the move's side (the router's side)
  POT_OF_GOLD     backs the longshot branch's side (the router's side)
  MODEL_FADE      backs the larger-net-edge side (the router's side)
  NO_BET / none   places nothing
For RIDE and FADE the side is derived here from the row and must equal the router's side; a disagreement skips.

Switch ARM_ORDERS: "on" -> the arm path replaces the old edge rule on routed rows; "dry" -> would-be orders are
logged, none placed, and the old rule runs exactly as before; anything else (default) -> OFF, today's behaviour.
Price and placement are the ADR-0072 policy (demo_fill_policy.decide: book anchor, 60 s cancel, max mid gap).
Stake goes through c4_risk_engine.arm_sizing.size_for (W113.1, via row_sizing: flat demo stake cut by the event / day /
arm / same-game caps; Kelly-shaped stake logged, never placed). The decision is logged on every order and skip. SIZER, if
set, overrides it (tests).
Every order and every would-be order carries: arm, leaf_id, split path (branch + filters fired), and the ADR-0072
assignment (treatment / control) the row would have had. Orders go to their own log so the placement comparison
(treatment vs control) is still read on its own rows.
Gates, in order: switch -> demo host -> kill switch (global + shadow band) -> arm -> side -> listing -> stake ->
per-event cap and daily breaker (c4 constants) -> cash -> placement policy. Production Kalshi or real funds: never.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from prediction_market_bot.c4_risk_engine import exposure_gate as xg
from prediction_market_bot.c4_risk_engine import risk
from prediction_market_bot.decision_trees import row_sizing as rs
from prediction_market_bot.c5_execution import demo_fill_policy as pol
from prediction_market_bot.c5_execution import kill_switch_state as ksw
from prediction_market_bot.c5_execution.shadow_flat_stake import SHADOW_KILL_BAND, demo_host_ok

BOOK = "ARM_ORDERS"
SWITCH_ENV = "ARM_ORDERS"
KILL_BAND = SHADOW_KILL_BAND
ORDER_EVENT = "arm_order"
WOULD_EVENT = "arm_would_order"
SKIP_EVENT = "arm_skip"
NOTIONAL_USD = xg.SHADOW_NOTIONAL_USD
OFF, DRY, ON = "off", "dry", "on"
ARMS = ("RIDE", "FADE", "MOMENTUM", "POT_OF_GOLD", "MODEL_FADE")
_BRANCH_ARM = {"MOMENTUM_FOLLOW": "MOMENTUM", "MOMENTUM_FADE": "MOMENTUM"}

# size_for hook: Block 112.2 sets this to its per-arm rule. None -> today's flat demo stake.
SIZER: Optional[Callable[[str, Any, dict], float]] = None


def mode() -> str:
    v = (pol.switch_value(SWITCH_ENV) or "").strip().lower()
    return v if v in (ON, DRY) else OFF


def order_log_path() -> Path:
    return pol.log_path().parent / "arm_orders" / "orders.jsonl"


def append_order_log(entry: dict, path: Optional[Path] = None) -> None:
    p = path or order_log_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    entry = {"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "book": BOOK, **entry}
    with open(p, "a") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")


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


def _placed(path: Optional[Path] = None) -> list:
    return [e for e in _read(path or order_log_path()) if e.get("event") == ORDER_EVENT and e.get("ok")]


def cap_reason(event: str, stake: float, day: str, path: Optional[Path] = None) -> Optional[str]:
    placed = _placed(path)
    if sum(float(e.get("stake_usd") or 0) for e in placed if e.get("event_ticker") == event) + stake > \
            risk._HARD_LIMITS["max_single_event_exposure_usd"]:
        return "per_event_cap"
    if sum(float(e.get("stake_usd") or 0) for e in placed if str(e.get("ts", "")).startswith(day)) + stake > \
            NOTIONAL_USD * risk.MAX_DAILY_LOSS_PCT:
        return "daily_breaker"
    return None


def feed_exposure_gate(path: Optional[Path] = None) -> None:
    try:
        xg.record_book(BOOK, xg.shadow_state(path or order_log_path(), NOTIONAL_USD, ORDER_EVENT), xg.load_settled()[0])
    except Exception as e:  # noqa: BLE001
        try:
            xg.mark_feed_failed(BOOK, repr(e)[:200])
        except Exception:  # noqa: BLE001
            pass


def size_for(arm: str, cell: Any, context: dict) -> float:
    """Stake in demo USD. Default = today's flat demo stake (ADR-0050 measurement stake). 112.2 replaces it via SIZER."""
    if SIZER is not None:
        return float(SIZER(arm, cell, context))
    from prediction_market_bot.run_t4_mlb_live import measurement_stake_and_stratum
    return float(measurement_stake_and_stratum(context["entry"])[0])


def sized_stake(arm: str, row: dict, router: dict, side: str, ctx: dict, log: Optional[Path], now: datetime):
    """(stake, {'size_for': {...}}). The SIZER hook (if set) wins and carries no decision; else layer 6, arm_sizing.size_for,
    with the open exposure and same-game legs read from the arm order log (W113.1)."""
    if SIZER is not None:
        return float(SIZER(arm, None, ctx)), {}
    flat = size_for(arm, None, ctx)
    d = rs.order_decision(row, router, side, flat, _placed(log), now)
    return float(d.stake_usd), d.as_row_fields()


def arm_of(router: Optional[dict]) -> Optional[str]:
    """The arm the router logged for this row, normalised; None when unrouted or NO_BET."""
    if not router or router.get("branch") in (None, "ERROR"):
        return None
    a = router.get("arm") or router.get("branch")
    a = _BRANCH_ARM.get(a, a)
    return a if a in ARMS else None


def side_for(arm: str, row: dict, router: dict) -> Optional[str]:
    """yes / no, or None. RIDE and FADE are derived from the row's mid and must match the router's side."""
    rs = (router.get("side") or "").lower() or None
    if arm in ("RIDE", "FADE"):
        mid = row.get("mid")
        if mid is None or float(mid) == 0.5:
            return None
        fav = "yes" if float(mid) > 0.5 else "no"
        want = fav if arm == "RIDE" else ("no" if fav == "yes" else "yes")
        return want if rs == want else None
    return rs if rs in ("yes", "no") else None


def is_routed(row: dict) -> bool:
    """True when the row carries a usable router decision (so the arm, not the old rule, owns it when ON)."""
    r = row.get("router")
    return bool(r) and r.get("branch") not in (None, "ERROR")


def act(row: dict, client: Any, now: Optional[datetime] = None, log: Optional[Path] = None) -> Optional[dict]:
    """One routed row -> at most one demo order. Returns the outcome dict, or None when the switch is OFF.
    Never raises on a refusal; every outcome is logged."""
    m = mode()
    if m == OFF:
        return None
    now = now or datetime.now(timezone.utc)
    ticker = row.get("market_ticker")
    rid = f"{row.get('run_id')}|{ticker}"
    router = row.get("router") or {}
    arm = arm_of(router)
    base = {"row_id": rid, "ticker": ticker, "event_ticker": row.get("event_ticker"), "sport": row.get("sport"),
            "market_type": row.get("market_type"), "band": row.get("band"), "mode": m,
            "arm": arm or router.get("branch") or "UNROUTED", "leaf_id": router.get("leaf_id"),
            "split_path": {"branch": router.get("branch"), "tier": router.get("tier"),
                           "filters_fired": router.get("filters_fired") or [], "reason": router.get("reason")}}

    def out(event, reason, **kw):
        r = {"event": event, "reason": reason, **base, **kw}
        append_order_log(r, log)
        return r

    if not demo_host_ok():
        return out(SKIP_EVENT, "production_host_refused")
    halted = ksw.halt_reason(band_name=KILL_BAND)
    if halted:
        return out(SKIP_EVENT, "kill_switch_halted", meta=halted)
    if arm is None:
        return out(SKIP_EVENT, "no_bet" if router.get("branch") == "NO_BET" else "unrouted")
    side = side_for(arm, row, router)
    if side is None:
        return out(SKIP_EVENT, "side_unavailable_or_disagrees", router_side=router.get("side"))
    mid = row.get("mid")
    if not ticker or mid is None:
        return out(SKIP_EVENT, "row_missing_fields")
    would = "treatment" if pol.assigned(rid) else "control"  # the ADR-0072 assignment this row would have had
    base["adr0072_assignment"] = would
    why = pol.listing_skip_reason(client, ticker)
    if why:
        return out(SKIP_EVENT, why)
    entry_guess = float(mid) if side == "yes" else 1.0 - float(mid)
    ctx = {"entry": entry_guess, "row": row, "router": router, "side": side, "assignment": would}
    stake, sz = sized_stake(arm, row, router, side, ctx, log, now)
    base.update(sz)
    base["size_arm"] = rs.sizing_arm(router)
    if stake <= 0:
        return out(SKIP_EVENT, "size_zero:" + str((sz.get("size_for") or {}).get("reason", "sizer")), stake_usd=stake)
    why = cap_reason(row.get("event_ticker") or ticker, stake, now.strftime("%Y-%m-%d"), log)
    if why:
        return out(SKIP_EVENT, why, stake_usd=stake)
    why = pol.cash_skip_reason(client, stake)
    if why:
        return out(SKIP_EVENT, why, stake_usd=stake)
    dec = pol.decide(client, ticker, side, float(mid), rid)  # ADR-0072 placement: book anchor, mid-gap skip
    if dec.action != "SUBMIT":
        return out(SKIP_EVENT, dec.reason, meta=dec.meta, stake_usd=stake)
    price_yes = dec.mid_price
    entry = price_yes if side == "yes" else 1.0 - price_yes
    if m == DRY:
        return out(WOULD_EVENT, "dry_run_no_order", side=side, stake_usd=stake, price_yes=price_yes, entry_price=entry)
    order = client.submit_order(ticker=ticker, side=side, size_usd=stake, mid_price=price_yes, band=KILL_BAND,
                                client_order_id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"arm-orders/{rid}")))
    r = {"event": ORDER_EVENT, "ok": order.ok, "order_id": order.order_id, "stake_usd": stake, "side": side,
         "price_yes": price_yes, "entry_price": entry, "error": order.error, **base}
    if not order.ok:
        r.update(pol.refusal_context(client, None))
    append_order_log(r, log)
    if order.ok and order.order_id:
        pol.schedule_cancel(client, order.order_id, rid, ticker)
    feed_exposure_gate(log)
    return r
