"""W105.6 pot-of-gold tree: take the other side of lottery-ticket buyers, from a table of measured cells.

Pure function of (family, time tier, listed YES price, book state) and a table. Returns FADE_LONGSHOT / TAKE_FAVOURITE /
BUY_LONGSHOT only when a cell for that exact situation has status HELD_OUT or FORWARD_PASSED with a net-of-fee lower
bound > 0; every other status, a missing cell, or a book wider than the cell was measured on returns NO_BET. No numbers
live in code: they come from longshot_cells.toml. Same status gate as ride.py (operator 2026-10-27).

When it applies: a pre-game, two-sided, priced market with listed YES mid in 1-15c or 85-99c. When it doesn't: anything
else. Nothing here sizes, places or logs, and nothing runs it (wiring into the router is Wave 106).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

try:
    import tomllib
except ImportError:  # the box is 3.9
    import tomli as tomllib  # type: ignore

from prediction_market_bot.quant.longshot_bias import (BUY_LONGSHOT, FADE_LONGSHOT, TAKE_FAVOURITE, pot_bucket)

NO_BET = "NO_BET"
IN_SAMPLE, HELD_OUT, FORWARD_PASSED, FAILED, UNTESTED = "IN_SAMPLE", "HELD_OUT", "FORWARD_PASSED", "FAILED", "UNTESTED"
ORDERABLE = (HELD_OUT, FORWARD_PASSED)
DEFAULT_TABLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "longshot_cells.toml")


@dataclass(frozen=True)
class LongshotCell:
    sport: str
    family: str
    tier: str
    bucket: str
    book: str
    route: str
    side: str
    status: str
    net_lo: float
    net_mean: Optional[float] = None
    max_half_spread: Optional[float] = None
    n: int = 0


@dataclass(frozen=True)
class LongshotDecision:
    action: str  # FADE_LONGSHOT | TAKE_FAVOURITE | BUY_LONGSHOT | NO_BET
    side: Optional[str]
    reason: str
    cell: Optional[LongshotCell] = None


class Table:
    def __init__(self, cells):
        self._c = {(c.family, c.tier, c.bucket, c.book): c for c in cells}

    def lookup(self, family, tier, bucket, book):
        return self._c.get((family, tier, bucket, book))

    def __len__(self):
        return len(self._c)


def load(path: str = DEFAULT_TABLE) -> Table:
    with open(path, "rb") as fh:
        doc = tomllib.load(fh)
    return Table(LongshotCell(
        sport=c["sport"], family=c["family"], tier=c["tier"], bucket=c["bucket"], book=c.get("book", "all"),
        route=c["route"], side=c["side"], status=c["status"], net_lo=float(c["net_lo"]),
        net_mean=c.get("net_mean"), max_half_spread=c.get("max_half_spread"), n=int(c.get("n", 0)))
        for c in doc.get("cell", []))


def decide(family: str, tier: str, yes_mid: float, half_spread: float, table: Optional[Table] = None) -> LongshotDecision:
    """Route for one priced market, or NO_BET with the reason. Never raises on a missing cell."""
    t = table if table is not None else load()
    b = pot_bucket(yes_mid)
    if b is None:
        return LongshotDecision(NO_BET, None, f"price {yes_mid:.3f} outside the pot-of-gold buckets")
    book = "tight" if half_spread <= 0.01 else "wide"
    for bk in (book, "all"):
        cell = t.lookup(family, tier, b, bk)
        if cell is not None:
            break
    else:
        return LongshotDecision(NO_BET, None, f"no cell for {family}/{tier}/{b}/{book}")
    if cell.status not in ORDERABLE:
        return LongshotDecision(NO_BET, None, f"cell status {cell.status} is not orderable", cell)
    if not cell.net_lo > 0:
        return LongshotDecision(NO_BET, None, "net lower bound not above zero", cell)
    if cell.max_half_spread is not None and half_spread > cell.max_half_spread:
        return LongshotDecision(NO_BET, None, "book wider than the cell was measured on", cell)
    return LongshotDecision(cell.route, cell.side, f"{cell.status} cell, net_lo {cell.net_lo:.4f}", cell)
