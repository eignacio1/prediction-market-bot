"""W90.2 router: sends one market situation to FADE, RIDE, MOMENTUM_FOLLOW, MOMENTUM_FADE or NO_BET.

Pure function of (situation, evidence). A tree gets traffic only when measured evidence supplied by the caller
says it should: no skill record -> no FADE; no ride-table cell with a positive net lower bound -> no RIDE; no
transition table -> no MOMENTUM. Everything else is NO_BET with reason codes. Nothing here sizes, places or logs.

When it applies: a pre-game, two-sided, priced market whose family has an evidence record. When it doesn't: in-play
markets, one-sided books, date-only tickers on game day (NFL D0) -- those are NO_BET by construction.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional, Protocol, Sequence

from prediction_market_bot.quant.money import net_edge

FADE, RIDE = "FADE", "RIDE"
MOMENTUM_FOLLOW, MOMENTUM_FADE = "MOMENTUM_FOLLOW", "MOMENTUM_FADE"
NO_BET = "NO_BET"
TREES = (FADE, RIDE, MOMENTUM_FOLLOW, MOMENTUM_FADE, NO_BET)

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
class RideCell:
    family: str
    tier: str
    bucket: str  # e.g. "20-25c"
    book: str  # "all" | "tight" | "wide"
    side: str  # "yes" | "no"
    net_lo: float  # net-of-fee lower bound per contract


class RideTable(Protocol):
    def lookup(self, family: str, tier: str, bucket: str, book: str) -> Optional[RideCell]: ...


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


@dataclass(frozen=True)
class Route:
    tree: str
    side: Optional[str]
    reasons: tuple
    agreed: bool = False


def _bucket(p: float) -> str:
    edges = [0.0, 0.01, 0.05] + [x / 100 for x in range(10, 100, 5)] + [0.99, 1.0001]
    for i in range(len(edges) - 1):
        if edges[i] <= p < edges[i + 1]:
            return f"{int(round(edges[i] * 100))}-{min(int(round(edges[i + 1] * 100)), 100)}c"
    return "99-100c"


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
    if ev.ride is None:
        return None, "ride:no_table"
    b = _bucket(s.mid)
    for book in book_classes(s):
        c = ev.ride.lookup(s.family, s.tier, b, book)
        if c is not None and c.net_lo > 0:
            return c.side, f"ride:cell_{s.tier}_{b}_{book}"
    return None, "ride:no_cell"


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


def route(s: Situation, ev: Evidence) -> Route:
    dq = _disqualify(s)
    if dq:
        return Route(NO_BET, None, (dq,))
    fside, fwhy = _fade(s, ev)
    rside, rwhy = _ride(s, ev)
    if fside and s.t3 == "FADE":  # ADR-0014 overlay: price moved against the model -> HOLD
        fside, fwhy = None, "t3_hold"
    if fside and rside:
        if fside != rside:
            return Route(NO_BET, None, ("conflict", fwhy, rwhy))
        return Route(RIDE, rside, (rwhy, "fade_agrees"), agreed=True)
    if rside:
        return Route(RIDE, rside, (rwhy,))
    if fside:
        return Route(FADE, fside, (fwhy,))
    mtree, mside, mwhy = _momentum(s, ev)
    if mtree:
        return Route(mtree, mside, (mwhy,))
    return Route(NO_BET, None, ("no_tree_claims", fwhy, rwhy, mwhy))
