"""EXP-040 forecaster: frozen minutes+injury challenger, KXNBAPTS strike 15 only. Same ticker parsing / player
resolution as EXP-039; returns None for any other strike. Per-row evidence (artifact sha, injury-snapshot slot,
minutes features) is kept in ``self.details[ticker]`` for the ledger."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Optional

from prediction_market_bot.c1_signal_ingestion.nba_injury_reports import InjurySnapshots
from prediction_market_bot.c1_signal_ingestion.nba_minutes_features import MinutesFeatureBuilder
from prediction_market_bot.c1_signal_ingestion.nba_player_features import PlayerFeatureBuilder
from prediction_market_bot.pregame_shadow.contract import PregameForecast
from prediction_market_bot.pregame_shadow.nba_forecaster import NBAScheduleIndex
from prediction_market_bot.pregame_shadow.nba_player_points_forecaster import (
    MARKET_TYPE, NBAPlayerResolver, parse_market_ticker)
from prediction_market_bot.pregame_shadow.nba_player_points_minutes_model import (
    REGISTERED_STRIKES, NBAPlayerPointsMinutesModel)

FROZEN_SHA256 = "c47cbac7378f160f2ed1cd31807663193cd4ce92df5ed00da6ed253ec3548527"   # EXP-040 pre-registration
SPORT = "NBAMIN"        # own ledger namespace (precedent: NFLQB); no new market type is created
DETAIL_KEYS = ("min10", "min30", "min_rank", "out_min", "out_fga", "own_quest", "own_prob", "inj_missing")


class NBAPlayerPointsMinutesForecaster:
    sport = SPORT

    def __init__(self, model: NBAPlayerPointsMinutesModel, builder: PlayerFeatureBuilder, schedule: NBAScheduleIndex,
                 season_for: Any, injuries: InjurySnapshots) -> None:
        if model.sha256 != FROZEN_SHA256:
            raise ValueError(f"EXP-040 artifact sha {model.sha256} != pre-registered {FROZEN_SHA256} -- refusing")
        self.model, self.schedule, self.injuries = model, schedule, injuries
        self.mfb = MinutesFeatureBuilder(builder)
        self.resolver = NBAPlayerResolver(builder.roster)
        self._season_for = season_for
        self._names = {p["player_id"]: p["name"] for ps in builder.roster.values() for p in ps}
        self.details: dict[str, dict] = {}

    def forecast(self, market_ticker: str, as_of_utc: datetime) -> Optional[PregameForecast]:
        p = parse_market_ticker(market_ticker)
        if p is None or p["points_threshold"] not in REGISTERED_STRIKES:
            return None
        g = self.schedule.game(p["game_date"], p["home"], p["away"])
        pid = self.resolver.resolve(p) if g else None
        if g is None or pid is None:
            return None
        opp = p["away"] if p["team"] == p["home"] else p["home"]
        snap, label, slot_utc = self.injuries.snapshot(g["tip_utc"], as_of_utc)
        f = self.mfb.row(pid, self._names[pid], p["team"], opp, p["team"] == g["home"], self._season_for(g),
                         g["tip_utc"], as_of_utc, snap)
        if f is None:
            return None
        p_yes = min(max(self.model.p_at_least(f, p["points_threshold"]), 1e-4), 1 - 1e-4)
        self.details[market_ticker] = {
            "experiment": "EXP-040", "artifact_sha256": self.model.sha256, "strike_points": p["points_threshold"],
            "injury_snapshot": label, "injury_snapshot_utc": slot_utc.isoformat() if slot_utc else None,
            "mean_points": round(self.model.mean_points(f), 4), **{k: f[k] for k in DETAIL_KEYS}}
        sha = hashlib.sha256(json.dumps(f, sort_keys=True).encode()).hexdigest()
        return PregameForecast("NBAMIN", MARKET_TYPE, p["event_ticker"], market_ticker, p_yes, as_of_utc,
                               self.model.model_id, self.model.sha256, sha)
