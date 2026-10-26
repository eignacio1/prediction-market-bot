"""W64.2 / ADR-0072 (PROPOSED): flat demo stakes on SHADOW cells. DEMO ONLY, OFF BY DEFAULT.

A SHADOW cell's forecast row is written first and is never altered by anything here. If the
row clears the edge gate and this switch is ON, ONE flat demo order is placed under the
demo_fill_policy placement rule. Stake = ADR-0050 flat measurement stake; kelly_fraction stays 0.

Switch: SHADOW_FLAT_STAKE (exact value ``on`` enables; anything else is OFF, fail closed).
It additionally requires DEMO_FILL_PLACEMENT_RULE to be ON: no shadow order is ever placed
under today's stale-mid behaviour.
"""
from __future__ import annotations

import os
import uuid
from typing import Any, Callable, Optional

from prediction_market_bot.c5_execution import demo_fill_policy as pol
from prediction_market_bot.c5_execution import kill_switch_state as ksw

SWITCH_ENV = "SHADOW_FLAT_STAKE"
EDGE_GATE = 0.0  # the shadow arm's own gate: net-of-fee (k007) edge > 0


def is_enabled() -> bool:
    return pol.switch_value(SWITCH_ENV) == "on" and pol.is_enabled()


def demo_host_ok() -> bool:
    """W68.2: DEMO ONLY, asserted at the point of use. True only when the order base URL resolves
    to the Kalshi DEMO host; the production host or an unrecognised BOT_ENV is refused (fail closed).
    This replaces the old 'NBA shadow is credential-free' guard: credentials are now allowed on
    shadow lines, but only ever against demo."""
    from prediction_market_bot.c5_execution import kalshi_client as kc
    try:
        return kc._kalshi_base_url() == kc._KALSHI_DEMO_BASE_URL
    except ValueError:
        return False


SHADOW_KILL_BAND = "shadow"  # GG-745: kill_switch_shadow.flag halts only the shadow staker


def maybe_place(
    row: dict[str, Any],
    client: Any,
    stake_fn: Optional[Callable[[float], float]] = None,
) -> Optional[dict[str, Any]]:
    """Called AFTER the shadow row is persisted. ``row`` is read, never mutated.
    Uses the runner's own row fields: market_ticker, mid (YES frame), e_net_yes_k007,
    e_net_no_k007. Gate = the net-of-fee edge the arm already logs is positive (> 0);
    direction = the side with the larger net edge."""
    if not is_enabled():
        return None
    if not demo_host_ok():
        pol.append_log({"event": "shadow_skip", "reason": "production_host_refused",
                        "row_id": f"{row.get('run_id')}|{row.get('market_ticker')}"})
        return None
    halted = ksw.halt_reason(band_name=SHADOW_KILL_BAND)  # GG-667: same NFR-03 flag state the C4/T4 paths honour
    if halted:
        pol.append_log({"event": "shadow_skip", "reason": "kill_switch_halted", "meta": halted,
                        "row_id": f"{row.get('run_id')}|{row.get('market_ticker')}"})
        return None
    ticker = row.get("market_ticker")
    ey, en, mid = row.get("e_net_yes_k007"), row.get("e_net_no_k007"), row.get("mid")
    rid = f"{row.get('run_id')}|{ticker}"
    if not ticker or ey is None or en is None or mid is None:
        pol.append_log({"event": "shadow_skip", "reason": "row_missing_fields", "row_id": rid})
        return None
    direction, edge = ("yes", ey) if ey >= en else ("no", en)
    if edge <= EDGE_GATE:
        return None  # arm's own gate not cleared: not an order candidate
    why = pol.listing_skip_reason(client, ticker)  # W67.2/GG-564: arm-blind, before assignment
    if why:
        pol.append_log({"event": "shadow_skip", "reason": why, "row_id": rid})
        return None
    if stake_fn is None:  # ADR-0050 flat measurement stake (lazy: heavy module)
        from prediction_market_bot.run_t4_mlb_live import measurement_stake_and_stratum
        stake_fn = lambda e: measurement_stake_and_stratum(e)[0]  # noqa: E731
    mid_entry = float(mid) if direction == "yes" else 1.0 - float(mid)
    why = pol.cash_skip_reason(client, float(stake_fn(mid_entry)))  # W77.1/GG-840: arm-blind, before assignment
    if why:
        pol.append_log({"event": "shadow_skip", "reason": why, "row_id": rid})
        return None
    treatment = pol.assigned(rid)
    if treatment:
        dec = pol.decide(client, ticker, direction, float(mid), rid)
        if dec.action != "SUBMIT":
            pol.append_log({"event": "shadow_skip", "reason": dec.reason, "row_id": rid, "meta": dec.meta})
            return None
        price_yes = dec.mid_price
    else:
        # W69.1/GG-586: the CONTROL arm places the order exactly as control does for MLB:
        # model-mid limit, no book read, no anchoring, no cancel. Same assignment hash and share.
        price_yes = float(mid)
    entry = price_yes if direction == "yes" else 1.0 - price_yes
    stake = float(stake_fn(entry))
    order = client.submit_order(ticker=ticker, side=direction, size_usd=stake,
                                mid_price=price_yes, band=SHADOW_KILL_BAND,
                                client_order_id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"shadow-flat-stake/{rid}")))
    pol.append_log({"event": "shadow_order", "row_id": rid, "ok": order.ok, "order_id": order.order_id,
                    "stake_usd": stake, "price_yes": price_yes, "side": direction,
                    "ticker": ticker, "error": order.error, "arm": "treatment" if treatment else "control"})
    if treatment and order.ok and order.order_id:
        pol.schedule_cancel(client, order.order_id, rid, ticker)
    feed_exposure_gate()
    return {"order_id": order.order_id, "ok": order.ok}


def feed_exposure_gate() -> None:
    """W87.2/GG-1082: the ledger-less SHADOW book reports its placed-order stake (from the shadow
    order log) to the exposure gate. Never raises; a failure marks the book failed (orders refused)."""
    from prediction_market_bot.c4_risk_engine import exposure_gate as xg
    try:
        xg.record_book("SHADOW", xg.shadow_state(pol.log_path()), xg.load_settled()[0])
    except Exception as e:  # noqa: BLE001
        try:
            xg.mark_feed_failed("SHADOW", repr(e)[:200])
        except Exception:  # noqa: BLE001
            pass


def make_on_row(adapter: Any) -> Optional[Callable[[dict], None]]:
    """on_row callback for pregame_shadow.runner.run_once, or None when the switch is OFF
    (so OFF passes exactly what the scripts passed before). Needs a signing client."""
    if not is_enabled():
        return None
    if not demo_host_ok():
        pol.append_log({"event": "shadow_skip", "reason": "production_host_refused_switch_inert"})
        return None
    client = getattr(adapter, "_client", None)
    if client is None or not client.has_signing_key():
        pol.append_log({"event": "shadow_skip", "reason": "no_signing_key_switch_inert"})
        return None
    pol.sweep_overdue(client)
    feed_exposure_gate()  # the book must exist before its first order (no writer = refused)
    return lambda row: maybe_place(row, client)
