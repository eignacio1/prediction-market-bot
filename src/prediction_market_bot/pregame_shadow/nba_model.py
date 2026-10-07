"""Frozen NBA pregame predictive distribution (EXP-038). Same model class as NFL (ridge means + probit-Platt
on the margin, one bivariate Gaussian per game; ADR-0070 deviation, NBA scope PENDING operator decision).
NBA has no ties and no draws: moneyline is P(margin > 0)."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Optional

from prediction_market_bot.c1_signal_ingestion.nba_pregame_features import FEATURE_NAMES
from prediction_market_bot.pregame_shadow.nfl_model import _phi, canonical_sha


class NBAPregameModel:
    def __init__(self, artifact: dict) -> None:
        if canonical_sha(artifact) != artifact.get("sha256"):
            raise ValueError("model artifact sha256 mismatch -- refusing to load")
        if artifact["feature_names"] != FEATURE_NAMES:
            raise ValueError("artifact feature_names differ from code FEATURE_NAMES")
        self.a, self.sha256, self.model_id = artifact, artifact["sha256"], artifact["model_id"]

    @classmethod
    def load(cls, path: str | Path) -> "NBAPregameModel":
        return cls(json.loads(Path(path).read_text()))

    def _lin(self, key: str, feats: dict[str, float]) -> float:
        m = self.a[key]
        z = [(feats[n] - mu) / sd for n, mu, sd in zip(FEATURE_NAMES, m["mean"], m["std"])]
        return m["intercept"] + sum(c * x for c, x in zip(m["coef"], z))

    def distribution(self, feats: dict[str, float]) -> dict[str, float]:
        sm, st, rho = self.a["sigma_margin"], self.a["sigma_total"], self.a["rho"]
        cal = self.a["platt"]
        return {"mu_margin": cal["a"] * self._lin("margin", feats) + cal["b"] * sm,
                "mu_total": self._lin("total", feats), "sigma_margin": sm, "sigma_total": st, "rho": rho}

    @staticmethod
    def p_home_win(d: dict[str, float]) -> float:
        return 1.0 - _phi((0.5 - d["mu_margin"]) / d["sigma_margin"])  # integer margin, no ties: P(m >= 1)

    @staticmethod
    def p_home_covers(d: dict[str, float], strike: float) -> float:
        return 1.0 - _phi((strike - d["mu_margin"]) / d["sigma_margin"])

    @staticmethod
    def p_total_over(d: dict[str, float], strike: float) -> float:
        return 1.0 - _phi((strike - d["mu_total"]) / d["sigma_total"])

    @staticmethod
    def p_team_total_over(d: dict[str, float], is_home: bool, strike: float) -> float:
        sgn = 1.0 if is_home else -1.0
        mean = (d["mu_total"] + sgn * d["mu_margin"]) / 2.0
        var = (d["sigma_total"] ** 2 + d["sigma_margin"] ** 2
               + sgn * 2.0 * d["rho"] * d["sigma_total"] * d["sigma_margin"]) / 4.0
        return 1.0 - _phi((strike - mean) / math.sqrt(var))


def p_yes_for(model: NBAPregameModel, feats: dict[str, float], market_type: str,
              *, subject_is_home: Optional[bool] = None, strike: Optional[float] = None) -> float:
    d = model.distribution(feats)
    if market_type == "NBA_MONEYLINE":
        p = model.p_home_win(d)
        return p if subject_is_home else 1.0 - p
    if market_type == "NBA_SPREAD":
        if subject_is_home:
            return model.p_home_covers(d, strike)
        return _phi((-strike - d["mu_margin"]) / d["sigma_margin"])
    if market_type == "NBA_GAME_TOTAL":
        return model.p_total_over(d, strike)
    if market_type == "NBA_TEAM_TOTAL":
        return model.p_team_total_over(d, bool(subject_is_home), strike)
    raise ValueError(f"unsupported market_type {market_type}")
