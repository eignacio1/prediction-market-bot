"""NFL temporal evolution -- ADR-0075's eighth component (W94.2 Part B).

How an applied factor's value, its stability and its weight change through a season and across seasons,
point-in-time. A factor here is any per-(team, game) number the engine reads (EPA/play, neutral pass rate,
pace ...), laid out as a long table with columns ``team, season, week, v``.

Point-in-time: every as-of quantity uses only games strictly before the one being predicted
(``asof_ew`` shifts by one; ``blend_weight_by_week`` builds its regressors from prior games only).

When each tool applies (the quant bar's one-liner):
- ``asof_ew``: a unit's current level when older games should count less (exponential half-life, in games).
- ``within_season_slope``: whether the league-wide level of a factor moves week to week inside a season
  (team-season demeaned, so roster/schedule composition is not mistaken for drift).
- ``reliability_gap``: whether *teams* drift against each other inside a season. Odd/even split reliability
  does not care about order; early/late split reliability does. Their gap is the drift signal.
- ``blend_weight_by_week``: the data-implied weight on this season's as-of mean vs last season's mean,
  by stretch of the season (how fast a prior should be released).
"""
from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

BOOT_SEED = 20261029


def asof_ew(values: Iterable[float], halflife: float) -> np.ndarray:
    """Exponentially weighted mean of strictly earlier observations; out[0] is NaN. Age 1 = previous game."""
    x = np.asarray(list(values), dtype=float)
    out = np.full(len(x), np.nan)
    for i in range(1, len(x)):
        age = np.arange(i, 0, -1, dtype=float)          # oldest first: i, i-1, ..., 1
        w = 0.5 ** ((age - 1.0) / halflife)
        m = ~np.isnan(x[:i])
        if m.any():
            out[i] = float(np.sum(w[m] * x[:i][m]) / np.sum(w[m]))
    return out


def _interval(draws: np.ndarray, level: float = 0.95) -> tuple[float, float]:
    a = (1.0 - level) / 2.0
    return float(np.quantile(draws, a)), float(np.quantile(draws, 1.0 - a))


def within_season_slope(d: pd.DataFrame, *, n_boot: int = 2000, seed: int = BOOT_SEED) -> dict:
    """League drift per week inside a season, averaged over seasons; interval by bootstrap over seasons.

    Per season: team-season-demeaned v regressed on centred week (OLS slope, units of v per week).
    """
    d = d.dropna(subset=["v"]).copy()
    d["vd"] = d.v - d.groupby(["team", "season"]).v.transform("mean")
    d["wc"] = d.week - d.groupby("season").week.transform("mean")
    per = {}
    for s, g in d.groupby("season"):
        den = float((g.wc ** 2).sum())
        if den > 0:
            per[int(s)] = float((g.wc * g.vd).sum() / den)
    sl = np.array(list(per.values()))
    rng = np.random.default_rng(seed)
    draws = np.array([sl[rng.integers(0, len(sl), len(sl))].mean() for _ in range(n_boot)])
    lo, hi = _interval(draws)
    return {"slope_per_week": float(sl.mean()), "lo": lo, "hi": hi, "n_seasons": len(sl),
            "n_rows": int(len(d)), "per_season": per}


def _half_means(d: pd.DataFrame, kind: str) -> pd.DataFrame:
    rows = []
    for (t, s), g in d.dropna(subset=["v"]).sort_values("week").groupby(["team", "season"]):
        v = g.v.to_numpy()
        if len(v) < 6:
            continue
        if kind == "odd_even":
            a, b = v[0::2], v[1::2]
        else:  # early_late
            h = len(v) // 2
            a, b = v[:h], v[len(v) - h:]
        rows.append((t, s, a.mean(), b.mean()))
    return pd.DataFrame(rows, columns=["team", "season", "a", "b"])


def _corr_demeaned(h: pd.DataFrame) -> float:
    a = h.a - h.groupby("season").a.transform("mean")
    b = h.b - h.groupby("season").b.transform("mean")
    den = float(np.sqrt((a ** 2).sum() * (b ** 2).sum()))
    return float((a * b).sum() / den) if den > 0 else float("nan")


def reliability_gap(d: pd.DataFrame, *, n_boot: int = 2000, seed: int = BOOT_SEED) -> dict:
    """Odd/even minus early/late split-half correlation across team-seasons (positive = teams drift in-season).

    Both halves use the same number of games, so the comparison is like-for-like. Paired bootstrap over
    team-seasons (the odd/even and early/late halves of a team-season are resampled together).
    """
    oe, el = _half_means(d, "odd_even"), _half_means(d, "early_late")
    m = oe.merge(el, on=["team", "season"], suffixes=("_oe", "_el"))
    oe_ = m[["team", "season", "a_oe", "b_oe"]].rename(columns={"a_oe": "a", "b_oe": "b"})
    el_ = m[["team", "season", "a_el", "b_el"]].rename(columns={"a_el": "a", "b_el": "b"})
    r_oe, r_el = _corr_demeaned(oe_), _corr_demeaned(el_)
    rng = np.random.default_rng(seed)
    n = len(m)
    gaps = np.empty(n_boot)
    for k in range(n_boot):
        ix = rng.integers(0, n, n)
        gaps[k] = _corr_demeaned(oe_.iloc[ix]) - _corr_demeaned(el_.iloc[ix])
    lo, hi = _interval(gaps)
    return {"r_odd_even": r_oe, "r_early_late": r_el, "gap": r_oe - r_el, "lo": lo, "hi": hi, "n_team_seasons": int(n)}


def blend_weight_by_week(d: pd.DataFrame, *, buckets=((3, 6), (7, 12), (13, 18)),
                         n_boot: int = 500, seed: int = BOOT_SEED) -> list[dict]:
    """OLS weight on this season's as-of mean vs last season's mean of the same team, by stretch of season.

    v is season-demeaned. Regressors for game g: mean of the team's earlier games this season, and the team's
    previous-season mean. Rows need >= 2 earlier games and a previous season. Interval: bootstrap over team-seasons.
    """
    d = d.dropna(subset=["v"]).sort_values(["team", "season", "week"]).copy()
    d["v"] = d.v - d.groupby("season").v.transform("mean")
    d["m_in"] = d.groupby(["team", "season"]).v.transform(lambda x: x.shift(1).expanding().mean())
    d["k_in"] = d.groupby(["team", "season"]).cumcount()
    prev = d.groupby(["team", "season"]).v.mean().rename("m_prev").reset_index()
    prev["season"] += 1
    d = d.merge(prev, on=["team", "season"], how="left")
    d = d[(d.k_in >= 2) & d.m_prev.notna() & d.m_in.notna()]
    rng = np.random.default_rng(seed)
    out = []
    for lo_w, hi_w in buckets:
        g = d[(d.week >= lo_w) & (d.week <= hi_w)]
        if len(g) < 50:
            continue

        def fit(x: pd.DataFrame) -> np.ndarray:
            X = np.column_stack([x.m_in.to_numpy(), x.m_prev.to_numpy()])
            return np.linalg.lstsq(X, x.v.to_numpy(), rcond=None)[0]

        b = fit(g)
        keys = g.groupby(["team", "season"]).ngroup().to_numpy()
        idx = [np.flatnonzero(keys == k) for k in range(keys.max() + 1)]
        draws = np.empty((n_boot, 2))
        for k in range(n_boot):
            pick = rng.integers(0, len(idx), len(idx))
            draws[k] = fit(g.iloc[np.concatenate([idx[i] for i in pick])])
        out.append({"weeks": f"{lo_w}-{hi_w}", "w_in_season": float(b[0]), "w_in_lo": _interval(draws[:, 0])[0],
                    "w_in_hi": _interval(draws[:, 0])[1], "w_prev_season": float(b[1]),
                    "w_prev_lo": _interval(draws[:, 1])[0], "w_prev_hi": _interval(draws[:, 1])[1],
                    "n_rows": int(len(g)), "n_team_seasons": len(idx)})
    return out
