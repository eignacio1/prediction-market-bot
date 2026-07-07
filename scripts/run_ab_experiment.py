#!/usr/bin/env python3
"""
run_ab_experiment — Driver for the A/B edge-delta harness (ab_harness.py)
Parent: EXP-017C / EXP-017B / GG-004

Registers the candidate "obvious fixes" from EXP-017B/017C as Strategy variants
and evaluates each vs baseline in BOTH modes:
    in_sample : select/score on all data  (shows the seductive in-sample gain)
    holdout   : fit/select on TRAIN days, score on TEST days (the valid test)

The point of the experiment: demonstrate that variants which look like
improvements in-sample are INCONCLUSIVE (or worse) out-of-sample — i.e. that at
current n they are noise-fitting, not defensible edge. This is the reusable
gate every future enhancer must pass.

Run:
  python3 scripts/run_ab_experiment.py
  python3 scripts/run_ab_experiment.py --cutoff 2026-07-03 --boot 10000 --seed 17
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ab_harness as H                        # noqa: E402
import run_exp017c_calibration_mlb as c17c    # noqa: E402

DEFAULT_PORTFOLIO = Path("logs/.vps_portfolio_cache_mlb.json")
OUT_DIR = Path("exp_output/EXP-017D-ABHARNESS")


def _platt_fitter(train: list[dict]) -> dict:
    if len(train) < 8:
        return {"a": 0.0, "b": 1.0}
    xs = [c17c.logit(r["_model_p"]) for r in train]
    ys = [r["_event"] for r in train]
    a, b = c17c.irls_logistic(xs, ys)
    return {"a": a, "b": b}


def _platt_rescore(rec: dict, params: dict) -> float:
    return c17c.sigmoid(params.get("a", 0.0) +
                        params.get("b", 1.0) * c17c.logit(rec["_model_p"]))


def build_strategies() -> tuple[H.Strategy, list[H.Strategy]]:
    baseline = H.Strategy(
        name="baseline",
        description="Take every resolved bet as-is (current book).",
        hypothesis="reference",
    )
    variants = [
        H.Strategy(
            name="quarantine_YES",
            description="Drop all YES-direction bets.",
            hypothesis="EXP-017B: YES is anti-predictive (-62%/staked, n=11) "
                       "-> removing it should IMPROVE the book.",
            select=lambda r: r["_dir"] == "NO",
        ),
        H.Strategy(
            name="min_edge_0.10",
            description="Keep only bets with recomputed fee-net-edge > 0.10.",
            hypothesis="EXP-017B: profit concentrates in the >0.10 tail -> "
                       "a min-edge filter should IMPROVE $/staked.",
            select=lambda r: r["_fne"] > 0.10,
        ),
        H.Strategy(
            name="YESquar+min_edge_0.03",
            description="Drop YES AND drop the near-zero edge band (<=0.03).",
            hypothesis="Combined 'reasonable' filter should IMPROVE the book.",
            select=lambda r: r["_dir"] == "NO" and r["_fne"] > 0.03,
        ),
        H.Strategy(
            name="platt_recal_edge>0",
            description="Recalibrate model_p via IRLS (fit on train), keep "
                        "bets whose recomputed edge stays > 0.",
            hypothesis="EXP-017C: calibration slope~0.85 -> recalibration "
                       "should barely change selection (near-null delta).",
            select=lambda r: r["_fne"] > 0.0,
            rescore=_platt_rescore,
        ),
    ]
    variants[-1]._fitter = _platt_fitter
    return baseline, variants


def _fmt_cmp(name: str, c: dict) -> str:
    mA, mB = c["metrics_A"], c["metrics_B"]
    if c.get("delta_ppd_point") is None:
        return f"  {name:<24} n_B={mB['n']:<3} {c['verdict']}"
    ci = c["delta_ppd_ci"]
    s = (f"  {name:<24} n_B={mB['n']:<3} "
         f"B $/staked={mB['pnl_per_dollar']*100:+6.2f}%  "
         f"Δ={c['delta_ppd_point']*100:+6.2f}pp "
         f"CI[{ci[0]*100:+.1f},{ci[1]*100:+.1f}] "
         f"P(Δ>0)={c['p_improve']*100:4.1f}%  {c['verdict']}")
    fd = c.get("filter_diag")
    if fd:
        s += (f"\n      └ removed n={fd['n_removed']} "
              f"removed $/staked={fd['removed_ppd']*100:+.1f}% "
              f"(pnl ${fd['removed_total_pnl']:+.2f})  "
              f"P(kept>removed)={fd['p_kept_gt_removed']*100:.1f}%")
    return s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--portfolio", type=Path, default=DEFAULT_PORTFOLIO)
    ap.add_argument("--cutoff", default="2026-07-03",
                    help="holdout: train < cutoff, test >= cutoff")
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=17)
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    args = ap.parse_args()

    recs = H.load(args.portfolio)
    report = {"meta": {"portfolio": str(args.portfolio), "n": len(recs),
                       "cutoff": args.cutoff, "boot": args.boot, "seed": args.seed}}

    print("=" * 100)
    print(f"A/B EDGE-DELTA HARNESS  |  n={len(recs)}  primary metric = pnl_per_$1_staked")
    print("=" * 100)

    for mode in ("in_sample", "holdout"):
        base, variants = build_strategies()   # fresh (params reset per mode)
        res = H.run_matrix(recs, base, variants, args.boot, args.seed,
                           mode=mode, cutoff=args.cutoff)
        report[mode] = res
        bm = res["baseline_metrics"]
        print(f"\n### MODE: {mode}   universe={res['universe']}")
        print(f"  baseline               n={bm['n']:<3} "
              f"$/staked={bm['pnl_per_dollar']*100:+6.2f}%  "
              f"EV/bet=${bm['ev_per_bet_usd']:+.3f}  PnL=${bm['total_pnl']:+.2f}")
        for name, c in res["comparisons"].items():
            print(_fmt_cmp(name, c))

    # invariants
    ins = report["in_sample"]
    report["invariants"] = {
        "baseline_n_in_sample": ins["baseline_metrics"]["n"],
        "holdout_train_plus_test":
            report["holdout"]["universe"]["n_train"] +
            report["holdout"]["universe"]["n_test"],
    }
    print("\n[invariants]", report["invariants"])

    args.out.mkdir(parents=True, exist_ok=True)
    out_json = args.out / "exp017d_abharness_results.json"
    out_json.write_text(json.dumps(report, indent=2, default=str))
    print(f"\nWrote {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
