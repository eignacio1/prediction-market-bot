"""W90.2 router: sends one market situation to FADE, RIDE, POT_OF_GOLD, MOMENTUM_FOLLOW, MOMENTUM_FADE or NO_BET.

Pure function of (situation, evidence). A tree gets traffic only when measured evidence supplied by the caller
says it should: no skill record -> no FADE; no ride-table cell with a positive net lower bound -> no RIDE; no
transition table -> no MOMENTUM; no HELD_OUT/FORWARD_PASSED longshot cell -> no POT_OF_GOLD (W106.1; precedence
pre-registered in 12_EXPLORATORY/pot_of_gold/ROUTER_PRECEDENCE.md). Everything else is NO_BET with reason codes. Nothing here sizes, places or logs.

When it applies: a pre-game, two-sided, priced market whose family has an evidence record. When it doesn't: in-play
markets, one-sided books, date-only tickers on game day (NFL D0) -- those are NO_BET by construction.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional, Protocol, Sequence

from prediction_market_bot.decision_trees import longshot, ride
from prediction_market_bot.decision_trees.ride import RideCell, RideTable  # noqa: F401  (re-exported)
from prediction_market_bot.quant.money import net_edge

FADE, RIDE = "FADE", "RIDE"
MOMENTUM_FOLLOW, MOMENTUM_FADE = "MOMENTUM_FOLLOW", "MOMENTUM_FADE"
POT_OF_GOLD = "POT_OF_GOLD"
NO_BET = "NO_BET"
TREES = (FADE, RIDE, POT_OF_GOLD, MOMENTUM_FOLLOW, MOMENTUM_FADE, NO_BET)

PRICE_MIN, PRICE_MAX = 0.01, 0.99
TIGHT_HALF_SPREAD = 0.01  # W89.2 book-class definition: tight = half-spread <= 1c


@dataclass(frozen=True)
class Situation:
    sport: str
    family: str  # series ticker, e.g. KXMLBHIT
    ticker: str
    event: str
    tier: Optional[str]  # time-to-start tier (W89.2 calib.tier); None = started / unparseable
    yes_bid: Optional[float]
    yes_ask: Optional[float]
    half_spread: Optional[float] = None
    model_p: Optional[float] = None
    move_1h: Optional[float] = None  # 1h change in yes mid
    t3: Optional[str] = None  # ADR-0014 overlay: CONFIRM | FADE | NEUTRAL
    market_type: Optional[str] = None  # W111.3: leaf-map coordinates (with band and prev_mid)
    band: Optional[str] = None
    prev_mid: Optional[float] = None  # the same ticker's previous logged mid, for the leaf's move bin

    @property
    def mid(self) -> Optional[float]:
        if self.yes_bid is None or self.yes_ask is None:
            return None
        return (self.yes_bid + self.yes_ask) / 2.0


@dataclass(frozen=True)
class Skill:
    """Model-vs-market evidence for a (sport, family). weight = clip(1 - Bm/Bk, 0, 1); ci_lo = lower bound of
    (market Brier - model Brier); n = games scored."""
    weight: float
    ci_lo: Optional[float]
    n: int


@dataclass(frozen=True)
class MomentumCell:
    tree: str  # MOMENTUM_FOLLOW | MOMENTUM_FADE
    min_move: float
    net_lo: float


@dataclass
class Evidence:
    skill: Mapping[tuple, Skill] = field(default_factory=dict)  # (sport, family) -> Skill
    ride: Optional[RideTable] = None
    momentum: Sequence[MomentumCell] = ()
    longshot: Optional[longshot.Table] = None  # None -> the shipped longshot_cells.toml (all IN_SAMPLE today)
    leaf_map: Optional[object] = None  # W111.3: a leaf_map.LeafMap; when set and the situation has a band, it decides


@dataclass(frozen=True)
class Route:
    tree: str
    side: Optional[str]
    reasons: tuple
    agreed: bool = False
    cell: Optional[object] = None  # the measured cell behind a POT_OF_GOLD route (carries its status for the order gate)
    leaf: Optional[object] = None  # W111.3: the leaf_map.LeafDecision behind the route (leaf_id, verbatim arm, held-out stats)


def book_classes(s: Situation) -> tuple:
    """Book classes a situation belongs to, most specific first; the 'all' view always applies."""
    hs = s.half_spread if s.half_spread is not None else (s.yes_ask - s.yes_bid) / 2.0
    return ("tight" if hs <= TIGHT_HALF_SPREAD else "wide", "all")


def _disqualify(s: Situation) -> Optional[str]:
    if s.yes_bid is None or s.yes_ask is None or s.yes_bid <= 0 or s.yes_ask >= 1 or s.yes_ask < s.yes_bid:
        return "no_two_sided_book"
    if s.tier is None:
        return "started_or_unparseable"
    if s.tier == "D0":
        return "date_only_game_day"
    m = s.mid
    if m < PRICE_MIN or m > PRICE_MAX:
        return "price_extreme"
    return None


def _fade(s: Situation, ev: Evidence):
    sk = ev.skill.get((s.sport, s.family))
    if sk is None or s.model_p is None:
        return None, "fade:no_skill_record_or_model_p"
    if not (sk.weight > 0 and sk.ci_lo is not None and sk.ci_lo > 0):
        return None, "fade:no_measured_skill"
    e = net_edge(s.model_p, s.yes_bid, s.yes_ask)
    if e["edge"] <= 0:
        return None, "fade:no_net_edge"
    return e["side"], "fade:measured_skill_and_edge"


def _ride(s: Situation, ev: Evidence):
    d = ride.decide(s.family, s.tier, s.mid, s.half_spread, ev.ride, book_classes(s))
    return d.side, d.reason


_DEFAULT_LONGSHOT: Optional[longshot.Table] = None


def _pot(s: Situation, ev: Evidence):
    global _DEFAULT_LONGSHOT
    t = ev.longshot
    if t is None:
        if _DEFAULT_LONGSHOT is None:
            _DEFAULT_LONGSHOT = longshot.load()
        t = _DEFAULT_LONGSHOT
    hs = s.half_spread if s.half_spread is not None else (s.yes_ask - s.yes_bid) / 2.0
    d = longshot.decide(s.family, s.tier, s.mid, hs, t)
    if d.action == longshot.NO_BET:
        return None, f"longshot:{d.reason}", d.cell
    return d.side, f"longshot:{d.action}", d.cell


def _momentum(s: Situation, ev: Evidence):
    if not ev.momentum or s.move_1h is None:
        return None, None, "momentum:no_table"
    for c in ev.momentum:
        if c.net_lo > 0 and abs(s.move_1h) >= c.min_move:
            up = s.move_1h > 0
            follow = c.tree == MOMENTUM_FOLLOW
            side = "yes" if up == follow else "no"
            return c.tree, side, "momentum:measured_transition"
    return None, None, "momentum:no_cell"


def _route_leaf(s: Situation, ev: Evidence) -> Route:
    """The per-leaf arm map decides (W111.3). Only the book and price-extreme checks apply: the band comes from the
    row, so the date-only (D0) ticker bound does not; the arm is read from the map's fit window, so the order gate's
    IN_SAMPLE status does not block the LOGGED arm (orders stay off in the caller). The legacy router result is kept
    in the reasons when it disagrees."""
    if s.yes_bid is None or s.yes_ask is None or s.yes_bid <= 0 or s.yes_ask >= 1 or s.yes_ask < s.yes_bid:
        return Route(NO_BET, None, ("no_two_sided_book",))
    if s.mid < PRICE_MIN or s.mid > PRICE_MAX:
        return Route(NO_BET, None, ("price_extreme",))
    from prediction_market_bot.decision_trees import leaf_map as lm

    row = lm.LeafMap.row_for(s.sport, s.market_type or "", s.band, s.mid, s.prev_mid)
    d = ev.leaf_map.decide(row, s.model_p)
    if d.arm == "NO_BET":
        return Route(NO_BET, None, (d.reason,), leaf=d)
    return Route(lm.ARM_TREE[d.arm], d.side, (d.reason,), leaf=d)


def route(s: Situation, ev: Evidence) -> Route:
    if ev.leaf_map is not None and s.band:
        return _route_leaf(s, ev)
    dq = _disqualify(s)
    if dq:
        return Route(NO_BET, None, (dq,))
    fside, fwhy = _fade(s, ev)
    rside, rwhy = _ride(s, ev)
    pside, pwhy, pcell = _pot(s, ev)
    if fside and s.t3 == "FADE":  # ADR-0014 overlay: price moved against the model -> HOLD
        fside, fwhy = None, "t3_hold"
    # ROUTER_PRECEDENCE.md: opposite sides -> NO_BET; same side -> named RIDE, then POT_OF_GOLD, then FADE.
    claims = [(t, sd, why) for t, sd, why in ((RIDE, rside, rwhy), (POT_OF_GOLD, pside, pwhy), (FADE, fside, fwhy)) if sd]
    if len({c[1] for c in claims}) > 1:
        return Route(NO_BET, None, ("conflict", fwhy, rwhy, pwhy))
    if claims:
        tree, side, why = claims[0]
        others = tuple(f"{t.lower()}_agrees" for t, _, _ in claims[1:])
        return Route(tree, side, (why,) + others, agreed=bool(others), cell=pcell if tree == POT_OF_GOLD else None)
    mtree, mside, mwhy = _momentum(s, ev)
    if mtree:
        return Route(mtree, mside, (mwhy,))
    return Route(NO_BET, None, ("no_tree_claims", fwhy, rwhy, pwhy, mwhy))
