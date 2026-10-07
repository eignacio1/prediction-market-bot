"""NBA settlement join (EXP-038). READ-ONLY: final scores in, y per market out. No ties exist in the NBA and
Kalshi strikes are half-points, so y is binary and never pushes."""
from __future__ import annotations

import math
from typing import Optional

from prediction_market_bot.pregame_shadow.nba_forecaster import parse_market_ticker
from prediction_market_bot.pregame_shadow.nfl_model import _phi


def climatology_p(clim: dict, parsed: dict, home: str) -> float:
    mt, strike = parsed["market_type"], parsed["strike"]
    sm, st, mm, mtot = clim["sd_margin"], clim["sd_total"], clim["mean_margin"], clim["mean_total"]
    if mt == "NBA_MONEYLINE":
        hw = clim["home_win_rate"]
        return hw if parsed["subject"] == home else 1.0 - hw
    if mt == "NBA_SPREAD":
        if parsed["subject"] == home:
            return 1.0 - _phi((strike - mm) / sm)
        return _phi((-strike - mm) / sm)
    if mt == "NBA_GAME_TOTAL":
        return 1.0 - _phi((strike - mtot) / st)
    sgn = 1.0 if parsed["subject"] == home else -1.0
    return 1.0 - _phi((strike - (mtot + sgn * mm) / 2.0) / math.sqrt((st ** 2 + sm ** 2) / 4.0))


def outcome(parsed: dict, home: str, home_score: float, away_score: float) -> float:
    mt, margin, total = parsed["market_type"], home_score - away_score, home_score + away_score
    subj_home = parsed["subject"] == home
    if mt == "NBA_MONEYLINE":
        return 1.0 if (margin > 0) == subj_home else 0.0
    if mt == "NBA_SPREAD":
        return 1.0 if (margin if subj_home else -margin) > parsed["strike"] else 0.0
    if mt == "NBA_GAME_TOTAL":
        return 1.0 if total > parsed["strike"] else 0.0
    return 1.0 if (home_score if subj_home else away_score) > parsed["strike"] else 0.0


def join_row(row: dict, home: str, away: str, home_score: float, away_score: float,
             clim: dict) -> Optional[dict]:
    parsed = parse_market_ticker(row["market_ticker"])
    if parsed is None:
        return None
    out = dict(row)
    out.update(y=outcome(parsed, home, home_score, away_score), p_clim=climatology_p(clim, parsed, home),
               game_key=f"{parsed['game_date']}:{parsed['away']}@{parsed['home']}")
    return out
