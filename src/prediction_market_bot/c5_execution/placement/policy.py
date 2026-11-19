"""W116.2 / B-095 Part C1: the per-arm placement policy, behind ARM_PLACEMENT_POLICY (default OFF).

OFF (the default, and any value other than exactly "on"): every arm order is placed as today - rest at our side's touch,
cancelled after 60 s (ADR-0072). Nothing in the order path changes.

ON: a FROZEN table (JSON, written from placement.model.option_table by a reviewed commit, never by the running bot - Hard
Rule 4) names one option per (arm) or (arm, leaf) cell: rest_touch / rest_inside / cross / no_place. A cell the table does
not name, or names with a choice the model did not mark supported, stays rest_touch. A missing or unreadable table is
rest_touch everywhere ("no_table"). Leaf beats arm. Turning it ON is the operator's decision (ADR-0072 addendum proposal,
W116.2); this module never turns itself on.

Applies when: the order is a router-arm demo order priced from the ADR-0072 book read (yes_bid / yes_ask). The price this
returns is in the YES frame, the value submit_order takes (it buys YES at it, or NO at 1 - it).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

SWITCH_ENV = "ARM_PLACEMENT_POLICY"
TABLE_ENV = "ARM_PLACEMENT_TABLE"
DEFAULT_TABLE = Path(__file__).resolve().parents[4] / "config" / "placement_policy.json"
OPTIONS = ("rest_touch", "rest_inside", "cross", "no_place")
TICK = 0.01


@dataclass(frozen=True)
class Placement:
    option: str           # one of OPTIONS
    price_yes: Optional[float]  # YES-frame limit for submit_order; None for no_place
    reason: str           # why this option: "switch_off", "no_table", "table:<cell>", "default_rest_touch", "inside_not_room"


def is_on(value: Optional[str] = None) -> bool:
    v = os.environ.get(SWITCH_ENV, "") if value is None else value
    return str(v).strip().lower() == "on"


def load_table(path: Optional[Path] = None) -> Optional[dict]:
    """{"cells": {"<arm>" | "<arm>|<leaf>": {"best": option, "supported": bool}}} or None."""
    p = Path(path or os.environ.get(TABLE_ENV) or DEFAULT_TABLE)
    try:
        t = json.loads(p.read_text())
    except (OSError, ValueError):
        return None
    return t if isinstance(t, dict) and isinstance(t.get("cells"), dict) else None


def in_share(key: str, share: float) -> bool:
    """Deterministic, outcome-blind split: True for ``share`` of keys (sha256 of the key). The same key always lands the same way."""
    return int(hashlib.sha256(str(key).encode()).hexdigest()[:8], 16) / 0x100000000 < share


def choice(arm: str, leaf: Optional[str], table: Optional[dict], order_key: Optional[str] = None) -> tuple:
    """(option, reason) from the table; rest_touch unless a supported cell names something else.
    A cell with ``share`` < 1 (W119.3 forward test) names its option for that share of orders by hash of ``order_key``; the rest
    stay rest_touch as the concurrent control ("control:<cell>"). Without an order_key a shared cell is NOT applied."""
    if table is None:
        return "rest_touch", "no_table"
    for key in ((f"{arm}|{leaf}",) if leaf else ()) + (str(arm),):
        c = table["cells"].get(key)
        if isinstance(c, dict) and c.get("supported") and c.get("best") in OPTIONS:
            share = c.get("share")
            if share is not None and float(share) < 1.0:
                if order_key is None or not in_share(order_key, float(share)):
                    return "rest_touch", f"control:{key}"
            return c["best"], f"table:{key}"
    return "rest_touch", "default_rest_touch"


def price_for(option: str, side: str, yes_bid: float, yes_ask: float) -> Optional[float]:
    """YES-frame limit for each option. Touch: our side's best bid (YES -> yes_bid; NO -> 1 - yes_ask, passed as yes_ask).
    Inside (W119.3): one tick better than our touch, or the mid when the spread is 2 ticks or more, snapped to the tick toward
    our own touch so it never crosses (YES buys round down, NO buys round up); None when the spread is under 2 ticks (no
    price strictly inside). Cross: the far touch."""
    if option == "no_place":
        return None
    if option == "rest_touch":
        return yes_bid if side == "yes" else yes_ask
    if option == "cross":
        return yes_ask if side == "yes" else yes_bid
    if option == "rest_inside":
        ticks = round((yes_ask - yes_bid) / TICK)
        if ticks < 2:
            return None
        half = ticks / 2.0
        # A NO buy is at 1 - p, so its own touch is the ask: its mid snaps UP (toward the ask); a YES buy snaps DOWN (toward the bid).
        p = round(yes_bid + (math.floor(half) if side == "yes" else math.ceil(half)) * TICK, 2)
        return p if yes_bid < p < yes_ask else None
    raise ValueError(option)


def place(arm: str, leaf: Optional[str], side: str, yes_bid: float, yes_ask: float, switch_value: Optional[str] = None,
          table: Optional[dict] = None, table_path: Optional[Path] = None, order_key: Optional[str] = None) -> Placement:
    """The placement for one order. OFF -> rest_touch at the touch, exactly today's price."""
    if not is_on(switch_value):
        return Placement("rest_touch", price_for("rest_touch", side, yes_bid, yes_ask), "switch_off")
    opt, why = choice(arm, leaf, table if table is not None else load_table(table_path), order_key)
    px = price_for(opt, side, yes_bid, yes_ask)
    if opt == "rest_inside" and px is None:  # a one-tick spread has no inside: fall back to the touch
        return Placement("rest_touch", price_for("rest_touch", side, yes_bid, yes_ask), "inside_not_room")
    return Placement(opt, px, why)


def table_from_options(options: dict) -> dict:
    """The frozen table's cells from placement.model.option_table output (``by`` = arm or arm|leaf). Only cells whose best
    option is supported are written; an unsupported cell is left out and stays rest_touch."""
    cells = {}
    for cell, row in options.items():
        best = row.get("best")
        if best in OPTIONS and (best == "no_place" or (row.get(best) or {}).get("supported")):
            cells[cell] = {"best": best, "supported": True, "best_net": row.get("best_net")}
    return {"cells": cells}


MIN_GAMES = 20   # W117.1: games per cell before a non-default option can be written (clustered, so games - not orders - are the n)


def table_from_clustered(clustered: dict, min_games: int = MIN_GAMES) -> dict:
    """W117.1 frozen-table rule, on model.option_net_clustered output (``by`` = arm). A cell names ``cross`` only when the
    game-clustered 95% interval of (cross - rest_touch) per order, on orders with a real logged/backfilled spread, lies wholly
    above zero AND the cell has >= ``min_games`` games. Anything else is left out and stays rest_touch (today's rule)."""
    cells = {}
    for cell, row in clustered.items():
        d = row.get("cross_minus_rest") or {}
        lo = d.get("ci", [None, None])[0]
        if lo is not None and lo > 0 and (d.get("n_games") or 0) >= min_games:
            cells[cell] = {"best": "cross", "supported": True, "best_net": (row.get("cross") or {}).get("net"),
                           "n_games": d["n_games"], "n_orders": d["n"], "diff_ci": d["ci"]}
    return {"cells": cells}
