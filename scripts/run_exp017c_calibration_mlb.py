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
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_exp017_mlb as e17          # noqa: E402  fee/edge helpers
import run_exp017b_decomp_mlb as d17b  # noqa: E402  loader + edge buckets

# T-280/B4 (WINDOW B, 2026-07-09): link functions, IRLS fit, reliability,
# Murphy decomposition, and ECE were lifted into a shared, dependency-free
# module (src/prediction_market_bot/analytics/calibration_diagnostics.py) so
# run_ab_experiment.py / run_band_monitor.py / ab_harness.py — none of which
# are EXP-017C-specific — stop reaching into this script's module namespace
# for generic calibration math. Imported (not just called) so every existing
# `import run_exp017c_calibration_mlb as c17c; c17c.<name>(...)` call site,
# and `tests/test_t280_cross_implementation_invariants.py`'s
# `from run_exp017c_calibration_mlb import brier_murphy, ece`, keep working
# unchanged — this file is now a thin re-export + EXP-017C-specific wrapper.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from prediction_market_bot.analytics.calibration_diagnostics import (  # noqa: E402
    EPS,
    logit,
    sigmoid,
    irls_logistic,
    reliability,
    brier_murphy,
    ece,
    calib_fit_ci,
)

DEFAULT_PORTFOLIO = Path("logs/.vps_portfolio_cache_mlb.json")
OUT_DIR = Path("exp_output/EXP-017C-CALIB")


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
