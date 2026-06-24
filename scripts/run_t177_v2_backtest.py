"""
T-177 Part C — v2 Model Anti-Predictive Backtest
=================================================

Script ID:    T-072-PART-C
ADR:          ADR-0031 Part D (Phase 3 start gate)
Purpose:      Re-evaluate the 114 closed NBA Finals paper positions using v2
              model predictions. Check whether v2's edge signal remains
              ANTI-PREDICTIVE or resolves to INCONCLUSIVE/MONOTONIC.

Phase 3 gate condition (DARK_PERIOD_PLAN.md):
  run_t177 on available NBA data WITH the fixed model must return
  INCONCLUSIVE or MONOTONIC (p > 0.05, not ANTI-PREDICTIVE) before the
  MLB C1 build begins.

Method:
  1. Load 114 closed positions from paper portfolio (Finals: June 5/8/10 2026).
  2. For each position: find player's last pre-Finals feature row in EXP-005.
  3. Add v1.4.0 playoff features:
       F-041 = 0.959603 (all Finals games are playoffs, calibrated multiplier)
       F-042 = NaN → imputed to 0.0 (no playoff TeamGameLog)
       F-043 = series_scoring_delta from prior Finals games (computed from
               paper portfolio actual_pts, which are ground truth)
  4. Apply v2 model (v2-065b9510) → v2_model_p.
  5. Compute v2_gross_edge = v2_model_p - mid_price_at_entry.
  6. Compute v2_fee_net_edge = v2_gross_edge - 0.07 * p * (1-p).
  7. Run Fisher's exact test on (edge > 0) vs (edge ≤ 0) outcome split.
  8. Compare verdict against v1 baseline (ANTI-PREDICTIVE at p=0.0505, n=114).

Approximation note:
  The feature vector for a Finals game should ideally use the player's L10
  from their most recent ~10 playoff games (late April – early June). The best
  available proxy is the player's LAST row in the EXP-005 matrix (May 25–30
  for playoff-tracked players, April 10–12 for regular-season-only players).
  This introduces measurement noise but is unbiased (the approximation does
  not systematically favor v2 over v1).

Usage:
    PYTHONPATH=src .venv/bin/python3 scripts/run_t177_v2_backtest.py

    --clean   : exclude fee-contaminated positions (default: include all)
    --verbose : print per-position detail
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

try:
    from scipy.stats import fisher_exact
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False

_SRC_ROOT = Path(__file__).parent.parent / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from prediction_market_bot.c2_feature_store.qualitative_store import (
    QualitativeSignalStore,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

PORTFOLIO_PATH  = Path("logs/paper_portfolio.json")
FEATURE_CSV     = Path("exp_output/EXP-005/EXP-005_feature_matrix.csv")
V2_MODEL_PATH   = Path("models/v2_model.joblib")
QS_CSV          = Path("qualitative_data/pam_v4/QS-2026-05-28-002_classifications.csv")
QS_ID           = "QS-2026-05-28-002"
SNAPSHOT_ID     = "SNAP-2026-05-28-002"

F041_MULTIPLIER = 0.959603   # Finals = playoffs, same as training calibration
KALSHI_FEE_RATE = 0.07       # 7% fee rate (fee = 0.07 * p * (1 - p))
ALPHA           = 0.05       # p-value threshold for ANTI-PREDICTIVE verdict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fee(mid_price: float) -> float:
    return KALSHI_FEE_RATE * mid_price * (1.0 - mid_price)


def _fisher_pvalue(n_pos_win: int, n_pos_tot: int, n_neg_win: int, n_neg_tot: int):
    a = n_pos_win;       b = n_pos_tot - n_pos_win
    c = n_neg_win;       d = n_neg_tot - n_neg_win
    if not _HAS_SCIPY:
        n = a + b + c + d
        if n == 0:
            return (1.0, 1.0)
        r1, r2 = a + b, c + d
        c1, c2 = a + c, b + d
        e_a = r1 * c1 / n; e_b = r1 * c2 / n
        e_c = r2 * c1 / n; e_d = r2 * c2 / n
        chi2 = sum(
            (o - e) ** 2 / e if e > 0 else 0.0
            for o, e in [(a, e_a), (b, e_b), (c, e_c), (d, e_d)]
        )
        if chi2 > 10.83: p = 0.001
        elif chi2 > 6.63: p = 0.01
        elif chi2 > 3.84: p = 0.05
        elif chi2 > 2.71: p = 0.10
        else: p = 0.20
        or_ = (a * d) / (b * c) if b > 0 and c > 0 else float("inf")
        return (or_, p)
    return fisher_exact([[a, b], [c, d]], alternative="two-sided")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(exclude_contaminated: bool = True, verbose: bool = False) -> int:
    # ------------------------------------------------------------------
    # 1. Load portfolio positions
    # ------------------------------------------------------------------
    with open(PORTFOLIO_PATH) as f:
        portfolio = json.load(f)

    positions = []
    for pos in portfolio.get("closed_positions", []):
        if pos.get("outcome") not in ("WIN", "LOSS"):
            continue
        if pos.get("duplicate_of"):
            continue
        if exclude_contaminated and pos.get("fee_contaminated"):
            continue
        positions.append(pos)

    print(f"Loaded {len(positions)} positions (exclude_contaminated={exclude_contaminated})")

    if len(positions) < 20:
        print(f"INCONCLUSIVE: n={len(positions)} < 20 minimum")
        return 0

    # ------------------------------------------------------------------
    # 2. Load EXP-005 feature matrix + QS
    # ------------------------------------------------------------------
    df = pd.read_csv(FEATURE_CSV, low_memory=False)
    df["game_date"] = pd.to_datetime(df["game_date"])

    from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
    logger = AuditLogger("logs/t177_v2.jsonl", min_severity="WARNING")
    qs = QualitativeSignalStore(logger=logger, snapshot_id=SNAPSHOT_ID)
    if not qs.load_ds01_snapshot(QS_CSV, QS_ID, session_id="T177-V2-BACKTEST"):
        print("ERROR: QS load failed", file=sys.stderr)
        return 1

    ok, df_q = qs.enrich_features(df, session_id="T177-V2-BACKTEST")
    if not ok:
        print("ERROR: QS enrichment failed", file=sys.stderr)
        return 1

    # ------------------------------------------------------------------
    # 3. Load v2 model
    # ------------------------------------------------------------------
    v2_artifact = joblib.load(V2_MODEL_PATH)
    v2_pipe     = v2_artifact["pipeline"]
    v2_features = v2_artifact["feature_names"]
    v2_medians  = v2_artifact["col_medians"]
    v2_version  = v2_artifact["model_version"]
    print(f"v2 model: {v2_version}")

    # ------------------------------------------------------------------
    # 4. Build per-position feature vectors and run v2 predictions
    # ------------------------------------------------------------------

    # Precompute F-043 series deltas from actual_pts in portfolio.
    # For each player: map game_date → list of prior Finals actual_pts and L10 mean.
    # Series = all Finals games for the same player (same opponent = Finals opponent).
    player_finals_history: dict[int, list[tuple]] = {}  # player_id → [(date, actual_pts, pts_l10_mean)]
    for pos in sorted(positions, key=lambda p: p["game_date"]):
        pid = int(pos["player_id"])
        gdate = pos["game_date"]
        actual = pos.get("actual_pts")
        if actual is None:
            continue
        if pid not in player_finals_history:
            player_finals_history[pid] = []
        player_finals_history[pid].append((gdate, float(actual)))

    results = []  # (v1_edge, v2_edge, win)
    skipped = 0

    for pos in sorted(positions, key=lambda p: p["game_date"]):
        pid        = int(pos["player_id"])
        game_date  = pos["game_date"]
        direction  = pos.get("direction", "YES")
        mid_price  = float(pos["mid_price_at_entry"])
        vig        = float(pos.get("vig_at_entry", 0.0))
        v1_model_p = float(pos["model_p"])
        v1_gross   = float(pos.get("gross_edge", v1_model_p - mid_price))
        v1_fee     = _fee(mid_price)
        v1_edge    = round(v1_gross - v1_fee, 6)
        win        = 1 if pos["outcome"] == "WIN" else 0

        # Find player's last matrix row before this Finals game
        player_rows = df_q[df_q["player_id"] == pid].sort_values("game_date")
        prior_rows  = player_rows[player_rows["game_date"] < game_date]
        if prior_rows.empty:
            if verbose:
                print(f"  SKIP player {pid} {game_date}: no prior matrix rows")
            skipped += 1
            continue

        last_row = prior_rows.iloc[-1].copy()
        pts_l10_mean = pd.to_numeric(last_row.get("pts_l10_mean"), errors="coerce")

        # F-041: Finals → playoffs multiplier
        last_row = last_row.copy()
        last_row["playoff_round_multiplier"]       = F041_MULTIPLIER
        last_row["opp_playoff_def_rating_l5_mean"] = np.nan

        # F-043: series_scoring_delta from prior Finals games
        history = player_finals_history.get(pid, [])
        prior_series_pts = [
            pts for (d, pts) in sorted(history)
            if d < game_date
        ]
        if prior_series_pts and not np.isnan(pts_l10_mean):
            last_row["series_scoring_delta"] = float(np.mean(prior_series_pts) - pts_l10_mean)
        else:
            last_row["series_scoring_delta"] = 0.0

        # Build feature vector
        feat_vals = []
        for feat in v2_features:
            val = last_row.get(feat, np.nan)
            try:
                feat_vals.append(float(val))
            except (TypeError, ValueError):
                feat_vals.append(np.nan)

        X = np.array(feat_vals, dtype=float).reshape(1, -1)
        # Impute with v2 training medians
        mask = np.isnan(X[0])
        X[0][mask] = v2_medians[mask]

        v2_model_p = float(v2_pipe.predict_proba(X)[0, 1])
        v2_gross   = v2_model_p - mid_price
        v2_edge    = round(v2_gross - v1_fee, 6)  # same fee structure

        results.append((v1_edge, v2_edge, win, pid, game_date, direction))

        if verbose:
            print(f"  {pos['player_name']:22s} {game_date} dir={direction:3s} "
                  f"v1_edge={v1_edge:+.4f} v2_edge={v2_edge:+.4f} "
                  f"win={win} f043={last_row['series_scoring_delta']:+.2f}")

    print(f"Evaluated: {len(results)}, skipped: {skipped}")

    # ------------------------------------------------------------------
    # 5. T-177 test: v1 and v2 comparison
    # ------------------------------------------------------------------
    def _run_t177(edges_wins, label):
        pos_group = [(e, w) for (e, w) in edges_wins if e > 0]
        neg_group = [(e, w) for (e, w) in edges_wins if e <= 0]

        n_pos_win = sum(w for _, w in pos_group)
        n_neg_win = sum(w for _, w in neg_group)
        n_pos = len(pos_group)
        n_neg = len(neg_group)

        if n_pos == 0 or n_neg == 0:
            print(f"\n{label}: INCONCLUSIVE — all positions on same side of edge=0")
            print(f"  edge>0: n={n_pos}  edge<=0: n={n_neg}")
            return "INCONCLUSIVE"

        wr_pos = n_pos_win / n_pos
        wr_neg = n_neg_win / n_neg
        or_, pval = _fisher_pvalue(n_pos_win, n_pos, n_neg_win, n_neg)

        if pval < ALPHA:
            verdict = "ANTI-PREDICTIVE" if wr_pos < wr_neg else "MONOTONIC"
        else:
            verdict = "INCONCLUSIVE"

        print(f"\n{label}:")
        print(f"  edge>0 : n={n_pos:3d}  wins={n_pos_win:3d}  winrate={wr_pos:.3f}")
        print(f"  edge<=0: n={n_neg:3d}  wins={n_neg_win:3d}  winrate={wr_neg:.3f}")
        print(f"  OR={or_:.3f}  p={pval:.4f}  verdict={verdict}")
        return verdict

    v1_pairs = [(r[0], r[2]) for r in results]
    v2_pairs = [(r[1], r[2]) for r in results]

    v1_verdict = _run_t177(v1_pairs, "v1 (28483b21) — baseline")
    v2_verdict = _run_t177(v2_pairs, f"v2 ({v2_version}) — retrained")

    # ------------------------------------------------------------------
    # 6. Phase 3 gate decision
    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    print(f"n evaluated: {len(results)}")
    print(f"v1 verdict:  {v1_verdict}")
    print(f"v2 verdict:  {v2_verdict}")
    print()

    if v2_verdict in ("INCONCLUSIVE", "MONOTONIC"):
        print("PHASE 3 GATE: OPEN — v2 edge signal is not anti-predictive.")
        print("  MLB C1 build may proceed per DARK_PERIOD_PLAN.md Phase 3.")
        exit_code = 0
    else:
        print("PHASE 3 GATE: BLOCKED — v2 edge signal remains ANTI-PREDICTIVE.")
        print("  Escalation: ADR-0031 risk register → Option A (halt + model class review).")
        exit_code = 2

    print("=" * 60)
    return exit_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="T-177 Part C: v2 model backtest")
    parser.add_argument("--clean",   action="store_true", default=False,
                        help="Exclude fee-contaminated positions (default: include all)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    sys.exit(main(exclude_contaminated=args.clean, verbose=args.verbose))
