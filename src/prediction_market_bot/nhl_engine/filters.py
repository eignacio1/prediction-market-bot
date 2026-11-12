"""NHL situation-split filter functions for the layered decision tree (W112.4 Part C, directive D-06).

Interface for decision_trees/router.py (112.1 owns the router): ``nhl_filters(home, away)`` returns {filter_name: leaf_label}.
``home`` / ``away`` are per-team dicts of point-in-time facts known before puck drop, built by ``factors_w112``:
  schedule: rest_days, back_to_back, games_last_7d, travel_km, tz_shift_h, neutral_site (``schedule_context`` row)
  league percentiles (0..1, rank among the 32 teams' latest states at that instant): hd_for, hd_against, top_share
Labels are categorical, thresholds fixed a priori (written here, not fitted), never a price or a side to bet: a filter names the
leaf; the tree scores which arm (ride / fade / momentum / no bet) that leaf earns. A missing fact yields "unknown".
Applies when: tagging an NHL shadow row with factor leaves before routing it to an arm.
"""
from __future__ import annotations

import math
from typing import Mapping

LOW, HIGH = 1 / 3, 2 / 3          # tercile edges on a mean of the two teams' league percentiles (game-level / total families)
SIDE_EDGE = 1 / 3                 # home-minus-away goodness percentile beyond +/- this = a side edge
REST_EDGE_DAYS = 1.0              # a full day more rest than the opponent
LONG_TRIP_KM, TZ_SHIFT_H, DENSE_GAMES = 2000.0, 2, 4


def _ok(*v) -> bool:
    return all(x is not None and not (isinstance(x, float) and math.isnan(x)) for x in v)


def rest_leaf(home: Mapping, away: Mapping) -> str:
    h, a = home.get("rest_days"), away.get("rest_days")
    if not _ok(h, a):
        return "unknown"
    hb, ab = bool(home.get("back_to_back")), bool(away.get("back_to_back"))
    if ab and not hb:
        return "home_rest_edge"
    if hb and not ab:
        return "away_rest_edge"
    d = h - a
    return "home_rest_edge" if d >= REST_EDGE_DAYS else "away_rest_edge" if d <= -REST_EDGE_DAYS else "even_rest"


def travel_leaf(home: Mapping, away: Mapping) -> str:
    """Who arrives off a long trip (>= 2000 km or >= 2 time zones from their previous venue)."""
    def long(t):
        km, tz = t.get("travel_km"), t.get("tz_shift_h")
        return None if not _ok(km, tz) else (km >= LONG_TRIP_KM or abs(tz) >= TZ_SHIFT_H)
    h, a = long(home), long(away)
    if h is None or a is None:
        return "unknown"
    return "both_long" if h and a else "home_long" if h else "away_long" if a else "short_trips"


def density_leaf(home: Mapping, away: Mapping) -> str:
    h, a = home.get("games_last_7d"), away.get("games_last_7d")
    if not _ok(h, a):
        return "unknown"
    hd, ad = h >= DENSE_GAMES, a >= DENSE_GAMES
    return "both_dense" if hd and ad else "home_dense" if hd else "away_dense" if ad else "normal_density"


def venue_leaf(home: Mapping) -> str:
    n = home.get("neutral_site")
    return "unknown" if n is None else "neutral" if n else "home_ice"


def total_leaf(p_home, p_away) -> str:
    if not _ok(p_home, p_away):
        return "unknown"
    m = (p_home + p_away) / 2.0
    return "high" if m > HIGH else "low" if m < LOW else "mid"


def side_leaf(p_home, p_away, higher_is_better: bool = True) -> str:
    if not _ok(p_home, p_away):
        return "unknown"
    g = (lambda p: p) if higher_is_better else (lambda p: 1.0 - p)
    d = g(p_home) - g(p_away)
    return "home_edge" if d > SIDE_EDGE else "away_edge" if d < -SIDE_EDGE else "neutral"


def nhl_filters(home: Mapping, away: Mapping) -> dict:
    out = {
        "rest@side": rest_leaf(home, away), "travel@side": travel_leaf(home, away), "density@total": density_leaf(home, away),
        "venue@side": venue_leaf(home),
    }
    hf, af, ha, aa = home.get("hd_for"), away.get("hd_for"), home.get("hd_against"), away.get("hd_against")
    # shot quality: a team's goodness = its high-danger share for minus against (both league percentiles; against is inverted)
    gh = None if not _ok(hf, ha) else (hf + (1.0 - ha)) / 2.0
    ga = None if not _ok(af, aa) else (af + (1.0 - aa)) / 2.0
    out["shot_quality@side"] = side_leaf(gh, ga)
    # total lean: how many high-danger chances the two teams' games carry (for + against, league percentiles)
    ph = None if not _ok(hf, ha) else (hf + ha) / 2.0
    pa = None if not _ok(af, aa) else (af + aa) / 2.0
    out["shot_quality@total"] = total_leaf(ph, pa)
    # deployment: top-heavy (high top_share) = depth-light; goodness of depth is the inverse
    out["deployment@side"] = side_leaf(home.get("top_share"), away.get("top_share"), higher_is_better=False)
    out["deployment@total"] = total_leaf(home.get("top_share"), away.get("top_share"))
    return out
