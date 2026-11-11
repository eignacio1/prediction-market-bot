"""W110.3 Part B -- the router's decision for a pre-game shadow row. Logging only: no order path, no sizing.

Applies to rows the shadow runner writes (bands T1/T2/T3, horizon known). Does not apply to in-play rows (none are
written here). FADE/MOMENTUM stay pending evidence (no skill record / 1h move in a shadow row), so the branch set a
cell can reach is RIDE, POT_OF_GOLD or NO_BET; the reason says why.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from prediction_market_bot.decision_trees import ride
from prediction_market_bot.decision_trees.coverage import DEPTH
from prediction_market_bot.decision_trees.router import Evidence, Situation, route


def tier_for_hours(h: Optional[float]) -> Optional[str]:
    """Same buckets as calib.tier (>=24 T>24h, >=6 T6-24h, >=2 T2-6h, else T0-2h)."""
    if h is None or h <= 0:
        return None
    return "T>24h" if h >= 24 else "T6-24h" if h >= 6 else "T2-6h" if h >= 2 else "T0-2h"


@lru_cache(maxsize=1)
def _ev() -> Evidence:
    return Evidence(ride=ride.load())


def router_fields(row: dict, series: str) -> dict:
    """{'router': {...}} for a shadow row; never raises (a failure is recorded as branch ERROR)."""
    try:
        s = Situation(sport=row.get("sport", ""), family=series, ticker=row["market_ticker"], event=row["event_ticker"],
                      tier=tier_for_hours(row.get("horizon_hours_to_start")), yes_bid=row["yes_bid"],
                      yes_ask=row["yes_ask"], half_spread=row.get("half_spread"), model_p=row.get("p_yes"))
        r = route(s, _ev())
        return {"router": {"branch": r.tree, "side": r.side, "depth": DEPTH.get(row.get("band"), "stripped"),
                           "tier": s.tier, "reason": ";".join(map(str, r.reasons)), "orders": "off"}}
    except Exception as e:  # noqa: BLE001
        return {"router": {"branch": "ERROR", "side": None, "depth": None, "tier": None,
                           "reason": type(e).__name__, "orders": "off"}}
