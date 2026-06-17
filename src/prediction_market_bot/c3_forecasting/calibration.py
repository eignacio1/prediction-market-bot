"""C3: Probability Calibration Layer — temperature scaling (ADR-0027 / GG-037).

Purpose
-------
The production T1 betting probability is a *pure Poisson* survival probability
(`game_state_model._poisson_cdf` on the opponent-adjusted last-10 mean). Poisson
assumes variance == mean, but NBA player scoring is over-dispersed
(var > mean — see `scoring_distribution.py`). A Poisson on the mean therefore
produces tail probabilities that are too extreme, i.e. systematic
*overconfidence*. The 158-bet NBA Finals dataset confirmed this empirically
(GG-037): directional Brier 0.2308, mean stated confidence 0.799 vs realized
0.601 — ~20 points overconfident, worst in the high-confidence buckets.

This module applies **temperature scaling** to the raw model probability:

    p_cal = sigmoid( logit(p) / T )

* T == 1.0  -> identity (no change).
* T  > 1.0  -> shrink toward 0.5 (reduce confidence). This is what an
  over-dispersed regime needs.
* T  < 1.0  -> sharpen (increase confidence) — not expected here.

Temperature scaling is monotone and frame-symmetric: because
logit(1-p) == -logit(p) and sigmoid(-x) == 1 - sigmoid(x), calibrating the
YES-frame probability and then taking the directional NO probability gives the
same result as calibrating the directional probability. So callers may apply it
to the raw YES-frame `p_threshold` directly.

Per-sport temperatures
----------------------
Calibration is regime-specific. A temperature fit on NBA Finals data must NOT
silently transfer to MLB or to NBA regular season. The registry is keyed by
sport and any sport without resolved data uses `DEFAULT_TEMPERATURE = 1.0`
(identity) — launching a new sport can never inherit another sport's shrink by
accident. Re-derive per sport from resolved outcomes via
`scripts/derive_calibration.py`.

IMPORTANT (GG-037 / GG-004): recalibration corrects *overconfidence*; it does
NOT create alpha. The Finals analysis showed the model's residual edge vs the
Kalshi price remains anti-predictive even after calibration. Calibration makes
the bot honest (and therefore decline most bets); it does not make this strategy
profitable. The commercial question stays open (GG-004) pending EXP-017 at scale.
"""

from __future__ import annotations

import math

# Identity temperature — used for any sport without resolved calibration data.
# Chosen so that adding a sport is fail-safe: no calibration data => no shrink.
DEFAULT_TEMPERATURE: float = 1.0

# Per-sport temperature registry. p_cal = sigmoid(logit(p)/T).
#
# nba: 2.05 — provisional. Derived from the 158-bet NBA Finals paper dataset
#      (ADR-0027). This is the OUT-OF-SAMPLE estimate (fit on G2-G4, validated on
#      G5: Brier 0.315 -> 0.282, mean confidence 0.807 -> 0.731 vs realized
#      0.537). The full-sample in-sample optimum was T=3.10; the more
#      conservative OOS-validated 2.05 is used. Single-series sample — MUST be
#      re-derived on NBA regular season (GG-037).
# mlb: 1.0 — identity. No MLB resolved data exists yet; toggled once the MLB
#      dark-period dataset is available (per DS directive 2026-06-16).
CALIBRATION_TEMPERATURE: dict[str, float] = {
    "nba": 2.05,
    "mlb": DEFAULT_TEMPERATURE,
}

_EPS: float = 1e-9


def temperature_scale(p: float, temperature: float) -> float:
    """Apply temperature scaling to a single probability.

    p_cal = sigmoid(logit(p) / temperature). Identity when temperature == 1.0.
    Clamps p into (0, 1) for numerical safety; output is in (0, 1).
    """
    T = float(temperature)
    if T <= 0.0:
        raise ValueError(f"temperature must be > 0, got {T}")
    if T == 1.0:
        return float(p)
    p_clamped = min(1.0 - _EPS, max(_EPS, float(p)))
    logit = math.log(p_clamped / (1.0 - p_clamped))
    return 1.0 / (1.0 + math.exp(-logit / T))


def calibrate_probability(p: float, sport: str = "nba") -> float:
    """Calibrate a raw model probability for the given sport.

    Looks up the per-sport temperature (DEFAULT_TEMPERATURE for unknown sports —
    fail-safe identity) and applies temperature scaling. Safe to apply to the
    YES-frame probability directly (frame-symmetric — see module docstring).
    """
    T = CALIBRATION_TEMPERATURE.get(sport, DEFAULT_TEMPERATURE)
    return temperature_scale(p, T)


def get_temperature(sport: str) -> float:
    """Return the configured temperature for a sport (DEFAULT if unregistered)."""
    return CALIBRATION_TEMPERATURE.get(sport, DEFAULT_TEMPERATURE)
