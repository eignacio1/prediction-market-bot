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

SWITCH_ENV = "SHADOW_FLAT_STAKE"
EDGE_GATE = 0.0  # the shadow arm's own gate: net-of-fee (k007) edge > 0


def is_enabled() -> bool:
    return os.environ.get(SWITCH_ENV, "").strip() == "on" and pol.is_enabled()


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
    if not pol.assigned(rid):
        pol.append_log({"event": "shadow_skip", "reason": "control_arm", "row_id": rid})
        return None
    dec = pol.decide(client, ticker, direction, float(mid), rid)
    if dec.action != "SUBMIT":
        pol.append_log({"event": "shadow_skip", "reason": dec.reason, "row_id": rid, "meta": dec.meta})
        return None
    entry = dec.mid_price if direction == "yes" else 1.0 - dec.mid_price
    if stake_fn is None:  # ADR-0050 flat measurement stake (lazy: heavy module)
        from prediction_market_bot.run_t4_mlb_live import measurement_stake_and_stratum
        stake_fn = lambda e: measurement_stake_and_stratum(e)[0]  # noqa: E731
    stake = float(stake_fn(entry))
    order = client.submit_order(ticker=ticker, side=direction, size_usd=stake,
                                mid_price=dec.mid_price, client_order_id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"shadow-flat-stake/{rid}")))
    pol.append_log({"event": "shadow_order", "row_id": rid, "ok": order.ok, "order_id": order.order_id,
                    "stake_usd": stake, "price_yes": dec.mid_price, "side": direction,
                    "ticker": ticker, "error": order.error})
    if order.ok and order.order_id:
        pol.schedule_cancel(client, order.order_id, rid, ticker)
    return {"order_id": order.order_id, "ok": order.ok}


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
    return lambda row: maybe_place(row, client)
