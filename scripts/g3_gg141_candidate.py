#!/usr/bin/env python3
"""
G3 (GG-141, T-405) -- opp_sp-inclusive candidate model + D1 overrides,
MAIN and T4.

A1 (this session, g3_backfill_opp_sp.py + t9_gg105_feature_discrimination.py
re-run against the backfilled CSV) found all four opp_sp/matchup features
INCONCLUSIVE as standalone raw predictors of the reconstructed event at
alpha=0.10 (opp_sp_era_l5 p=0.78, opp_sp_k9_l5 p=0.58, opp_sp_bb9_l5 p=0.27,
opp_runs_allowed_l10 p=0.23). That result already argues against GG-141 as
the GG-105 fix, but a raw single-feature test cannot rule out an
interaction/multivariate effect -- this script builds the actual A2/A3-style
candidate (out-of-fold L2 logistic regression) with the backfilled opp_sp
block added to A2's original FEATURE_COLS, for BOTH resolved books (MAIN
t1t2t3 and T4), and writes two --overrides-file JSONs for the real D1
harness (scripts/what_if_harness.py) to score.

Sample restriction: complete-case on the five opp_sp columns (i.e. rows
where the opposing SP was resolved AND had >=2 prior 2026 starts, matching
TI-01's min_periods=2 floor already enforced upstream by
MLBPitcherStatsStore). This mirrors A1's own null-handling (A1 also only
scores non-null rows per feature) rather than introducing a new imputation
assumption this session did not test.

RESEARCH ONLY. No epoch bump, no live sizing change, no refit of the frozen
production model (Hard Rule 4) -- this fits a wholly separate, offline,
research-only LogisticRegression candidate for --overrides-file scoring
only, exactly the established T9 A2/A3 precedent. Reads only from
exp_output/T9_GG105_REWORK/ and logs/; writes only to
exp_output/T9_GG105_REWORK/.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from exp_retrospective_core import load_portfolio, deduplicate  # noqa: E402
import run_band_monitor as bm  # noqa: E402  load_t4_ledger, to_mlb_positions

MAIN_PORTFOLIO = Path("logs/.vps_portfolio_cache_mlb.json")
T4_LEDGER = Path("logs/t4_mlb_resolved_ledger.jsonl")
FEATURE_CSV = Path("exp_output/T9_GG105_REWORK/mlb_feature_matrix_oppsp_backfilled.csv")
OUT_DIR = Path("exp_output/T9_GG105_REWORK")

BASE_FEATURE_COLS = ["ba_l10_shrunk", "bb_rate_l10", "days_rest", "park_factor_hits", "is_home_game"]
OPP_SP_COLS = ["opp_sp_era_l5", "opp_sp_k9_l5", "opp_sp_bb9_l5", "opp_runs_allowed_l10"]
FEATURE_COLS = BASE_FEATURE_COLS + OPP_SP_COLS


def load_feature_index() -> dict[tuple[str, str], dict]:
    groups: dict[tuple[str, str], list[dict]] = {}
    with open(FEATURE_CSV) as fh:
        for row in csv.DictReader(fh):
            groups.setdefault((row["player_id"], row["game_date"]), []).append(row)
    index = {}
    for key, rows in groups.items():
        if len(rows) == 1:
            index[key] = rows[0]
            continue
        first = rows[0]
        if all(r.get(c) == first.get(c) for r in rows[1:] for c in FEATURE_COLS):
            index[key] = first
    return index


def reconstruct_event(p) -> int:
    return 1 if ((p.direction == "YES") == (p.outcome == "WIN")) else 0


def row_complete(row: dict) -> bool:
    for c in FEATURE_COLS:
        v = row.get(c, "")
        if v is None or v == "" or v == "nan":
            return False
        try:
            if np.isnan(float(v)):
                return False
        except (TypeError, ValueError):
            return False
    return True


def fit_oof_candidate(joined: list[tuple[object, dict]]) -> tuple[np.ndarray, np.ndarray]:
    X = np.array([[float(row[c]) for c in FEATURE_COLS] for _, row in joined])
    interaction = X[:, 0] * X[:, 1]  # ba_l10_shrunk * bb_rate_l10, same as A2
    X = np.column_stack([X, interaction])
    y = np.array([reconstruct_event(p) for p, _ in joined])

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=17)
    oof_pred = np.full(len(y), np.nan)
    for train_idx, test_idx in skf.split(X, y):
        scaler = StandardScaler().fit(X[train_idx])
        clf = LogisticRegression(C=1.0, max_iter=1000)
        clf.fit(scaler.transform(X[train_idx]), y[train_idx])
        oof_pred[test_idx] = clf.predict_proba(scaler.transform(X[test_idx]))[:, 1]
    assert not np.isnan(oof_pred).any()
    return oof_pred, y


def run_book(label: str, positions: list, feature_index: dict, out_name: str) -> None:
    joined = []
    for p in positions:
        row = feature_index.get((str(p.player_id), p.game_date))
        if row is not None and row_complete(row):
            joined.append((p, row))
    print(f"[{label}] complete-case (opp_sp) joined n={len(joined)} "
          f"(of {len(positions)} resolved positions)")

    if len(joined) < 10:
        print(f"[{label}] SKIP -- too few complete-case rows to fit a candidate model.")
        return

    oof_pred, y = fit_oof_candidate(joined)
    print(f"[{label}] Event base rate: {y.mean():.3f} (n={len(y)})")
    print(f"[{label}] OOF candidate_model_p: mean={oof_pred.mean():.3f}, "
          f"std={oof_pred.std():.3f}, min={oof_pred.min():.3f}, max={oof_pred.max():.3f}")

    order = np.argsort(oof_pred)
    thirds = np.array_split(order, 3)
    er = [y[idx].mean() for idx in thirds]
    print(f"[{label}] OOF candidate_p terciles (bottom->top) event rate: "
          f"{er[0]:.3f} / {er[1]:.3f} / {er[2]:.3f}")

    overrides = {}
    for (p, _row), pred in zip(joined, oof_pred):
        key = f"{p.player_id}|{p.game_date}|{p.threshold}"
        overrides[key] = float(pred)

    overrides_path = OUT_DIR / out_name
    overrides_path.write_text(json.dumps(overrides, indent=2))
    print(f"[{label}] Wrote {len(overrides)} overrides -> {overrides_path}\n")


def main() -> int:
    feature_index = load_feature_index()

    main_positions = deduplicate(load_portfolio(MAIN_PORTFOLIO))
    run_book("MAIN (t1t2t3)", main_positions, feature_index, "g3_a2_candidate_overrides_main.json")

    t4_recs = bm.load_t4_ledger(T4_LEDGER)
    t4_positions = bm.to_mlb_positions(t4_recs)
    run_book("T4", t4_positions, feature_index, "g3_a2_candidate_overrides_t4.json")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
