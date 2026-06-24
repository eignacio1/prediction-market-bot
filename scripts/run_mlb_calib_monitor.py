#!/usr/bin/env python3
"""
T-187F: MLB Calibration Monitor
=================================
Reads closed positions from paper_portfolio_mlb.json, computes ECE per
threshold (t=1, t=2), derives recommended calibration temperature T, reports
reliability buckets and anti-predictive check.

ADR-0027 (calibration policy) / GG-042 (t=3 excluded) / GG-004 (alpha gap)

Usage:
    python scripts/run_mlb_calib_monitor.py [path/to/paper_portfolio_mlb.json]

Exit codes:
  0 = CALIBRATED or insufficient data (n < MIN_N_DIAGNOSE for all thresholds)
  1 = MISCALIBRATED — ECE > 0.05 on at least one threshold (n >= MIN_N_DIAGNOSE)
  2 = ANTI_PREDICTIVE — edge>0 cohort wins at lower rate than edge<=0 cohort

Output is captured by cron → logs/mlb_calib_monitor.log.
Does NOT write to calibration.py — temperature changes require an ADR.

Minimum data requirements:
  MIN_N_DIAGNOSE = 50 positions per threshold for ECE diagnosis.
  Temperature derivation requires MIN_N_DIAGNOSE positions overall.
  Below threshold: CALIBRATED verdict returned, diagnosis deferred.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import numpy as np
    from scipy.optimize import minimize_scalar
except ImportError:
    print("requires numpy + scipy", file=sys.stderr)
    sys.exit(2)

_SRC_ROOT = Path(__file__).parent.parent
if str(_SRC_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT / "src"))

_DEFAULT_PORTFOLIO = _SRC_ROOT / "logs" / "paper_portfolio_mlb.json"

_MODEL_THRESHOLDS = frozenset({1, 2})   # t=3 excluded per GG-042
MIN_N_DIAGNOSE    = 50                  # min closed positions per threshold
ECE_THRESHOLD     = 0.05               # shadow gate pass threshold (ADR-0027)
_EPS              = 1e-6

# ---------------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------------

def _clip(p: float) -> float:
    return min(1.0 - _EPS, max(_EPS, p))


def _logit(p: np.ndarray) -> np.ndarray:
    return np.log(p / (1.0 - p))


def _sig(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def _brier(p: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean((p - y) ** 2))


def _logloss(p: np.ndarray, y: np.ndarray) -> float:
    p = np.clip(p, _EPS, 1.0 - _EPS)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def derive_temperature(P: np.ndarray, Y: np.ndarray) -> float:
    """Fit temperature T minimising log-loss of sigmoid(logit(P)/T).

    Mirrors derive_calibration.py. T>1 shrinks (overconfident model);
    T<1 sharpens (underconfident model); T=1 is identity.
    """
    res = minimize_scalar(
        lambda T: _logloss(_sig(_logit(P) / T), Y),
        bounds=(0.3, 8.0),
        method="bounded",
    )
    return float(res.x)


def compute_ece(P_cal: np.ndarray, Y: np.ndarray) -> float:
    """Expected Calibration Error over 5 reliability buckets [0.5, 1.0)."""
    n = len(Y)
    if n == 0:
        return 0.0
    ece = 0.0
    for lo, hi in [(0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.01)]:
        idx = (P_cal >= lo) & (P_cal < hi)
        n_b = int(idx.sum())
        if n_b:
            ece += (n_b / n) * abs(float(P_cal[idx].mean()) - float(Y[idx].mean()))
    return ece


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_positions(path: Path) -> list[dict]:
    """Load closed MLB positions from paper_portfolio_mlb.json.

    Mirrors _load_portfolio() in run_exp017_mlb.py but returns raw dicts
    rather than typed namedtuples — calibration monitor needs fewer fields.
    """
    with open(path) as fh:
        data = json.load(fh)
    out: list[dict] = []
    for p in data.get("closed_positions", []):
        if p.get("duplicate_of"):
            continue
        outcome = p.get("outcome", "")
        if outcome not in ("WIN", "LOSS"):
            continue
        raw_model_p = p.get("model_p")
        if raw_model_p is None:
            continue
        try:
            model_p = float(raw_model_p)
            mip     = float(p["mid_price_at_entry"])
        except (KeyError, TypeError, ValueError):
            continue
        direction = str(p.get("direction", "YES")).upper()
        try:
            threshold = int(p.get("threshold", p.get("kalshi_threshold", 0)))
        except (TypeError, ValueError):
            threshold = 0
        pnl = float(p.get("pnl", 0.0) or 0.0)
        out.append({
            "model_p":   model_p,
            "mip":       mip,
            "direction": direction,
            "outcome":   outcome,
            "threshold": threshold,
            "pnl":       pnl,
        })
    return out


def to_arrays(
    positions: list[dict],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Convert position dicts to directional (P, MIP, Y, PNL) numpy arrays.

    Directional frame: for YES bets P=model_p; for NO bets P=1-model_p.
    This is the same frame used in derive_calibration.py.
    """
    P, MIP, Y, PNL = [], [], [], []
    for pos in positions:
        yes = pos["direction"] == "YES"
        p   = _clip(pos["model_p"] if yes else 1.0 - pos["model_p"])
        m   = pos["mip"]   if yes else 1.0 - pos["mip"]
        P.append(p)
        MIP.append(m)
        Y.append(1.0 if pos["outcome"] == "WIN" else 0.0)
        PNL.append(pos["pnl"])
    return (
        np.array(P,   dtype=float),
        np.array(MIP, dtype=float),
        np.array(Y,   dtype=float),
        np.array(PNL, dtype=float),
    )


# ---------------------------------------------------------------------------
# Reporting helpers
# ---------------------------------------------------------------------------

def _print_reliability(label: str, P_cal: np.ndarray, Y: np.ndarray) -> None:
    print(f"\n-- Reliability ({label}, calibrated) --")
    any_printed = False
    for lo, hi in [(0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.01)]:
        idx = (P_cal >= lo) & (P_cal < hi)
        if idx.sum():
            any_printed = True
            print(f"  [{lo:.1f},{hi:.1f}) n={int(idx.sum()):3d}  "
                  f"pred={float(P_cal[idx].mean()):.3f}  "
                  f"actual={float(Y[idx].mean()):.3f}  "
                  f"gap={float(P_cal[idx].mean()) - float(Y[idx].mean()):+.3f}")
    if not any_printed:
        print("  (no positions in [0.5, 1.0) — all directional P below 0.5)")


def _diagnose_threshold(
    threshold: int,
    positions: list[dict],
    T_global: float,
) -> tuple[float | None, bool]:
    """Diagnose ECE for a single threshold using the global calibration T.

    Uses T_global (derived on all thresholds combined) to avoid underfitting
    on per-threshold sample sizes that may be < MIN_N_DIAGNOSE.

    Returns (ece, is_miscalibrated).
    ece is None when n < MIN_N_DIAGNOSE (insufficient data; not diagnosed).
    """
    n = len(positions)
    print(f"\n{'='*60}")
    print(f"THRESHOLD t={threshold}  (n={n})")
    print(f"{'='*60}")

    if n < MIN_N_DIAGNOSE:
        print(f"  [INSUFFICIENT DATA] {n}/{MIN_N_DIAGNOSE} required for ECE diagnosis.")
        return None, False

    P, MIP, Y, PNL = to_arrays(positions)
    PC  = _sig(_logit(P) / T_global)
    ece = compute_ece(PC, Y)
    status = "PASS" if ece <= ECE_THRESHOLD else "FAIL"

    print(f"\nRAW  Brier={_brier(P, Y):.4f}  LogLoss={_logloss(P, Y):.4f}  "
          f"mean_conf={float(P.mean()):.3f}  realized={float(Y.mean()):.3f}")
    print(f"CAL  Brier={_brier(PC, Y):.4f}  LogLoss={_logloss(PC, Y):.4f}  "
          f"mean_conf={float(PC.mean()):.3f}")
    print(f"ECE  {ece:.4f}  (threshold={ECE_THRESHOLD})  → {status}")
    _print_reliability(f"t={threshold}", PC, Y)

    return ece, ece > ECE_THRESHOLD


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else _DEFAULT_PORTFOLIO

    if not path.exists():
        print(f"[T-187F] Portfolio not found: {path} — no MLB positions yet. Exit 0.")
        return 0

    all_positions = load_positions(path)
    active = [p for p in all_positions if p["threshold"] in _MODEL_THRESHOLDS]
    n_total = len(active)

    print(f"\n[T-187F] MLB CALIBRATION MONITOR")
    print(f"Portfolio:        {path}")
    print(f"Closed positions: {n_total}  (t∈{{1,2}} only; t=3 excluded per GG-042)")

    if n_total == 0:
        print("[T-187F] No resolved positions with active thresholds. Exit 0.")
        return 0

    # Temperature derivation on full dataset for statistical power.
    # Per-threshold diagnosis reuses T_global to avoid underfitting.
    T_global = 1.0   # identity fallback when insufficient data
    if n_total >= MIN_N_DIAGNOSE:
        P_all, _, Y_all, _ = to_arrays(active)
        T_global = derive_temperature(P_all, Y_all)
        direction = "shrink" if T_global > 1 else ("sharpen" if T_global < 1 else "identity")
        print(f"\nRECOMMENDED TEMPERATURE T = {T_global:.3f}  ({direction})")
        print(f"Current MLB temperature:   1.000 (identity)")
        print("  (review before writing to c3_forecasting/calibration.py "
              "— model change requires ADR)")
    else:
        print(f"\n[T-187F] n={n_total} < {MIN_N_DIAGNOSE} — temperature derivation "
              f"deferred until {MIN_N_DIAGNOSE} resolved positions.")
        print(f"Current MLB temperature:   1.000 (identity)")

    # Per-threshold ECE diagnosis
    any_miscalibrated = False
    for t in sorted(_MODEL_THRESHOLDS):
        t_positions = [p for p in active if p["threshold"] == t]
        _, is_misc = _diagnose_threshold(t, t_positions, T_global)
        if is_misc:
            any_miscalibrated = True

    # Overall edge-realization + anti-predictive check
    if n_total >= MIN_N_DIAGNOSE:
        P_all, MIP_all, Y_all, PNL_all = to_arrays(active)
        PC_all = _sig(_logit(P_all) / T_global)
        edge   = PC_all - MIP_all - 0.07 * MIP_all * (1.0 - MIP_all)
        order  = np.argsort(edge)

        print(f"\n{'='*60}")
        print(f"OVERALL EDGE-REALIZATION (n={n_total})")
        print(f"{'='*60}")
        print("\n-- Edge-realization terciles (calibrated edge, low→high) --")
        for i, part in enumerate(np.array_split(order, 3)):
            print(f"  T{i+1}: edge[{float(edge[part].min()):+.3f},"
                  f"{float(edge[part].max()):+.3f}] "
                  f"n={len(part):3d}  winrate={float(Y_all[part].mean()):.3f}  "
                  f"P&L=${float(PNL_all[part].sum()):+.2f}")

        hi_edge = edge > 0
        anti_predictive = False
        if hi_edge.sum() and (~hi_edge).sum():
            wr_hi = float(Y_all[hi_edge].mean())
            wr_lo = float(Y_all[~hi_edge].mean())
            print(f"\n  ANTI-PREDICTIVE CHECK: edge>0 winrate={wr_hi:.3f} "
                  f"vs edge≤0 winrate={wr_lo:.3f}")
            if wr_hi < wr_lo:
                print("  *** WARNING: edge signal is ANTI-PREDICTIVE (GG-037) — "
                      "calibration does not imply alpha on MLB data. ***")
                anti_predictive = True
            else:
                print("  PASS: edge>0 cohort outperforms edge≤0.")
        elif not hi_edge.sum():
            print("\n  ANTI-PREDICTIVE CHECK: no positions with edge>0 — skipped.")
        else:
            print("\n  ANTI-PREDICTIVE CHECK: no positions with edge≤0 — skipped.")

        if anti_predictive:
            print(f"\n[T-187F] Result: ANTI_PREDICTIVE. Exit 2.")
            return 2

    if any_miscalibrated:
        print(f"\n[T-187F] Result: MISCALIBRATED — ECE > {ECE_THRESHOLD} on at "
              f"least one threshold. Exit 1.")
        return 1

    print(f"\n[T-187F] Result: CALIBRATED (or insufficient data for diagnosis). Exit 0.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
