"""W82.2 Part B: the one definition of a cell's DISPLAY state, shared by the visual dashboard grid and the
project-state cell matrix.

`wins` is the only state drawn green. A cell is `wins` only when BOTH hold:
  1. the calibration engine released the cell's own pre-registered verdict at judged n (status JUDGED) and that
     verdict is the positive one its pre-registration defines (CANDIDATE-PENDING-CAPACITY, calibration_engine.verdict);
  2. if the cell places demo orders (registry status ACTIVE), P&L per filled bet has a game-clustered 95% CI whose
     lower bound is above zero (`pnl_ci` = (lo, hi), supplied by the caller; absent -> not green).
The engine<->registry join is made from code (engine sport/market_type/band fields); an engine cell that is missing,
duplicated or whose name does not match its own fields is an unresolvable join, and an unresolvable join is not green.
"""
from __future__ import annotations

from typing import Optional

POSITIVE_VERDICTS = frozenset({"CANDIDATE-PENDING-CAPACITY"})
STATUS_JUDGED = "JUDGED"

# Registry status value -> display state. Anything not listed maps to "unmapped" (never green, never silently blank).
DISPLAY_OF_STATUS = {"active": "active", "shadow": "shadow", "not_implemented": "not_implemented",
                     "blocked": "blocked", "dark": "dark", "ruled_out": "ruled_out"}


def resolve_engine_cell(engine_cells: list, market_type: str, band: str) -> Optional[dict]:
    """The single engine cell for registry key (market_type, band), or None when absent, ambiguous or inconsistent."""
    hits = []
    for c in engine_cells or []:
        if c.get("market_type") is None and not c.get("cell"):
            continue
        sport = str(c.get("sport") or "")
        if str(c.get("band")) != band:
            continue
        # engine cell id is f"{sport}_{registry MarketType.name}_{band}"; the registry name already carries the sport prefix
        # for game markets (NFL_GAME_TOTAL) so match on the id built from the registry name, never on a fuzzy suffix.
        if c.get("cell") == f"{sport}_{market_type}_{band}":
            hits.append(c)
    return hits[0] if len(hits) == 1 else None


def display_state(status: str, engine_cell: Optional[dict], pnl_ci: Optional[tuple] = None) -> str:
    base = DISPLAY_OF_STATUS.get(status, "unmapped")
    if engine_cell is None:
        return base
    if engine_cell.get("status") != STATUS_JUDGED:
        return base
    v = engine_cell.get("verdict") or {}
    if v.get("verdict") not in POSITIVE_VERDICTS:
        return base
    if status == "active":                       # places demo orders: the money has to agree with the forecast
        if not pnl_ci or pnl_ci[0] is None or not pnl_ci[0] > 0:
            return base
    return "wins"
