"""NFL QB challenger PregameForecaster (W65.3): KXNFLGAME home-win moneyline only, sport label "NFLQB".

Mirrors NFLForecaster so the same markets, same as-of and same schedule index give a paired row. Evaluate-and-log
only: imports no order, position or sizing code. Projected-starter audit (home/away QB ids) is kept in ``audit``.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from prediction_market_bot.c1_signal_ingestion.nfl_qb_features import NFLQBFeatureBuilder
from prediction_market_bot.pregame_shadow.contract import PregameForecast
from prediction_market_bot.pregame_shadow.nfl_forecaster import NFLScheduleIndex, parse_market_ticker
from prediction_market_bot.pregame_shadow.nfl_model import p_yes_for
from prediction_market_bot.pregame_shadow.nfl_qb_model import NFLQBChallengerModel


class NFLQBChallengerForecaster:
    sport = "NFLQB"

    def __init__(self, model: NFLQBChallengerModel, builder: NFLQBFeatureBuilder, schedule: NFLScheduleIndex) -> None:
        self.model, self.builder, self.schedule = model, builder, schedule
        self.audit: list[dict] = []

    def forecast(self, market_ticker: str, as_of_utc: datetime) -> Optional[PregameForecast]:
        p = parse_market_ticker(market_ticker)
        if p is None or p["market_type"] != "NFL_MONEYLINE":
            return None
        g = self.schedule.game(p["game_date"], p["home"], p["away"])
        if g is None:
            return None
        row = self.builder.row(g["home"], g["away"], as_of_utc, g["home_rest"], g["away_rest"])
        if row is None:
            return None
        p_yes = p_yes_for(self.model, row["features"], "NFL_MONEYLINE", subject_is_home=(p["subject"] == g["home"]))
        p_yes = min(max(p_yes, 1e-4), 1 - 1e-4)
        self.audit.append({"market_ticker": market_ticker, "as_of": as_of_utc.isoformat(),
                           "feature_row_sha256": row["sha256"], **row["audit"],
                           "qb_epa_h": row["features"]["qb_epa_h"], "qb_epa_a": row["features"]["qb_epa_a"]})
        return PregameForecast("NFLQB", "NFL_MONEYLINE", p["event_ticker"], market_ticker, p_yes,
                               as_of_utc, self.model.model_id, self.model.sha256, row["sha256"])
