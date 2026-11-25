"""NFL factor splits on team totals and alternate ladders (W126.5, EXP-NFLSPLITS-001; PREREG 12_EXPLORATORY/nfl_splits/PREREG.md).

Five layer-2 splits tag a game (or a team side) with a categorical leaf before routing it to an arm:
  S1 ``qb@team``      -- the team's starter differs from its previous regular-season starter (``qb_new``) or not (``qb_same``).
  S2 ``rest@team``    -- days of rest: short <=5, normal 6-8, long >=9; game level is the home-away differential.
  S3 ``officials@game`` -- the referee's shrunk prior (earlier games only) in fit-season terciles.
  S4 ``weather@game`` -- FORECAST-only dome / adverse / benign; a realised or too-late forecast raises ``PITViolation``.
  S5 ``matchup@game`` -- the MatchupBook cross score in fit-season terciles (2022+).
Point-in-time: every input is pre-kick; a prior-game date on or after the game date raises ``PITViolation``.
Unjoined inputs give ``unknown``, which is never scored as a leaf. Applies when: tagging an NFL row before routing.
Default off: ``nfl_splits_on()`` needs PM_NFL_SPLITS=on. Interface: ``split_leaves(...)`` -> {split_name: leaf}.
"""
from __future__ import annotations

import os
from datetime import date
from typing import Optional, Sequence

from prediction_market_bot.nfl_engine import weather_factor as wf

SPLIT_NAMES = ("qb@team", "rest@team", "officials@game", "weather@game", "matchup@game")
SHORT_REST, LONG_REST, REST_DIFF = 5, 9, 3
REF_K = 20.0          # shrink the referee's mean total residual toward 0 with this many pseudo-games
WIND_ADVERSE, COLD_ADVERSE = 15.0, 32.0


class PITViolation(ValueError):
    """An input that was not known before kickoff."""


def nfl_splits_on() -> bool:
    return os.environ.get("PM_NFL_SPLITS", "off").strip().lower() == "on"


def qb_leaf(prev_starter: Optional[str], starter: Optional[str]) -> str:
    if not prev_starter or not starter:
        return "unknown"
    return "qb_same" if prev_starter == starter else "qb_new"


def game_qb_leaf(home: str, away: str) -> str:
    if "unknown" in (home, away):
        return "unknown"
    return "any_new" if "qb_new" in (home, away) else "none"


def rest_leaf(days: Optional[float]) -> str:
    if days is None:
        return "unknown"
    return "short" if days <= SHORT_REST else "long" if days >= LONG_REST else "normal"


def rest_diff_leaf(home_days: Optional[float], away_days: Optional[float]) -> str:
    if home_days is None or away_days is None:
        return "unknown"
    d = home_days - away_days
    return "home_rest_edge" if d >= REST_DIFF else "away_rest_edge" if d <= -REST_DIFF else "even"


def ref_prior(prior_residuals: Sequence[float]) -> Optional[float]:
    """Shrunk mean of (total - total_line) over the referee's EARLIER games (caller filters by date); None when there are none."""
    r = [x for x in prior_residuals if x is not None]
    return None if not r else sum(r) / (len(r) + REF_K)


def tercile_leaf(value: Optional[float], cuts: Optional[tuple], names: tuple) -> str:
    """cuts = (low_cut, high_cut) fixed on the FIT seasons; names = (low, mid, high)."""
    if value is None or cuts is None:
        return "unknown"
    lo, hi = cuts
    return names[0] if value <= lo else names[2] if value >= hi else names[1]


def referee_leaf(prior: Optional[float], cuts: Optional[tuple]) -> str:
    return tercile_leaf(prior, cuts, ("ref_low", "ref_mid", "ref_high"))


def matchup_leaf(score: Optional[float], cuts: Optional[tuple]) -> str:
    return tercile_leaf(score, cuts, ("mu_low", "mu_mid", "mu_high"))


def weather_leaf(ctx: Optional[wf.WeatherContext]) -> str:
    """Forecast-only. ``source=='realised'`` or a forecast issued too late raises (point-in-time); no forecast -> unknown."""
    if ctx is None or ctx.source == "none":
        return "unknown"
    try:
        wf.assert_priceable(ctx, min_lead_h=0.0)
    except ValueError as e:
        raise PITViolation(str(e)) from e
    if wf.is_indoor(ctx.roof):
        return "dome"
    if ctx.temp_f is None and ctx.wind_mph is None:
        return "unknown"
    adverse = (ctx.wind_mph is not None and ctx.wind_mph >= WIND_ADVERSE) or (ctx.temp_f is not None and ctx.temp_f <= COLD_ADVERSE)
    return "adverse" if adverse else "benign"


def assert_prior(prev_game: Optional[date], game_day: date) -> None:
    if prev_game is not None and prev_game >= game_day:
        raise PITViolation(f"previous game {prev_game} is not before the game day {game_day}")


def split_leaves(*, game_day: date, prev_home_game: Optional[date], prev_away_game: Optional[date],
                 home_prev_qb: Optional[str], home_qb: Optional[str], away_prev_qb: Optional[str], away_qb: Optional[str],
                 home_rest: Optional[float], away_rest: Optional[float], ref_prior_value: Optional[float],
                 ref_cuts: Optional[tuple], weather: Optional[wf.WeatherContext], matchup_score: Optional[float],
                 matchup_cuts: Optional[tuple]) -> dict:
    """{split_name: leaf} for one game; team-level splits carry both sides as ``home|away`` in the leaf of the ``@team`` names."""
    assert_prior(prev_home_game, game_day)
    assert_prior(prev_away_game, game_day)
    hq, aq = qb_leaf(home_prev_qb, home_qb), qb_leaf(away_prev_qb, away_qb)
    return {
        "qb@team": f"{hq}|{aq}",
        "qb@game": game_qb_leaf(hq, aq),
        "rest@team": f"{rest_leaf(home_rest)}|{rest_leaf(away_rest)}",
        "rest@game": rest_diff_leaf(home_rest, away_rest),
        "officials@game": referee_leaf(ref_prior_value, ref_cuts),
        "weather@game": weather_leaf(weather),
        "matchup@game": matchup_leaf(matchup_score, matchup_cuts),
    }
