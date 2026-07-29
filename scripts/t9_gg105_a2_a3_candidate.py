#!/usr/bin/env python3
"""
T9 / A2+A3 -- propose and score a rank-ordering candidate (GG-105 rework)

A1 (scripts/t9_gg105_feature_discrimination.py) found, on the real MAIN
resolved ledger joined to the historical C2 feature matrix (n=313):
  - NO individual raw pregame feature (ba_l10, ba_l10_shrunk, slg_l10,
    obp_l10, ops_l10, h_l10_mean, k_rate_l10, hr_rate_l10, days_rest,
    park_factor_hits, is_home_game, b2b_flag) is MONOTONIC at alpha=0.10.
  - bb_rate_l10 is weakly ANTI-PREDICTIVE (p=0.072, not significant at 0.05).
  - The market-relative proxy (ba_l10_shrunk - mip), which mirrors the
    live model's own edge-generation logic, is STRONGLY ANTI-PREDICTIVE
    (p<0.0001): the more the model's recency read diverges above market
    price, the LESS likely the player actually clears the threshold.
  - matchup/opponent (opp_sp_era_l5/k9_l5/bb9_l5, opp_runs_allowed_l10) is
    a dead C2 column, 100% blank across the full 17,145-row history --
    not scoreable, registered as its own gap (GG-141 below).
  - order-slot has no pregame C2 column at all (T4-only live field).

A2 candidate rationale
-----------------------
A fixed-weight blend of model_p toward mip is PROVABLY still a monotonic
transform of the existing (broken) edge: if new_p = a*model_p+(1-a)*mip
then new_edge = new_p - mip = a*(model_p - mip) = a*old_edge for a
constant a > 0 -- a positive rescaling that preserves rank order and
therefore cannot repair an inverted tercile (this is exactly the
Platt/isotonic/temperature trap the session premise already rules out,
just reached by a different road). Any real candidate must make the
RANK ORDER of positions change relative to fee_net_edge alone, which
requires an interaction with a variable other than (model_p, mip).

This candidate is a genuinely different model class: an L2-regularized
logistic regression fit directly on reconstructed outcomes (not a
transform of the live model's score at all), using the only features A1
found with any independent read on outcomes (bb_rate_l10) plus its
interaction with ba_l10_shrunk, alongside days_rest/park_factor_hits/
is_home_game as controls. Predictions are out-of-fold (5-fold CV) to
avoid the in-sample overfit that a same-sample fit-and-score would
produce on n=313 -- an honest test needs held-out predictions, not
training-set self-scoring.

This is explicitly a WEAK-PRIOR candidate (bb_rate_l10's own signal did
not clear p<0.05 in A1) proposed because it is the only scoreable lever
left after A1 -- not because it is expected to pass. The single
strongest theoretical lever (opponent pitcher quality) is NOT scoreable
this session because the underlying C2 data does not exist historically
(dead columns, see A1) -- that is a data-engineering gap to register, not
a model to fit today.

A3: writes an --overrides-file keyed exactly as what_if_harness.py's
_override_key() expects (f"{player_id}|{game_date}|{threshold}") with the
out-of-fold candidate_model_p, then invokes the real D1 harness
(scripts/what_if_harness.py) against it -- per A3's literal instruction to
score "via the D1 harness". No live file is touched; --overrides-file is
D1's own documented extension point for exactly this use case.

NO epoch bump. NO live sizing change. Read/compute-only; writes only to
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
from exp_retrospective_core import load_portfolio, deduplicate  # noqa: E402

PORTFOLIO = Path("logs/.vps_portfolio_cache_mlb.json")
FEATURE_CSV = Path("exp_output/T9_GG105_REWORK/mlb_feature_matrix.csv")
OUT_DIR = Path("exp_output/T9_GG105_REWORK")
FEATURE_COLS = ["ba_l10_shrunk", "bb_rate_l10", "days_rest", "park_factor_hits", "is_home_game"]


def load_feature_index():
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


def main() -> int:
    positions = deduplicate(load_portfolio(PORTFOLIO))
    feature_index = load_feature_index()

    joined = []
    for p in positions:
        row = feature_index.get((str(p.player_id), p.game_date))
        if row is not None:
            joined.append((p, row))
    print(f"Joined n={len(joined)} (of {len(positions)} MAIN resolved positions)")

    X = np.array([[float(row[c]) for c in FEATURE_COLS] for _, row in joined])
    # interaction term: ba_l10_shrunk * bb_rate_l10 -- the only feature A1
    # found with even a weak independent read (p=0.072, anti-predictive)
    interaction = X[:, 0] * X[:, 1]
    X = np.column_stack([X, interaction])
    y = np.array([reconstruct_event(p) for p, _ in joined])

    print(f"Event base rate: {y.mean():.3f} (n={len(y)})")

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=17)
    oof_pred = np.full(len(y), np.nan)
    for train_idx, test_idx in skf.split(X, y):
        scaler = StandardScaler().fit(X[train_idx])
        clf = LogisticRegression(C=1.0, max_iter=1000)
        clf.fit(scaler.transform(X[train_idx]), y[train_idx])
        oof_pred[test_idx] = clf.predict_proba(scaler.transform(X[test_idx]))[:, 1]
    assert not np.isnan(oof_pred).any()

    print(f"Out-of-fold candidate_model_p: mean={oof_pred.mean():.3f}, "
          f"std={oof_pred.std():.3f}, min={oof_pred.min():.3f}, max={oof_pred.max():.3f}")

    # Sanity: does candidate_model_p itself rank-order the reconstructed
    # event any better than the raw features did alone? (quick in-script
    # check before handing to the real D1 harness for the authoritative
    # fee_net_edge-based tercile test)
    order = np.argsort(oof_pred)
    n = len(order)
    thirds = np.array_split(order, 3)
    er = [y[idx].mean() for idx in thirds]
    print(f"OOF candidate_p terciles (bottom->top) event rate: {er[0]:.3f} / {er[1]:.3f} / {er[2]:.3f}")

    overrides = {}
    for (p, _row), pred in zip(joined, oof_pred):
        key = f"{p.player_id}|{p.game_date}|{p.threshold}"
        overrides[key] = float(pred)

    overrides_path = OUT_DIR / "a3_candidate_overrides.json"
    overrides_path.write_text(json.dumps(overrides, indent=2))
    print(f"\nWrote {len(overrides)} overrides -> {overrides_path}")
    print("\nNext: run scripts/what_if_harness.py --book t1t2t3 "
          f"--overrides-file {overrides_path} --portfolio {PORTFOLIO}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
