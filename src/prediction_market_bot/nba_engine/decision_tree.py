"""NBA per-market decision tree, depth by horizon -- ADR-0075 component 1 for NBA (W109.1 Part A; ADR-0068).

The longer the horizon, the deeper the tree. A band permits a set of factor classes; the tree consults the permitted set
intersected with what has actually arrived by the decision time (lineups/injury reports land ~1.5h before tip). Pricing is the
engine's own (``engine_v2``): one (m, t) from the consulted factors, then the family's closed form and its Platt step.
In play (T4) the tree is two arithmetic operations: a remaining-time mean update and a sd shrink.

Applies when: pricing one NBA market (ml / spread / total / team_total) at a stated hours-to-tip, with whatever factors exist.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Tuple

import numpy as np

from prediction_market_bot.nba_engine import engine_v2 as V

# band -> (min hours to tip, permitted factor classes). Data, not code: a deeper band is a longer set.
BANDS: Tuple[Tuple[str, float, Tuple[str, ...]], ...] = (
    ("T1", 12.0, ("ratings", "rest", "lineup", "matchup", "venue", "qualitative")),
    ("T2", 3.0, ("ratings", "rest", "lineup", "matchup")),
    ("T3", 0.0, ("ratings", "lineup")),
)
# factor name -> (class, hours-to-tip at or below which it is knowable). Lineups land ~1.5h out; schedule-derived factors always.
ALWAYS = 1e9
FACTOR_CLASS: Dict[str, Tuple[str, float]] = {
    "exp_missing": ("lineup", 1.5), "lineup_net": ("lineup", 1.5),
    "d_exp_missing": ("lineup", 1.5), "s_exp_missing": ("lineup", 1.5),
    "d_lineup_net": ("lineup", 1.5), "s_lineup_net": ("lineup", 1.5),
    "rest_diff": ("rest", ALWAYS), "b2b_home": ("rest", ALWAYS), "b2b_away": ("rest", ALWAYS),
    "matchup_cross": ("matchup", ALWAYS), "travel": ("venue", ALWAYS),
}


def band_for(hours_to_tip: float) -> str:
    """In play (hours_to_tip < 0) is T4; otherwise the deepest band whose lead is satisfied."""
    if hours_to_tip < 0:
        return "T4"
    for name, lead, _ in BANDS:
        if hours_to_tip >= lead:
            return name
    return "T3"


def permitted_classes(band: str) -> Tuple[str, ...]:
    return () if band == "T4" else next(c for n, _, c in BANDS if n == band)


@dataclass
class TreeResult:
    p: float
    raw: float
    band: str
    m: float
    t: float
    used: List[str]
    skipped: Dict[str, str]
    path: List[str]


def usable_factors(x: Mapping[str, float], hours_to_tip: float) -> Tuple[Dict[str, float], Dict[str, str]]:
    """Consult only factors in a permitted class AND already knowable at ``hours_to_tip`` (no future information)."""
    band = band_for(hours_to_tip)
    ok = set(permitted_classes(band))
    use, skip = {}, {}
    for f, v in x.items():
        cls, avail = FACTOR_CLASS.get(f, ("unknown", float("inf")))
        if cls not in ok:
            skip[f] = f"class {cls} not permitted at {band}"
        elif hours_to_tip > avail:
            skip[f] = f"not knowable until {avail}h before tip"
        else:
            use[f] = v
    return use, skip


def price(p: V.V2Params, family: str, mu_h: float, mu_a: float, x: Mapping[str, float], hours_to_tip: float, n: int = 1,
          calibrate: bool = True) -> TreeResult:
    """Pre-game price of one market under the band's tree."""
    band = band_for(hours_to_tip)
    if band == "T4":
        raise ValueError("in play: use price_inplay")
    use, skip = usable_factors(x, hours_to_tip)
    m, t = V.game_means(p, mu_h, mu_a, use)
    raw = V.raw_prob(p, family, m, t, n)
    q = V.calibrated(p, family, raw) if calibrate else raw
    path = [f"band={band}", f"classes={','.join(permitted_classes(band))}", f"factors={','.join(sorted(use)) or 'none'}",
            f"family={family}"]
    return TreeResult(q, raw, band, m, t, sorted(use), skip, path)


def price_inplay(p: V.V2Params, family: str, m_pre: float, t_pre: float, frac_played: float, margin_now: float,
                 total_now: float, n: int = 1) -> TreeResult:
    """T4, shallow: remaining mean = pre-game mean x (1 - f) added to the score now; sd scales by sqrt(1 - f)."""
    f = float(np.clip(frac_played, 0.0, 0.999))
    m = margin_now + m_pre * (1 - f)
    t = total_now + t_pre * (1 - f)
    s = float(np.sqrt(1 - f))
    q = V.V2Params(p.hca, p.tbias, p.sd_margin * s, p.sd_total * s, p.shift_margin, p.shift_total, p.platt)
    raw = V.raw_prob(q, family, m, t, n)
    return TreeResult(raw, raw, "T4", m, t, [], {}, ["band=T4", f"f={f:.3f}", f"family={family}"])
