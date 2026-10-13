"""Frozen EXP-040 challenger: EXP-039's NB/Platt recipe over the ``minutes_inj`` feature set (strike 15 registered).
Feature names come from the artifact (not the module constant); sha256 is verified on load."""
from __future__ import annotations

import json
import math
from pathlib import Path

from prediction_market_bot.pregame_shadow.nba_player_points_model import MEAN_FLOOR, logit, nb_sf
from prediction_market_bot.pregame_shadow.nfl_model import canonical_sha

REGISTERED_STRIKES = (15,)


class NBAPlayerPointsMinutesModel:
    def __init__(self, artifact: dict) -> None:
        if canonical_sha(artifact) != artifact.get("sha256"):
            raise ValueError("model artifact sha256 mismatch -- refusing to load")
        self.a, self.sha256, self.model_id = artifact, artifact["sha256"], artifact["model_id"]
        self.names = artifact["feature_names"]

    @classmethod
    def load(cls, path: str | Path) -> "NBAPlayerPointsMinutesModel":
        return cls(json.loads(Path(path).read_text()))

    def mean_points(self, feats: dict[str, float]) -> float:
        m = self.a["mean_model"]
        z = [(feats[n] - mu) / sd for n, mu, sd in zip(self.names, m["mean"], m["std"])]
        return max(m["intercept"] + sum(c * x for c, x in zip(m["coef"], z)), MEAN_FLOOR)

    def p_at_least(self, feats: dict[str, float], strike_points: int) -> float:
        if strike_points not in REGISTERED_STRIKES:
            raise ValueError(f"EXP-040 registers strike {REGISTERED_STRIKES} only; got {strike_points}")
        raw = nb_sf(strike_points, self.mean_points(feats), self.a["dispersion_r"])
        pl = self.a["platt"]
        return 1.0 / (1.0 + math.exp(-(pl["a"] * logit(raw) + pl["b"])))
