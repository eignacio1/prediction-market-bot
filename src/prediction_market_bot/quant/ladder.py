"""W86.2 ladder helpers: parse a Kalshi strike ladder, fit the implied margin/total distribution.

Pure functions, no I/O. Measure-only (no order path). Candidates for the quant core are named in
results_W86.md; nothing here imports other blocks' code.

Strike rule (verified on 27 settled tickers, NFL/NBA/MLB spread/total/team-total): ticker suffix N
means floor_strike N-0.5, i.e. the contract pays on X > N-0.5 (equivalently X >= N for integer X).
"""
from __future__ import annotations

import math
import re
from datetime import datetime, timezone

import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm

_SUFFIX = re.compile(r"^([A-Za-z]*)(\d+)$")
_TS = re.compile(r"^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2}):(\d{2})(\.\d+)?(Z|[+-]\d{2}:?\d{2})?$")


def parse_ts(s: str) -> datetime:
    """Tolerant ISO parse (py3.9 rejects Kalshi's 5-digit fractions); always returns aware UTC."""
    m = _TS.match(s.strip())
    if not m:
        raise ValueError(f"bad timestamp {s!r}")
    d, hh, mm, ss, _frac, tz = m.groups()
    dt = datetime.fromisoformat(f"{d}T{hh}:{mm}:{ss}+00:00")
    if tz and tz != "Z":
        sign = 1 if tz[0] == "+" else -1
        digits = "".join(tz[1:].split(":"))
        from datetime import timedelta
        dt = dt - sign * timedelta(hours=int(digits[:2]), minutes=int(digits[2:]))
    return dt.astimezone(timezone.utc)


def parse_ticker(ticker: str):
    """'KXNFLSPREAD-26OCT04DENSF-SF8' -> (event_ticker, team_or_'' , strike=7.5)."""
    event, _, suffix = ticker.rpartition("-")
    m = _SUFFIX.match(suffix)
    if not event or not m:
        raise ValueError(f"unparseable ticker {ticker!r}")
    team, n = m.group(1), int(m.group(2))
    return event, team, n - 0.5


def survival_points(rows, kind: str):
    """Build (x, S, w_bid, w_ask) points for ONE event at ONE snapshot.

    rows: dicts with ticker, bid, ask (floats). kind 'total' -> S(x)=P(T>x) read directly.
    kind 'margin' -> reference team = alphabetically first code present; the other team's
    'wins by over k-0.5' contract is P(M_ref < -(k-0.5)) so it enters as (x=-(k-0.5), S=1-mid).
    Returns list of (x, mid) sorted by x.
    """
    pts = []
    teams = sorted({parse_ticker(r["ticker"])[1] for r in rows})
    ref = teams[0] if kind == "margin" else ""
    for r in rows:
        _, team, k = parse_ticker(r["ticker"])
        bid, ask = r["bid"], r["ask"]
        if bid is None or ask is None or ask < bid:
            continue
        mid = 0.5 * (bid + ask)
        if kind == "margin" and team != ref:
            pts.append((-k, 1.0 - mid))
        else:
            pts.append((k, mid))
    pts.sort()
    return pts


def fit_normal(pts, lo: float = 0.03, hi: float = 0.97, min_pts: int = 3):
    """Weighted probit-linear fit of S(x)=1-Phi((x-mu)/sigma). Returns dict or None.

    Applies when the ladder has >= min_pts strikes with mid in [lo,hi] and is roughly bell-shaped;
    fails (None) on 1-2 strike ladders, flat/non-monotone ladders (slope <= 0).
    """
    xs = np.array([p[0] for p in pts if lo <= p[1] <= hi], float)
    ss = np.array([p[1] for p in pts if lo <= p[1] <= hi], float)
    if len(xs) < min_pts:
        return None
    z = norm.ppf(1.0 - ss)
    # delta-method weights: var(z) ~ S(1-S)/phi(z)^2 (binomial-ish mid noise), so w = phi^2/(S(1-S))
    w = norm.pdf(z) ** 2 / (ss * (1.0 - ss))
    A = np.vstack([xs, np.ones_like(xs)]).T
    W = np.sqrt(w)[:, None]
    coef, *_ = np.linalg.lstsq(A * W, z * W[:, 0], rcond=None)
    a, b = coef
    if a <= 1e-9:
        return None
    sigma, mu = 1.0 / a, -b / a
    pred = 1.0 - norm.cdf((xs - mu) / sigma)
    return {"mu": float(mu), "sigma": float(sigma), "n": int(len(xs)),
            "rmse": float(np.sqrt(np.mean((pred - ss) ** 2)))}


def surv_normal(x, mu, sigma):
    return 1.0 - norm.cdf((np.asarray(x, float) - mu) / sigma)


# ---- key-number-aware discrete margin distribution --------------------------------------------
_M = np.arange(-70, 71)


def keynum_pmf(mu: float, sigma: float, w3: float, w7: float):
    """Discretised normal on integer margins with mass multipliers w3 at |m|=3 and w7 at |m|=7."""
    p = norm.cdf((_M + 0.5 - mu) / sigma) - norm.cdf((_M - 0.5 - mu) / sigma)
    p = np.where(np.abs(_M) == 3, p * w3, p)
    p = np.where(np.abs(_M) == 7, p * w7, p)
    return p / p.sum()


def surv_keynum(x, mu, sigma, w3, w7):
    """P(M > x) for half-integer x under the key-number pmf."""
    p = keynum_pmf(mu, sigma, w3, w7)
    tail = np.cumsum(p[::-1])[::-1]  # tail[i] = P(M >= _M[i])
    out = []
    for xi in np.atleast_1d(x):
        k = int(math.floor(xi) + 1)  # first integer strictly above xi
        out.append(tail[k - _M[0]] if _M[0] <= k <= _M[-1] else (1.0 if k < _M[0] else 0.0))
    return np.array(out)


def fit_keynum(pts, w3: float, w7: float, lo: float = 0.03, hi: float = 0.97, min_pts: int = 3):
    """Least-squares (mu, sigma) at FIXED key weights; returns dict with sse or None."""
    sel = [(x, s) for x, s in pts if lo <= s <= hi]
    if len(sel) < min_pts:
        return None
    xs = np.array([p[0] for p in sel]); ss = np.array([p[1] for p in sel])
    nf = fit_normal(pts, lo, hi, min_pts)
    x0 = [nf["mu"], nf["sigma"]] if nf else [0.0, 13.0]

    def sse(t):
        if t[1] < 1.0:
            return 1e3
        return float(np.sum((surv_keynum(xs, t[0], t[1], w3, w7) - ss) ** 2))

    r = minimize(sse, x0, method="Nelder-Mead", options={"xatol": 1e-3, "fatol": 1e-9, "maxiter": 400})
    return {"mu": float(r.x[0]), "sigma": float(r.x[1]), "sse": float(r.fun), "n": len(sel)}


def decompose(x, p_model, mid, fit_m, fit_k):
    """Split p_model - mid into CENTER, WIDTH (+ fit residual) using the two fitted normals.

    fit_m, fit_k: dicts with mu, sigma for model ladder and market ladder. Shapley average of the
    two orderings; also returns both orderings. width_only is the effect of replacing the model's
    sigma by the market's with the model's centre kept (=P_m - D).
    """
    x = np.asarray(x, float)
    Pm = surv_normal(x, fit_m["mu"], fit_m["sigma"])
    Pk = surv_normal(x, fit_k["mu"], fit_k["sigma"])
    C = surv_normal(x, fit_k["mu"], fit_m["sigma"])   # market centre, model width
    D = surv_normal(x, fit_m["mu"], fit_k["sigma"])   # model centre, market width
    width_wf = Pm - D          # width first
    center_wf = D - Pk
    center_cf = Pm - C         # centre first
    width_cf = C - Pk
    return {
        "delta_fit": Pm - Pk,
        "center": 0.5 * (center_wf + center_cf),
        "width": 0.5 * (width_wf + width_cf),
        "width_first": (width_wf, center_wf),
        "center_first": (center_cf, width_cf),
        "residual": (np.asarray(p_model, float) - np.asarray(mid, float)) - (Pm - Pk),
        "width_only": width_wf,
    }
