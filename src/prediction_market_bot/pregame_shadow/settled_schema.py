"""One settled-row schema for NFL / NHL / MLB / NBA shadow cells (W59.2 Part C, GG-499).

Raw ledgers and settle outputs are never rewritten. Every reader normalises at read time through `normalize`,
which returns a NEW dict: all original keys kept, plus the canonical ones below.

  y          float 0/0.5/1   from `y` (NFL, MLB) or `outcome` (NHL)
  game_key   str             from `game_key` (NFL, MLB), else the row's or the joined ledger row's `event_ticker` (NHL)
  p_clim     float | absent  passed through where the sport has one; NEVER invented (MLB and NHL have none; NBA settle writes one)

A row with no resolvable y (or, for scoring, game_key) is unsettled/void and normalises to None.
"""
from __future__ import annotations

from typing import Any


def settled_y(row: dict) -> float | None:
    """Outcome of a settled row under either historical field name, or None if unsettled."""
    v = row.get("y")
    if v is None:
        v = row.get("outcome")
    return None if v is None else float(v)


def normalize(row: dict, ledger_row: dict | None = None) -> dict | None:
    y = settled_y(row)
    if y is None:
        return None
    base = {**(ledger_row or {}), **row}                 # settled fields win over the joined ledger row
    gk = row.get("game_key") or base.get("event_ticker")
    if not gk:
        return None
    out: dict[str, Any] = {**base, "y": y, "game_key": gk}
    return out


def counts_toward_judged_n(row: dict) -> bool:
    """False for preseason / smoke-test rows (EXP-038 sec. 4): excluded_from_judged_n=true or season_phase=preseason.
    They may be banked and counted for the descriptive report, never scored and never counted toward judged n."""
    return not (row.get("excluded_from_judged_n") or row.get("season_phase") == "preseason")


def is_settled(row: dict) -> bool:
    return settled_y(row) is not None
