"""NFL play-level personnel / coverage / motion crosses as layer-2 splits (W128.3, EXP-NFLPLAYLEVEL-001; PREREG 12_EXPLORATORY/nfl_playlevel/PREREG.md).

Each cross reads a team's OFFENSE tendency against the OPPOSING defense's tendency, both point-in-time (trailing 17 games with data, strictly before
the game day, minimum 6 games), and returns a 2x2 leaf ``hi_hi / hi_lo / lo_hi / lo_lo`` cut at fit-season medians:
  X1 ``x1_personnel_shell``  -- 11-personnel share (offense) x two-high shell share (defense)
  X2 ``x2_motion_man``       -- FTN motion rate (offense) x man-coverage share (defense)
  X3 ``x3_success_shell``    -- offense EPA per play vs two-high shells (shrunk, k=60) x two-high shell share (defense)
Game level: spreads read ``home_only / neither_or_both / away_only`` (which side's offence is ``hi_hi``); totals read ``none / one / both``.
Unjoined or thin inputs give ``unknown``, never scored. ``carried`` marks a tendency whose newest game with data is from a prior season
(2026 has no participation feed). Applies when: tagging an NFL row before routing. Default off: ``PM_NFL_PLAYLEVEL=on``.
"""
from __future__ import annotations

import os
from datetime import date
from typing import Optional, Sequence

CROSS_NAMES = ("x1_personnel_shell", "x2_motion_man", "x3_success_shell")
WINDOW, MIN_GAMES, EPA_K = 17, 6, 60.0


class PITViolation(ValueError):
    """An aggregate that was not known before the game day."""


def nfl_playlevel_on() -> bool:
    return os.environ.get("PM_NFL_PLAYLEVEL", "off").strip().lower() == "on"


def trailing_ratio(history: Sequence[tuple], game_day: date, prior: float = 0.0, k: float = 0.0) -> Optional[float]:
    """history = [(game_day, numerator, denominator), ...] in any order, one entry per earlier game WITH data.
    Pooled ratio over the last WINDOW games dated strictly before ``game_day``; an entry on or after it raises (point-in-time).
    ``prior``/``k`` shrink toward the league value with k pseudo-denominators (0 = none). < MIN_GAMES games -> None."""
    for d, _, _ in history:
        if d >= game_day:
            raise PITViolation(f"aggregate dated {d} is not before the game day {game_day}")
    last = sorted(history, key=lambda h: h[0])[-WINDOW:]
    if len(last) < MIN_GAMES:
        return None
    num, den = sum(h[1] for h in last), sum(h[2] for h in last)
    if den + k <= 0:
        return None
    return (num + prior * k) / (den + k)


def is_carried(newest_data_season: Optional[int], game_season: int) -> bool:
    """True when the newest game with participation data is from an earlier season than the priced game (2026: no feed)."""
    return newest_data_season is not None and newest_data_season < game_season


def cross_leaf(off: Optional[float], dfn: Optional[float], cuts: Optional[tuple]) -> str:
    """cuts = (offense_median, defense_median) fixed on the FIT seasons."""
    if off is None or dfn is None or cuts is None:
        return "unknown"
    return ("hi" if off >= cuts[0] else "lo") + "_" + ("hi" if dfn >= cuts[1] else "lo")


def game_leaf_spread(home: str, away: str) -> str:
    if "unknown" in (home, away):
        return "unknown"
    h, a = home == "hi_hi", away == "hi_hi"
    return "home_only" if h and not a else "away_only" if a and not h else "neither_or_both"


def game_leaf_total(home: str, away: str) -> str:
    if "unknown" in (home, away):
        return "unknown"
    n = (home == "hi_hi") + (away == "hi_hi")
    return ("none", "one", "both")[n]


def playlevel_leaves(*, game_day: date, home: dict, away: dict, cuts: dict) -> dict:
    """home / away = {cross_name: (offense_tendency, opposing_defense_tendency)} for that team's OFFENCE (defense = the other team's).
    cuts = {cross_name: (off_median, def_median)}. -> {cross@home, cross@away, cross@spread, cross@total} per cross."""
    out = {}
    for c in CROSS_NAMES:
        h = cross_leaf(*home.get(c, (None, None)), cuts.get(c))
        a = cross_leaf(*away.get(c, (None, None)), cuts.get(c))
        out[f"{c}@home"], out[f"{c}@away"] = h, a
        out[f"{c}@spread"], out[f"{c}@total"] = game_leaf_spread(h, a), game_leaf_total(h, a)
    return out
