"""NBA situation-split filter functions for the layered decision tree (W111.4 Part C, directive D-06).

Interface for decision_trees/router.py (111.3 owns the router): ``nba_filters(home, away)`` returns {filter_name: leaf_label}.
``home`` / ``away`` map an index entry name to that team's league percentile (0..1, of the RAW metric value) at the end of the
PRIOR season (point in time for any game of the next season), built by 12_EXPLORATORY/granularity_index_nba/score_leaves.py.
Labels are categorical, thresholds fixed a priori (terciles), never a price or a side to bet: a filter names the leaf; the tree
scores which arm (ride / fade / momentum / no bet) that leaf earns. A missing team percentile yields "unknown".
Applies when: tagging an NBA row with the granularity-index leaves before routing it to an arm.
"""
from __future__ import annotations

from typing import Mapping

LOW, HIGH = 1 / 3, 2 / 3          # tercile edges on the mean of the two teams' raw percentiles (game-level families)
SIDE_EDGE = 1 / 3                 # home-minus-away goodness percentile beyond +/- this = a side edge

# Index entry -> higher value is better for the unit (team-level entries only; lineup entries need tonight's lineup).
HIGHER_IS_BETTER: dict = {
    "clutch_offence_ppp": True, "clutch_defence_ppp": False, "trailing_big_q4_offence_ppp": True,
    "leading_big_q4_defence_ppp": False, "pace_seconds_per_possession": False, "pace_after_made_shot": False,
    "pace_after_missed_shot": False, "ppp_after_live_ball_turnover": True, "second_chance_ppp": True,
    "turnover_rate": False, "turnovers_forced_rate": True, "three_attempt_rate": True,
    "three_attempt_rate_allowed": False, "free_throw_rate": True, "first_four_minutes_ppp": True,
    "shooting_lineup_offence_ppp": True, "defensive_lineup_defence_ppp": False, "shooters_vs_defenders_offence_ppp": True,
    "rim_fg_allowed": False, "corner_three_make_rate": True, "above_break_three_make_rate": True, "midrange_make_rate": True,
}
TOTAL_FAMILIES = ("GAME_TOTAL", "TEAM_TOTAL")
SIDE_FAMILIES = ("SPREAD", "MONEYLINE")


def total_leaf(p_home, p_away) -> str:
    """Game-level lean of a metric: high / mid / low on the mean of the two teams' raw percentiles."""
    if p_home is None or p_away is None:
        return "unknown"
    m = (p_home + p_away) / 2.0
    return "high" if m > HIGH else "low" if m < LOW else "mid"


def side_leaf(name: str, p_home, p_away) -> str:
    """Which side the metric favours: home_edge / away_edge / neutral on the goodness-percentile difference."""
    if p_home is None or p_away is None or name not in HIGHER_IS_BETTER:
        return "unknown"
    good = (lambda p: p) if HIGHER_IS_BETTER[name] else (lambda p: 1.0 - p)
    d = good(p_home) - good(p_away)
    return "home_edge" if d > SIDE_EDGE else "away_edge" if d < -SIDE_EDGE else "neutral"


def nba_filters(home: Mapping, away: Mapping) -> dict:
    """{'<entry>@total': leaf, '<entry>@side': leaf} for every team-level index entry."""
    out = {}
    for name in HIGHER_IS_BETTER:
        h, a = home.get(name), away.get(name)
        out[f"{name}@total"] = total_leaf(h, a)
        out[f"{name}@side"] = side_leaf(name, h, a)
    return out
