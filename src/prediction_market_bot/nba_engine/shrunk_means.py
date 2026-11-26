"""W129.2 EXP-047-S: pure shrinkage of a player's per-minute rate and minutes (H-DEPTH-PAM-3 §4), no I/O.
shrunk_rate = (M*r_obs + k_s*prior_s) / (M + k_s); prior_s = (m_prev*r_prev + 500*r_league) / (m_prev + 500);
shrunk_minutes = (n*mbar + k_min*m_prev_mean) / (n + k_min).  The constants are the PAM-3 draft fit on 2016-2022
(12_EXPLORATORY/pam_stability/trait_reliability_draft.json); they are frozen here and a test pins them to that file."""
from __future__ import annotations

from typing import Mapping, Optional, Sequence

import numpy as np

STATS = ("points", "rebounds", "assists", "threes")
K = {"points": 60.10269995218529, "rebounds": 27.269351099650788, "assists": 30.157803327847574, "threes": 66.70643543370875}
K_MIN = 0.821042732732454
PSEUDO_LEAGUE_MIN = 500.0
BAND_CUTS = (15.0, 22.0, 29.0)
MU_FLOOR = 1e-3


def band(mpg: float) -> int:
    return int(np.digitize([mpg], BAND_CUTS)[0])


def league_band_rates(season_totals: Mapping[str, Mapping[str, float]]) -> dict:
    """{player: {min, games, points, rebounds, assists, threes}} for ONE season -> {band: {stat: stat per minute}} pooled over the band."""
    acc: dict = {}
    for t in season_totals.values():
        if t["games"] <= 0 or t["min"] <= 0:
            continue
        a = acc.setdefault(band(t["min"] / t["games"]), {"min": 0.0, **{s: 0.0 for s in STATS}})
        a["min"] += t["min"]
        for s in STATS:
            a[s] += t[s]
    return {b: {s: a[s] / a["min"] for s in STATS} for b, a in acc.items() if a["min"] > 0}


def shrunk_rate(m_obs: float, r_obs: float, k: float, prior: float) -> float:
    return (m_obs * r_obs + k * prior) / (m_obs + k) if m_obs + k > 0 else prior


def prior_rate(prev: Optional[Mapping[str, float]], stat: str, league_rate: float) -> float:
    """The previous-season per-minute rate blended to the league rate; no previous season -> the league rate."""
    if not prev or prev.get("min", 0.0) <= 0:
        return league_rate
    return (prev["min"] * (prev[stat] / prev["min"]) + PSEUDO_LEAGUE_MIN * league_rate) / (prev["min"] + PSEUDO_LEAGUE_MIN)


def shrunk_minutes(n: int, mbar: float, prev: Optional[Mapping[str, float]], k_min: float = K_MIN) -> float:
    if not prev or prev.get("games", 0.0) <= 0:
        return mbar
    return (n * mbar + k_min * prev["min"] / prev["games"]) / (n + k_min)


def shrunk_mu(prior_rows: Sequence[Mapping[str, float]], prev: Optional[Mapping[str, float]], league: Mapping[int, Mapping[str, float]],
              k: Mapping[str, float] = K, k_min: float = K_MIN) -> Optional[dict]:
    """One player: his prior games THIS team-season (dicts with min, points, rebounds, assists, threes) -> {stat: mu}.
    ``league`` = ``league_band_rates`` of the previous season. None when no league rate is available for his band (caller falls back)."""
    n = len(prior_rows)
    M = float(sum(r["min"] for r in prior_rows))
    if n == 0 or M <= 0:
        return None
    mbar = M / n
    b = band(prev["min"] / prev["games"]) if prev and prev.get("games", 0.0) > 0 else band(mbar)
    lg = league.get(b)
    if lg is None:
        return None
    sm = shrunk_minutes(n, mbar, prev, k_min)
    return {s: max(shrunk_rate(M, sum(r[s] for r in prior_rows) / M, k[s], prior_rate(prev, s, lg[s])) * sm, MU_FLOOR) for s in STATS}


def estimate_k(rates_half_a: np.ndarray, rates_half_b: np.ndarray, size: float) -> float:
    """Split-half reliability -> k (pseudo-minutes), as PAM-3: Spearman-Brown on the half correlation, k = size*(1-r)/r."""
    r_half = float(np.corrcoef(rates_half_a, rates_half_b)[0, 1])
    r = 2 * r_half / (1 + r_half)
    return float(size * (1 - r) / r) if r > 0 else float("inf")
