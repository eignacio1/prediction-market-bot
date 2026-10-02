"""NFL settlement join (EXP-037 / D2b). READ-ONLY: final scores in, y per market out.

Uses c5_execution.game_market_settlement.derive_actual_stat (unmodified). Scalar settlements:
moneyline tie -> y=0.5 (Kalshi $0.50/$0.50 split); half-point strikes never push.
Also attaches climatology p and the game cluster key.
"""
from __future__ import annotations

from typing import Optional

from prediction_market_bot.c5_execution.game_market_settlement import derive_actual_stat
from prediction_market_bot.c5_execution.market_type_registry import MarketType
from prediction_market_bot.pregame_shadow.nfl_forecaster import parse_market_ticker
from prediction_market_bot.pregame_shadow.nfl_model import _phi
import math


def climatology_p(clim: dict, parsed: dict, home: str) -> float:
    mt, strike = parsed["market_type"], parsed["strike"]
    sm, st = clim["sd_margin"], clim["sd_total"]
    mm, mtot = clim["mean_margin"], clim["mean_total"]
    if mt == "NFL_MONEYLINE":
        hw = clim["home_win_rate_ex_ties"]
        return hw if parsed["subject"] == home else 1.0 - hw
    if mt == "NFL_SPREAD":
        if parsed["subject"] == home:
            return 1.0 - _phi((strike - mm) / sm)
        return _phi((-strike - mm) / sm)
    if mt == "NFL_GAME_TOTAL":
        return 1.0 - _phi((strike - mtot) / st)
    sgn = 1.0 if parsed["subject"] == home else -1.0
    mean = (mtot + sgn * mm) / 2.0
    sd = math.sqrt((st ** 2 + sm ** 2) / 4.0)  # rho taken as 0 for the climatological reference
    return 1.0 - _phi((strike - mean) / sd)


def join_row(row: dict, home: str, away: str, home_score: float, away_score: float,
             clim: dict) -> Optional[dict]:
    parsed = parse_market_ticker(row["market_ticker"])
    if parsed is None:
        return None
    mt = MarketType[row["market_type"]]
    kalshi_tkr = row["market_ticker"]
    # derive_actual_stat takes Kalshi's own team-code alphabet in the ticker suffix; nflverse
    # LA/JAX differ from Kalshi LAR/JAC (Washington is WAS in both), so map the ticker side explicitly.
    actual, _ = derive_actual_stat(mt, kalshi_tkr, _to_kalshi(home), _to_kalshi(away),
                                   home_score, away_score)
    if parsed["market_type"] == "NFL_MONEYLINE":
        y = 0.5 if actual == 0 else (1.0 if actual > 0 else 0.0)
    elif parsed["market_type"] == "NFL_SPREAD":
        y = 1.0 if actual > parsed["strike"] else 0.0
    else:
        y = 1.0 if actual > parsed["strike"] else 0.0
    out = dict(row)
    out.update(y=y, p_clim=climatology_p(clim, parsed, home),
               game_key=f"{parsed['game_date']}:{parsed['away']}@{parsed['home']}")
    return out


def _to_kalshi(code: str) -> str:
    return {"LA": "LAR", "JAX": "JAC"}.get(code, code)
