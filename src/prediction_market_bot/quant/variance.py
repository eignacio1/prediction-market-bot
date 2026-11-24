"""Variance tools (W124.1): get a smaller interval from the same games, and state power in games, not rows.

Every function is pure Python 3.9 (no numpy), deterministic, and says where it applies and where it does not.
The unit of independence is the game (or event): rows from one game share information, so every standard error
here is cluster-robust. Descriptive aids only: nothing here changes a pre-registered rule or a verdict, and a
tighter interval is not an edge (report gross, round cost and net side by side).
"""
from __future__ import annotations

import math
from statistics import NormalDist
from typing import Dict, Hashable, Iterable, List, Mapping, Optional, Sequence, Tuple

_N = NormalDist()


def _z(level: float) -> float:
    return _N.inv_cdf(0.5 + level / 2.0)


def clustered_mean(y: Sequence[float], clusters: Sequence[Hashable], level: float = 0.90) -> dict:
    """Mean of rows with a cluster-robust (CR1) standard error and a normal interval.
    se^2 = G/(G-1) * sum_g (sum_{i in g} (y_i - ybar))^2 / N^2.
    Applies when rows in a cluster are dependent and clusters are independent, G >~ 30 (normal interval).
    Does not apply with few clusters (the interval undercovers) or when clusters are not independent (one team all season)."""
    n = len(y)
    if n != len(clusters) or n == 0:
        raise ValueError("y and clusters must be the same non-zero length")
    m = sum(y) / n
    sums: Dict[Hashable, float] = {}
    for v, g in zip(y, clusters):
        sums[g] = sums.get(g, 0.0) + (v - m)
    G = len(sums)
    if G < 2:
        return {"mean": m, "se": float("nan"), "lo": float("nan"), "hi": float("nan"), "n_rows": n, "n_clusters": G}
    se = math.sqrt(G / (G - 1.0) * sum(s * s for s in sums.values())) / n
    z = _z(level)
    return {"mean": m, "se": se, "lo": m - z * se, "hi": m + z * se, "n_rows": n, "n_clusters": G}


def icc(y: Sequence[float], clusters: Sequence[Hashable]) -> float:
    """Intra-cluster correlation, one-way ANOVA estimator for unbalanced clusters (Searle n0). Clamped to [0, 1].
    Applies to a single outcome measured on several rows per game; not defined with one row per cluster."""
    by: Dict[Hashable, List[float]] = {}
    for v, g in zip(y, clusters):
        by.setdefault(g, []).append(v)
    k = len(by)
    n = len(y)
    if k < 2 or n <= k:
        return 0.0
    grand = sum(y) / n
    ssb = sum(len(v) * (sum(v) / len(v) - grand) ** 2 for v in by.values())
    ssw = sum(sum((x - sum(v) / len(v)) ** 2 for x in v) for v in by.values())
    msb, msw = ssb / (k - 1), ssw / (n - k)
    n0 = (n - sum(len(v) ** 2 for v in by.values()) / n) / (k - 1)
    var_b = (msb - msw) / n0 if n0 > 0 else 0.0
    tot = var_b + msw
    return 0.0 if tot <= 0 else min(1.0, max(0.0, var_b / tot))


def design_effect(y: Sequence[float], clusters: Sequence[Hashable]) -> dict:
    """Design effect of clustering by game: deff = 1 + (m_eff - 1) * icc, m_eff = sum m_g^2 / sum m_g.
    Returns icc, deff, rows, games, mean rows per game and the effective number of independent rows (rows / deff).
    Applies to any row-level outcome with several rows per game; with one row per game deff = 1."""
    sizes: Dict[Hashable, int] = {}
    for g in clusters:
        sizes[g] = sizes.get(g, 0) + 1
    n, G = len(y), len(sizes)
    m_eff = sum(s * s for s in sizes.values()) / n if n else 0.0
    r = icc(y, clusters)
    deff = 1.0 + (m_eff - 1.0) * r
    return {"icc": r, "deff": deff, "n_rows": n, "n_games": G, "rows_per_game": n / G if G else 0.0,
            "m_eff": m_eff, "n_eff_rows": n / deff if deff > 0 else float("nan")}


def mde_clustered(sd: float, n_games: int, rows_per_game: float, icc: float, alpha: float = 0.05,
                  power: float = 0.80, two_sided: bool = False) -> float:
    """Minimum detectable true mean at (alpha, power) when n_games games each contribute rows_per_game rows with
    intra-game correlation icc: MDE = (z_a + z_b) * sd * sqrt(deff / (n_games * rows_per_game)), deff = 1 + (m-1) icc.
    Power is stated in GAMES: with icc ~ 1 extra rows per game buy nothing, with icc 0 they count in full.
    alpha is one-sided by default (the project's 'is the net above zero' look); two_sided=True halves it."""
    if n_games <= 0 or rows_per_game <= 0 or sd <= 0:
        return float("nan")
    a = alpha / 2.0 if two_sided else alpha
    deff = 1.0 + (rows_per_game - 1.0) * icc
    return (_N.inv_cdf(1.0 - a) + _N.inv_cdf(power)) * sd * math.sqrt(deff / (n_games * rows_per_game))


def games_needed(sd: float, rows_per_game: float, icc: float, effect: float, alpha: float = 0.05,
                 power: float = 0.80, two_sided: bool = False) -> float:
    """Inverse of mde_clustered: independent games needed to detect `effect` at (alpha, power). Returned as a float."""
    if effect <= 0 or sd <= 0 or rows_per_game <= 0:
        return float("nan")
    a = alpha / 2.0 if two_sided else alpha
    deff = 1.0 + (rows_per_game - 1.0) * icc
    return ((_N.inv_cdf(1.0 - a) + _N.inv_cdf(power)) * sd / effect) ** 2 * deff / rows_per_game


def clv(entry_price: float, close_mid: float, side: str) -> float:
    """Per-contract closing-line value on the order's own side, in dollars on a $1 payout.
    entry_price is what was paid for the contract on `side` (its own ask / fill price); close_mid is the closing
    mid of the YES contract. YES: close_mid - entry. NO: (1 - close_mid) - entry. Positive = the close moved our way.
    Gross: no fee and no exit cost. Applies where the close is a calibrated estimate of settlement (H-MEAS-1 licences
    that per family); where it is not licensed CLV is a descriptive number, never a verdict."""
    s = str(side).strip().lower()
    if s == "yes":
        return close_mid - entry_price
    if s == "no":
        return (1.0 - close_mid) - entry_price
    raise ValueError(f"side must be 'yes' or 'no', got {side!r}")


def control_variate(y: Sequence[float], x: Sequence[float], clusters: Sequence[Hashable],
                    fit: Sequence[bool], x_mean: Optional[float] = None, level: float = 0.90) -> dict:
    """CUPED-style adjustment: y* = y - theta * (x - x_mean), theta = cov(y, x) / var(x) FIT ON THE FIT ROWS ONLY,
    then the mean of y* and its clustered interval are read on the other (judged) rows.
    x must be known before the outcome (a pre-entry quantity). x_mean is the known population mean of x; if None it is
    the fit-window mean, which is unbiased only if x is stationary between the windows (the report says so by showing
    both means). Returns raw and adjusted means with intervals and variance_reduction = 1 - se_adj^2 / se_raw^2.
    Applies when x correlates with y and the rows are clustered by game; does not apply when x is measured after the
    outcome starts (that leaks) or when fit and judged rows share a game (pass `fit` by date, not by row)."""
    n = len(y)
    if not (n == len(x) == len(clusters) == len(fit)):
        raise ValueError("y, x, clusters, fit must be the same length")
    fy = [v for v, f in zip(y, fit) if f]
    fx = [v for v, f in zip(x, fit) if f]
    if len(fy) < 3:
        raise ValueError("need at least 3 fit rows")
    mx, my = sum(fx) / len(fx), sum(fy) / len(fy)
    vx = sum((a - mx) ** 2 for a in fx) / (len(fx) - 1)
    cxy = sum((a - mx) * (b - my) for a, b in zip(fx, fy)) / (len(fx) - 1)
    theta = cxy / vx if vx > 0 else 0.0
    center = mx if x_mean is None else x_mean
    jy = [v for v, f in zip(y, fit) if not f]
    jx = [v for v, f in zip(x, fit) if not f]
    jg = [g for g, f in zip(clusters, fit) if not f]
    if len(jy) < 3:
        raise ValueError("need at least 3 judged rows")
    adj = [b - theta * (a - center) for a, b in zip(jx, jy)]
    raw = clustered_mean(jy, jg, level)
    ad = clustered_mean(adj, jg, level)
    vr = 1.0 - (ad["se"] ** 2) / (raw["se"] ** 2) if raw["se"] and raw["se"] > 0 else float("nan")
    return {"theta": theta, "x_center": center, "x_mean_fit": mx, "x_mean_judged": sum(jx) / len(jx),
            "raw": raw, "adjusted": ad, "variance_reduction": vr, "n_fit": len(fy), "n_judged": len(jy)}


def paired_within_cluster(rows: Iterable[Tuple[Hashable, float, float]], level: float = 0.90) -> dict:
    """Difference of two arms (or two rules) on the same game: rows = (game, value_a, value_b). Each game's
    differences are averaged, then the mean difference has a game-clustered interval. Also returns the interval the
    UNPAIRED comparison would have had (independent se of the two arm means, same games) and the variance reduction
    from pairing, 1 - se_paired^2 / se_unpaired^2. Applies when both arms are scored on every game in the sample;
    games where only one arm exists must be dropped first (and counted by the caller)."""
    rows = list(rows)
    if not rows:
        raise ValueError("no rows")
    g = [r[0] for r in rows]
    a = [r[1] for r in rows]
    b = [r[2] for r in rows]
    d = [x - y for x, y in zip(a, b)]
    paired = clustered_mean(d, g, level)
    ca, cb = clustered_mean(a, g, level), clustered_mean(b, g, level)
    se_un = math.sqrt(ca["se"] ** 2 + cb["se"] ** 2)
    z = _z(level)
    vr = 1.0 - (paired["se"] ** 2) / (se_un ** 2) if se_un > 0 else float("nan")
    return {"mean_diff": paired["mean"], "se": paired["se"], "lo": paired["lo"], "hi": paired["hi"],
            "n_rows": paired["n_rows"], "n_games": paired["n_clusters"],
            "mean_a": ca["mean"], "mean_b": cb["mean"],
            "unpaired_se": se_un, "unpaired_lo": paired["mean"] - z * se_un, "unpaired_hi": paired["mean"] + z * se_un,
            "variance_reduction": vr}


def partial_pool(cells: Mapping[Hashable, Tuple[float, float]], level: float = 0.90) -> dict:
    """Normal-normal empirical Bayes: cell means m_i with (cluster-robust) standard errors s_i, true cell effects
    theta_i ~ N(mu, tau^2). tau^2 by DerSimonian-Laird; mu = precision-weighted mean with weights 1/(s_i^2 + tau^2);
    shrunk_i = B_i * mu + (1 - B_i) * m_i, B_i = s_i^2 / (s_i^2 + tau^2). Posterior variance includes the uncertainty in
    mu: (1 - B_i) s_i^2 + B_i^2 / sum(w). Returns mu, tau, Q, per-cell shrunk mean, interval and shrinkage weight B.
    cells = {label: (mean, se)}. Applies when cells are exchangeable (same sport / family / arm, different leaves) and
    their errors are independent; cells sharing games are positively dependent, so use clustered SEs and read tau as a
    lower bound on heterogeneity. Does not apply to a single cell, or to cells that differ by design (headline vs props)."""
    labels = list(cells)
    k = len(labels)
    if k < 2:
        raise ValueError("need at least 2 cells")
    m = [cells[l][0] for l in labels]
    s2 = [cells[l][1] ** 2 for l in labels]
    if any(v <= 0 or math.isnan(v) for v in s2):
        raise ValueError("every cell needs a positive finite se")
    w = [1.0 / v for v in s2]
    sw = sum(w)
    mu_f = sum(wi * mi for wi, mi in zip(w, m)) / sw
    q = sum(wi * (mi - mu_f) ** 2 for wi, mi in zip(w, m))
    c = sw - sum(wi * wi for wi in w) / sw
    tau2 = max(0.0, (q - (k - 1)) / c) if c > 0 else 0.0
    ws = [1.0 / (v + tau2) for v in s2]
    sws = sum(ws)
    mu = sum(wi * mi for wi, mi in zip(ws, m)) / sws
    z = _z(level)
    out = []
    for lab, mi, v in zip(labels, m, s2):
        b = v / (v + tau2)
        sh = b * mu + (1.0 - b) * mi
        pv = (1.0 - b) * v + b * b / sws
        out.append({"cell": lab, "raw": mi, "raw_se": math.sqrt(v), "shrunk": sh, "post_se": math.sqrt(pv),
                    "lo": sh - z * math.sqrt(pv), "hi": sh + z * math.sqrt(pv), "B": b})
    return {"mu": mu, "se_mu": math.sqrt(1.0 / sws), "tau": math.sqrt(tau2), "Q": q, "df": k - 1,
            "i2": max(0.0, (q - (k - 1)) / q) if q > 0 else 0.0, "cells": out}
