#!/usr/bin/env python3
"""A2 (Window A, GG-105) -- train the control/candidate C3 refit variants.

Invokes train_mlb_model.py's main() programmatically twice (control,
candidate), each with an isolated model_path/meta_path under
models/a2_refit/ -- NEVER the live models/mlb_v1_model.joblib /
models/mlb_v1_model_meta.json (Hard Rule 4: no automated retraining in
production; the live frozen artifact must not be overwritten by an offline
experimental refit).

Both variants use --force-save: the ADR-0009 shadow gate compares against a
null baseline and is not the calibration-gate criteria A2 is being evaluated
against (edge-tercile monotonicity / calibration-slope CI / Brier+ECE vs.
ADR-0046) -- that evaluation happens downstream via what_if_harness.py against
the real resolved ledger, not via this script's shadow-gate metrics. Saving
regardless of shadow-gate outcome lets that downstream evaluation run either
way; the shadow-gate PASS/FAIL is still printed and recorded in each variant's
own meta.json for reference.

Run:
  PYTHONPATH=src python3 scripts/run_a2_train_variants.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import train_mlb_model  # noqa: E402

OUT_ROOT = Path("models/a2_refit")

VARIANTS = {
    "control": Path("exp_output/MLB/a2_refit_full/control.csv"),
    "candidate": Path("exp_output/MLB/a2_refit_full/candidate.csv"),
}


def run() -> None:
    for name, csv_path in VARIANTS.items():
        if not csv_path.exists():
            print(f"ERROR: {csv_path} not found -- run build_a2_refit_variants.py first.",
                  file=sys.stderr)
            sys.exit(1)

        model_path = OUT_ROOT / f"{name}_model.joblib"
        meta_path = OUT_ROOT / f"{name}_model_meta.json"
        print(f"\n{'#'*70}\n# Training variant: {name}\n# csv={csv_path}\n"
              f"# model_path={model_path}\n# meta_path={meta_path}\n{'#'*70}")

        train_mlb_model.main(
            csv_path=csv_path,
            dry_run=False,
            force_save=True,
            model_path=model_path,
            meta_path=meta_path,
        )


if __name__ == "__main__":
    run()
