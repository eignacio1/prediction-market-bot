"""Peaks-over-threshold (generalized Pareto) tails for per-game losses and drawdown depth (W88.1).

WHEN IT APPLIES: losses are roughly independent ACROSS games (resample whole games, never bets) and
there are enough exceedances over the threshold to estimate a shape (rule used here: >= MIN_EXC = 15).
WHEN IT DOES NOT: fewer than MIN_EXC exceedances -> `fit_pot` returns status="TOO_FEW" and no level is
quoted from the fit; the empirical quantile (if the sample even reaches that far) is the only number.
A 1-in-1,000 level needs > 1,000 games to be observed; below that it is an extrapolation of the fitted
tail and is labelled `extrapolated`.
"""
from __future__ import annotations

import numpy as np
from scipy import stats

MIN_EXC = 15


def fit_pot(losses, q=0.75, min_exc=MIN_EXC):
    """Fit a GPD to exceedances of `losses` (positive = loss) over the q-quantile. Pure."""
    x = np.asarray(losses, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return {"status": "TOO_FEW", "n": 0, "n_exc": 0}
    u = float(np.quantile(x, q))
    exc = x[x > u] - u
    if len(exc) < min_exc:
        return {"status": "TOO_FEW", "n": len(x), "n_exc": int(len(exc)), "u": u}
    xi, _, sigma = stats.genpareto.fit(exc, floc=0.0)
    return {"status": "OK", "n": len(x), "n_exc": int(len(exc)), "u": u, "xi": float(xi), "sigma": float(sigma)}


def return_level(fit, m):
    """Loss exceeded once in `m` games (m = 100, 1000). Needs an OK fit."""
    if fit.get("status") != "OK":
        return None
    p_u = fit["n_exc"] / fit["n"]
    xi, s, u = fit["xi"], fit["sigma"], fit["u"]
    r = m * p_u
    if r <= 1:                      # inside the sample's own body; not a tail question
        return None
    if abs(xi) < 1e-9:
        return float(u + s * np.log(r))
    return float(u + s / xi * (r ** xi - 1.0))


def normal_level(losses, m):
    """What a normal fit would say for the same 1-in-m game loss."""
    x = np.asarray(losses, float)
    return float(x.mean() + x.std(ddof=1) * stats.norm.isf(1.0 / m))


def cluster_bootstrap_levels(losses, ms=(100, 1000), q=0.75, n_boot=1000, seed=20261027):
    """Resample games (the unit of `losses`), refit, return per-m 95% percentile interval + fit-fail rate."""
    x = np.asarray(losses, float)
    rng = np.random.default_rng(seed)
    out = {m: [] for m in ms}
    fails = 0
    for _ in range(n_boot):
        f = fit_pot(rng.choice(x, size=len(x), replace=True), q=q)
        if f["status"] != "OK":
            fails += 1
            continue
        for m in ms:
            v = return_level(f, m)
            if v is not None and np.isfinite(v):
                out[m].append(v)
    ci = {m: (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) if len(v) >= 50 else None
          for m, v in out.items()}
    return ci, fails / n_boot


def sample_tail_model(losses, fit, size, rng):
    """Draw game losses: empirical below the threshold, fitted GPD above it (smoothed bootstrap)."""
    x = np.asarray(losses, float)
    if fit.get("status") != "OK":
        return rng.choice(x, size=size, replace=True)
    d = rng.choice(x, size=size, replace=True)
    hit = d > fit["u"]              # replace the empirical tail draws themselves; do not add tail mass
    d[hit] = fit["u"] + stats.genpareto.rvs(fit["xi"], loc=0, scale=fit["sigma"], size=int(hit.sum()), random_state=rng)
    return d


def max_drawdown(pnl_paths):
    """Max peak-to-trough drop of cumulative P&L, per path (rows = paths). Starts from 0."""
    c = np.cumsum(pnl_paths, axis=1)
    peak = np.maximum.accumulate(np.concatenate([np.zeros((c.shape[0], 1)), c], axis=1), axis=1)[:, 1:]
    return (peak - c).max(axis=1)


def drawdown_levels(game_pnl, n_games, fit=None, n_paths=40000, seed=20261027, qs=(0.99, 0.999)):
    """Bootstrap n_games-long paths of game P&L (iid across games); optional GPD-smoothed loss tail.
    Returns max-drawdown quantiles in the same unit as game_pnl."""
    rng = np.random.default_rng(seed)
    g = np.asarray(game_pnl, float)
    if fit is None or fit.get("status") != "OK":
        paths = rng.choice(g, size=(n_paths, n_games), replace=True)
    else:
        flat = sample_tail_model(-g, fit, n_paths * n_games, rng)   # losses -> negate for pnl
        paths = -flat.reshape(n_paths, n_games)
    dd = max_drawdown(paths)
    return {f"q{q}": float(np.quantile(dd, q)) for q in qs}
