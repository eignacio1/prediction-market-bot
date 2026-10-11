"""Frozen NFL QB-shrunk challenger model (W65.3, pre-registration ACCEPTED 2026-10-10).

Same recipe as the frozen EXP-037 margin model (ridge lambda=100 on home margin, probit-Platt on margin/sigma),
13 features instead of 11. Moneyline only (the only cell the pre-registration covers). The artifact is frozen and
its sha256 is verified on load (Hard Rule 4: no production retraining).
"""
from __future__ import annotations

from prediction_market_bot.pregame_shadow.nfl_model import NFLPregameModel


class NFLQBChallengerModel(NFLPregameModel):
    def _lin(self, key: str, feats: dict[str, float]) -> float:
        m = self.a[key]
        z = [(feats[n] - mu) / sd for n, mu, sd in zip(self.a["feature_names"], m["mean"], m["std"])]
        return m["intercept"] + sum(c * x for c, x in zip(m["coef"], z))

    def distribution(self, feats: dict[str, float]) -> dict[str, float]:
        sm = self.a["sigma_margin"]
        cal = self.a["platt"]
        return {"mu_margin": cal["a"] * self._lin("margin", feats) + cal["b"] * sm, "sigma_margin": sm}


