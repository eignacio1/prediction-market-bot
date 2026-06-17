#!/usr/bin/env python3
"""Derive + report probability calibration from a resolved-bet dataset.

ADR-0027 / GG-037. Two jobs:

  1. DERIVE the temperature T for `c3_forecasting/calibration.py` from resolved
     paper-trade outcomes (re-runnable per sport — this is how MLB / NBA regular
     season get their own T instead of inheriting NBA Finals').
  2. REPORT calibration health (reliability buckets) and edge-realization
     deciles — the monitor mandated by GG-037 so overconfidence and edge
     inversion are caught automatically going forward, not by hand at season end.

Usage:
    python scripts/derive_calibration.py data/nba_finals_clean_dataset.csv

Expects columns: model_p, mid_price_at_entry, direction, outcome, realized_pnl.
`model_p` is the YES-frame model probability; `direction` in {YES, NO}; `outcome`
in {WIN, LOSS}. Reports in the DIRECTIONAL frame (the side actually bet).

This script does NOT write the temperature back into calibration.py — that is a
model change requiring an ADR. It prints the recommended value for human review.
"""
from __future__ import annotations

import csv
import math
import sys

try:
    import numpy as np
    from scipy.optimize import minimize_scalar
except ImportError:
    print("requires numpy + scipy", file=sys.stderr)
    sys.exit(2)

_EPS = 1e-6


def _clip(p: float) -> float:
    return min(1.0 - _EPS, max(_EPS, p))


def _load(path: str):
    P, MIP, Y, PNL = [], [], [], []
    with open(path) as fh:
        for r in csv.DictReader(fh):
            try:
                p = float(r["model_p"])
                m = float(r["mid_price_at_entry"])
            except (ValueError, KeyError, TypeError):
                continue
            yes = r["direction"].upper() == "YES"
            P.append(_clip(p if yes else 1.0 - p))
            MIP.append(m if yes else 1.0 - m)
            Y.append(1 if r["outcome"].upper() == "WIN" else 0)
            try:
                PNL.append(float(r.get("realized_pnl", 0.0) or 0.0))
            except ValueError:
                PNL.append(0.0)
    return np.array(P), np.array(MIP), np.array(Y), np.array(PNL)


def _logit(p):
    return np.log(p / (1.0 - p))


def _sig(x):
    return 1.0 / (1.0 + np.exp(-x))


def _brier(p, y):
    return float(np.mean((p - y) ** 2))


def _logloss(p, y):
    p = np.clip(p, _EPS, 1.0 - _EPS)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def derive_temperature(P, Y) -> float:
    """Fit T minimizing log-loss of sigmoid(logit(P)/T)."""
    res = minimize_scalar(
        lambda T: _logloss(_sig(_logit(P) / T), Y), bounds=(0.3, 8.0), method="bounded"
    )
    return float(res.x)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    P, MIP, Y, PNL = _load(path)
    n = len(P)
    if n == 0:
        print("no resolved rows found")
        return 1

    T = derive_temperature(P, Y)
    PC = _sig(_logit(P) / T)

    print(f"=== Calibration derivation — {path} (n={n}) ===")
    print(f"RAW    Brier={_brier(P, Y):.4f}  LogLoss={_logloss(P, Y):.4f}  "
          f"mean_conf={P.mean():.3f}  realized={Y.mean():.3f}")
    print(f"CAL    Brier={_brier(PC, Y):.4f}  LogLoss={_logloss(PC, Y):.4f}  "
          f"mean_conf={PC.mean():.3f}")
    print(f"\nRECOMMENDED TEMPERATURE T = {T:.3f}  "
          f"({'shrink' if T > 1 else 'sharpen' if T < 1 else 'identity'})")
    print("  (review before writing to c3_forecasting/calibration.py — model "
          "change requires ADR)")

    print("\n-- Reliability (directional, calibrated) --")
    for lo, hi in [(0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.01)]:
        idx = (PC >= lo) & (PC < hi)
        if idx.sum():
            print(f"  [{lo:.1f},{hi:.1f}) n={int(idx.sum()):3d}  "
                  f"pred={PC[idx].mean():.3f}  actual={Y[idx].mean():.3f}  "
                  f"gap={PC[idx].mean() - Y[idx].mean():+.3f}")

    # Edge-realization monitor (GG-037): does higher calibrated edge => better?
    edge = PC - MIP - 0.07 * MIP * (1.0 - MIP)
    order = np.argsort(edge)
    print("\n-- Edge-realization terciles (calibrated edge, low->high) --")
    for i, part in enumerate(np.array_split(order, 3)):
        print(f"  T{i + 1}: edge[{edge[part].min():+.3f},{edge[part].max():+.3f}] "
              f"n={len(part):3d}  winrate={Y[part].mean():.3f}  "
              f"P&L=${PNL[part].sum():+.2f}")
    hi_edge = edge > 0
    if hi_edge.sum() and (~hi_edge).sum():
        print(f"\n  ANTI-PREDICTIVE CHECK: edge>0 winrate={Y[hi_edge].mean():.3f} "
              f"vs edge<=0 winrate={Y[~hi_edge].mean():.3f}")
        if Y[hi_edge].mean() < Y[~hi_edge].mean():
            print("  *** WARNING: edge signal is anti-predictive on this dataset "
                  "(GG-037) — calibration does not imply alpha. ***")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
