"""NHL temporal evolution (W109.2): how a factor's level, team-level stability and weight move through a season and across
seasons, point-in-time. Maps the NHL game number onto the NFL module's ``week`` axis and reuses its tested generics
(``asof_ew``, ``within_season_slope``, ``reliability_gap``, ``blend_weight_by_week``) rather than copying them.

Long-table contract: columns ``team, season, week, v`` where ``week`` is the team's game number in its season (1-based)
and ``v`` is any per-(team, game) number the engine reads (regulation goals for / against, shots, ...).

When it applies: a factor measured once per team-game in a regular season. When it does not: factors that only exist at
game level (a total split between two teams cannot be attributed to one), and the playoffs (short, uneven series).
Point-in-time: every as-of quantity uses games strictly earlier than the one predicted (inherited from the NFL module).
"""
from __future__ import annotations

import pandas as pd

from prediction_market_bot.nfl_engine.temporal_evolution import (  # noqa: F401  (re-exported tools)
    BOOT_SEED, asof_ew, blend_weight_by_week, reliability_gap, within_season_slope)

# game-number stretches of an 82-game season (early / middle / late)
NHL_BUCKETS = ((10, 25), (26, 50), (51, 82))


def team_game_long(tg: pd.DataFrame, metric: str) -> pd.DataFrame:
    """Long table from ``granularity_index.team_games`` output for one metric ('gf', 'ga' or 'total')."""
    return pd.DataFrame({"team": tg["team"].to_numpy(), "season": tg["season"].to_numpy(),
                         "week": tg["game_no"].to_numpy(), "v": tg[metric].to_numpy(float)})


def nhl_blend_weight(d: pd.DataFrame, **kw) -> list:
    """``blend_weight_by_week`` with the NHL game-number stretches."""
    return blend_weight_by_week(d, buckets=NHL_BUCKETS, **kw)
