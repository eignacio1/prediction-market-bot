"""
C3: Scoring Distribution Model — Strategy I (Poisson/NB)
=========================================================
Module:   c3_forecasting.scoring_distribution
Phase:    Phase 7 (Strategy I — T-076, EXP-013)
Purpose:  Fit a per-player scoring distribution (Negative Binomial or Poisson)
          from training data. Enables pricing any threshold line from one model
          fit — vs. the current LR approach which prices only one specific line.

Core advantage:
  Current ModelForecaster (Strategy A): one probability per one Kalshi line
  ScoringDistributionModel (Strategy I): one λ estimate → P(X≥n) for ANY n

This multiplies addressable markets without new data or retraining:
  Any new player prop line Kalshi introduces is immediately priceable.

Distribution selection:
  NBA scoring has overdispersion (var > mean). If var(pts) > mean(pts),
  Negative Binomial is used. Otherwise falls back to Poisson.

NB parameterization (method of moments):
  μ = mean(pts)
  σ² = var(pts)
  r = μ² / (σ² - μ)   [shape; r → ∞ = Poisson limit]
  p = r / (r + μ)      [success probability in NB PMF]

  PMF: P(X=k) = Γ(k+r) / (k! Γ(r)) × p^r × (1-p)^k
  CDF: scipy.stats.nbinom.cdf(n-1, r, p)
  P(X≥n) = 1 - CDF(n-1, r, p)

Calibration:
  Raw NB probabilities are not Platt-scaled. They represent parametric
  distribution fits and may be better or worse calibrated than LR+Platt
  depending on player-level distribution shapes. EXP-013 evaluates this.

References:
  STRATEGY_OVERVIEW.md Strategy I
  EXP-013 experiment runner: run_exp013.py
  ADR-0004 (model class confirmation — LR is the current production model;
  ScoringDistributionModel is an experimental supplement, not a replacement)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy.stats import nbinom, poisson


# ---------------------------------------------------------------------------
# Per-player parameters
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PlayerDistribution:
    """
    Fitted scoring distribution parameters for one player.

    Fields
    ------
    player_id : int
    dist_type : str
        'nb' (Negative Binomial) or 'poisson' (fallback when var ≤ mean).
    mu : float
        Mean points (λ for Poisson; r(1-p)/p for NB).
    r : float | None
        NB shape parameter. None when dist_type == 'poisson'.
    p : float | None
        NB success probability. None when dist_type == 'poisson'.
    n_samples : int
        Number of training game observations used to fit.
    """
    player_id: int
    dist_type: str
    mu: float
    r: Optional[float]
    p: Optional[float]
    n_samples: int


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


# Minimum training games required to fit a reliable distribution
MIN_FIT_SAMPLES: int = 20

# Minimum dispersion ratio (var/mean) to use NB instead of Poisson
# If var/mean < this, fall back to Poisson (not meaningfully overdispersed)
MIN_OVERDISPERSION_RATIO: float = 1.05


class ScoringDistributionModel:
    """
    Per-player Negative Binomial scoring distribution for threshold pricing.

    Fits one distribution per player from training game-level pts values.
    Prices any threshold line via the survival function: P(X ≥ n).

    Usage::

        model = ScoringDistributionModel()

        # Fit from training data:
        #   pts_by_player = {player_id: np.array([25, 31, 18, ...])}
        model.fit(pts_by_player)

        # Price any threshold:
        p = model.predict_threshold_prob(player_id=203507, threshold=25.0)
        # → calibrated P(player scores ≥ 25)

        # Price multiple lines at once:
        probs = model.price_all_lines(player_id=203507, thresholds=[20, 22, 25, 28, 30])

    Temporal integrity (TI-01):
        pts_by_player must contain ONLY training set observations.
        This model must not be retrained in production (frozen model policy).
    """

    def __init__(self, min_samples: int = MIN_FIT_SAMPLES) -> None:
        self._min_samples = min_samples
        self._distributions: dict[int, PlayerDistribution] = {}
        self._is_fitted: bool = False

    # ------------------------------------------------------------------
    # Fitting
    # ------------------------------------------------------------------

    def fit(self, pts_by_player: dict[int, np.ndarray]) -> "ScoringDistributionModel":
        """
        Fit a scoring distribution for each player.

        Parameters
        ----------
        pts_by_player:
            Dict mapping player_id → 1D array of points scored (training set only).
            Values must be non-negative integers or floats.
            Players with < min_samples observations are skipped.

        Returns
        -------
        self (fluent interface)
        """
        self._distributions = {}

        for player_id, pts_array in pts_by_player.items():
            pts = np.asarray(pts_array, dtype=float)
            pts = pts[~np.isnan(pts)]

            if len(pts) < self._min_samples:
                continue

            dist = self._fit_player(player_id, pts)
            if dist is not None:
                self._distributions[player_id] = dist

        self._is_fitted = True
        return self

    def _fit_player(
        self, player_id: int, pts: np.ndarray
    ) -> Optional[PlayerDistribution]:
        """Fit a single player's distribution using method of moments."""
        mu = float(np.mean(pts))
        var = float(np.var(pts, ddof=1)) if len(pts) > 1 else mu

        if mu <= 0:
            return None

        # Use NB if overdispersed (var > mean × threshold); else Poisson
        if var > mu * MIN_OVERDISPERSION_RATIO:
            excess = var - mu
            r = mu**2 / excess
            p = r / (r + mu)
            r = max(r, 0.01)  # numerical stability floor
            p = float(np.clip(p, 1e-6, 1 - 1e-6))
            return PlayerDistribution(
                player_id=player_id,
                dist_type="nb",
                mu=mu,
                r=r,
                p=p,
                n_samples=len(pts),
            )
        else:
            return PlayerDistribution(
                player_id=player_id,
                dist_type="poisson",
                mu=mu,
                r=None,
                p=None,
                n_samples=len(pts),
            )

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def predict_threshold_prob(
        self,
        player_id: int,
        threshold: float,
    ) -> Optional[float]:
        """
        Return P(player scores ≥ threshold) using the fitted distribution.

        Parameters
        ----------
        player_id:
            NBA player ID. Must have been fitted.
        threshold:
            Points threshold (e.g. 25.0 → P(X ≥ 25)).
            Non-integer thresholds are ceiled to the nearest integer.
            (Kalshi markets are typically integer + 0.5; ceil handles this.)

        Returns
        -------
        float | None
            Probability in [0, 1]. None if player not fitted.
        """
        if not self._is_fitted:
            raise RuntimeError("Model not fitted — call fit() first")

        dist = self._distributions.get(player_id)
        if dist is None:
            return None

        # Kalshi uses integer + 0.5 lines (e.g. ≥ 25.5 pts).
        # Treat threshold=25.5 as "must score at least 26 whole points."
        n = int(np.ceil(threshold))

        return self._survival_prob(dist, n)

    def price_all_lines(
        self,
        player_id: int,
        thresholds: list[float],
    ) -> list[Optional[float]]:
        """
        Price multiple threshold lines for one player from a single model fit.

        This is the key advantage over ModelForecaster: one distribution fit
        covers all possible Kalshi lines for the player — no retraining needed
        when Kalshi introduces a new threshold.

        Parameters
        ----------
        player_id:
            NBA player ID.
        thresholds:
            List of point thresholds to price (e.g. [18, 20, 22, 25, 28, 30]).

        Returns
        -------
        list[float | None]
            One probability per threshold, in the same order.
        """
        return [self.predict_threshold_prob(player_id, t) for t in thresholds]

    def get_fitted_player_ids(self) -> list[int]:
        """Return list of player IDs with fitted distributions."""
        return list(self._distributions.keys())

    def get_distribution(self, player_id: int) -> Optional[PlayerDistribution]:
        """Return the fitted PlayerDistribution for a player, or None."""
        return self._distributions.get(player_id)

    @property
    def n_fitted_players(self) -> int:
        return len(self._distributions)

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _survival_prob(dist: PlayerDistribution, n: int) -> float:
        """P(X ≥ n) = 1 - P(X ≤ n-1) using the fitted distribution."""
        if n <= 0:
            return 1.0

        if dist.dist_type == "poisson":
            return float(1.0 - poisson.cdf(n - 1, dist.mu))
        else:
            # nbinom.cdf uses: P(X ≤ k | r, p) in scipy's parameterization
            # scipy.stats.nbinom(n, p) where n=r, p=p
            return float(1.0 - nbinom.cdf(n - 1, dist.r, dist.p))
