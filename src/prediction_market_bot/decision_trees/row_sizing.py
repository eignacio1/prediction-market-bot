"""W113.1 Part A (D6 layers 6 -> 7): where a routed row meets ``c4_risk_engine.arm_sizing.size_for``.

Two callers, one rule:
  * ``order_decision`` - the full context an arm ORDER is sized with: what is already open on the event / the day / the arm
    (read from the arm order log) and the open legs of the SAME GAME, so the same-game cluster cap can bind.
  * ``row_decision``   - the row-level decision a ROUTED SHADOW ROW carries as ``size_for`` (layer-6 evidence): the same
    rule on an empty book. Cheap and pure: no log read, no I/O. It is evidence of the rule, not an order.

Kelly stays 0 (arm_sizing never places a Kelly stake; the Kelly-shaped stake is logged only). Demo only.

SAME-GAME LEGS. The rule merges open legs whose draws move together (phi >= 0.90). Order rows do not carry the engine's
joint draws, so today a leg's draws are built from its identity: the same market and the same side is the SAME event (one
exposure), the opposite side is its complement, a different market is independent. That is a floor, not the joint: a home
moneyline and a home spread are correlated and are NOT merged until ``DRAWS_PROVIDER`` is set to the 113.3 joint
(``provider(leg) -> bool ndarray`` over shared draws). Declared here so nobody reads "correlated legs are capped" as more than it is.
"""
from __future__ import annotations

import zlib
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional

import numpy as np

from prediction_market_bot.c4_risk_engine import arm_sizing as asz

N_DRAWS = 2000
# 113.3 plugs the NBA joint in here: leg dict {ticker, event_ticker, side, price_yes, market_type} -> bool array or None.
DRAWS_PROVIDER: Optional[Callable[[dict], Any]] = None

_MOMENTUM = ("MOMENTUM_FOLLOW", "MOMENTUM_FADE")
_REG: Dict[tuple, Any] = {}


def sizing_arm(router: Optional[dict]) -> Optional[str]:
    """The arm_sizing name for a router decision. arm_sizing has no MOMENTUM or MODEL_FADE: the router's branch names the
    momentum direction; MODEL_FADE (fade the market on the model's larger net edge) sizes as FADE. None -> unrouted."""
    if not router or router.get("branch") in (None, "ERROR"):
        return None
    branch, arm = router.get("branch"), router.get("arm")
    if branch in _MOMENTUM:
        return branch
    a = arm or branch
    if a == "MOMENTUM":
        return "MOMENTUM_FOLLOW"
    if a == "MODEL_FADE":
        return "FADE"
    return a


def cell_for(row: dict) -> Any:
    """The registry cell of a row (market_type name + band value), or None when the row names none."""
    if not _REG:
        try:
            from prediction_market_bot.c5_execution.market_type_registry import MARKET_TYPE_REGISTRY
            for (mt, band), c in MARKET_TYPE_REGISTRY.items():
                _REG[(mt.name, band.value)] = c
        except Exception:  # noqa: BLE001
            _REG[("", "")] = None
    return _REG.get((str(row.get("market_type")), str(row.get("band"))))


def _p_win(row: dict, side: Optional[str]) -> Optional[float]:
    p = row.get("p_yes")
    if p is None or side not in ("yes", "no"):
        return None
    try:
        return float(p) if side == "yes" else 1.0 - float(p)
    except (TypeError, ValueError):
        return None


def _price(row: dict, side: Optional[str]) -> Optional[float]:
    mid = row.get("mid")
    if mid is None or side not in ("yes", "no"):
        return None
    return float(mid) if side == "yes" else 1.0 - float(mid)


def game_key(event_ticker: Optional[str]) -> str:
    """KXNBAGAME-26NOV12LALBOS and KXNBASPREAD-26NOV12LALBOS are the same game: the part after the series."""
    e = str(event_ticker or "")
    return e.split("-", 1)[1] if "-" in e else e


def leg_draws(leg: dict) -> Optional[np.ndarray]:
    """Boolean 'this leg wins' draws. The provider (113.3 joint) when set, else identity draws (see module doc)."""
    if DRAWS_PROVIDER is not None:
        d = DRAWS_PROVIDER(leg)
        if d is not None:
            return np.asarray(d, bool)
    t = leg.get("ticker")
    if not t:
        return None
    yes = np.random.default_rng(zlib.crc32(str(t).encode())).random(N_DRAWS) < 0.5
    return yes if leg.get("side") == "yes" else ~yes


def open_exposure(placed: Iterable[dict], event_ticker: Optional[str], day: str, arm: str) -> dict:
    """Stake already placed (arm order log, ok orders) on this event / this UTC day / this arm, and the legs of this game."""
    ev, dy, am = 0.0, 0.0, 0.0
    legs: List[dict] = []
    gk = game_key(event_ticker)
    for e in placed:
        s = float(e.get("stake_usd") or 0)
        if e.get("event_ticker") == event_ticker:
            ev += s
        if str(e.get("ts", "")).startswith(day):
            dy += s
            if (e.get("size_arm") or e.get("arm")) == arm:
                am += s
        if gk and game_key(e.get("event_ticker")) == gk:
            legs.append(e)
    return {"event": ev, "day": dy, "arm": am, "legs": legs}


def order_decision(row: dict, router: dict, side: str, flat_stake_usd: float, placed: Iterable[dict],
                   now: Optional[datetime] = None) -> asz.SizeDecision:
    """Size one arm order. ``placed`` = the arm order log's ok orders (read once by the caller)."""
    now = now or datetime.now(timezone.utc)
    arm = sizing_arm(router) or "NO_BET"
    ex = open_exposure(placed, row.get("event_ticker"), now.strftime("%Y-%m-%d"), arm)
    new = {"ticker": row.get("market_ticker"), "event_ticker": row.get("event_ticker"), "side": side,
           "price_yes": row.get("mid"), "market_type": row.get("market_type")}
    open_legs = [asz.OpenLeg(float(o.get("stake_usd") or 0),
                             leg_draws({"ticker": o.get("ticker"), "event_ticker": o.get("event_ticker"),
                                        "side": o.get("side"), "price_yes": o.get("price_yes"),
                                        "market_type": o.get("market_type")}), str(o.get("order_id") or ""))
                 for o in ex["legs"]]
    ctx = asz.SizingContext(price=_price(row, side), p_win=_p_win(row, side), flat_stake_usd=float(flat_stake_usd),
                            open_event_usd=ex["event"], open_day_usd=ex["day"], open_arm_usd=ex["arm"],
                            new_leg_draws=leg_draws(new), same_game_open=tuple(open_legs))
    return asz.size_for(arm, cell_for(row), ctx)


def row_decision(row: dict, router: dict) -> Optional[dict]:
    """``{'size_for': {...}}`` for a routed shadow row (layer-6 evidence), or None when the row is unrouted / errored."""
    arm = sizing_arm(router)
    if arm is None:
        return None
    side = (router.get("side") or "").lower() or None
    d = asz.size_for(arm, cell_for(row), asz.SizingContext(price=_price(row, side), p_win=_p_win(row, side)))
    out = d.as_row_fields()
    out["size_for"]["context"] = "row_level_empty_book"
    if arm != (router.get("arm") or router.get("branch")):
        out["size_for"]["router_arm"] = router.get("arm") or router.get("branch")
    return out
