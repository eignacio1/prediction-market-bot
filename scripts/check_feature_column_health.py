#!/usr/bin/env python3
"""
Feature column health scan (GG-141 preventive check, T-405).

GG-141: opp_sp_era_l5 / opp_sp_k9_l5 / opp_sp_bb9_l5 / opp_runs_allowed_l10
were 100% blank and opp_sp_is_known was hardcoded 0.0 across the entire MLB
feature matrix for ~5 weeks (a resumable cache in generate_mlb_features.py
silently cached an empty fetch result around 2026-06-24). Nothing caught it:
a blank/constant column is syntactically valid data (parses to NaN or a
single repeated value), produces no exception, and is invisible to
CLAUDE.md's Step 2 stub scan, which only greps source-code comments
(`# stub`/`# TBD`/`# placeholder`) -- it has no visibility into data at all.

This script is the data-layer companion to that comment-layer scan: it flags
columns in the C2 feature matrix that are (a) blank/near-blank (null rate
above threshold) or (b) degenerate (a single repeated non-null value across
enough rows to rule out early-season/small-n coincidence) -- the exact two
shapes GG-141 took (opp_sp_era_l5 was case (a), opp_sp_is_known was case (b)).

Two ways this is meant to be used:
  1. Proactive, same-day: called inline by generate_mlb_features.py right
     after the combined feature DataFrame is built, so a poisoned cache or
     broken upstream fetch is visible in that day's cron log immediately --
     not discovered five weeks and several GG-105 sessions later.
  2. Retroactive, on demand: run standalone against any feature CSV
     (production or an exp_output/ research copy) as a session-start /
     audit-time companion to the Step 2 stub scan.

Non-fatal by design when called as a library function (returns findings,
caller decides). The CLI exits 1 if any BLANK or DEGENERATE finding exists,
0 otherwise, so it can be used as a soft gate (warn, don't block) or a hard
gate (fail CI/cron) depending on the caller's choice -- this script does not
decide that for its callers.

RESEARCH/TOOLING ONLY. Read-only: never writes to the feature CSV.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import pandas as pd

CANONICAL_CSV = Path("exp_output/MLB/mlb_feature_matrix.csv")

# Identifier/metadata columns excluded from health checks: high-cardinality
# by design (ids, names, timestamps) or expected-constant within a single
# generation run (snapshot_id, feature_version) -- flagging these would be
# noise, not signal. Every column NOT in this list is a computed/raw C2
# feature and is expected to vary and be populated.
EXCLUDE_COLS = {
    "player_id", "player_name", "team_id", "team_abbreviation",
    "game_id", "game_date", "season", "season_type", "matchup",
    "opponent_team_abbr", "snapshot_id", "ingestion_run_id", "ingested_at",
    "temporal_cutoff", "feature_run_id", "feature_version", "train_test_label",
}

NULL_RATE_BLANK = 0.95   # >= this fraction null -> BLANK (GG-141's opp_sp_era_l5 shape)
NULL_RATE_SPARSE = 0.50  # >= this fraction null (but < BLANK) -> SPARSE (warn only)
MIN_ROWS_FOR_VARIANCE = 10  # below this, a single-value column is plausibly real, not a bug


def scan_columns(
    df: pd.DataFrame,
    exclude: set[str] = EXCLUDE_COLS,
    null_blank: float = NULL_RATE_BLANK,
    null_sparse: float = NULL_RATE_SPARSE,
    min_rows_for_variance: int = MIN_ROWS_FOR_VARIANCE,
) -> list[dict[str, Any]]:
    """Return a list of findings, most-severe first. Empty list = clean."""
    findings: list[dict[str, Any]] = []
    n = len(df)
    if n == 0:
        return findings

    for col in df.columns:
        if col in exclude:
            continue
        series = df[col]
        null_count = int(series.isna().sum())
        # Also treat empty-string as null -- CSV round-trips can produce "" not NaN.
        if series.dtype == object:
            null_count += int((series.fillna("").astype(str).str.strip() == "").sum() - series.isna().sum())
        null_rate = null_count / n

        nonnull = series.dropna()
        if series.dtype == object:
            nonnull = nonnull[nonnull.astype(str).str.strip() != ""]
        unique_nonnull = nonnull.nunique()

        if null_rate >= null_blank:
            findings.append({
                "column": col, "flag": "BLANK", "severity": "HIGH",
                "null_rate": round(null_rate, 4), "unique_nonnull": int(unique_nonnull), "n": n,
                "detail": f"{null_rate:.1%} null/blank (>= {null_blank:.0%} threshold)",
            })
            continue

        if len(nonnull) >= min_rows_for_variance and unique_nonnull <= 1:
            sample = nonnull.iloc[0] if len(nonnull) else None
            findings.append({
                "column": col, "flag": "DEGENERATE", "severity": "HIGH",
                "null_rate": round(null_rate, 4), "unique_nonnull": int(unique_nonnull), "n": n,
                "detail": f"single repeated value ({sample!r}) across {len(nonnull)} non-null rows",
            })
            continue

        if null_rate >= null_sparse:
            findings.append({
                "column": col, "flag": "SPARSE", "severity": "WARN",
                "null_rate": round(null_rate, 4), "unique_nonnull": int(unique_nonnull), "n": n,
                "detail": f"{null_rate:.1%} null/blank (>= {null_sparse:.0%} threshold, < BLANK)",
            })

    findings.sort(key=lambda f: (f["severity"] != "HIGH", -f["null_rate"]))
    return findings


def print_report(findings: list[dict[str, Any]], source: str) -> None:
    print(f"\n{'='*65}")
    print(f"FEATURE COLUMN HEALTH SCAN — {source}")
    print(f"{'='*65}")
    if not findings:
        print("CLEAN — no blank, degenerate, or sparse feature columns found")
    else:
        for f in findings:
            print(f"[{f['severity']}] {f['flag']:<10} {f['column']:<28} {f['detail']}")
    print(f"{'='*65}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--csv", type=Path, default=CANONICAL_CSV, help=f"Feature CSV to scan (default: {CANONICAL_CSV})")
    args = parser.parse_args()

    if not args.csv.exists():
        print(f"FATAL: {args.csv} does not exist.", file=sys.stderr)
        return 2

    df = pd.read_csv(args.csv, low_memory=False)
    findings = scan_columns(df)
    print_report(findings, str(args.csv))

    return 1 if any(f["severity"] == "HIGH" for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
