"""W127.2: the MLB engine's joint board behind the shadow ``PregameForecaster`` interface (ADR-0073, ADR-0077).

Applies: one priced board per game (``joint_board.price_games``: the 9-inning sim, one draw set for the whole board)
read out at the Kalshi rung a ticker names. The price is a layer-1 INPUT to the tree, never the bet; this class
only answers ``forecast()`` and has no order path.
Does not apply: pricing itself (the board is precomputed offline by the caller, so no network and no store here),
the KXMLBHIT prop ladder (``joint_board`` prices it; no registered shadow cell logs it yet), same-game parlays.
Point-in-time: ``forecast`` only looks up a board its caller built from information at or before ``as_of_utc``.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Dict, Optional, Tuple

from prediction_market_bot.pregame_shadow.contract import PregameForecast
from prediction_market_bot.pregame_shadow.mlb_forecaster import ET, parse_market_ticker

MODEL_ID = "mlb_engine_joint_board_v0"
BoardKey = Tuple[str, str, str]          # (home code, away code, ET game date ISO)


def _col(p: dict) -> Optional[tuple]:
    """(column, flip) for the rung a parsed ticker names; flip = take 1 - column."""
    mt, k = p["market_type"], None if p["strike"] is None else int(round(p["strike"] + 0.5))
    side = None if p["subject"] is None else ("home" if p["subject"] == p["home"] else "away")
    if mt == "MLB_MONEYLINE":
        return "p_home_ml", side == "away"
    if mt == "MLB_GAME_TOTAL":
        return f"ge_total_{k}", False
    if mt == "MLB_RUN_LINE":
        return f"{side}_by_ge_{k}", False
    if mt == "MLB_TEAM_TOTAL":
        return f"{side}_runs_ge_{k}", False
    return None


class MLBEngineForecaster:
    sport = "MLB"

    def __init__(self, board: Dict[BoardKey, Dict[str, float]], n_draws: int = 4000) -> None:
        self.board = board
        self.model_id = f"{MODEL_ID}_n{n_draws}"
        self.sha256 = hashlib.sha256(self.model_id.encode()).hexdigest()

    def forecast(self, market_ticker: str, as_of_utc: datetime) -> Optional[PregameForecast]:
        p = parse_market_ticker(market_ticker)
        if p is None:
            return None
        day = p["start_utc"].astimezone(ET).date().isoformat()
        prices = self.board.get((p["home"], p["away"], day))
        c = _col(p)
        if prices is None or c is None or c[0] not in prices:
            return None                                   # no board for this game, or a rung off the priced ladder
        v = prices[c[0]]
        p_yes = min(max(1.0 - v if c[1] else v, 1e-4), 1 - 1e-4)
        row = hashlib.sha256(json.dumps({c[0]: prices[c[0]], "k": [p["home"], p["away"], day]},
                                        sort_keys=True).encode()).hexdigest()
        return PregameForecast(self.sport, p["market_type"], p["event_ticker"], market_ticker, p_yes,
                               as_of_utc, self.model_id, self.sha256, row, None)
