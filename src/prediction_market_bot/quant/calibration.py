"""Calibration: reliability bins, ECE, Murphy decomposition, slope/intercept."""
from __future__ import annotations

import math
from typing import Sequence

N_BINS = 10


def reliability_bins(ps: Sequence[float], ys: Sequence[float], n_bins: int = N_BINS) -> list[dict]:
    """Equal-width bins on [0,1]; p == 1.0 falls in the last bin. Applies at any n, but bins with n < ~10 are noise."""
    bins: list[list[tuple[float, float]]] = [[] for _ in range(n_bins)]
    for p, y in zip(ps, ys):
        bins[min(int(p * n_bins), n_bins - 1)].append((p, y))
    return [{"lo": i / n_bins, "hi": (i + 1) / n_bins, "n": len(b),
             "mean_p": sum(p for p, _ in b) / len(b) if b else None,
             "obs_freq": sum(y for _, y in b) / len(b) if b else None} for i, b in enumerate(bins)]


def ece(ps: Sequence[float], ys: Sequence[float], n_bins: int = N_BINS) -> float:
    """Expected calibration error (n-weighted mean |mean_p - obs|). Biased UP at small n; compare only at similar n and bins."""
    n = len(ps)
    return sum(b["n"] / n * abs(b["mean_p"] - b["obs_freq"]) for b in reliability_bins(ps, ys, n_bins) if b["n"])


def murphy(ps: Sequence[float], ys: Sequence[float], n_bins: int = N_BINS) -> dict:
    """Murphy decomposition. rel - res + unc equals the BINNED Brier (forecasts replaced by bin means) exactly;
    full Brier = binned + within-bin variance (reported as `within_bin`, >= 0). Applies to binary y in {0,1};
    a 0.5 push breaks the identity (use rows with y in {0,1})."""
    n = len(ps)
    ybar = sum(ys) / n
    rel = res = 0.0
    bins = reliability_bins(ps, ys, n_bins)
    for b in bins:
        if b["n"]:
            rel += b["n"] * (b["mean_p"] - b["obs_freq"]) ** 2
            res += b["n"] * (b["obs_freq"] - ybar) ** 2
    rel, res, unc = rel / n, res / n, ybar * (1 - ybar)
    full = sum((p - y) ** 2 for p, y in zip(ps, ys)) / n
    return {"brier": full, "brier_binned": rel - res + unc, "reliability": rel, "resolution": res,
            "uncertainty": unc, "within_bin": full - (rel - res + unc), "bins": n_bins}


def _logit(p: float) -> float:
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def slope_intercept(ps: Sequence[float], ys: Sequence[float], iters: int = 50) -> tuple[float, float]:
    """Logistic recalibration y ~ sigmoid(a + b*logit(p)) -> (intercept a, slope b) by Newton/IRLS.
    b < 1 = overconfident, b > 1 = underconfident. Applies to y in {0,1} with both classes present and p non-constant;
    returns (nan, nan) otherwise. Separation (perfect prediction) is damped by a small ridge (1e-6)."""
    xs, y = [_logit(p) for p in ps], list(ys)
    if len(set(y)) < 2 or max(xs) - min(xs) < 1e-12:
        return float("nan"), float("nan")
    a, b = 0.0, 1.0
    for _ in range(iters):
        g0 = g1 = h00 = h01 = h11 = 0.0
        for x, yi in zip(xs, y):
            q = 1 / (1 + math.exp(-(a + b * x)))
            w = q * (1 - q) + 1e-12
            g0 += yi - q; g1 += (yi - q) * x
            h00 += w; h01 += w * x; h11 += w * x * x
        h00 += 1e-6; h11 += 1e-6
        det = h00 * h11 - h01 * h01
        da, db = (h11 * g0 - h01 * g1) / det, (h00 * g1 - h01 * g0) / det
        a, b = a + da, b + db
        if abs(da) + abs(db) < 1e-10:
            break
    return a, b
