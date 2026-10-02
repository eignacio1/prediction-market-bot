"""Frozen NFL pregame predictive distribution (EXP-037 / T-608, D3).

ONE bivariate-Gaussian distribution over (margin = home - away, total) per game.
Every strike on every ladder (moneyline, spread, game total, team total) is read
off that single distribution, so the four families are coherent by construction
(P(spread>k) is monotone in k, team totals sum to the game total, etc.).

Model class: ridge-linear means for margin and total + probit-Platt recalibration
of the margin (affine map on the standardized margin). This is the documented
LR+Platt-equivalent: ADR-0004 names LR+Platt for a binary target; a ladder of
strikes needs a distribution, and the probit-Platt step is the same two-parameter
affine recalibration applied on the probit scale instead of the logit scale.
A PROPOSED ADR records the deviation. The artifact is frozen (no production
retraining, Hard Rule 4); the loader verifies its sha256.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Optional

from prediction_market_bot.c1_signal_ingestion.nfl_pregame_features import FEATURE_NAMES

# Historical NFL tie rate is ~0.4%; a tie pays $0.50 per side on the Kalshi moneyline.


def _phi(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def canonical_sha(artifact: dict) -> str:
    body = {k: v for k, v in artifact.items() if k != "sha256"}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


class NFLPregameModel:
    def __init__(self, artifact: dict) -> None:
        if canonical_sha(artifact) != artifact.get("sha256"):
            raise ValueError("model artifact sha256 mismatch -- refusing to load")
        self.a = artifact
        self.sha256 = artifact["sha256"]
        self.model_id = artifact["model_id"]

    @classmethod
    def load(cls, path: str | Path) -> "NFLPregameModel":
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
        mu_m = cal["a"] * mu_m_raw + cal["b"] * sm  # probit-Platt on the margin mean
        return {"mu_margin": mu_m, "mu_total": mu_t, "sigma_margin": sm,
                "sigma_total": st, "rho": rho}

    # ---- strike probabilities, all derived from one distribution ----------
    @staticmethod
    def p_moneyline_home(d: dict[str, float]) -> float:
        s = d["sigma_margin"]
        p_win = 1.0 - _phi((0.5 - d["mu_margin"]) / s)
        p_tie = _phi((0.5 - d["mu_margin"]) / s) - _phi((-0.5 - d["mu_margin"]) / s)
        return p_win + 0.5 * p_tie

    @staticmethod
    def p_spread_home_covers(d: dict[str, float], strike: float) -> float:
        """P(home wins by more than `strike`) (half-point strike)."""
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


def p_yes_for(model: NFLPregameModel, feats: dict[str, float], market_type: str,
              *, subject_is_home: Optional[bool] = None, strike: Optional[float] = None) -> float:
    """Dispatch used by the forecaster. ``market_type`` is a MarketType name."""
    d = model.distribution(feats)
    if market_type == "NFL_MONEYLINE":
        p_home = model.p_moneyline_home(d)
        return p_home if subject_is_home else 1.0 - p_home
    if market_type == "NFL_SPREAD":
        if subject_is_home:
            return model.p_spread_home_covers(d, strike)
        # away wins by more than strike  <=>  margin < -strike
        return _phi((-strike - d["mu_margin"]) / d["sigma_margin"])
    if market_type == "NFL_GAME_TOTAL":
        return model.p_total_over(d, strike)
    if market_type == "NFL_TEAM_TOTAL":
        return model.p_team_total_over(d, bool(subject_is_home), strike)
    raise ValueError(f"unsupported market_type {market_type}")
