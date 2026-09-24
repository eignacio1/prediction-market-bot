#!/usr/bin/env python3
"""T-571 Deliverable 2: recompute T-565's headline figures restricted to
Kalshi-confirmed-FILLED rows only, within T-565's original committed window
(2026-07-31 .. 2026-08-13, clean_n=765).

Does NOT modify t565_calibration_model_vs_market.py. Imports its functions
unchanged (build_rows, clean_filter, cohort_summary) and applies them to a
row subset selected via t571_verify_t4mproj_kalshi_fills.py's per-order
Kalshi verdicts (exp_output/T565_calibration_benchmark/
t571_kalshi_verification_results.json). Read-only: no ledger file written,
no row edited/excluded in the live ledger, no clean_n restated anywhere
outside this scratch analysis's own output.

Two variants reported, per the DO-NOT list's ban on inferring a fill from a
local status field alone:
  Variant A: exclude only rows CONFIRMED CANCELED within the original window.
             (Finding: zero such rows exist in-window -- all 139 CANCELED
             rows are from the later 2026-09-22 batch, outside this window.
             So Variant A == the original 765-row cohort, unchanged.)
  Variant B: restrict to ONLY rows CONFIRMED FILLED within the window (the
             most conservative verified-only cohort, n=34).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from t565_calibration_model_vs_market import (  # noqa: E402
    build_rows, clean_filter, cohort_summary, print_summary,
)

OUT_DIR = REPO_ROOT / "exp_output" / "T565_calibration_benchmark"
WINDOW_START = "2026-07-31"
WINDOW_END = "2026-08-13"

# The TRUE original T-565 committed baseline (n=765), from
# 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T565_RESULTS_calibration_model_vs_market.md
# -- NOT this session's own n=905 re-pull. Reproduced here only for the
# side-by-side delta printout; not recomputed by this script.
ORIGINAL_T565_BASELINE = {
    "clean_n": 765,
    "model_brier": 0.2191,
    "market_brier": 0.1890,
    "paired_bet_level": {"mean_diff": 0.0301, "se": 0.0053, "t": 5.66},
    "paired_day_clustered": {"mean_diff": 0.0593, "se": 0.0207, "t": 2.87, "n_days": 11},
    "span": (WINDOW_START, WINDOW_END),
}


def main() -> None:
    verif = json.load(open(OUT_DIR / "t571_kalshi_verification_results.json"))
    verdict_by_pid = {r["position_id"]: r["verdict"] for r in verif["results"]}

    portfolio = json.load(open(OUT_DIR / "paper_portfolio_mlb_t4.LIVE.20260922.json"))
    closed = portfolio.get("closed_positions", [])

    in_window = [
        p for p in closed
        if p.get("band") == "T4M-PROJ" and WINDOW_START <= p.get("game_date", "") <= WINDOW_END
    ]
    print(f"in-window (T4M-PROJ, {WINDOW_START}..{WINDOW_END}) raw rows: {len(in_window)}")

    verdict_counts_in_window = {"FILLED": 0, "CANCELED": 0, "NOT_RETRIEVABLE": 0, "NO_VERDICT": 0}
    for p in in_window:
        v = verdict_by_pid.get(p.get("position_id"), "NO_VERDICT")
        verdict_counts_in_window[v] = verdict_counts_in_window.get(v, 0) + 1
    print(f"verdict breakdown in-window: {verdict_counts_in_window}")

    # Variant A: exclude only CONFIRMED CANCELED in-window.
    variant_a_raw = [p for p in in_window if verdict_by_pid.get(p.get("position_id")) != "CANCELED"]
    variant_a_rows = clean_filter(build_rows(variant_a_raw), "T4M-PROJ")
    variant_a = cohort_summary(variant_a_rows, "Variant A: exclude confirmed-CANCELED in-window")

    # Variant B: restrict to CONFIRMED FILLED only, in-window.
    variant_b_raw = [p for p in in_window if verdict_by_pid.get(p.get("position_id")) == "FILLED"]
    variant_b_rows = clean_filter(build_rows(variant_b_raw), "T4M-PROJ")
    variant_b = cohort_summary(variant_b_rows, "Variant B: confirmed-FILLED-only, in-window (n=34 expected)")

    print()
    print_summary(variant_a)
    print_summary(variant_b)

    out = {
        "window": [WINDOW_START, WINDOW_END],
        "original_t565_baseline": ORIGINAL_T565_BASELINE,
        "verdict_counts_in_window": verdict_counts_in_window,
        "variant_a_exclude_confirmed_canceled": variant_a,
        "variant_b_confirmed_filled_only": variant_b,
    }
    out_path = OUT_DIR / "t571_deliverable2_recompute.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
