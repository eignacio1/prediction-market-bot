#!/usr/bin/env python3
"""A2 (Window A, ITERATION_PLAN_MC_REMEDIATION_2026-07-22 / GG-105) --
build the control vs. candidate feature-CSV variants for the offline refit.

Per the DECISION_LOG.md 2026-07-24 A2-scoping entry (commit d12393d): A2's
refit is a single-variable swap against MAIN's (T1/T2/T3) feature set --
"control" replicates the live frozen model's exact 18-feature input
(models/mlb_v1_model_meta.json), "candidate" swaps raw ba_l10 for
ba_l10_shrunk_a1_candidate (APR-0025 formula, A1_CANDIDATE_SHRINKAGE_K=400,
holdout-tuned) and nothing else.

WHY NOT JUST USE THE CSV'S EXISTING ba_l10_shrunk / ba_l10_shrunk_a1_candidate
COLUMNS DIRECTLY
------------------------------------------------------------------------------
The pulled exp_output/MLB/mlb_feature_matrix.csv (scp'd from the VPS) has
ba_l10_shrunk (K=40, live production, ADR-0047) but NOT
ba_l10_shrunk_a1_candidate -- that column only materializes when
ENABLE_A1_SHRINKAGE_CANDIDATE is set at feature-generation time, and this
CSV predates that flag being set. Regenerating the full C1/C2 pipeline is a
~30min, external-API-dependent operation this script avoids: h_sum/ab_sum
(the two real inputs the shrinkage formula needs) are reconstructed directly
from the raw per-game (player_id, game_date, ab, h) columns already present
in this CSV, using the IDENTICAL windowing logic
(scripts/tune_a1_shrinkage_k.py::_reconstruct_rolling_sums, itself copied
from mlb_features.py::_compute_rolling_batter_features: window=10,
min_periods=3, shift(1)) A1 already built and validated for this exact
purpose. This script reuses that function rather than re-deriving it.

VALIDATION (do not skip)
-------------------------
Before trusting the K=400 candidate column, this script recomputes K=40 from
the reconstructed h_sum/ab_sum and diffs it against the CSV's own
(production-computed) ba_l10_shrunk column. A large mismatch means the
windowing logic has drifted from production and the candidate column cannot
be trusted -- the script aborts rather than silently producing a wrong
candidate.

TWO OUTPUT CSVs (both == full row set, only the feature columns differ)
--------------------------------------------------------------------------
  control.csv    -- ba_l10_shrunk column DROPPED (it doesn't exist in the
                     live frozen model's feature set: models/mlb_v1_model_
                     meta.json's feature_names has raw ba_l10, not
                     ba_l10_shrunk -- leaving it in would silently add a 19th
                     feature to "control" that the live model never had,
                     confounding the comparison). ba_l10 left untouched.
  candidate.csv  -- same drop, PLUS ba_l10 column VALUES overwritten with the
                     reconstructed ba_l10_shrunk_a1_candidate (K=400) values,
                     column NAME kept as "ba_l10" so train_mlb_model.py's
                     automatic feature inclusion (_extract_feature_matrix)
                     treats this as a true single-variable swap, not an
                     additive 19th feature.

Run:
  python3 scripts/build_a2_refit_variants.py \
      --input exp_output/MLB/mlb_feature_matrix.csv \
      --out-dir exp_output/MLB/a2_refit
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tune_a1_shrinkage_k import _reconstruct_rolling_sums  # noqa: E402  reuse A1's exact windowing logic

GG105_SHRINKAGE_K = 40           # ADR-0047, live production (mlb_features.py)
GG105_SHRINKAGE_PRIOR = 0.2512   # ADR-0047, live production
A1_CANDIDATE_SHRINKAGE_K = 400   # A1, holdout-tuned (mlb_features.py)
VALIDATION_TOLERANCE = 1e-6      # max allowed |reconstructed_k40 - csv ba_l10_shrunk|


def build(input_csv: Path, out_dir: Path) -> None:
    print(f"[1/6] Loading {input_csv} ...")
    df = pd.read_csv(input_csv, low_memory=False)
    print(f"      {len(df):,} rows, {len(df.columns)} columns")

    if "ba_l10_shrunk" not in df.columns:
        print("ERROR: input CSV has no ba_l10_shrunk column -- cannot validate "
              "the reconstruction against production. Aborting.", file=sys.stderr)
        sys.exit(1)

    print("[2/6] Reconstructing per-player rolling h_sum/ab_sum "
          "(A1's _reconstruct_rolling_sums, window=10, min_periods=3, shift(1)) ...")
    raw_cols = ["player_id", "game_date", "ab", "h"]
    enriched = _reconstruct_rolling_sums(df[raw_cols].copy())
    # _reconstruct_rolling_sums sorts by (player_id, game_date) and resets the
    # index -- merge back onto the original df's row order via the natural key.
    enriched["game_date"] = enriched["game_date"].astype(str)
    df["_game_date_str"] = pd.to_datetime(df["game_date"]).astype(str)
    merged = df.merge(
        enriched[["player_id", "game_date", "h_sum", "ab_sum"]],
        left_on=["player_id", "_game_date_str"],
        right_on=["player_id", "game_date"],
        how="left",
        suffixes=("", "_recon"),
    )
    print(f"      merged rows: {len(merged):,}  "
          f"(h_sum/ab_sum non-null: {merged['ab_sum'].notna().sum():,})")

    print("[3/6] Validating reconstruction: recompute K=40 and diff vs. CSV's "
          "production ba_l10_shrunk ...")
    recon_k40 = (merged["h_sum"] + GG105_SHRINKAGE_K * GG105_SHRINKAGE_PRIOR) / (
        merged["ab_sum"] + GG105_SHRINKAGE_K
    )
    both_present = merged["ba_l10_shrunk"].notna() & recon_k40.notna()
    diff = (recon_k40[both_present] - merged.loc[both_present, "ba_l10_shrunk"]).abs()
    n_checked = int(both_present.sum())
    max_diff = float(diff.max()) if n_checked else float("nan")
    n_bad = int((diff > VALIDATION_TOLERANCE).sum()) if n_checked else 0
    print(f"      checked {n_checked:,} rows; max|diff|={max_diff:.2e}; "
          f"rows exceeding tolerance ({VALIDATION_TOLERANCE:.0e}): {n_bad}")
    if n_checked == 0:
        print("ERROR: 0 rows had both a reconstructed and production ba_l10_shrunk "
              "value -- validation could not run. Aborting.", file=sys.stderr)
        sys.exit(1)
    if n_bad > 0:
        print(f"ERROR: reconstruction diverges from production on {n_bad}/{n_checked} rows "
              f"(max diff {max_diff:.2e} > tolerance {VALIDATION_TOLERANCE:.0e}). "
              f"Windowing logic has drifted -- do NOT trust the K=400 candidate. Aborting.",
              file=sys.stderr)
        sys.exit(1)
    print("      VALIDATION PASSED -- reconstruction matches production exactly.")

    print(f"[4/6] Computing ba_l10_shrunk_a1_candidate (K={A1_CANDIDATE_SHRINKAGE_K}) ...")
    candidate_vals = (merged["h_sum"] + A1_CANDIDATE_SHRINKAGE_K * GG105_SHRINKAGE_PRIOR) / (
        merged["ab_sum"] + A1_CANDIDATE_SHRINKAGE_K
    )
    candidate_vals = candidate_vals.where(merged["ab_sum"].notna())
    print(f"      candidate non-null: {candidate_vals.notna().sum():,} / {len(merged):,}")

    out_dir.mkdir(parents=True, exist_ok=True)

    print("[5/6] Writing control.csv (drop ba_l10_shrunk, ba_l10 untouched) ...")
    control = merged.drop(columns=["h_sum", "ab_sum", "_game_date_str", "game_date_recon",
                                    "ba_l10_shrunk"], errors="ignore")
    control_path = out_dir / "control.csv"
    control.to_csv(control_path, index=False)
    print(f"      wrote {control_path} ({len(control):,} rows, {len(control.columns)} cols)")

    print("[6/6] Writing candidate.csv (ba_l10 <- ba_l10_shrunk_a1_candidate values) ...")
    candidate = merged.drop(columns=["h_sum", "ab_sum", "_game_date_str", "game_date_recon",
                                      "ba_l10_shrunk"], errors="ignore").copy()
    n_before = candidate["ba_l10"].notna().sum()
    candidate["ba_l10"] = candidate_vals.values
    n_after = candidate["ba_l10"].notna().sum()
    candidate_path = out_dir / "candidate.csv"
    candidate.to_csv(candidate_path, index=False)
    print(f"      wrote {candidate_path} ({len(candidate):,} rows, {len(candidate.columns)} cols)")
    print(f"      ba_l10 non-null: {n_before:,} (raw) -> {n_after:,} (shrunk K=400)")

    assert list(control.columns) == list(candidate.columns), \
        "control/candidate column sets diverged -- not a clean single-variable swap"
    diverge_cols = [c for c in control.columns
                     if c != "ba_l10" and not control[c].astype(str).equals(candidate[c].astype(str))]
    if diverge_cols:
        print(f"WARNING: columns other than ba_l10 differ between control/candidate: "
              f"{diverge_cols} -- this should be empty for a true single-variable swap.",
              file=sys.stderr)
    else:
        print("      Confirmed: control.csv and candidate.csv differ ONLY in ba_l10 values.")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", type=Path, default=Path("exp_output/MLB/mlb_feature_matrix.csv"))
    p.add_argument("--out-dir", type=Path, default=Path("exp_output/MLB/a2_refit"))
    return p


def main() -> int:
    args = _build_parser().parse_args()
    if not args.input.exists():
        print(f"ERROR: input not found: {args.input}", file=sys.stderr)
        return 1
    build(args.input, args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
