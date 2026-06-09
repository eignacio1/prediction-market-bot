#!/usr/bin/env python3
"""
EXP-019C — Spread Characterization: Per-Band Spread Cost Model
Status: SKELETON — requires spread_observations.jsonl from ≥3 game nights of T4 data.

ADR-0018 §7 specifies: fit per-band models for:
  - spread_cost(time_remaining_min)
  - spread_cost(pts_so_far)
  - spread_cost(threshold)
to determine whether spread cost exceeds or is comparable to NOISE_BUFFER_BAND.

Data source: logs/spread_observations.jsonl
  Written by run_t4_live.py each cycle since: 2026-06-09 (Finals G4+)
  Fields: ticker, timestamp_utc, bid, ask, mid, time_remaining_min, pts_so_far, threshold

Run after: 3 game nights of data (est. Finals G4 Jun 10 + G5 Jun 12 + one more)
"""
import json
import sys
from pathlib import Path

PROJ      = Path(__file__).parent.parent
SPREAD_LOG = PROJ / "logs" / "spread_observations.jsonl"
OUT_PATH   = PROJ / "exp_output" / "EXP-019" / "EXP-019C_results.json"


def load_spread_observations() -> list[dict]:
    if not SPREAD_LOG.exists():
        print(f"ERROR: {SPREAD_LOG} does not exist.")
        print("run_t4_live.py writes this file during T4 cycles. Run Finals G4+ first.")
        sys.exit(1)
    obs = []
    with open(SPREAD_LOG) as f:
        for line in f:
            line = line.strip()
            if line:
                obs.append(json.loads(line))
    return obs


def compute_spread_stats(obs: list[dict]) -> dict:
    """
    For each observation: spread = ask - bid; spread_pct = spread / mid.
    Bin by time_remaining_min, pts_so_far, threshold and compute mean/p50/p90.
    """
    spreads = []
    for o in obs:
        bid, ask, mid = o["bid"], o["ask"], o["mid"]
        if bid is None or ask is None or mid is None or mid <= 0:
            continue
        spread = ask - bid
        spread_pct = spread / mid
        spreads.append({
            "ticker": o["ticker"],
            "spread": spread,
            "spread_pct": spread_pct,
            "time_remaining_min": o["time_remaining_min"],
            "pts_so_far": o["pts_so_far"],
            "threshold": o["threshold"],
        })

    if not spreads:
        return {"error": "no valid spread observations"}

    n = len(spreads)
    raw_spreads = sorted(s["spread"] for s in spreads)
    raw_spread_pcts = sorted(s["spread_pct"] for s in spreads)
    mean_spread = sum(raw_spreads) / n
    p50_spread  = raw_spreads[n // 2]
    p90_spread  = raw_spreads[int(n * 0.9)]
    mean_spread_pct = sum(raw_spread_pcts) / n
    p90_spread_pct  = raw_spread_pcts[int(n * 0.9)]

    # Time-bucket analysis: early (<20 min remaining), mid (10-20), late (<10)
    def bucket_stats(bucket: list[float]) -> dict:
        if not bucket:
            return {"n": 0, "mean": None, "p50": None, "p90": None}
        bucket_sorted = sorted(bucket)
        nb = len(bucket_sorted)
        return {
            "n": nb,
            "mean": sum(bucket_sorted) / nb,
            "p50": bucket_sorted[nb // 2],
            "p90": bucket_sorted[int(nb * 0.9)],
        }

    early_spreads = [s["spread"] for s in spreads if s["time_remaining_min"] > 20]
    mid_spreads   = [s["spread"] for s in spreads if 10 <= s["time_remaining_min"] <= 20]
    late_spreads  = [s["spread"] for s in spreads if s["time_remaining_min"] < 10]

    return {
        "n_total": n,
        "overall": {
            "mean_spread": round(mean_spread, 5),
            "p50_spread":  round(p50_spread, 5),
            "p90_spread":  round(p90_spread, 5),
            "mean_spread_pct": round(mean_spread_pct, 4),
            "p90_spread_pct":  round(p90_spread_pct, 4),
        },
        "by_time_bucket": {
            "early_gt20min": bucket_stats(early_spreads),
            "mid_10_20min":  bucket_stats(mid_spreads),
            "late_lt10min":  bucket_stats(late_spreads),
        },
    }


def main() -> None:
    print("=" * 64)
    print("EXP-019C — Spread Characterization (T4 band, Kalshi NBA)")
    print("=" * 64)

    obs = load_spread_observations()
    print(f"Observations loaded: {len(obs)}")

    stats = compute_spread_stats(obs)
    if "error" in stats:
        print(f"ERROR: {stats['error']}")
        sys.exit(1)

    n = stats["n_total"]
    ov = stats["overall"]
    print(f"Valid observations:  {n}")
    print()
    print("── Overall spread ───────────────────────────────────────────")
    print(f"  mean: {ov['mean_spread']:.5f}   p50: {ov['p50_spread']:.5f}   p90: {ov['p90_spread']:.5f}")
    print(f"  mean%: {ov['mean_spread_pct']:.4f}  p90%: {ov['p90_spread_pct']:.4f}")
    print()
    print("── By time remaining ────────────────────────────────────────")
    for label, bkt in stats["by_time_bucket"].items():
        if bkt["n"] == 0:
            print(f"  {label}: no data")
        else:
            print(f"  {label}: n={bkt['n']}  mean={bkt['mean']:.5f}  p50={bkt['p50']:.5f}  p90={bkt['p90']:.5f}")
    print()

    # Compare to NOISE_BUFFER_BAND_T4 = 0.13905
    print("── Exit band vs spread ──────────────────────────────────────")
    nbb = 0.13905
    print(f"  NOISE_BUFFER_BAND_T4 = {nbb}")
    print(f"  p90 spread = {ov['p90_spread']:.5f}")
    ratio = ov["p90_spread"] / nbb
    print(f"  p90 spread / NOISE_BUFFER = {ratio:.3f}")
    if ratio > 0.5:
        print("  WARNING: spread is >50% of exit band — exit signal may be masked by costs")
    else:
        print("  OK: spread materially below exit band threshold")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "exp_id":   "EXP-019C",
        "mode":     "empirical",
        "n_observations": n,
        **stats,
        "noise_buffer_band_t4": nbb,
        "spread_to_band_ratio_p90": round(ratio, 4),
    }
    with open(OUT_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Results saved: {OUT_PATH.relative_to(PROJ)}")
    print("=" * 64)


if __name__ == "__main__":
    main()
