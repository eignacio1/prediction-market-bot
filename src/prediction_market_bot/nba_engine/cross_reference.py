"""NBA cross-reference compatibility -- ADR-0075 component 4 for NBA (W109.1 Part B).

One fact, every market it touches, one consistent answer. A game's (mean margin m, mean total t) and the engine's
shape parameters are the single source: moneyline, spread, total and both team totals are all functions of the same
joint (home, away) distribution. This module (1) prices the whole board from one (m, t), (2) checks the board's internal
consistency (identities and monotonicity that any coherent set of prices must satisfy, joint simulation vs closed form),
and (3) propagates ONE fact (a change in a factor value, e.g. a starter ruled out) to every family and checks the
direction of every move against the direction the fact implies.

Applies when: a price for one market is about to be placed and the engine's other markets for the same game must not
contradict it (and when a fact arrives, to see which markets it should move and which sign each move must have).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional

import numpy as np

from prediction_market_bot.nba_engine import engine_v2 as V

TOL = 1e-9


@dataclass
class Board:
    ml_home: float
    spread: Dict[int, float]            # home margin >= n
    total: Dict[int, float]             # total >= n
    tt_home: Dict[int, float]           # home points >= n
    tt_away: Dict[int, float]           # away points >= n


def price_board(p: V.V2Params, m: float, t: float, spreads=(-10, -5, -1, 1, 5, 10), totals=(200, 215, 230, 245),
                team_totals=(100, 107, 114, 121, 128)) -> Board:
    """Raw (pre-Platt) probabilities for the whole board from one (m, t)."""
    return Board(
        ml_home=V.raw_prob(p, "ml", m, t, 1),
        spread={n: V.raw_prob(p, "spread", m, t, n) for n in spreads},
        total={n: V.raw_prob(p, "total", m, t, n) for n in totals},
        tt_home={n: V.raw_prob(p, "team_total", m, t, n) for n in team_totals},
        tt_away={n: V.raw_prob(p, "team_total", -m, t, n) for n in team_totals})


@dataclass
class Report:
    violations: List[str] = field(default_factory=list)
    max_sim_gap: float = 0.0

    @property
    def ok(self) -> bool:
        return not self.violations


def check_board(p: V.V2Params, m: float, t: float, board: Optional[Board] = None, sims: int = 200_000,
                seed: int = 0, sim_tol: float = 0.01) -> Report:
    """Internal-consistency checks. Identities are exact; the simulation gap is Monte Carlo (``sim_tol`` = 1 pt)."""
    b = board or price_board(p, m, t)
    rep = Report()
    if abs(b.ml_home - b.spread.get(1, V.raw_prob(p, "spread", m, t, 1))) > TOL:
        rep.violations.append("ml != spread(home wins by >=1)")
    for name, d in (("spread", b.spread), ("total", b.total), ("tt_home", b.tt_home), ("tt_away", b.tt_away)):
        ks = sorted(d)
        if any(d[ks[i]] < d[ks[i + 1]] - TOL for i in range(len(ks) - 1)):
            rep.violations.append(f"{name} not non-increasing in the line")
    if not all(0.0 <= v <= 1.0 for d in (b.spread, b.total, b.tt_home, b.tt_away) for v in d.values()):
        rep.violations.append("probability outside [0, 1]")
    h, a = V.simulate(p, m, t, n=sims, seed=seed)
    gaps = [abs(float(np.mean((h - a) >= 1)) - b.ml_home)]
    gaps += [abs(float(np.mean((h - a) >= n)) - v) for n, v in b.spread.items() if n >= 1]
    gaps += [abs(float(np.mean((h + a) >= n)) - v) for n, v in b.total.items()]
    gaps += [abs(float(np.mean(h >= n)) - v) for n, v in b.tt_home.items()]
    gaps += [abs(float(np.mean(a >= n)) - v) for n, v in b.tt_away.items()]
    rep.max_sim_gap = max(gaps)
    if rep.max_sim_gap > sim_tol:
        rep.violations.append(f"closed form vs joint simulation gap {rep.max_sim_gap:.4f} > {sim_tol}")
    if abs(float(np.mean(h + a)) - t) > 0.15 or abs(float(np.mean(h - a)) - m) > 0.15:
        rep.violations.append("simulated mean margin/total do not return the inputs")
    return rep


def joint_prob(p: V.V2Params, m: float, t: float, legs, sims: int = 200_000, seed: int = 0) -> float:
    """P(all legs) from ONE joint simulation -- parlay correlation included. Leg = (kind, n): kind in
    margin_ge / total_ge / home_ge / away_ge."""
    h, a = V.simulate(p, m, t, n=sims, seed=seed)
    stat = {"margin_ge": h - a, "total_ge": h + a, "home_ge": h, "away_ge": a}
    ok = np.ones(sims, dtype=bool)
    for kind, n in legs:
        ok &= stat[kind] >= n
    return float(ok.mean())


# direction a "more of this" in the factor must push each family (per the engine's own shift signs, not asserted a priori)
def propagate_fact(p: V.V2Params, mu_h: float, mu_a: float, before: Mapping[str, float], after: Mapping[str, float],
                   lines: Optional[Mapping[str, int]] = None) -> dict:
    """Apply one fact (factor values before -> after) to every family; return per-family deltas and whether each move's
    sign agrees with the sign implied by the factor's own coefficients on margin and total."""
    lines = lines or {"spread": 1, "total": 225, "tt_home": 112, "tt_away": 112}
    m0, t0 = V.game_means(p, mu_h, mu_a, before)
    m1, t1 = V.game_means(p, mu_h, mu_a, after)
    b0, b1 = price_board(p, m0, t0, spreads=(lines["spread"],), totals=(lines["total"],), team_totals=(lines["tt_home"],)), \
        price_board(p, m1, t1, spreads=(lines["spread"],), totals=(lines["total"],), team_totals=(lines["tt_home"],))
    dm, dt = m1 - m0, t1 - t0
    d = {"ml": b1.ml_home - b0.ml_home, "spread": b1.spread[lines["spread"]] - b0.spread[lines["spread"]],
         "total": b1.total[lines["total"]] - b0.total[lines["total"]],
         "tt_home": b1.tt_home[lines["tt_home"]] - b0.tt_home[lines["tt_home"]],
         "tt_away": b1.tt_away[lines["tt_home"]] - b0.tt_away[lines["tt_home"]]}
    want = {"ml": np.sign(dm), "spread": np.sign(dm), "total": np.sign(dt), "tt_home": np.sign(dt + dm), "tt_away": np.sign(dt - dm)}
    agree = {k: bool(np.sign(v) == want[k] or abs(v) < TOL) for k, v in d.items()}
    return {"d_margin": dm, "d_total": dt, "delta_p": d, "sign_agrees": agree, "all_agree": all(agree.values())}
