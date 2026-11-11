"""NFL weather factor class, point-in-time (W110.1, B-069). Factor N14 in SEATS/nfl.toml.

FORECAST vs REALISED -- the rule this module enforces:
  * a FORECAST (issued >= MIN_LEAD_H before kickoff) is what was knowable when a price is set. It may price.
  * REALISED weather (the observed kickoff conditions in nflverse `games`) is a leak for pricing: nobody holds it at
    T1. It may TRAIN effect sizes on past games (labels are in the past) and may serve as a labelled upper bound in a
    study, never as a price input. `assert_priceable` raises on it.
Indoor exposure: a dome / closed roof zeroes the weather terms (an open-roof game keeps them).
Effects are three scalars (points of TOTAL per unit exposure) fitted on past games only; the shift is split evenly
between the teams. Pure functions; no I/O.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

import numpy as np

MIN_LEAD_H = 12.0          # a priceable forecast must be issued at least this long before kickoff
WIND_KNEE_MPH = 10.0       # wind below this has no modelled effect
COLD_KNEE_F = 50.0         # cold exposure = degrees below this
INDOOR_ROOFS = {"dome", "closed"}
SOURCES = ("forecast", "realised", "none")


@dataclass(frozen=True)
class WeatherContext:
    source: str                       # 'forecast' | 'realised' | 'none'
    roof: Optional[str] = None
    temp_f: Optional[float] = None
    wind_mph: Optional[float] = None
    precip_mm: Optional[float] = None
    lead_h: Optional[float] = None    # hours between forecast issue and kickoff (forecast only)

    def __post_init__(self):
        if self.source not in SOURCES:
            raise ValueError(f"unknown weather source {self.source!r}")


@dataclass(frozen=True)
class WeatherEffects:
    """Points of game TOTAL per unit of exposure. Fitted on past games only (see fit_effects)."""
    wind: float = 0.0       # per mph above WIND_KNEE_MPH
    cold: float = 0.0       # per degree F below COLD_KNEE_F
    precip: float = 0.0     # per mm of hourly precipitation


def assert_priceable(ctx: WeatherContext) -> None:
    """Raise unless `ctx` could have been known before kickoff."""
    if ctx.source == "realised":
        raise ValueError("realised weather is a look-ahead leak for pricing; use a forecast")
    if ctx.source == "forecast" and (ctx.lead_h is None or ctx.lead_h < MIN_LEAD_H):
        raise ValueError(f"forecast lead {ctx.lead_h}h < {MIN_LEAD_H}h minimum")


def is_indoor(roof: Optional[str]) -> bool:
    return (roof or "").strip().lower() in INDOOR_ROOFS


def exposure(ctx: WeatherContext) -> dict:
    """Exposure terms. Indoor or missing weather -> zero (documented imputation: no information, no shift)."""
    if ctx.source == "none" or is_indoor(ctx.roof):
        return {"wind": 0.0, "cold": 0.0, "precip": 0.0}
    w = 0.0 if ctx.wind_mph is None or np.isnan(ctx.wind_mph) else max(0.0, float(ctx.wind_mph) - WIND_KNEE_MPH)
    c = 0.0 if ctx.temp_f is None or np.isnan(ctx.temp_f) else max(0.0, COLD_KNEE_F - float(ctx.temp_f))
    p = 0.0 if ctx.precip_mm is None or np.isnan(ctx.precip_mm) else max(0.0, float(ctx.precip_mm))
    return {"wind": w, "cold": c, "precip": p}


def fit_effects(wind: Iterable[float], cold: Iterable[float], precip: Iterable[float], residual_total: Iterable[float],
                ridge: float = 1e-6) -> WeatherEffects:
    """Through-origin OLS of (actual total - baseline total) on exposure, fitted on PAST games only."""
    X = np.column_stack([np.asarray(list(v), float) for v in (wind, cold, precip)])
    y = np.asarray(list(residual_total), float)
    ok = np.isfinite(X).all(1) & np.isfinite(y)
    X, y = X[ok], y[ok]
    beta = np.linalg.solve(X.T @ X + ridge * np.eye(3), X.T @ y)
    return WeatherEffects(*map(float, beta))


def total_shift(ctx: WeatherContext, eff: WeatherEffects, *, pricing: bool = True) -> float:
    """Points added to the game total. pricing=True enforces the forecast-only rule."""
    if pricing:
        assert_priceable(ctx)
    e = exposure(ctx)
    return eff.wind * e["wind"] + eff.cold * e["cold"] + eff.precip * e["precip"]


def apply_to_means(mu_home: float, mu_away: float, shift_total: float) -> tuple:
    """Split the total shift evenly; never push a team mean below 1 point."""
    return max(mu_home + shift_total / 2.0, 1.0), max(mu_away + shift_total / 2.0, 1.0)
