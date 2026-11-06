"""Tails (W103.1, B-044): peaks-over-threshold GPD, VaR / expected shortfall, and drawdown-breach resampling.

All functions are pure and take losses as POSITIVE numbers (a loss of 3 is 3). Resample whole clusters
(a day or a game), never single bets - bets inside one game or day are not independent.

WHEN THE GPD FIT APPLIES: a sample of cluster-level losses that is roughly independent across clusters and has at
least `min_exc` exceedances over the threshold (default 15). WHEN IT DOES NOT: fewer exceedances (`status="TOO_FEW"`,
no level is quoted), or any single binary contract's own loss (bounded at its stake, so EVT is undefined there).
Quantiles beyond the sample (m > n) are extrapolations and are labelled by the caller.

WHEN THE BREACH SIMULATOR APPLIES: a book whose stake is a fixed fraction of current bankroll per bet, with a
measured cluster return distribution. It is bootstrap-only: it cannot produce a loss worse than the worst observed
cluster unless a fitted tail is passed in. Money math is NOT here: per-bet P&L comes from `quant/money.py`.
"""
from __future__ import annotations

import numpy as np
from scipy import stats

MIN_EXC = 15


def mean_excess(x, thresholds):
    """Mean excess e(u) = E[X - u | X > u] at each threshold (None where nothing exceeds). A GPD tail has e(u) linear in u."""
    x = np.asarray(x, float)
    out = []
    for u in thresholds:
        e = x[x > u] - u
        out.append(float(e.mean()) if len(e) else None)
    return out


def pot_fit(losses, q=0.75, min_exc=MIN_EXC):
    """GPD fit to exceedances of `losses` over the q-quantile (maximum likelihood, location fixed at 0)."""
    x = np.asarray(losses, float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return {"status": "TOO_FEW", "n": 0, "n_exc": 0}
    u = float(np.quantile(x, q))
    exc = x[x > u] - u
    if len(exc) < min_exc:
        return {"status": "TOO_FEW", "n": int(len(x)), "n_exc": int(len(exc)), "u": u, "q": q}
    xi, _, sigma = stats.genpareto.fit(exc, floc=0.0)
    return {"status": "OK", "n": int(len(x)), "n_exc": int(len(exc)), "u": u, "q": q,
            "xi": float(xi), "sigma": float(sigma)}


def choose_threshold(losses, qs=(0.5, 0.6, 0.7, 0.8, 0.9), min_exc=MIN_EXC, tol=0.15):
    """Threshold by shape stability: the lowest q whose shape estimate stays within `tol` of the next two valid
    thresholds' estimates (lowest keeps the most exceedances). Falls back to the highest valid q, flagged unstable.
    Returns {'fit', 'stable', 'scan'}; fit is a TOO_FEW fit if no q has `min_exc` exceedances."""
    scan = [pot_fit(losses, q=q, min_exc=min_exc) for q in qs]
    ok = [f for f in scan if f["status"] == "OK"]
    if not ok:
        return {"fit": scan[0] if scan else {"status": "TOO_FEW", "n": 0, "n_exc": 0}, "stable": False, "scan": scan}
    for i, f in enumerate(ok):
        nxt = ok[i + 1:i + 3]
        if len(nxt) == 2 and all(abs(f["xi"] - g["xi"]) <= tol for g in nxt):
            return {"fit": f, "stable": True, "scan": scan}
    return {"fit": ok[-1], "stable": False, "scan": scan}


def var(fit, p):
    """Value at risk at confidence p (e.g. 0.99): the loss exceeded with probability 1 - p. Needs an OK fit and
    1 - p below the exceedance probability (otherwise the point is inside the body, not the tail -> None)."""
    if fit.get("status") != "OK":
        return None
    p_u = fit["n_exc"] / fit["n"]
    tail = 1.0 - p
    if tail <= 0 or tail >= p_u:
        return None
    xi, s, u = fit["xi"], fit["sigma"], fit["u"]
    r = tail / p_u
    if abs(xi) < 1e-9:
        return float(u - s * np.log(r))
    return float(u + s / xi * (r ** (-xi) - 1.0))


def expected_shortfall(fit, p):
    """Expected loss given the loss exceeds VaR_p. Finite only for shape xi < 1 (otherwise None)."""
    v = var(fit, p)
    if v is None or fit["xi"] >= 1.0:
        return None
    return float((v + fit["sigma"] - fit["xi"] * fit["u"]) / (1.0 - fit["xi"]))


def shape_ci(losses, q=0.75, n_boot=500, seed=20261105, min_exc=MIN_EXC):
    """95% percentile interval for the shape xi from cluster resampling of `losses` (one entry per cluster).
    Returns {'xi', 'lo', 'hi', 'class', 'fail_rate'}; class is 'heavy' (lo > 0.1), 'light' (hi < 0.1) or 'undetermined'."""
    x = np.asarray(losses, float)
    base = pot_fit(x, q=q, min_exc=min_exc)
    if base["status"] != "OK":
        return {"xi": None, "lo": None, "hi": None, "class": "too_few", "fail_rate": None}
    rng = np.random.default_rng(seed)
    xs, fails = [], 0
    for _ in range(n_boot):
        f = pot_fit(rng.choice(x, size=len(x), replace=True), q=q, min_exc=min_exc)
        if f["status"] == "OK":
            xs.append(f["xi"])
        else:
            fails += 1
    if len(xs) < 50:
        return {"xi": base["xi"], "lo": None, "hi": None, "class": "undetermined", "fail_rate": fails / n_boot}
    lo, hi = float(np.percentile(xs, 2.5)), float(np.percentile(xs, 97.5))
    cls = "heavy" if lo > 0.1 else "light" if hi < 0.1 else "undetermined"
    return {"xi": base["xi"], "lo": lo, "hi": hi, "class": cls, "fail_rate": fails / n_boot}


def max_drawdown_frac(returns):
    """Max peak-to-trough fall of compounded equity, per path. `returns` rows = paths, columns = steps, each the
    fractional equity change of that step (-0.02 = down 2%). Equity starts at 1 and is floored at 0."""
    r = np.maximum(np.asarray(returns, float), -1.0)
    eq = np.cumprod(1.0 + r, axis=1)
    eq = np.concatenate([np.ones((eq.shape[0], 1)), eq], axis=1)
    peak = np.maximum.accumulate(eq, axis=1)
    return ((peak - eq) / peak).max(axis=1)


def breach_probability(cluster_returns, stake_frac, horizon, dd_limit=0.20, day_limit=0.15,
                       n_paths=20000, n_outer=200, seed=20261105, tail_fit=None):
    """Probability that a book trips (a) the max-drawdown kill switch (`dd_limit` fall from peak equity) and (b) the
    daily breaker (a step falling `day_limit` or more) within `horizon` steps.

    `cluster_returns`: one number per observed cluster-step (a day): the sum over that day's bets of
    (P&L per $ staked). With `stake_frac` of bankroll staked per bet, the day's equity change is stake_frac * that sum.
    Outer loop resamples the observed days (so the interval carries the sampling error of the book itself); the inner
    loop draws `n_paths` paths of `horizon` days from that resample. `tail_fit` (a pot_fit on the losses of
    `cluster_returns`) replaces the empirical tail draws with fitted GPD draws. Returns point (pooled) and a 95% interval
    across outer resamples."""
    x = np.asarray(cluster_returns, float)
    if len(x) == 0:
        return None
    rng = np.random.default_rng(seed)
    per_outer = max(1, n_paths // n_outer)
    dd_hits, day_hits = [], []
    for _ in range(n_outer):
        base = rng.choice(x, size=len(x), replace=True)
        draws = rng.choice(base, size=(per_outer, horizon), replace=True)
        if tail_fit is not None and tail_fit.get("status") == "OK":
            loss = -draws
            hit = loss > tail_fit["u"]
            k = int(hit.sum())
            if k:
                loss[hit] = tail_fit["u"] + stats.genpareto.rvs(tail_fit["xi"], loc=0, scale=tail_fit["sigma"],
                                                                size=k, random_state=rng)
            draws = -loss
        step = stake_frac * draws
        dd_hits.append(float((max_drawdown_frac(step) >= dd_limit).mean()))
        day_hits.append(float((step.min(axis=1) <= -day_limit).mean()))
    def summ(v):
        return {"p": float(np.mean(v)), "lo": float(np.percentile(v, 2.5)), "hi": float(np.percentile(v, 97.5))}
    return {"drawdown_kill": summ(dd_hits), "daily_breaker": summ(day_hits), "horizon": horizon, "stake_frac": stake_frac}


def stake_for_breach(cluster_returns, horizon, target=0.05, dd_limit=0.20, lo=1e-5, hi=0.5, iters=18, **kw):
    """Largest per-bet stake fraction whose drawdown-kill breach probability within `horizon` stays <= `target`
    (bisection; breach probability rises with stake). Returns None if even `lo` breaches above target (the book's own
    drift breaches at any stake), else the stake fraction."""
    def p(s):
        return breach_probability(cluster_returns, s, horizon, dd_limit=dd_limit, **kw)["drawdown_kill"]["p"]
    if p(lo) > target:
        return None
    if p(hi) <= target:
        return hi
    a, b = lo, hi
    for _ in range(iters):
        m = (a + b) / 2
        if p(m) <= target:
            a = m
        else:
            b = m
    return float(a)
