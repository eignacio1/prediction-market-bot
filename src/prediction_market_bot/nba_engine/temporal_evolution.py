"""NBA temporal evolution -- ADR-0075 component 8 for NBA (W109.1 Part B).

How a per-(team, game) factor's level, stability and weight change through an 82-game season, point-in-time.
The estimators are the sport-agnostic ones in ``nfl_engine.temporal_evolution`` (they only need ``team, season, week, v``);
what is NBA here is the clock: ``week`` is the team's game number in the season (1..82, back-to-backs and the
schedule's irregular spacing make calendar weeks meaningless), and the blend-weight stretches are in games.

Point-in-time: ``asof_ew`` shifts by one game; ``blend_weight_by_game`` builds its regressors from earlier games only.
Applies when: deciding how fast a team rating should release its prior (last season's level) as games accumulate, and
whether a rolling factor (net rating, availability, lineup net) drifts team-by-team inside a season.
"""
from __future__ import annotations

import pandas as pd

from prediction_market_bot.nfl_engine import temporal_evolution as _te

BOOT_SEED = _te.BOOT_SEED
# Stretches of the 82-game season, in the team's game number (early / mid / late).
GAME_BUCKETS = ((5, 20), (21, 50), (51, 82))

asof_ew = _te.asof_ew
within_season_slope = _te.within_season_slope
reliability_gap = _te.reliability_gap


def team_game_long(games: pd.DataFrame, home_col: str, away_col: str) -> pd.DataFrame:
    """Per-game frame -> long (team, season, week, v). ``games`` needs ``season, date, home, away`` plus the two value
    columns; ``week`` is each team's game number in its season by date (ties by index order)."""
    h = games.assign(team=games["home"], v=games[home_col])[["team", "season", "date", "v"]]
    a = games.assign(team=games["away"], v=games[away_col])[["team", "season", "date", "v"]]
    long = pd.concat([h, a], ignore_index=True).sort_values(["season", "team", "date"], kind="stable")
    long["week"] = long.groupby(["season", "team"]).cumcount() + 1
    return long[["team", "season", "week", "v"]].reset_index(drop=True)


def blend_weight_by_game(d: pd.DataFrame, *, buckets=GAME_BUCKETS, n_boot: int = 500, seed: int = BOOT_SEED) -> list[dict]:
    """Data-implied weight on this season's as-of mean vs last season's mean, by stretch of the season (game numbers)."""
    out = _te.blend_weight_by_week(d, buckets=buckets, n_boot=n_boot, seed=seed)
    for r in out:
        r["games"] = r.pop("weeks")
    return out
