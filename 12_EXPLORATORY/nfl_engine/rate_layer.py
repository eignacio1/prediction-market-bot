"""EXPLORATORY -- sport-neutral rate layer (W75.2, GG-756). Layer 1 of INTERFACE.md: rates(inputs) -> mean points.

A `Factor` turns (as_of, offense, defense) into a points-per-game adjustment for the OFFENSE, or None (= league average,
never a silent drop). The layer knows nothing about football: every later factor class plugs in by implementing `Factor`
and getting a fitted coefficient. Coefficients are fitted outside (training seasons only) and passed in.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional, Protocol, Sequence

import pandas as pd


class Factor(Protocol):
    name: str

    def points(self, as_of: pd.Timestamp, offense: str, defense: str) -> Optional[float]:
        """Expected extra points for `offense` vs `defense`, using only data dated <= as_of. None = league average."""


@dataclass
class GameInputs:
    as_of: pd.Timestamp
    home: str
    away: str
    base_mu_home: float            # base rating layer mean points (e.g. ridge + calibration)
    base_mu_away: float


@dataclass
class TeamRates:
    mu_home: float
    mu_away: float
    populated: dict = field(default_factory=dict)   # factor name -> (home_term, away_term) as used


def rates(inputs: GameInputs, factors: Sequence[Factor], betas: Mapping[str, float]) -> TeamRates:
    mh, ma, pop = inputs.base_mu_home, inputs.base_mu_away, {}
    for f in factors:
        b = betas.get(f.name, 0.0)
        th = f.points(inputs.as_of, inputs.home, inputs.away)
        ta = f.points(inputs.as_of, inputs.away, inputs.home)
        pop[f.name] = (th, ta)
        mh += b * (th or 0.0)
        ma += b * (ta or 0.0)
    return TeamRates(mh, ma, pop)
