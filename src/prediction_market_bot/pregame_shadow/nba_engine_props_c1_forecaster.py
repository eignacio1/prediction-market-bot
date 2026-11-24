"""EXP-047-C1 (W125.4): EXP-047 with the lineup-cross usage shift. Same inputs, same seeds, same draws; the only change is that
players listed Out at the pre-tip cutoff have their expected stats absorbed by teammates through the shared rule
(``nba_engine.usage_redistribution``, NBA-10's consumer on the props side). EVALUATE-AND-LOG only. Frozen constants are hashed
into its own ``model_sha256``; with nobody Out it prices exactly as EXP-047 does (test)."""
from __future__ import annotations

import dataclasses
import hashlib
import json
from datetime import datetime
from typing import Callable, Collection, Optional

from prediction_market_bot.c1_signal_ingestion.nba_injury_reports import norm_name
from prediction_market_bot.nba_engine import props as P
from prediction_market_bot.nba_engine.usage_redistribution import redistribute
from prediction_market_bot.pregame_shadow import nba_engine_props_forecaster as F
from prediction_market_bot.pregame_shadow.contract import PregameForecast

MODEL_ID = "nba_engine_v2_props_c1_w125_4"
_C1 = dict(base=F._CONSTANTS, points_rest=F.POINTS_REST, rule="proportional_absorption", out_p=0.0, other_p=1.0)
MODEL_SHA256 = hashlib.sha256(json.dumps(_C1, sort_keys=True).encode()).hexdigest()


class NBAEnginePropsC1(F.NBAEngineProps):
    """``out_lookup(parsed_ticker, as_of_utc) -> collection of normalised names listed Out`` (injected; None/empty = nobody)."""

    def __init__(self, games: dict, player_rows: dict, tips, out_lookup: Callable[[dict, datetime], Collection[str]]) -> None:
        super().__init__(games, player_rows, tips)
        self.out_lookup = out_lookup
        self._out: frozenset = frozenset()

    def _mu(self, ros: list, p: dict) -> dict:
        base = super()._mu(ros, p)
        out = self._out
        pp = [0.0 if norm_name(n) in out else 1.0 for _, n, _ in ros]
        if all(x == 1.0 for x in pp):
            return base
        return {s: redistribute(base[s], pp) for s in P.STATS}

    def forecast(self, market_ticker: str, as_of_utc: datetime) -> Optional[PregameForecast]:
        p = F.parse_market_ticker(market_ticker)
        if p is None:
            return None
        self._out = frozenset(norm_name(x) for x in (self.out_lookup(p, as_of_utc) or ()))
        key_out = tuple(sorted(self._out))
        self._tag = key_out            # the split cache is per (game, team, stat, Out set)
        fc = super().forecast(market_ticker, as_of_utc)
        if fc is None:
            return None
        row = hashlib.sha256((fc.feature_row_sha256 + "|" + ",".join(key_out)).encode()).hexdigest()
        return dataclasses.replace(fc, model_id=MODEL_ID, model_sha256=MODEL_SHA256, feature_row_sha256=row)
