"""NFL filter functions for the layered decision tree (W110.1, operator 2026-11-10 21:35 PT).

Interface for decision_trees/router.py (110.3 owns the router): `nfl_filters(...)` returns {filter_name: leaf_label}.
Labels are categorical, thresholds fixed a priori (not fitted), point-in-time only: weather must be a FORECAST
(weather_factor.assert_priceable) and matchup terms come from MatchupBook (prior weeks only). A filter never returns a
price or a side to bet: it names the leaf; the tree scores which arm (ride / fade / momentum / no bet) that leaf earns.
"""
from __future__ import annotations

from typing import Mapping, Optional

from .matchup_cross import Terms
from .weather_factor import MIN_LEAD_H, WeatherContext, assert_priceable, exposure, is_indoor

WIND_HIGH_MPH = 15.0
COLD_F = 35.0
PASS_MISMATCH_PTS = 1.5   # summed home+away pass-cross terms (EPA points) beyond +/- this = shootout / grind lean
SIDE_EDGE_PTS = 2.0       # home-minus-away summed pass+rush cross beyond +/- this = a side edge


def weather_leaf(ctx: WeatherContext, min_lead_h: float = MIN_LEAD_H) -> str:
    assert_priceable(ctx, min_lead_h) if ctx.source != "none" else None
    if ctx.source == "none":
        return "unknown"
    if is_indoor(ctx.roof):
        return "indoor"
    e = exposure(ctx)
    if e["precip"] > 0:
        return "wet"
    if ctx.wind_mph is not None and ctx.wind_mph >= WIND_HIGH_MPH:
        return "windy"
    if ctx.temp_f is not None and ctx.temp_f < COLD_F:
        return "cold"
    return "calm" if ctx.wind_mph is not None or ctx.temp_f is not None else "unknown"


def matchup_total_leaf(h: Terms, a: Terms) -> str:
    s = h.pass_ + a.pass_
    return "pass_mismatch_high" if s > PASS_MISMATCH_PTS else "pass_mismatch_low" if s < -PASS_MISMATCH_PTS else "neutral"


def matchup_side_leaf(h: Terms, a: Terms) -> str:
    d = (h.pass_ + h.rush) - (a.pass_ + a.rush)
    return "home_edge" if d > SIDE_EDGE_PTS else "away_edge" if d < -SIDE_EDGE_PTS else "neutral"


def market_state_leaf(spread_line: Optional[float], total_line: Optional[float]) -> dict:
    if spread_line is None or total_line is None or spread_line != spread_line or total_line != total_line:
        return {"spread_bucket": "unknown", "total_bucket": "unknown"}   # no line published yet: say so, never guess
    s = abs(spread_line)
    return {"spread_bucket": "pk" if s < 3.5 else "mid" if s <= 7 else "big",
            "total_bucket": "low" if total_line < 42 else "high" if total_line > 47 else "mid"}


def nfl_filters(ctx: WeatherContext, terms_home: Terms, terms_away: Terms, spread_line: float, total_line: float,
                min_lead_h: float = MIN_LEAD_H) -> dict:
    return {"weather": weather_leaf(ctx, min_lead_h), "matchup_total": matchup_total_leaf(terms_home, terms_away),
            "matchup_side": matchup_side_leaf(terms_home, terms_away), **market_state_leaf(spread_line, total_line)}


# --- W113.2 Part B: granularity-index split leaves (12_EXPLORATORY/granularity_index_nfl; directive D-06) -------------------
# Entry -> is a higher raw value better for the unit. Values are the PRIOR season's league percentile (0..1, of the raw
# value) per team, from decision_trees/filter_data/nfl_team_percentiles.json (point in time for any game of the next season).
LOW, HIGH, SIDE_EDGE = 1 / 3, 2 / 3, 1 / 3
HIGHER_IS_BETTER: dict = {
    "rush_success_vs_loaded_box": True, "rush_success_vs_light_box": True, "rush_success_allowed_loaded_box": False,
    "rush_stuff_rate_defence": True, "rush_stuffed_rate_offence": False, "loaded_box_rate_faced": False,
    "rush_success_with_motion": True, "pass_success_vs_man": True, "pass_success_vs_zone": True,
    "pass_success_allowed_vs_man": False, "pass_success_vs_cover3": True, "pass_success_allowed_cover6_vs_3wr": False,
    "pass_success_3wr_sets": True, "pass_success_allowed_vs_3wr": False, "three_wr_rate": True,
    "pass_success_with_motion": True, "play_action_success": True, "pass_success_vs_blitz": True, "blitz_rate_defence": True,
    "red_zone_td_rate": True, "red_zone_td_rate_allowed": False, "third_down_success": True,
    "third_down_success_allowed": False, "explosive_pass_rate": True, "explosive_pass_rate_allowed": False,
}


# Entries scored per leaf on the 2026 shadow rows (score_leaves.py, 70/30 held out): the ones with >= 1 scored leaf. The other
# index entries are thin at the current n (fit leaves < MIN_FIT_ROWS / MIN_FIT_GAMES) and are re-looked as rows accumulate.
TESTED_SPLITS = frozenset(['pass_success_3wr_sets', 'pass_success_vs_blitz', 'pass_success_vs_cover3', 'pass_success_vs_man', 'pass_success_vs_zone', 'pass_success_with_motion', 'red_zone_td_rate', 'rush_stuff_rate_defence', 'rush_stuffed_rate_offence', 'rush_success_allowed_loaded_box', 'rush_success_vs_loaded_box', 'rush_success_with_motion', 'third_down_success'])


def split_total_leaf(p_home, p_away) -> str:
    if p_home is None or p_away is None:
        return "unknown"
    m = (p_home + p_away) / 2.0
    return "high" if m > HIGH else "low" if m < LOW else "mid"


def split_side_leaf(name: str, p_home, p_away) -> str:
    if p_home is None or p_away is None or name not in HIGHER_IS_BETTER:
        return "unknown"
    good = (lambda p: p) if HIGHER_IS_BETTER[name] else (lambda p: 1.0 - p)
    d = good(p_home) - good(p_away)
    return "home_edge" if d > SIDE_EDGE else "away_edge" if d < -SIDE_EDGE else "neutral"


def nfl_split_filters(home: Mapping, away: Mapping, keep=None) -> dict:
    """{'<entry>@total': leaf, '<entry>@side': leaf}; `keep` restricts to the entries that passed their held-out test."""
    out = {}
    for name in HIGHER_IS_BETTER:
        if keep is not None and name not in keep:
            continue
        h, a = home.get(name), away.get(name)
        out[f"{name}@total"] = split_total_leaf(h, a)
        out[f"{name}@side"] = split_side_leaf(name, h, a)
    return out
