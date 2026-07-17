"""
Calibration Diagnostics — link functions, IRLS logistic fit, reliability,
Murphy decomposition, ECE (T-280 WINDOW B / B4)

Component:    Analytics — sport-agnostic calibration diagnostics
Status:       NEW — 2026-07-09 (WINDOW B, math-rigor hardening, B4)

Purpose
-------
This logic originated in `scripts/run_exp017c_calibration_mlb.py` (EXP-017C,
the calibration root-cause analysis for the MLB non-monotonic-edge finding).
Three other scripts (`run_ab_experiment.py`, `run_band_monitor.py`,
`ab_harness.py`) subsequently grew a dependency on that script's module
namespace purely to reach these functions — none of them are EXP-017C-specific.
This module is the single source of truth; `run_exp017c_calibration_mlb.py`
re-exports these names so existing `import run_exp017c_calibration_mlb as c17c`
call sites are unaffected (see that file's imports).

Scope note (T-281, deliberately NOT resolved here)
----------------------------------------------------
`reliability()`/`ece()` below bin with `edges = [i / bins for i in range(bins
+ 1)]` (pure division). `c7_monitoring/monitor.py`'s `_compute_ece` bins with
`np.linspace(0.0, 1.0, n_bins + 1)`. These are numerically NOT always
identical (see `tests/test_t280_cross_implementation_invariants.py::
test_exact_decile_inputs_can_legitimately_diverge_between_implementations`
for a locked-in example — 0.28181818181818186 vs 0.40909090909090917 on
identical inputs, different bin-count conventions). `monitor.py`'s ECE feeds
a live, ADR-0004-governed drift-alert ladder (`ECE_BASELINE`, `ECE_L2_DELTA`)
calibrated against its own bin-edge numerics; changing that convention would
shift live alert thresholds and requires its own ADR-level review, not a
math-rigor test-suite pass. T-281 stays open and deferred — this module does
not touch `monitor.py`.

Design
------
Records are plain `dict`s carrying (at minimum) `_model_p` (float, forecast
probability of the reconstructed binary event) and `_event` (0/1, the
reconstructed outcome) — the convention already established by
`run_exp017b_decomp_mlb.load_records()`. Kept dependency-free (stdlib
`math`/`random` only) so it can be imported from any C-component or script
without pulling in numpy/pandas.
"""
from __future__ import annotations

import math
import random
from typing import Any

EPS = 1e-9


# ── link functions ────────────────────────────────────────────────────────────

def logit(p: float) -> float:
    p = min(1.0 - EPS, max(EPS, p))
    return math.log(p / (1.0 - p))


def sigmoid(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


# ── IRLS 2-param logistic:  event ~ a + b*logit(model_p) ───────────────────────

def irls_logistic(xs: list[float], ys: list[int], iters: int = 50) -> tuple[float, float]:
    """Fit logit(P(y=1)) = a + b*x by iteratively reweighted least squares.
    Returns (a, b). x is expected to be logit(model_p)."""
    a, b = 0.0, 1.0
    n = len(xs)
    if n < 3:
        return (0.0, 1.0)
    for _ in range(iters):
        # accumulate Fisher information (2x2) and score (2,)
        s00 = s01 = s11 = 0.0
        g0 = g1 = 0.0
        for x, y in zip(xs, ys):
            p = sigmoid(a + b * x)
            w = max(p * (1.0 - p), EPS)
            r = y - p
            g0 += r
            g1 += r * x
            s00 += w
            s01 += w * x
            s11 += w * x * x
        det = s00 * s11 - s01 * s01
        if abs(det) < EPS:
            break
        # Newton step: delta = I^{-1} g
        da = (s11 * g0 - s01 * g1) / det
        db = (-s01 * g0 + s00 * g1) / det
        a += da
        b += db
        if abs(da) < 1e-8 and abs(db) < 1e-8:
            break
    return (a, b)


# ── reliability / scoring ───────────────────────────────────────────────────────

def reliability(recs: list[dict[str, Any]], bins: int) -> list[dict[str, Any]]:
    """Equal-width model_p bins -> (n, mean_forecast, empirical_rate)."""
    edges = [i / bins for i in range(bins + 1)]
    rows = []
    for i in range(bins):
        lo, hi = edges[i], edges[i + 1]
        grp = [r for r in recs if (lo <= r["_model_p"] < hi) or
               (i == bins - 1 and r["_model_p"] == hi)]
        if not grp:
            rows.append({"bin": f"[{lo:.2f},{hi:.2f})", "n": 0})
            continue
        n = len(grp)
        f = sum(r["_model_p"] for r in grp) / n
        o = sum(r["_event"] for r in grp) / n
        rows.append({"bin": f"[{lo:.2f},{hi:.2f})", "n": n,
                     "mean_forecast": f, "empirical_rate": o,
                     "gap": f - o})
    return rows


def brier_murphy(recs: list[dict[str, Any]], bins: int) -> dict[str, Any]:
    """Brier score and its Murphy 3-component decomposition.

    The identity REL - RES + UNC == *binned* Brier holds exactly (forecasts
    replaced by their per-bin means). The full-resolution Brier exceeds the
    binned Brier by the within-bin forecast variance (WBV >= 0), which is
    reported separately rather than swept into a false residual.
    """
    n = len(recs)
    o_bar = sum(r["_event"] for r in recs) / n
    brier_full = sum((r["_model_p"] - r["_event"]) ** 2 for r in recs) / n
    rows = reliability(recs, bins)
    # bin membership for within-bin variance
    def bin_of(p: float) -> int:
        i = min(int(p * bins), bins - 1)
        return i
    fbar: dict[int, list[float]] = {i: [] for i in range(bins)}
    for r in recs:
        fbar[bin_of(r["_model_p"])].append(r["_model_p"])
    means = {i: (sum(v) / len(v) if v else 0.0) for i, v in fbar.items()}
    # Brier computed directly with per-bin mean forecasts (independent of the
    # decomposition) -- REL - RES + UNC must equal THIS exactly (Murphy identity).
    brier_binned_direct = sum(
        (means[bin_of(r["_model_p"])] - r["_event"]) ** 2 for r in recs) / n
    rel = res = 0.0
    for row in rows:
        if row["n"] == 0:
            continue
        nk = row["n"]
        rel += nk * (row["mean_forecast"] - row["empirical_rate"]) ** 2
        res += nk * (row["empirical_rate"] - o_bar) ** 2
    rel /= n
    res /= n
    unc = o_bar * (1.0 - o_bar)
    decomposition = rel - res + unc
    return {"brier_full": brier_full, "brier_binned": brier_binned_direct,
            "reliability": rel, "resolution": res, "uncertainty": unc,
            "decomposition_(rel-res+unc)": decomposition,
            "binning_gap_(full-binned)": brier_full - brier_binned_direct,
            "base_rate": o_bar,
            "recompose_ok": abs(decomposition - brier_binned_direct) < 1e-9}


def ece(recs: list[dict[str, Any]], bins: int) -> float:
    n = len(recs)
    tot = 0.0
    for row in reliability(recs, bins):
        if row["n"] == 0:
            continue
        tot += (row["n"] / n) * abs(row["mean_forecast"] - row["empirical_rate"])
    return tot


def calib_fit_ci(recs: list[dict[str, Any]], boot: int, rng: random.Random) -> dict[str, Any]:
    xs = [logit(r["_model_p"]) for r in recs]
    ys = [r["_event"] for r in recs]
    a, b = irls_logistic(xs, ys)
    n = len(recs)
    bs_a, bs_b = [], []
    for _ in range(boot):
        idx = [rng.randrange(n) for _ in range(n)]
        aa, bb = irls_logistic([xs[i] for i in idx], [ys[i] for i in idx])
        bs_a.append(aa); bs_b.append(bb)
    bs_a.sort(); bs_b.sort()
    def ci(v: list[float]) -> tuple[float, float]: return (v[int(0.025 * boot)], v[min(int(0.975 * boot), boot - 1)])
    la, ha = ci(bs_a); lb, hb = ci(bs_b)
    return {"intercept_a": a, "slope_b": b,
            "a_ci": [la, ha], "b_ci": [lb, hb],
            "b_excludes_1": not (lb <= 1.0 <= hb),
            "interpretation": ("overconfident" if b < 1 else
                               "underconfident" if b > 1 else "calibrated")}
