"""NFL filter functions for the layered decision tree (W110.1, operator 2026-11-10 21:35 PT).

Interface for decision_trees/router.py (110.3 owns the router): `nfl_filters(...)` returns {filter_name: leaf_label}.
Labels are categorical, thresholds fixed a priori (not fitted), point-in-time only: weather must be a FORECAST
(weather_factor.assert_priceable) and matchup terms come from MatchupBook (prior weeks only). A filter never returns a
price or a side to bet: it names the leaf; the tree scores which arm (ride / fade / momentum / no bet) that leaf earns.
"""
from __future__ import annotations

from typing import Optional

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
