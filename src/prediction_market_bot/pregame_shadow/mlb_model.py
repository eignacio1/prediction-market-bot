"""Frozen MLB pregame predictive distribution (EXP-037 / T-608, MLB).

Mirrors nfl_model.py: ONE bivariate-Gaussian over (margin = home - away runs, total runs) per game; the
moneyline, run line, game total and team total strikes are all read off that single distribution, so the
four ladders are coherent by construction. Ridge-linear means + probit-Platt on the margin; frozen artifact,
sha256 verified at load (Hard Rule 4: no production retraining).

MLB has no ties (extra innings): the moneyline is P(margin > 0) with the Gaussian mass on |margin| < 0.5
split evenly between sides. Known weakness: a continuous Gaussian over integer run margins.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Optional

from prediction_market_bot.c1_signal_ingestion.mlb_game_pregame_features import FEATURE_NAMES


def _phi(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def canonical_sha(artifact: dict) -> str:
    body = {k: v for k, v in artifact.items() if k != "sha256"}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


class MLBPregameModel:
    def __init__(self, artifact: dict) -> None:
        if canonical_sha(artifact) != artifact.get("sha256"):
            raise ValueError("model artifact sha256 mismatch -- refusing to load")
        self.a = artifact
        self.sha256 = artifact["sha256"]
        self.model_id = artifact["model_id"]

    @classmethod
    def load(cls, path: str | Path) -> "MLBPregameModel":
        return cls(json.loads(Path(path).read_text()))

    def _lin(self, key: str, feats: dict[str, float]) -> float:
        m = self.a[key]
        z = [(feats[n] - mu) / sd for n, mu, sd in zip(FEATURE_NAMES, m["mean"], m["std"])]
        return m["intercept"] + sum(c * x for c, x in zip(m["coef"], z))

    def distribution(self, feats: dict[str, float]) -> dict[str, float]:
        mu_m_raw = self._lin("margin", feats)
        mu_t = self._lin("total", feats)
        sm, st, rho = self.a["sigma_margin"], self.a["sigma_total"], self.a["rho"]
        cal = self.a["platt"]
        mu_m = cal["a"] * mu_m_raw + cal["b"] * sm
        return {"mu_margin": mu_m, "mu_total": mu_t, "sigma_margin": sm, "sigma_total": st, "rho": rho}

    @staticmethod
    def p_moneyline_home(d: dict[str, float]) -> float:
        return 1.0 - _phi((0.0 - d["mu_margin"]) / d["sigma_margin"])

    @staticmethod
    def p_runline_home_covers(d: dict[str, float], strike: float) -> float:
        """P(home wins by more than `strike`) (half-run strike)."""
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


def p_yes_for(model: MLBPregameModel, feats: dict[str, float], market_type: str, *,
              subject_is_home: Optional[bool] = None, strike: Optional[float] = None) -> float:
    d = model.distribution(feats)
    if market_type == "MLB_MONEYLINE":
        p_home = model.p_moneyline_home(d)
        return p_home if subject_is_home else 1.0 - p_home
    if market_type == "MLB_RUN_LINE":
        if subject_is_home:
            return model.p_runline_home_covers(d, strike)
        return _phi((-strike - d["mu_margin"]) / d["sigma_margin"])
    if market_type == "MLB_GAME_TOTAL":
        return model.p_total_over(d, strike)
    if market_type == "MLB_TEAM_TOTAL":
        return model.p_team_total_over(d, bool(subject_is_home), strike)
    raise ValueError(f"unsupported market_type {market_type}")
