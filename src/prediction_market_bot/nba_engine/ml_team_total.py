"""W117.3 Part A: NBA moneyline and team totals priced from the SAME GameSample draws that price the spread and the total.

No new model: every number is a sample frequency of ``engine.simulate`` (point in time -- the caller passes the pre-tip inputs).
Kalshi strike rule: a ticker suffix N pays on X > N-0.5, i.e. P(X >= N) for integer points (engine docstring).
``consistency_checks`` is the audit the tests and the shadow rows use: win probabilities sum to 1, the two team means add to the
game-total mean exactly (same draws), and the ladders are monotone.
"""
from __future__ import annotations

import math
from typing import Dict, Iterable

from . import engine as E

# Stated tolerance: the sample-frequency moneyline vs the normal-margin approximation implied by the spread ladder
# (mean/sd of the margin draws). Integer scores and the OT tail make the normal approximation slightly off; 0.02 is the
# measured worst gap (0.017, a +6 pts/100 favorite: OT and score-grid tails) rounded up, and is what the test asserts.
SPREAD_IMPLIED_TOL = 0.02


def price_moneyline_and_team_totals(s: E.GameSample, home_strikes: Iterable[int], away_strikes: Iterable[int]) -> dict:
    """{'home_win','away_win','home_pts_ge':{N:p},'away_pts_ge':{N:p},'mean_home','mean_away'} from one sample."""
    return {
        "home_win": E.p_moneyline_home(s),
        "away_win": E.p_away_margin_ge(s, 1),
        "home_pts_ge": {int(n): E.p_team_total_ge(s, "home", int(n)) for n in home_strikes},
        "away_pts_ge": {int(n): E.p_team_total_ge(s, "away", int(n)) for n in away_strikes},
        "mean_home": float(s.home_pts.mean()),
        "mean_away": float(s.away_pts.mean()),
    }


def spread_implied_home_win(s: E.GameSample) -> float:
    """P(home wins) implied by the spread distribution alone: normal margin with the draws' mean and sd, strike 0.5
    (the n=1 rung of the spread ladder). Independent of the integer sample frequency, so it is a real cross-check."""
    mu, sd = float(s.margin.mean()), float(s.margin.std())
    return 0.5 * math.erfc((0.5 - mu) / (sd * math.sqrt(2.0)))


def consistency_checks(s: E.GameSample, priced: Dict) -> Dict[str, float]:
    """Absolute gaps, all of which should be ~0 / within tolerance: win-prob sum, team means vs game-total mean, ML vs spread-implied."""
    return {
        "win_sum_gap": abs(priced["home_win"] + priced["away_win"] - 1.0),
        "team_means_vs_total_gap": abs(priced["mean_home"] + priced["mean_away"] - float(s.total.mean())),
        "ml_vs_spread_implied_gap": abs(priced["home_win"] - spread_implied_home_win(s)),
        "ladder_monotone_violations": float(sum(
            1 for lad in (priced["home_pts_ge"], priced["away_pts_ge"])
            for a, b in zip(sorted(lad), sorted(lad)[1:]) if lad[b] > lad[a] + 1e-12)),
    }
