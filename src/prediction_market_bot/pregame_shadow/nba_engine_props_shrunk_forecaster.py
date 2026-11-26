"""EXP-047-S (W129.2): EXP-047-C2 with its per-player base mean replaced by shrunk per-minute rate x shrunk minutes
(H-DEPTH-PAM-3 licence; 12_EXPLORATORY/nba_props_shrunk/PREREG.md). The usage shift (``c2_means``, frozen lambdas), the engine draws and
the strike-probability code are C2's, unchanged. A player with no prior-game rows on this team prices from the same raw mean as C2.
``prev`` = {normalised name: previous-season totals}, ``league`` = ``league_band_rates`` of that season. EVALUATE-AND-LOG only."""
from __future__ import annotations

import dataclasses
import hashlib
import json
from datetime import datetime
from typing import Callable, Collection, Mapping, Optional

from prediction_market_bot.c1_signal_ingestion.nba_injury_reports import norm_name
from prediction_market_bot.nba_engine import shrunk_means as S
from prediction_market_bot.nba_engine.player_means import c2_means
from prediction_market_bot.pregame_shadow import nba_engine_props_c2_forecaster as C2
from prediction_market_bot.pregame_shadow import nba_engine_props_forecaster as F
from prediction_market_bot.pregame_shadow.contract import PregameForecast

MODEL_ID = "nba_engine_v2_props_shrunk_w129_2"
_S = dict(base=C2._C2, rule="shrunk_rate_x_shrunk_minutes_then_c2_shift", k=S.K, k_min=S.K_MIN, pseudo=S.PSEUDO_LEAGUE_MIN, cuts=S.BAND_CUTS)
MODEL_SHA256 = hashlib.sha256(json.dumps(_S, sort_keys=True, default=list).encode()).hexdigest()


class NBAEnginePropsShrunk(C2.NBAEnginePropsC2):
    def __init__(self, games: dict, player_rows: dict, tips, out_lookup: Callable[[dict, datetime], Collection[str]],
                 att_rows: Optional[dict] = None, prev: Optional[Mapping[str, Mapping[str, float]]] = None,
                 league: Optional[Mapping[int, Mapping[str, float]]] = None, lam: Optional[Mapping[str, float]] = None,
                 k: Optional[Mapping[str, float]] = None, k_min: Optional[float] = None) -> None:
        super().__init__(games, player_rows, tips, out_lookup, att_rows, lam)
        self.prev, self.league = dict(prev or {}), dict(league or {})
        self.k, self.k_min = dict(S.K if k is None else k), (S.K_MIN if k_min is None else k_min)   # overridden only by the decomposition arms

    def _shrunk_base(self, ros: list, p: dict) -> dict:
        raw = {s: [r[2][s] for r in ros] for s in F.P.STATS}
        out = {s: list(v) for s, v in raw.items()}
        for i, (_, name, _) in enumerate(ros):
            rows = [r for d, r in self.pl.get((p.get("team"), name), ()) if d < p.get("game_date", "9999")]
            mu = S.shrunk_mu(rows, self.prev.get(norm_name(name)), self.league, self.k, self.k_min)
            if mu is not None:
                for s in F.P.STATS:
                    out[s][i] = mu[s]
        return out

    def _mu(self, ros: list, p: dict) -> dict:
        base = self._shrunk_base(ros, p)
        pp = [0.0 if norm_name(n) in self._out else 1.0 for _, n, _ in ros]
        if all(x == 1.0 for x in pp):
            return base
        att = [self._prior_att(p.get("team"), n, p.get("game_date", "9999")) for _, n, _ in ros]
        return c2_means(base, pp, att, self.lam)

    def forecast(self, market_ticker: str, as_of_utc: datetime) -> Optional[PregameForecast]:
        fc = super().forecast(market_ticker, as_of_utc)
        if fc is None:
            return None
        return dataclasses.replace(fc, model_id=MODEL_ID, model_sha256=MODEL_SHA256)
