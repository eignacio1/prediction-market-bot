"""H-DEPTH-PAM-5 forward arm (W130.4): EXP-047-S unchanged, plus the player archetype x opponent archetype cell for every
row, written to ``reasons``. p_yes is S's probability, bit for bit: the matchup-cross calibration is applied at JUDGING time
from a frozen factor table committed before the first 2026-27 row (12_EXPLORATORY/pam_archetype/PREREG.md section 4), so
this arm can never drift from S and places no order. EVALUATE-AND-LOG only. ``lookup(name, team, game_date)`` returns
(top archetype id or None, mixture weight of that archetype); it reads PIT records with ``known_at`` <= game_date."""
from __future__ import annotations

import dataclasses
import hashlib
import json
from datetime import datetime
from typing import Callable, Optional, Tuple

from prediction_market_bot.pregame_shadow import nba_engine_props_forecaster as F
from prediction_market_bot.pregame_shadow import nba_engine_props_shrunk_forecaster as SH
from prediction_market_bot.pregame_shadow.contract import PregameForecast

MODEL_ID = "nba_engine_v2_props_pam5_archetype_cell_w130_4"
ANCHOR = "PRF-9"
ANCHOR_MIN_W = 0.5
MODEL_SHA256 = hashlib.sha256(json.dumps(dict(base=SH.MODEL_SHA256, rule="s_prob_plus_archetype_cell", anchor=ANCHOR,
                                              anchor_w=ANCHOR_MIN_W), sort_keys=True).encode()).hexdigest()
Lookup = Callable[[str, str, str], Tuple[Optional[str], float]]


class NBAEnginePropsArchetype(SH.NBAEnginePropsShrunk):
    def __init__(self, *a, lookup: Optional[Lookup] = None, **k) -> None:
        super().__init__(*a, **k)
        self.lookup = lookup

    def cell(self, p: dict, name: str) -> Optional[tuple]:
        if self.lookup is None:
            return None
        arch, w = self.lookup(name, p["team"], p["game_date"])
        opp = p["away"] if p["team"] == p["home"] else p["home"]
        anchor = any((lambda r: r[0] == ANCHOR and r[1] >= ANCHOR_MIN_W)(self.lookup(n, opp, p["game_date"]))
                     for _, n, _ in self.roster(opp, p["game_date"]))
        return (("player_arch", arch or "unclassified", round(w, 4)), ("opp_anchor", "anchor" if anchor else "none", 0.0))

    def forecast(self, market_ticker: str, as_of_utc: datetime) -> Optional[PregameForecast]:
        fc = super().forecast(market_ticker, as_of_utc)
        if fc is None:
            return None
        p = F.parse_market_ticker(market_ticker)
        ros = self.roster(p["team"], p["game_date"])
        hits = [n for _, n, _ in ros if F._initial(n) == p["initial"] and F._norm_surname(n) == p["surname"]]
        return dataclasses.replace(fc, model_id=MODEL_ID, model_sha256=MODEL_SHA256,
                                   reasons=self.cell(p, hits[0]) if len(hits) == 1 else None)
