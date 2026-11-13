"""NBA shot-distance index filters (W113.4 Part C, directive D-06) -- interface handed to 113.1 (owner of decision_trees/filter_supply.py).

Source of the split definition: NBA.com "Teams Opponent Shooting by distance" (archive table family graded VERIFIED by recompute,
12_EXPLORATORY/archive_intake/GRADES.md). The VALUES come from the bot's own event store, never from the archive, so the entries
are point-in-time. Bins are the exact-distance bins hypot(x_legacy, y_legacy)/10 ft: lt5, 5_9, 10_14, 15_19, 20_24, 25plus.
Entry names: ``opp_fg_pct_<bin>`` (opponent FG% allowed in the bin) and ``opp_fga_share_<bin>`` (share of opponent shots taken
there); both are defence-side. Leaves are the same categorical labels as ``nba_engine.filters``: ``<name>@total`` (high/mid/low) and
``<name>@side`` (home_edge/away_edge/neutral), from the mean / difference of the two teams' prior-season league percentiles.
Interface: ``distance_filters(home, away)`` with home/away = {entry name: raw-value percentile 0..1}; returns {filter_name: leaf}.
Applies when: tagging an NBA row with distance-allowed leaves before routing it to an arm.
"""
from __future__ import annotations

from typing import Mapping

from prediction_market_bot.nba_engine import filters as nf

BINS = ("lt5", "5_9", "10_14", "15_19", "20_24", "25plus")
# Defence-side entries: a LOWER value allowed is better for the unit (FG% allowed, share of shots allowed in the bin).
HIGHER_IS_BETTER: dict = {**{f"opp_fg_pct_{b}": False for b in BINS}, **{f"opp_fga_share_{b}": False for b in BINS}}


def side_leaf(name: str, p_home, p_away) -> str:
    if p_home is None or p_away is None or name not in HIGHER_IS_BETTER:
        return "unknown"
    good = (lambda p: p) if HIGHER_IS_BETTER[name] else (lambda p: 1.0 - p)
    d = good(p_home) - good(p_away)
    return "home_edge" if d > nf.SIDE_EDGE else "away_edge" if d < -nf.SIDE_EDGE else "neutral"


def distance_filters(home: Mapping, away: Mapping) -> dict:
    out = {}
    for name in HIGHER_IS_BETTER:
        h, a = home.get(name), away.get(name)
        out[f"{name}@total"] = nf.total_leaf(h, a)
        out[f"{name}@side"] = side_leaf(name, h, a)
    return out
