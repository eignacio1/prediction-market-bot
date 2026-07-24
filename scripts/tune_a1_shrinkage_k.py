#!/usr/bin/env python3
"""A1 (Window A, ITERATION_PLAN_MC_REMEDIATION_2026-07-22) — holdout K-tuning for
the ba_l10 empirical-Bayes shrinkage candidate.

Distinct from ADR-0047 (GG105_SHRINKAGE_K=40, DS-approved, immutable, live in
production since epoch 8). This script tunes a NEW candidate K on a chronological
holdout for evaluation by Window D's offline replay harness. It does not write to
any live epoch and does not modify mlb_features.py's ADR-0047 constants.

Formula (APR-0025): ba_l10_shrunk = (ab_sum*ba_l10 + K*PRIOR) / (ab_sum + K)
                                   = (h_sum + K*PRIOR) / (ab_sum + K)

Methodology:
  1. Reconstruct per-player rolling h_sum/ab_sum (L10, shift(1), min_periods=3)
     from the raw batter game log, using the identical windowing logic as
     mlb_features.py::_compute_rolling_batter_features (window=10, min_periods=3).
  2. TRAIN rows tune nothing (K is not fit by gradient descent — it is a prior-
     strength hyperparameter swept over a grid). VALIDATION/TEST-labeled rows
     (chronologically after TRAIN, per TI-02) are the holdout: for each candidate
     K, score the shrunk pre-game estimate against that SAME game's actual
     (ab, h) outcome — the estimate is computed from strictly prior games
     (shift(1)), so this is a genuine out-of-sample, temporally-clean score
     (TI-01/TI-02 preserved).
  3. Scoring: per-at-bat Brier score, treating each of a row's `ab` at-bats as
     independent Bernoulli(p_pred) trials (matching how T4M-PROJ's Binomial
     hit-probability calc actually consumes this field):
         brier = sum_i[ h_i*(1-p_i)^2 + (ab_i-h_i)*p_i^2 ] / sum_i[ab_i]
     Lower is better. K minimizing holdout Brier is selected.

Usage:
    python3 scripts/tune_a1_shrinkage_k.py \
        --input exp_output/MLB/mlb_feature_matrix.csv \
        --prior 0.2512 \
        --k-grid 5,10,20,30,40,50,60,80,100,120,150,200

Prints a K-vs-Brier table and the selected K. Read-only against the input CSV;
writes nothing except stdout (caller redirects to a report file).
"""

from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd

WINDOW = 10
MIN_PERIODS = 3


def _reconstruct_rolling_sums(game_log: pd.DataFrame) -> pd.DataFrame:
    """Recompute per-player rolling h_sum/ab_sum exactly as production C2 does."""
    df = game_log.copy()
    df["game_date"] = pd.to_datetime(df["game_date"])
    df = df.sort_values(["player_id", "game_date"]).reset_index(drop=True)

    chunks = []
    for _, g in df.groupby("player_id", sort=False):
        g = g.sort_values("game_date").reset_index(drop=True)
        h_sum = g["h"].shift(1).rolling(WINDOW, min_periods=MIN_PERIODS).sum()
        ab_sum = g["ab"].shift(1).rolling(WINDOW, min_periods=MIN_PERIODS).sum()
        g["h_sum"] = h_sum
        g["ab_sum"] = ab_sum
        chunks.append(g)
    return pd.concat(chunks, ignore_index=True)


def _brier_for_k(holdout: pd.DataFrame, k: float, prior: float) -> tuple[float, int]:
    """Per-at-bat weighted Brier score for candidate K over the holdout set."""
    valid = holdout.dropna(subset=["h_sum", "ab_sum"])
    valid = valid[(valid["ab_sum"] > 0) & (valid["ab"] > 0)]
    if valid.empty:
        return float("nan"), 0

    p_pred = (valid["h_sum"] + k * prior) / (valid["ab_sum"] + k)
    p_pred = p_pred.clip(0.0, 1.0)

    h = valid["h"].to_numpy(dtype=float)
    ab = valid["ab"].to_numpy(dtype=float)
    p = p_pred.to_numpy(dtype=float)

    sq_err_hit = (1.0 - p) ** 2
    sq_err_miss = p ** 2
    weighted_sq_err = h * sq_err_hit + (ab - h) * sq_err_miss

    total_ab = ab.sum()
    brier = float(weighted_sq_err.sum() / total_ab) if total_ab > 0 else float("nan")
    return brier, int(total_ab)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="exp_output/MLB/mlb_feature_matrix.csv")
    parser.add_argument("--prior", type=float, default=0.2512, help="GG105_SHRINKAGE_PRIOR (APR-0025)")
    parser.add_argument(
        "--k-grid",
        default="5,10,15,20,25,30,40,50,60,80,100,120,150,200",
        help="comma-separated K candidates",
    )
    parser.add_argument(
        "--holdout-labels",
        default="TEST",
        help="comma-separated train_test_label values to treat as holdout (chronological)",
    )
    args = parser.parse_args()

    cols = ["player_id", "game_date", "ab", "h", "train_test_label"]
    raw = pd.read_csv(args.input, usecols=cols)
    raw = raw.dropna(subset=["player_id", "game_date"])
    raw["ab"] = pd.to_numeric(raw["ab"], errors="coerce").fillna(0)
    raw["h"] = pd.to_numeric(raw["h"], errors="coerce").fillna(0)

    enriched = _reconstruct_rolling_sums(raw)

    holdout_labels = {s.strip() for s in args.holdout_labels.split(",")}
    holdout = enriched[enriched["train_test_label"].isin(holdout_labels)]

    if holdout.empty:
        print(f"ERROR: no rows matched holdout labels {holdout_labels}", file=sys.stderr)
        return 1

    k_grid = [float(x) for x in args.k_grid.split(",")]

    print(f"Input: {args.input}")
    print(f"Holdout labels: {sorted(holdout_labels)} (n_rows={len(holdout)})")
    print(f"PRIOR: {args.prior}")
    print()
    print(f"{'K':>8} | {'holdout_brier':>14} | {'n_atbats':>10}")
    print("-" * 40)

    results: list[tuple[float, float, int]] = []
    for k in k_grid:
        brier, n_ab = _brier_for_k(holdout, k, args.prior)
        results.append((k, brier, n_ab))
        print(f"{k:8.1f} | {brier:14.6f} | {n_ab:10d}")

    # Baseline: raw ba_l10 (no shrinkage, K=0)
    baseline_brier, baseline_n = _brier_for_k(holdout, 0.0, args.prior)
    print("-" * 40)
    print(f"{'0.0 (raw)':>8} | {baseline_brier:14.6f} | {baseline_n:10d}")

    valid_results = [(k, b, n) for k, b, n in results if not np.isnan(b)]
    if not valid_results:
        print("ERROR: all candidates produced NaN Brier", file=sys.stderr)
        return 1

    best_k, best_brier, best_n = min(valid_results, key=lambda t: t[1])
    print()
    print(f"SELECTED K = {best_k} (holdout Brier = {best_brier:.6f}, n_atbats = {best_n})")
    print(f"vs. raw ba_l10 (K=0) Brier = {baseline_brier:.6f}")
    print(f"vs. production ADR-0047 K=40 Brier = {dict((k, b) for k, b, _ in results).get(40.0, float('nan')):.6f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
