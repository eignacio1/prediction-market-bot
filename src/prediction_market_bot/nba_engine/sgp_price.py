"""Same-game combo pricing from the NBA joint (W113.3 Part C, B-086): the bot's own fair value for 2-3 leg parlays.

One ``GameDraws`` = one simulation (engine_v2 team scores + joint.py player stats, same draw index). A combo's joint is the
share of draws where every leg holds; the naive product is what a retail parlay prices (legs treated as independent);
``lift = joint / naive`` is the correlation that parlay ignores. Fair value only: no Kalshi NBA same-game combo market was
open at W110.4 / W113.3, so no market price or fee schedule is applied here (``quant/money.py`` / ``quant/costs.py`` do that).

When it applies: legs all from one game's draws. When it does not: a joint below ~5 hits in the draws is flagged unresolved
(``resolved``) and must not be used as a price; the joint is only as right as the dependence the draws carry (measured per
pair class in 12_EXPLORATORY/sgp_correlation/RESULT_W113_3.md).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np

from prediction_market_bot.quant import sgp as S

KINDS = ("ml", "spread", "total", "team_total", "player")


@dataclass(frozen=True)
class LegSpec:
    """kind: ml (side wins) | spread (side margin >= line, i.e. side -line / +line as margin >= line) | total (home+away >= line)
    | team_total (side points >= line) | player (stat of `player` >= line). side is 'home' or 'away'."""
    kind: str
    line: float = 0.0
    side: str = "home"
    player: str | None = None
    stat: str | None = None

    def key(self) -> str:
        if self.kind == "player":
            return f"{self.side}:{self.player}:{self.stat}>={self.line:g}"
        return f"{self.kind}:{self.side}>={self.line:g}"


@dataclass(frozen=True)
class GameDraws:
    home: np.ndarray
    away: np.ndarray
    players: Mapping[tuple, np.ndarray]     # (side, player, stat) -> (n,) draws

    @property
    def n(self) -> int:
        return len(self.home)


def build_leg(g: GameDraws, s: LegSpec) -> np.ndarray:
    if s.kind == "ml":
        m = (g.home - g.away) if s.side == "home" else (g.away - g.home)
        return m >= 1
    if s.kind == "spread":
        m = (g.home - g.away) if s.side == "home" else (g.away - g.home)
        return m >= s.line
    if s.kind == "total":
        return (g.home + g.away) >= s.line
    if s.kind == "team_total":
        return (g.home if s.side == "home" else g.away) >= s.line
    if s.kind == "player":
        return np.asarray(g.players[(s.side, s.player, s.stat)]) >= s.line
    raise ValueError(f"unknown leg kind {s.kind!r}")


def price_combo(g: GameDraws, specs: Sequence[LegSpec]) -> dict:
    """Joint, naive product, lift, MC se, resolved flag and Frechet bounds for 2-3 legs from one game's draws."""
    if not 2 <= len(specs) <= 3:
        raise ValueError("a combo is 2 or 3 legs")
    legs = [build_leg(g, s) for s in specs]
    pj, pi = S.joint(*legs), S.independent(*legs)
    lo, hi = S.frechet_bounds(*legs)
    return dict(legs=[s.key() for s in specs], p_marginals=[S.marginal(l) for l in legs], p_joint=pj, p_naive=pi,
                lift=(pj / pi if pi > 0 else float("nan")), excess=pj - pi, mc_se=S.mc_se(pj, g.n),
                resolved=bool(S.resolved(pj, g.n)), frechet_lo=lo, frechet_hi=hi, n_draws=g.n)
