"""W91.2 ride tree: decide whether to take the market's side, from a table of measured cells.

Pure function of (family, time tier, price, book state, kind) and a table. RIDE-YES / RIDE-NO only when a cell for
that exact situation has status HELD_OUT or FORWARD_PASSED and a net-of-fee lower bound > 0; every other status
(IN_SAMPLE, FAILED, UNTESTED), a missing cell, or a book wider than the cell was measured on returns NONE. No numbers
live here: they come from ride_cells.toml. Two kinds share the table: CALIBRATION (the whole market is biased at this
price) and LADDER (a strike quoted off its own ladder; the ride takes the ladder's side).

When it applies: a pre-game, two-sided, priced market. When it doesn't: anything not in the table. Nothing here sizes,
places or logs, and nothing runs it.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, Optional, Protocol

try:
    import tomllib  # py3.11+
except ImportError:  # the box is 3.9
    import tomli as tomllib  # type: ignore

RIDE_YES, RIDE_NO, NONE = "RIDE-YES", "RIDE-NO", "NONE"
CALIBRATION, LADDER = "CALIBRATION", "LADDER"
IN_SAMPLE, HELD_OUT, FORWARD_PASSED, FAILED, UNTESTED = "IN_SAMPLE", "HELD_OUT", "FORWARD_PASSED", "FAILED", "UNTESTED"
RIDEABLE = (HELD_OUT, FORWARD_PASSED)
DEFAULT_TABLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ride_cells.toml")


@dataclass(frozen=True)
class RideCell:
    family: str
    tier: str
    bucket: str  # e.g. "20-25c"; LADDER cells use the gap bucket from their results file
    book: str  # "all" | "tight" | "wide"
    side: str  # "yes" | "no"
    net_lo: float  # net-of-fee lower bound per contract
    kind: str = CALIBRATION
    status: str = HELD_OUT
    net_mean: Optional[float] = None
    net_hi: Optional[float] = None
    max_half_spread: Optional[float] = None
    n: int = 0


class RideTable(Protocol):
    def lookup(self, family: str, tier: str, bucket: str, book: str, kind: Optional[str] = None) -> Optional[RideCell]: ...


@dataclass(frozen=True)
class RideDecision:
    action: str  # RIDE-YES | RIDE-NO | NONE
    side: Optional[str]
    net_mean: Optional[float]
    net_lo: Optional[float]
    net_hi: Optional[float]
    reason: str
    cell: Optional[RideCell] = None


class Table:
    """Cells keyed on (kind, family, tier, bucket, book). Built from a list, or from ride_cells.toml via load()."""

    def __init__(self, cells: Iterable[RideCell] = ()):
        self.c = {(x.kind, x.family, x.tier, x.bucket, x.book): x for x in cells}

    def lookup(self, family, tier, bucket, book, kind=None):
        for k in ((kind,) if kind else (CALIBRATION, LADDER)):
            c = self.c.get((k, family, tier, bucket, book))
            if c is not None:
                return c
        return None

    def __len__(self):
        return len(self.c)


def load(path: str = DEFAULT_TABLE) -> Table:
    with open(path, "rb") as fh:
        raw = tomllib.load(fh)
    keys = ("family", "tier", "bucket", "book", "side", "net_lo", "kind", "status", "net_mean", "net_hi",
            "max_half_spread", "n")
    return Table(RideCell(**{k: d[k] for k in keys if k in d}) for d in raw.get("cell", []))


def bucket(p: float) -> str:
    edges = [0.0, 0.01, 0.05] + [x / 100 for x in range(10, 100, 5)] + [0.99, 1.0001]
    for i in range(len(edges) - 1):
        if edges[i] <= p < edges[i + 1]:
            return f"{int(round(edges[i] * 100))}-{min(int(round(edges[i + 1] * 100)), 100)}c"
    return "99-100c"


def _none(reason, cell=None):
    return RideDecision(NONE, None, None, None, None, reason, cell)


def decide(family: str, tier: Optional[str], price: float, half_spread: Optional[float], table: Optional[RideTable],
           book_classes: tuple = ("all",), kind: Optional[str] = None) -> RideDecision:
    """price = YES mid; book_classes = most specific first (e.g. ('tight', 'all')); kind None = any kind."""
    if table is None:
        return _none("ride:no_table")
    if tier is None or price is None:
        return _none("ride:no_cell")
    b = bucket(price)
    for book in book_classes:
        c = table.lookup(family, tier, b, book, kind) if kind else table.lookup(family, tier, b, book)
        if c is None:
            continue
        if c.status not in RIDEABLE:
            return _none(f"ride:status_{c.status}", c)
        if not c.net_lo > 0:
            return _none("ride:no_positive_lower_bound", c)
        if c.max_half_spread is not None and (half_spread is None or half_spread > c.max_half_spread):
            return _none("ride:book_wider_than_cell", c)
        return RideDecision(RIDE_YES if c.side == "yes" else RIDE_NO, c.side, c.net_mean, c.net_lo, c.net_hi,
                            f"ride:cell_{tier}_{b}_{book}", c)
    return _none("ride:no_cell")
