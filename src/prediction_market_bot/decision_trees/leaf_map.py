"""W111.3 Part A -- the W110.5 per-leaf arm map, read by the router. Logging only: no order path, no sizing.

A leaf is (sport, market_type, band, favoured-side price bin, last move). The map fixes one arm per leaf on the FIT
window only (earliest 70% of games); held-out status is carried for the log and never chooses an arm. Thin leaves
(fit rows < 60 or fit games < 20) route to NO_BET and say so.
When it applies: pre-game shadow rows of cells the map covers. When it doesn't: a leaf the map has never seen is
NO_BET ("leaf_not_in_map"), not a guess; in-play bands are not in the map.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from prediction_market_bot.quant import retro_route as rr

DEFAULT_MAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leaf_map.json")
ARM_SOURCE = "leaf_map_w110_5_fit_window"
# map arm -> router tree. MODEL_FADE (model price vs market) and FADE (against the favourite) both land in the FADE tree.
ARM_TREE = {"RIDE": "RIDE", "FADE": "FADE", "MODEL_FADE": "FADE", "MOMENTUM": "MOMENTUM_FOLLOW",
            "POT_OF_GOLD": "POT_OF_GOLD"}


@dataclass(frozen=True)
class LeafDecision:
    leaf_id: str
    arm: str  # map arm, or NO_BET
    side: Optional[str]  # "yes" | "no" | None
    reason: str
    thin: bool
    known: bool
    fit: Optional[dict] = None
    heldout: Optional[dict] = None
    bh: bool = False


class LeafMap:
    def __init__(self, doc: dict):
        self.doc = doc
        self.leaves = doc["leaves"]

    @classmethod
    def load(cls, path: str = DEFAULT_MAP) -> "LeafMap":
        with open(path) as fh:
            return cls(json.load(fh))

    @staticmethod
    def row_for(sport: str, market_type: str, band: str, mid: float, prev_mid: Optional[float]) -> dict:
        r = {"sport": sport, "market_type": market_type, "band": band, "mid": mid}
        r["move"] = None if prev_mid is None else mid - prev_mid
        return r

    def leaf_id(self, r: dict) -> str:
        return "|".join(str(x) for x in rr.leaf_key(r))

    def decide(self, r: dict, p_yes: Optional[float] = None) -> LeafDecision:
        lid = self.leaf_id(r)
        rec = self.leaves.get(lid)
        if rec is None:
            return LeafDecision(lid, "NO_BET", None, "leaf_not_in_map", False, False)
        ho = rec.get("test")
        base = dict(thin=rec["thin"], known=True, fit=rec["fit"], heldout=ho, bh=rec["bh"])
        if rec["thin"]:
            return LeafDecision(lid, "NO_BET", None, "leaf_thin", **base)
        arm = rec["arm"]
        if arm == "NO_BET":
            return LeafDecision(lid, "NO_BET", None, "leaf_no_arm_positive_in_fit", **base)
        fs = rr.fav_side(r).lower()
        other = "no" if fs == "yes" else "yes"
        if arm == "RIDE":
            side = fs
        elif arm == "FADE":
            side = other
        elif arm == "MOMENTUM":
            m = r.get("move")
            if m is None or abs(m) < rr.FLAT_BAND:
                return LeafDecision(lid, "NO_BET", None, "momentum_needs_a_move", **base)
            side = "yes" if m > 0 else "no"
        elif arm == "MODEL_FADE":
            if p_yes is None:
                return LeafDecision(lid, "NO_BET", None, "model_fade_needs_model_p", **base)
            ey = rr.side_net({**r, "y": float(p_yes)}, "YES")
            en = rr.side_net({**r, "y": float(p_yes)}, "NO")
            if max(ey, en) <= 0:
                return LeafDecision(lid, "NO_BET", None, "model_fade_no_net_edge_now", **base)
            side = "yes" if ey >= en else "no"
        else:
            return LeafDecision(lid, "NO_BET", None, f"unknown_arm:{arm}", **base)
        return LeafDecision(lid, arm, side, f"leaf_arm:{arm}", **base)


@lru_cache(maxsize=1)
def default_map() -> LeafMap:
    return LeafMap.load()
