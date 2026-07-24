#!/usr/bin/env python3
"""A2 (Window A, GG-105) -- build --overrides-file JSON(s) for what_if_harness.py.

For each real resolved MAIN-book (t1t2t3) position (logs/.vps_portfolio_cache_mlb.json),
looks up its (player_id, game_date) row in the A2 refit variant feature CSVs
(exp_output/MLB/a2_refit_full/{control,candidate}.csv), extracts the 18
features in that variant's own trained feature_names order, imputes NaN via
that variant's own col_medians (both read from models/a2_refit/*_model.joblib
-- the isolated offline-refit artifacts, NEVER the live model, Hard Rule 4),
and runs the matching per-threshold sklearn pipeline's predict_proba to get
an externally-derived model_p. Writes the result keyed by
"<player_id>|<game_date>|<threshold>" -- what_if_harness.py's _override_key
format -- to a JSON overrides file, one per variant.

Ambiguous joins: (player_id, game_date) pairs matching >1 feature-CSV row
(doubleheaders) cannot be disambiguated -- MLBPosition carries no game_id --
and are dropped from the overrides file rather than guessed, consistent with
apply_overrides()'s own drop-unmatched discipline in what_if_harness.py.
Positions at threshold=3 are also dropped: the trained variants only carry
pipelines for thresholds {1, 2} (THRESHOLDS/_EXCLUDED_THRESHOLDS in
train_mlb_model.py), matching the real ledger, which itself has zero
threshold=3 positions (confirmed empirically, 2026-07-24).

Run:
  PYTHONPATH=src python3 scripts/build_a2_overrides.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from exp_retrospective_core import load_portfolio, deduplicate  # noqa: E402

PORTFOLIO_PATH = Path("logs/.vps_portfolio_cache_mlb.json")
FEATURE_CSVS = {
    "control": Path("exp_output/MLB/a2_refit_full/control.csv"),
    "candidate": Path("exp_output/MLB/a2_refit_full/candidate.csv"),
    # A3 (GG-105 A2-FAIL contingency): same feature CSV as A2's candidate
    # (ba_l10_shrunk_a1_candidate) -- only the calibration method changed
    # (sigmoid -> isotonic, run_a3_train_isotonic.py) -- so it reuses
    # candidate.csv, not a fourth CSV variant.
    "candidate_isotonic": Path("exp_output/MLB/a2_refit_full/candidate.csv"),
}
MODEL_PATHS = {
    "control": Path("models/a2_refit/control_model.joblib"),
    "candidate": Path("models/a2_refit/candidate_model.joblib"),
    "candidate_isotonic": Path("models/a2_refit/candidate_isotonic_model.joblib"),
}
OUT_PATHS = {
    "control": Path("exp_output/MLB/a2_refit_full/control_overrides.json"),
    "candidate": Path("exp_output/MLB/a2_refit_full/candidate_overrides.json"),
    "candidate_isotonic": Path("exp_output/MLB/a2_refit_full/candidate_isotonic_overrides.json"),
}


def _impute(X: np.ndarray, medians: np.ndarray) -> np.ndarray:
    """Mirrors train_mlb_model.py::_impute() exactly (NaN -> column median,
    all-NaN column -> 0.0)."""
    X = X.copy().astype(float)
    mask = np.isnan(X)
    if mask.any():
        safe_medians = np.where(np.isnan(medians), 0.0, medians)
        X[mask] = np.take(safe_medians, np.where(mask)[1])
    return X


def build_variant_overrides(name: str, positions: list) -> dict[str, float]:
    csv_path = FEATURE_CSVS[name]
    model_path = MODEL_PATHS[name]
    print(f"\n--- variant={name} ---")
    print(f"  csv={csv_path}")
    print(f"  model={model_path}")

    df = pd.read_csv(csv_path)
    artifact = joblib.load(model_path)
    pipelines: dict[int, object] = artifact["pipelines"]
    feature_names: list[str] = artifact["feature_names"]
    col_medians: np.ndarray = artifact["col_medians"]

    # Index rows by (player_id, game_date); ambiguous (>1 row) groups are
    # excluded up front so they never silently pick a doubleheader game.
    group_sizes = df.groupby(["player_id", "game_date"]).size()
    ambiguous_keys = set(group_sizes[group_sizes > 1].index)
    unique_df = df[~df.set_index(["player_id", "game_date"]).index.isin(ambiguous_keys)]
    row_by_key = {
        (row.player_id, row.game_date): row
        for row in unique_df.itertuples(index=False)
    }
    print(f"  feature rows: {len(df)} total, {len(ambiguous_keys)} ambiguous "
          f"(player_id, game_date) groups excluded, {len(row_by_key)} usable")

    overrides: dict[str, float] = {}
    n_no_feature_row = 0
    n_ambiguous = 0
    n_bad_threshold = 0

    # Batch by threshold so each variant's pipeline.predict_proba() runs once
    # per threshold rather than once per position.
    by_threshold: dict[int, list] = {}
    for p in positions:
        key = (p.player_id, p.game_date)
        if key in ambiguous_keys:
            n_ambiguous += 1
            continue
        if key not in row_by_key:
            n_no_feature_row += 1
            continue
        if p.threshold not in pipelines:
            n_bad_threshold += 1
            continue
        by_threshold.setdefault(p.threshold, []).append((p, row_by_key[key]))

    for threshold, pairs in sorted(by_threshold.items()):
        X = np.array(
            [[getattr(row, fname) for fname in feature_names] for _, row in pairs],
            dtype=np.float64,
        )
        X = _impute(X, col_medians)
        probs = pipelines[threshold].predict_proba(X)[:, 1]
        for (p, _row), prob in zip(pairs, probs):
            override_key = f"{p.player_id}|{p.game_date}|{p.threshold}"
            overrides[override_key] = float(prob)

    print(f"  matched: {len(overrides)}/{len(positions)}  "
          f"(dropped: {n_no_feature_row} no-feature-row, "
          f"{n_ambiguous} ambiguous, {n_bad_threshold} bad-threshold)")
    return overrides


def run() -> None:
    for path in list(FEATURE_CSVS.values()) + list(MODEL_PATHS.values()) + [PORTFOLIO_PATH]:
        if not path.exists():
            print(f"ERROR: {path} not found.", file=sys.stderr)
            sys.exit(1)

    positions = load_portfolio(PORTFOLIO_PATH)
    positions = deduplicate(positions)
    print(f"Loaded {len(positions)} resolved MAIN-book (t1t2t3) positions.")

    for name in ("control", "candidate", "candidate_isotonic"):
        overrides = build_variant_overrides(name, positions)
        out_path = OUT_PATHS[name]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(overrides, indent=2, sort_keys=True))
        print(f"  wrote {out_path} ({len(overrides)} keys)")


if __name__ == "__main__":
    run()
