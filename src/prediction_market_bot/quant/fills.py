"""Fill probability and post-fill markout (adverse selection) for resting orders. W104.1, B-048.

Descriptive and held-out only: nothing here places, sizes or gates an order.

Three tools, each with a known-answer test in tests/test_quant_fills.py:

  fit_logit / predict_logit      Ridge-stabilised logistic regression (IRLS) with Wald SEs.
                                 Applies when the outcome is binary and features are few and dense
                                 (fill / no fill; win / loss). Not for rare events with separation.
  person_period / fit_hazard     Discrete-time hazard for time-to-fill with cancellation as
                                 censoring: one row per (order, interval at risk). Applies when
                                 orders rest for a known, bounded time and are cancelled by the bot
                                 (right censoring that is independent of the unseen fill time).
  ols_cluster                    OLS with cluster-robust (CR1) SEs, for markout ~ features on fills.
                                 Clusters = games: fills in one game share an outcome path.
  gap_explained                  How much of the (fills - non-fills) win-rate gap is carried by
                                 OBSERVED covariates: re-weight non-fills to the fills' covariate mix
                                 with propensity odds (ATT weights). What remains after re-weighting
                                 is the part the covariates cannot explain (information in WHICH
                                 orders fill). Applies only inside the covariates' common support.

Features are plain numpy matrices; callers add the intercept via ``add_const``.
"""
from __future__ import annotations

from typing import Optional, Sequence

import numpy as np


def add_const(X: np.ndarray) -> np.ndarray:
    X = np.asarray(X, dtype=float)
    if X.ndim == 1:
        X = X[:, None]
    return np.hstack([np.ones((X.shape[0], 1)), X])


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -35, 35)))


def fit_logit(X: np.ndarray, y: np.ndarray, l2: float = 1e-4, w: Optional[np.ndarray] = None,
              iters: int = 60, tol: float = 1e-9) -> dict:
    """Logistic regression by IRLS. X must already include the intercept column (``add_const``).
    The intercept (column 0) is not penalised. Returns beta, se (Wald from the penalised Hessian), n, converged."""
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    n, k = X.shape
    w = np.ones(n) if w is None else np.asarray(w, float)
    pen = np.eye(k) * l2
    pen[0, 0] = 0.0
    beta = np.zeros(k)
    converged = False
    for _ in range(iters):
        p = _sigmoid(X @ beta)
        s = w * p * (1 - p) + 1e-12
        H = X.T @ (X * s[:, None]) + pen
        g = X.T @ (w * (y - p)) - pen @ beta
        step = np.linalg.solve(H, g)
        beta = beta + step
        if np.max(np.abs(step)) < tol:
            converged = True
            break
    p = _sigmoid(X @ beta)
    s = w * p * (1 - p) + 1e-12
    H = X.T @ (X * s[:, None]) + pen
    se = np.sqrt(np.diag(np.linalg.inv(H)))
    return {"beta": beta, "se": se, "n": int(n), "converged": converged}


def predict_logit(fit: dict, X: np.ndarray) -> np.ndarray:
    return _sigmoid(np.asarray(X, float) @ fit["beta"])


def person_period(durations: Sequence[float], filled: Sequence[bool], edges: Sequence[float]) -> tuple:
    """Expand orders to discrete-time rows. ``durations``: seconds from submit to fill (filled) or to
    cancel (not filled, censored). ``edges``: increasing interval upper bounds, e.g. (5, 15, 30, 60).
    Returns (order_index, interval_index, event) arrays; an order contributes a row for every interval it
    was still resting at the start of; event=1 only in the interval the fill landed in."""
    oi, ii, ev = [], [], []
    lo = [0.0] + list(edges[:-1])
    for i, (d, f) in enumerate(zip(durations, filled)):
        for j, (a, b) in enumerate(zip(lo, edges)):
            if d <= a:
                break
            hit = bool(f) and d <= b
            oi.append(i)
            ii.append(j)
            ev.append(1 if hit else 0)
            if d <= b:
                break
    return np.array(oi, int), np.array(ii, int), np.array(ev, int)


def fit_hazard(durations: Sequence[float], filled: Sequence[bool], X: np.ndarray, edges: Sequence[float],
               l2: float = 1e-4) -> dict:
    """Discrete-time fill hazard: logit h(interval, x) = a_interval + x'b. Interval effects are dummies
    (no separate intercept); X is the order-level feature matrix WITHOUT an intercept."""
    X = np.asarray(X, float)
    if X.ndim == 1:
        X = X[:, None]
    oi, ii, ev = person_period(durations, filled, edges)
    J = len(edges)
    D = np.zeros((len(oi), J))
    D[np.arange(len(oi)), ii] = 1.0
    Z = np.hstack([D, X[oi]])
    pen_cols = np.arange(J, Z.shape[1])  # interval dummies are unpenalised; ridge on features only
    beta, se = _ridge_irls_dummies(Z, ev.astype(float), pen_cols, l2)
    return {"alpha": beta[:J], "beta": beta[J:], "edges": list(edges), "rows": int(len(oi)),
            "events": int(ev.sum()), "se": se[J:]}


def _ridge_irls_dummies(Z: np.ndarray, y: np.ndarray, pen_cols: np.ndarray, l2: float, iters: int = 60) -> tuple:
    k = Z.shape[1]
    pen = np.zeros((k, k))
    pen[pen_cols, pen_cols] = l2
    beta = np.zeros(k)
    for _ in range(iters):
        p = _sigmoid(Z @ beta)
        s = p * (1 - p) + 1e-12
        H = Z.T @ (Z * s[:, None]) + pen + 1e-10 * np.eye(k)
        g = Z.T @ (y - p) - pen @ beta
        step = np.linalg.solve(H, g)
        beta = beta + step
        if np.max(np.abs(step)) < 1e-9:
            break
    p = _sigmoid(Z @ beta)
    s = p * (1 - p) + 1e-12
    H = Z.T @ (Z * s[:, None]) + pen + 1e-10 * np.eye(k)
    return beta, np.sqrt(np.diag(np.linalg.inv(H)))


def hazard_fill_by(h: dict, x: np.ndarray, horizon_s: float) -> float:
    """P(fill within ``horizon_s``) for one feature vector under the fitted hazard."""
    surv = 1.0
    lo = 0.0
    for a, b in zip(h["alpha"], h["edges"]):
        if lo >= horizon_s:
            break
        hz = float(_sigmoid(a + float(np.dot(h["beta"], x))))
        frac = min(1.0, (horizon_s - lo) / (b - lo))
        surv *= (1 - hz) ** frac
        lo = b
    return 1.0 - surv


def ols_cluster(X: np.ndarray, y: np.ndarray, clusters: Sequence) -> dict:
    """OLS with CR1 cluster-robust standard errors. X includes the intercept (``add_const``)."""
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    n, k = X.shape
    XtXi = np.linalg.pinv(X.T @ X)
    beta = XtXi @ X.T @ y
    e = y - X @ beta
    labels = np.asarray(clusters)
    uniq, inv = np.unique(labels, return_inverse=True)
    G = len(uniq)
    S = np.zeros((G, k))
    np.add.at(S, inv, X * e[:, None])
    meat = S.T @ S
    c = (G / max(G - 1, 1)) * ((n - 1) / max(n - k, 1))
    V = c * XtXi @ meat @ XtXi
    se = np.sqrt(np.clip(np.diag(V), 0, None))
    return {"beta": beta, "se": se, "n": int(n), "clusters": int(G)}


def calibration(p: np.ndarray, y: np.ndarray, bins: int = 10) -> dict:
    """Equal-count calibration table, expected calibration error and Brier score."""
    p = np.asarray(p, float)
    y = np.asarray(y, float)
    order = np.argsort(p)
    chunks = np.array_split(order, bins)
    rows, ece = [], 0.0
    for c in chunks:
        if len(c) == 0:
            continue
        mp, my = float(p[c].mean()), float(y[c].mean())
        rows.append({"n": int(len(c)), "mean_p": mp, "obs": my})
        ece += len(c) / len(p) * abs(mp - my)
    return {"bins": rows, "ece": ece, "brier": float(np.mean((p - y) ** 2)),
            "base_brier": float(np.mean((y.mean() - y) ** 2))}


def gap_explained(win: np.ndarray, filled: np.ndarray, p_fill: np.ndarray, clusters: Optional[Sequence] = None,
                  reps: int = 1000, seed: int = 11, clip: float = 0.02) -> dict:
    """Decompose ``win(fills) - win(non-fills)`` into the part covariates carry and the rest.

    p_fill: propensity of a fill given the OBSERVED covariates (from a model fitted elsewhere, e.g. on
    earlier days). Non-fills are re-weighted by p/(1-p) so their covariate mix matches the fills (ATT).
        raw       = mean_win[fills] - mean_win[non-fills]
        adjusted  = mean_win[fills] - weighted mean_win[non-fills]
        explained = raw - adjusted   (share = explained / raw)
    ``adjusted`` is what covariates cannot account for. Intervals: cluster bootstrap (clusters = games)."""
    win = np.asarray(win, float)
    f = np.asarray(filled, bool)
    p = np.clip(np.asarray(p_fill, float), clip, 1 - clip)

    def stat(idx: np.ndarray) -> Optional[tuple]:
        ff, nn = idx[f[idx]], idx[~f[idx]]
        if len(ff) == 0 or len(nn) == 0:
            return None
        w = p[nn] / (1 - p[nn])
        raw = win[ff].mean() - win[nn].mean()
        adj = win[ff].mean() - float(np.sum(w * win[nn]) / np.sum(w))
        return raw, adj

    base = stat(np.arange(len(win)))
    if base is None:
        raise ValueError("need both fills and non-fills")
    raw, adj = base
    out = {"n_fill": int(f.sum()), "n_nonfill": int((~f).sum()), "raw": raw, "adjusted": adj,
           "explained": raw - adj, "share_explained": (raw - adj) / raw if raw != 0 else float("nan")}
    if clusters is not None:
        lab = np.asarray(clusters)
        uniq, inv = np.unique(lab, return_inverse=True)
        groups = [np.where(inv == g)[0] for g in range(len(uniq))]
        rng = np.random.default_rng(seed)
        shares, adjs = [], []
        for _ in range(reps):
            pick = rng.integers(0, len(groups), len(groups))
            s = stat(np.concatenate([groups[g] for g in pick]))
            if s is None or s[0] == 0:
                continue
            shares.append((s[0] - s[1]) / s[0])
            adjs.append(s[1])
        if shares:
            out["share_ci90"] = (float(np.percentile(shares, 5)), float(np.percentile(shares, 95)))
            out["adjusted_ci90"] = (float(np.percentile(adjs, 5)), float(np.percentile(adjs, 95)))
        out["clusters"] = len(groups)
    return out
