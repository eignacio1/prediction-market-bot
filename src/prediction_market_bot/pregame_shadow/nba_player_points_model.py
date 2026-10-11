"""Frozen NBA player-points distribution (EXP-039): ridge-linear mean -> one negative binomial per player-game
(fixed dispersion) -> every strike read off that one distribution -> one Platt (a, b) on the logit.
Strikes are therefore coherent (P(pts >= k) is non-increasing in k before and after the monotone Platt map)."""
from __future__ import annotations

import json
import math
from pathlib import Path

from prediction_market_bot.c1_signal_ingestion.nba_player_features import FEATURE_NAMES
from prediction_market_bot.pregame_shadow.nfl_model import canonical_sha

MEAN_FLOOR = 0.5   # ridge mean can go below zero for end-of-bench players; the NB needs mu > 0


def nb_sf(k: int, mu: float, r: float) -> float:
    """P(Y >= k) for NB with mean mu, size r (Var = mu + mu^2/r)."""
    if k <= 0:
        return 1.0
    p = r / (r + mu)
    lp, lq = math.log(p), math.log1p(-p)
    cdf = 0.0
    for y in range(k):
        cdf += math.exp(math.lgamma(y + r) - math.lgamma(r) - math.lgamma(y + 1) + r * lp + y * lq)
    return min(max(1.0 - cdf, 0.0), 1.0)


def logit(p: float) -> float:
    p = min(max(p, 1e-9), 1 - 1e-9)
    return math.log(p / (1 - p))


class NBAPlayerPointsModel:
    def __init__(self, artifact: dict) -> None:
        if canonical_sha(artifact) != artifact.get("sha256"):
            raise ValueError("model artifact sha256 mismatch -- refusing to load")
        if artifact["feature_names"] != FEATURE_NAMES:
            raise ValueError("artifact feature_names differ from code FEATURE_NAMES")
        self.a, self.sha256, self.model_id = artifact, artifact["sha256"], artifact["model_id"]

    @classmethod
    def load(cls, path: str | Path) -> "NBAPlayerPointsModel":
        return cls(json.loads(Path(path).read_text()))

    def mean_points(self, feats: dict[str, float]) -> float:
        m = self.a["mean_model"]
        z = [(feats[n] - mu) / sd for n, mu, sd in zip(FEATURE_NAMES, m["mean"], m["std"])]
        return max(m["intercept"] + sum(c * x for c, x in zip(m["coef"], z)), MEAN_FLOOR)

    def raw_p_at_least(self, feats: dict[str, float], strike_points: int) -> float:
        return nb_sf(strike_points, self.mean_points(feats), self.a["dispersion_r"])

    def p_at_least(self, feats: dict[str, float], strike_points: int) -> float:
        raw = self.raw_p_at_least(feats, strike_points)
        pl = self.a["platt"]
        z = pl["a"] * logit(raw) + pl["b"]
        return 1.0 / (1.0 + math.exp(-z))
