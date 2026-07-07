#!/usr/bin/env python3
"""
EXP-017C MLB — Calibration Root-Cause of the Non-Monotonic Edge (Finding 3)
Parent: EXP-017B / EXP-017 / GG-004 / ADR-0024 / ADR-0004 (model class)

QUESTION
--------
EXP-017B found the model's edge signal is NON-MONOTONIC with realized profit:
mid-conviction bets (fee-net-edge 0.03-0.06) lose while both extremes behave.
A well-calibrated probability model should be monotonic. This experiment asks:

    Is the non-monotonicity a CALIBRATION defect (model_p != empirical event
    frequency, region-specific) or a PAYOFF/PRICING artifact (model_p fine, but
    vig/mip structure eats the mid band)?

The answer routes the fix:
    calibration defect  -> recalibrate model_p (Platt/logistic re-fit, ADR-0004)
    payoff artifact     -> bet-selection / min-edge rule, no model change

METHOD
------
Binary event reconstructed EXACTLY (verified 0/151 mismatch vs actual_hits):
    event = 1 if player reached kalshi_threshold else 0
          = (direction == "YES") == (outcome == "WIN")
Forecast = model_p (model P(hit >= threshold), YES-frame).

Diagnostics (all on the same deduped 151-position EXP-017 universe):
  1. Reliability diagram  : model_p bins -> mean forecast vs empirical rate
  2. Brier score + Murphy decomposition (reliability - resolution + uncertainty)
  3. ECE                  : Sum (n_k/N) |f_k - o_k|
  4. Logistic calibration : IRLS fit  logit(event) = a + b*logit(model_p)
                            b=1,a=0 perfect; b<1 overconfident; b>1 underconfident
                            bootstrap 95% CI on (a, b)
  5. Per-threshold split  : k=1 vs k=2 calibration separately
  6. Edge-realization     : per fee-net-edge bucket, decompose realized pnl vs
                            (i) model-expected pnl (what model_p implies) and
                            (ii) calibrated-expected pnl (what recalibrated p implies)
                            -> attributes the mid-band loss to calibration vs payoff

Methodology matches EXP-017/017B (same loader, dedup, direction-aware edge/GG-077).

Run:
  python3 scripts/run_exp017c_calibration_mlb.py
  python3 scripts/run_exp017c_calibration_mlb.py --bins 5 --boot 10000 --seed 17
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_exp017_mlb as e17          # noqa: E402  fee/edge helpers
import run_exp017b_decomp_mlb as d17b  # noqa: E402  loader + edge buckets

DEFAULT_PORTFOLIO = Path("logs/.vps_portfolio_cache_mlb.json")
OUT_DIR = Path("exp_output/EXP-017C-CALIB")
EPS = 1e-9


# ── link functions ───────────────────────────────────────────────────────────────

def logit(p: float) -> float:
    p = min(1.0 - EPS, max(EPS, p))
    return math.log(p / (1.0 - p))


def sigmoid(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


# ── IRLS 2-param logistic:  event ~ a + b*logit(model_p) ─────────────────────────

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


# ── reliability / scoring ─────────────────────────────────────────────────────────

def reliability(recs: list[dict], bins: int) -> list[dict]:
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


def brier_murphy(recs: list[dict], bins: int) -> dict:
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


def ece(recs: list[dict], bins: int) -> float:
    n = len(recs)
    tot = 0.0
    for row in reliability(recs, bins):
        if row["n"] == 0:
            continue
        tot += (row["n"] / n) * abs(row["mean_forecast"] - row["empirical_rate"])
    return tot


def calib_fit_ci(recs: list[dict], boot: int, rng: random.Random) -> dict:
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
    def ci(v): return (v[int(0.025 * boot)], v[min(int(0.975 * boot), boot - 1)])
    la, ha = ci(bs_a); lb, hb = ci(bs_b)
    return {"intercept_a": a, "slope_b": b,
            "a_ci": [la, ha], "b_ci": [lb, hb],
            "b_excludes_1": not (lb <= 1.0 <= hb),
            "interpretation": ("overconfident" if b < 1 else
                               "underconfident" if b > 1 else "calibrated")}


# ── edge realization: calibration-cause vs payoff-cause ──────────────────────────

def expected_pnl_per_dollar(direction: str, p_hit: float, mip: float, vig: float) -> float:
    """Expected pnl per $1 staked GIVEN a probability p_hit of the hit event,
    using the same half-vig entry price as compute_pnl_unit. Bet stake=$1."""
    half = vig / 2.0
    if direction == "YES":
        price = mip + half
        p_win = p_hit
    else:
        price = (1.0 - mip) + half
        p_win = 1.0 - p_hit
    # per $1 staked: win -> (1-price)/price ; loss -> -1
    if price <= 0:
        return 0.0
    return p_win * ((1.0 - price) / price) + (1.0 - p_win) * (-1.0)


def realized_pnl_per_dollar(recs: list[dict]) -> float:
    tot_size = sum(r["_size"] for r in recs)
    return (sum(r["_pnl"] for r in recs) / tot_size) if tot_size else 0.0


def edge_realization(recs: list[dict], a: float, b: float) -> list[dict]:
    """Per fee-net-edge bucket: realized vs model-expected vs calibrated-expected
    pnl per $1 staked. Splits the profit gap into calibration vs payoff."""
    buckets: dict[str, list[dict]] = {}
    for r in recs:
        buckets.setdefault(d17b.edge_bucket(r["_fne"]), []).append(r)
    rows = []
    for k in sorted(buckets):
        grp = buckets[k]
        n = len(grp)
        model_exp = sum(expected_pnl_per_dollar(r["_dir"], r["_model_p"],
                        r["_mip"], float(r.get("vig_at_entry", 0) or 0))
                        for r in grp) / n
        calib_exp = sum(expected_pnl_per_dollar(
                        r["_dir"], sigmoid(a + b * logit(r["_model_p"])),
                        r["_mip"], float(r.get("vig_at_entry", 0) or 0))
                        for r in grp) / n
        realized = realized_pnl_per_dollar(grp)
        rows.append({"bucket": k, "n": n,
                     "model_expected_$/staked": model_exp,
                     "calibrated_expected_$/staked": calib_exp,
                     "realized_$/staked": realized,
                     "calib_gap(model-calib)": model_exp - calib_exp,
                     "residual(calib-realized)": calib_exp - realized})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--portfolio", type=Path, default=DEFAULT_PORTFOLIO)
    ap.add_argument("--bins", type=int, default=5)
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=17)
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    args = ap.parse_args()
    rng = random.Random(args.seed)

    recs = d17b.load_records(args.portfolio)
    for r in recs:  # attach reconstructed binary event
        r["_event"] = 1 if ((r["_dir"] == "YES") == (r["_win"] == 1)) else 0

    fit = calib_fit_ci(recs, args.boot, rng)
    report = {
        "meta": {"portfolio": str(args.portfolio), "n": len(recs),
                 "bins": args.bins, "boot": args.boot, "seed": args.seed},
        "reliability_all": reliability(recs, args.bins),
        "brier_murphy_all": brier_murphy(recs, args.bins),
        "ece_all": ece(recs, args.bins),
        "calibration_fit_all": fit,
        "per_threshold": {},
        "edge_realization": edge_realization(recs, fit["intercept_a"], fit["slope_b"]),
        "invariants": {},
    }
    for k in sorted({r["_thr"] for r in recs}):
        grp = [r for r in recs if r["_thr"] == k]
        report["per_threshold"][f"k={k}"] = {
            "n": len(grp),
            "reliability": reliability(grp, args.bins),
            "brier_murphy": brier_murphy(grp, args.bins),
            "ece": ece(grp, args.bins),
            "calibration_fit": calib_fit_ci(grp, min(args.boot, 4000),
                                            random.Random(args.seed + k)),
        }

    # invariants
    bm = report["brier_murphy_all"]
    report["invariants"] = {
        "reliability_n_sums": sum(row["n"] for row in report["reliability_all"]),
        "murphy_recompose_ok": bm["recompose_ok"],  # binned + WBV == full Brier
        "n_total": len(recs),
    }

    args.out.mkdir(parents=True, exist_ok=True)
    out_json = args.out / "exp017c_calibration_results.json"
    out_json.write_text(json.dumps(report, indent=2))

    # ── console ──
    print("=" * 96)
    print(f"EXP-017C CALIBRATION ROOT-CAUSE  |  n={len(recs)}  |  {args.portfolio}")
    print("=" * 96)
    print("\n[reliability — ALL]  (perfect: mean_forecast == empirical_rate)")
    for row in report["reliability_all"]:
        if row["n"] == 0:
            print(f"  {row['bin']:<14} n=0"); continue
        print(f"  {row['bin']:<14} n={row['n']:<3} forecast={row['mean_forecast']:.3f} "
              f"empirical={row['empirical_rate']:.3f}  gap={row['gap']:+.3f}")
    print(f"\n[Brier/Murphy — ALL]  {bm}")
    print(f"[ECE — ALL] {report['ece_all']:.4f}")
    print(f"\n[calibration fit — ALL] a={fit['intercept_a']:+.3f} "
          f"b={fit['slope_b']:.3f}  b_CI={[round(x,3) for x in fit['b_ci']]}  "
          f"-> {fit['interpretation']} (b excludes 1: {fit['b_excludes_1']})")
    for k, v in report["per_threshold"].items():
        f = v["calibration_fit"]
        print(f"  {k}: n={v['n']} a={f['intercept_a']:+.3f} b={f['slope_b']:.3f} "
              f"b_CI={[round(x,3) for x in f['b_ci']]} -> {f['interpretation']}  "
              f"ECE={v['ece']:.3f} brier={v['brier_murphy']['brier_full']:.3f}")
    print("\n[edge realization — $/staked]  model_exp | calib_exp | realized")
    for row in report["edge_realization"]:
        print(f"  {row['bucket']:<14} n={row['n']:<3} "
              f"model={row['model_expected_$/staked']*100:+6.1f}%  "
              f"calib={row['calibrated_expected_$/staked']*100:+6.1f}%  "
              f"realized={row['realized_$/staked']*100:+7.1f}%  "
              f"(calib_gap={row['calib_gap(model-calib)']*100:+.1f}pp, "
              f"residual={row['residual(calib-realized)']*100:+.1f}pp)")
    print("\n[invariants]", report["invariants"])
    print(f"\nWrote {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
