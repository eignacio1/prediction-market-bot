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
# W116.1: PM_LEAF_MAP_VERSION picks the map the router reads. "v1" (default) = the frozen W110.5 per-leaf map above;
# "v2" = leaf_maps/leaf_map_v2.json (pooled posterior + e-process, W115.1). Anything else is refused, not guessed.
MAP_VERSIONS = {"v1": DEFAULT_MAP,
                "v2": os.path.join(os.path.dirname(os.path.abspath(__file__)), "leaf_maps", "leaf_map_v2.json"),
                # W119.1: v2 with the NHL leaves re-run on the 2026-27 shadow rows (consensus prior). Opt-in only; default stays v1.
                "nhl_v2": os.path.join(os.path.dirname(os.path.abspath(__file__)), "leaf_maps", "nhl_v2.json"),
                # W121.2: NBA player-prop market-state leaves + the 4 PREREG'd player splits (EXP-NBAPROPS-001). Candidate only.
                "nba_props": os.path.join(os.path.dirname(os.path.abspath(__file__)), "leaf_maps", "nba_props_v2.json")}


def map_path(version: Optional[str] = None) -> str:
    v = (version if version is not None else os.environ.get("PM_LEAF_MAP_VERSION", "v1")).strip().lower() or "v1"
    v = v.split("+", 1)[0] or "v1"   # W119.2: "+nba_depth" is a feature suffix (depth_enabled), not a different map file
    if v not in MAP_VERSIONS:
        raise ValueError(f"PM_LEAF_MAP_VERSION={v!r}: expected one of {sorted(MAP_VERSIONS)}")
    return MAP_VERSIONS[v]


def depth_enabled(version: Optional[str] = None) -> bool:
    """W119.2: the NBA depth splits (leaf_maps/nba_depth_v2.json) apply only when PM_LEAF_MAP_VERSION carries ``+nba_depth``
    (e.g. ``v1+nba_depth``). Default off: v1 output is unchanged and nothing is flipped by this code."""
    v = (version if version is not None else os.environ.get("PM_LEAF_MAP_VERSION", "v1")).strip().lower()
    return "nba_depth" in v.split("+")[1:]


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
    posterior: Optional[dict] = None  # v2: arm -> [mean net, sd, P(net>0)]
    source: Optional[dict] = None  # v2: arm -> [path node with most evidence, log path e-value]


class LeafMap:
    def __init__(self, doc: dict):
        self.doc = doc
        self.leaves = doc["leaves"]

    @classmethod
    def load(cls, path: str = DEFAULT_MAP) -> "LeafMap":
        with open(path) as fh:
            return cls(json.load(fh))

    @staticmethod
    def row_for(sport: str, market_type: str, band: str, mid: float, prev_mid: Optional[float],
                ticker: Optional[str] = None, yes_bid: Optional[float] = None, yes_ask: Optional[float] = None) -> dict:
        # W116.3 (GG-1939): the MODEL_FADE arm prices both sides with retro_route.side_net, which needs the ticker (fee
        # series) and the book; without them every MODEL_FADE leaf raised KeyError('market_ticker') -> router ERROR.
        r = {"sport": sport, "market_type": market_type, "band": band, "mid": mid,
             "market_ticker": ticker, "yes_bid": yes_bid, "yes_ask": yes_ask}
        r["move"] = None if prev_mid is None else mid - prev_mid
        return r

    def leaf_id(self, r: dict) -> str:
        return "|".join(str(x) for x in rr.leaf_key(r))

    def decide(self, r: dict, p_yes: Optional[float] = None, arm_override: Optional[str] = None) -> LeafDecision:
        """arm_override (W112.1): a KEPT filter split's arm replaces the market-state leaf's arm; the leaf's own thin /
        unknown checks still apply, and the arm's side rules (momentum needs a move, model fade needs model p) are unchanged."""
        lid = self.leaf_id(r)
        rec = self.leaves.get(lid)
        if rec is None:
            return LeafDecision(lid, "NO_BET", None, "leaf_not_in_map", False, False)
        ho = rec.get("test")
        base = dict(thin=rec.get("thin", False), known=True, fit=rec.get("fit"), heldout=ho, bh=rec.get("bh", False),
                    posterior=rec.get("posterior"), source=rec.get("source"))
        if base["thin"]:
            return LeafDecision(lid, "NO_BET", None, "leaf_thin", **base)
        arm = arm_override or rec["arm"]
        if arm == "NO_BET":
            why = "leaf_no_arm_earned_v2" if self.doc.get("version") == "v2" else "leaf_no_arm_positive_in_fit"
            return LeafDecision(lid, "NO_BET", None, why, **base)
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
            if not r.get("market_ticker") or r.get("yes_bid") is None or r.get("yes_ask") is None:
                return LeafDecision(lid, "NO_BET", None, "model_fade_needs_ticker_and_book", **base)
            ey = rr.side_net({**r, "y": float(p_yes)}, "YES")
            en = rr.side_net({**r, "y": float(p_yes)}, "NO")
            if max(ey, en) <= 0:
                return LeafDecision(lid, "NO_BET", None, "model_fade_no_net_edge_now", **base)
            side = "yes" if ey >= en else "no"
        else:
            return LeafDecision(lid, "NO_BET", None, f"unknown_arm:{arm}", **base)
        return LeafDecision(lid, arm, side, f"leaf_arm:{arm}", **base)


DEFAULT_SPLITS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "filter_splits.json")


class FilterSplits:
    """W112.1 Part B -- the tested filter splits (filter_splits.json, built by scripts/build_filter_splits_w112.py).

    A leaf = market-state leaf x filter condition. A split is KEPT (may change the logged arm) only where its leaf was tested
    per leaf: not thin, arm != NO_BET, held-out games >= 10 and held-out net after fee > 0. An untested filter value, or a tested
    one that failed that rule, is logged and never split on. Several kept splits that disagree on the arm change nothing
    (``split_conflict``): the market-state leaf's arm stands."""

    def __init__(self, doc: dict):
        self.doc = doc
        self.index = {(s["sport"], s["series"], s["filter"], s["leaf"]): s for s in doc["splits"] if s["series"]}
        self.index_any = {(s["sport"], s["filter"], s["leaf"]): s for s in doc["splits"] if not s["series"]}

    @classmethod
    def load(cls, path: str = DEFAULT_SPLITS) -> "FilterSplits":
        with open(path) as fh:
            return cls(json.load(fh))

    def lookup(self, sport: str, series: str, filters: dict) -> dict:
        """-> {'kept': [...], 'logged_only': [...], 'untested': [...], 'arm': arm|None, 'conflict': bool}; entries are 'filter=leaf'."""
        kept, logged, untested = [], [], []
        for name in sorted(filters):
            leaf = filters[name]
            if leaf in (None, False, "unknown"):
                continue
            s = self.index.get((sport, series, name, leaf)) or self.index_any.get((sport, name, leaf))
            tag = f"{name}={leaf}"
            if s is None:
                untested.append(tag)
            elif s["kept"]:
                kept.append((tag, s["arm"]))
            else:
                logged.append(f"{tag}[{s['why']}]")
        arms = {a for _, a in kept}
        return {"kept": [f"{t}->{a}" for t, a in kept], "logged_only": logged, "untested": untested,
                "arm": next(iter(arms)) if len(arms) == 1 else None, "conflict": len(arms) > 1}


DEPTH_SPLITS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leaf_maps", "nba_depth_v2.json")


class DepthSplits:
    """W119.2: the 12 KEPT NBA depth splits (nba_depth_v2.json, EXP-NBADEPTH-001), keyed (market_type, band, filter, leaf).
    Same kept rule and conflict rule as FilterSplits; only KEPT entries are indexed, every other depth value is logged."""

    def __init__(self, doc: dict):
        self.doc = doc
        self.kept = {}
        self.tested = set()
        for s in doc["splits"]:
            k = ("NBA_" + s["series"], s["band"], s["filter"], s["leaf"])
            self.tested.add(k)
            if s["kept"]:
                self.kept.setdefault(k, set()).add(s["arm"])

    @classmethod
    def load(cls, path: str = DEPTH_SPLITS) -> "DepthSplits":
        with open(path) as fh:
            return cls(json.load(fh))

    def lookup(self, market_type: str, band: str, depth: dict) -> dict:
        kept, logged = [], []
        for name in sorted(depth):
            leaf = depth[name]
            if leaf in (None, False, "unknown"):
                continue
            k = (market_type, band, name, leaf)
            arms = self.kept.get(k)
            if arms and len(arms) == 1:
                kept.append((f"{name}={leaf}", next(iter(arms))))
            elif k in self.tested:
                logged.append(f"{name}={leaf}")
        arms = {a for _, a in kept}
        return {"kept": [f"{t}->{a}" for t, a in kept], "logged_only": logged, "untested": [],
                "arm": next(iter(arms)) if len(arms) == 1 else None, "conflict": len(arms) > 1}


class PropSplits:
    """W121.2: the NBA player-prop splits (nba_props_v2.json, EXP-NBAPROPS-001), keyed (market-state leaf id, split, split leaf).
    Only KEPT entries are indexed; `earned` (BH-significant) is reported beside the arm. Same conflict rule as DepthSplits:
    kept splits that disagree change nothing."""

    def __init__(self, doc: dict):
        self.kept, self.tested = {}, set()
        for s in doc["splits"]:
            k = (s["leaf"], s["split"], s["split_leaf"])
            self.tested.add(k)
            if s["kept"]:
                self.kept.setdefault(k, {})[s["arm"]] = bool(s.get("earned"))

    @classmethod
    def load(cls, path: Optional[str] = None) -> "PropSplits":
        with open(path or MAP_VERSIONS["nba_props"]) as fh:
            return cls(json.load(fh))

    def lookup(self, leaf_id: str, props: dict) -> dict:
        kept, logged = [], []
        for name in sorted(props):
            leaf = props[name]
            if leaf in (None, False, "unknown"):
                continue
            k = (leaf_id, name, leaf)
            arms = self.kept.get(k)
            if arms and len(arms) == 1:
                arm, earned = next(iter(arms.items()))
                kept.append((f"{name}={leaf}", arm, earned))
            elif k in self.tested:
                logged.append(f"{name}={leaf}")
        arms = {a for _, a, _ in kept}
        return {"kept": [f"{t}->{a}" for t, a, _ in kept], "earned": [t for t, _, e in kept if e], "logged_only": logged,
                "arm": next(iter(arms)) if len(arms) == 1 else None, "conflict": len(arms) > 1}


@lru_cache(maxsize=1)
def default_prop_splits() -> PropSplits:
    return PropSplits.load()


@lru_cache(maxsize=1)
def default_depth_splits() -> DepthSplits:
    return DepthSplits.load()


@lru_cache(maxsize=1)
def default_splits() -> FilterSplits:
    return FilterSplits.load()


@lru_cache(maxsize=None)
def _load_version(path: str) -> LeafMap:
    return LeafMap.load(path)


def default_map() -> LeafMap:
    """The map PM_LEAF_MAP_VERSION names (default v1), cached per file."""
    return _load_version(map_path())
