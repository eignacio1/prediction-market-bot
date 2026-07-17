"""
EXP-010: EV Re-estimation — Refreshed Model (L1+L2, 78 features) vs Kalshi Vig
================================================================================
Experiment ID:   EXP-010
Phase:           Phase 6 Planning (T-069 — EV re-estimation with current model)
Status:          CANONICAL RUNNER — 2026-05-28

Purpose:
    Re-run EXP-004-style EV analysis using the current production model
    (L1+L2: 31 quant + 47 qual, QS-2026-05-28-002) against the 2025-26
    TEST set. EXP-004 used the 2021-24 model on the 2023-24 TEST set;
    this updates both the model and the evaluation window.

Key improvements over EXP-004:
    - Model trained on 5 seasons (2021-26) vs 3 seasons (2021-24)
    - Qualitative features (PRF archetypes + modifiers) add structural context
    - TEST set is 2025-26 regular season — current, more relevant market

Part A: historical vig backtest on 2025-26 TEST set using MEASURED_VIG_20260528
Part B: live market alignment for today's games (hotel wifi / hotspot required)

EXP-004 baseline (2023-24 model, 2023-24 TEST): EV +$0.0855/bet, 59% win rate

How to run:
    VENUE_API_KEY=$(grep VENUE_API_KEY .env | cut -d= -f2) \\
    PYTHONPATH=src .venv/bin/python3 src/prediction_market_bot/run_exp010.py

    Part B requires live Kalshi connectivity (hotel wifi or mobile hotspot).
    Part A runs offline if DS-02 unavailable.

Security (NFR-05):
    - VENUE_API_KEY from environment only; never logged
    - No order placement (read-only)
    - BOT_C4_ACTIVE must NOT be set
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

_SRC_ROOT = Path(__file__).parent.parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from prediction_market_bot.c2_feature_store.qualitative_store import (
    QualitativeSignalStore, DS01_FEATURE_NAMES,
)
from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

EXP_ID     = "EXP-010"
SESSION_ID = f"EXP-010-{uuid.uuid4().hex[:8].upper()}"

FEATURE_CSV = Path("exp_output/EXP-005/EXP-005_feature_matrix.csv")
QS_CSV      = Path("qualitative_data/pam_v4/QS-2026-05-28-002_classifications.csv")
QS_ID       = "QS-2026-05-28-002"
OUTPUT_DIR  = Path("exp_output/EXP-010")

FEATURE_WINDOW = 10
NULL_BRIER = 0.2500
MEASURED_VIG_20260528 = 0.01

EDGE_THRESHOLD_YES =  0.02
EDGE_THRESHOLD_NO  = -0.02

SNAPSHOT_ID = "SNAP-2026-05-28-002"

# EXP-004 comparison points
EXP004_EV_PER_BET    = 0.0855
EXP004_WIN_RATE      = 0.590
EXP004_BRIER_MODEL   = 0.2416
EXP004_TEST_SET      = "2023-24 regular season"

_PRUNED_V110 = {
    "season_type_is_playoffs","days_since_last_game","b2b_flag",
    "load_games_l7d","eri_prev_hot","eri_prev_cold","eri_consec_cold_games",
}
_NON_FEATURE_BASE = {
    "player_id","player_name","team_id","team_abbreviation",
    "game_id","game_date","season","season_type",
    "min","pts","reb","ast","stl","blk","tov","pf",
    "fgm","fga","fg_pct","fg3m","fg3a","fg3_pct","ftm","fta","ft_pct","plus_minus",
    "snapshot_id","ingestion_run_id","ingested_at",
    "temporal_cutoff","feature_run_id","feature_version","train_test_label","y_target",
    "prf_primary","prf_secondary","prf_hybrid_weight",
} | _PRUNED_V110


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

def _build_target(df: pd.DataFrame) -> pd.Series:
    col = f"pts_l{FEATURE_WINDOW}_mean"
    if col not in df.columns or "pts" not in df.columns:
        return pd.Series([np.nan]*len(df), index=df.index)
    pts = pd.to_numeric(df["pts"], errors="coerce")
    pm  = pd.to_numeric(df[col], errors="coerce")
    t   = (pts >= pm).astype("Int8")
    t[pts.isna() | pm.isna()] = pd.NA
    return t

def _impute(X: np.ndarray) -> np.ndarray:
    X = X.copy().astype(float)
    med = np.nanmedian(X, axis=0)
    med = np.where(np.isnan(med), 0.0, med)
    mask = np.isnan(X)
    X[mask] = np.take(med, np.where(mask)[1])
    return X

def _fit(X: np.ndarray, y: np.ndarray) -> Pipeline:
    base = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000,
                               random_state=42, class_weight="balanced")
    pipe = Pipeline([("sc", StandardScaler()),
                     ("clf", CalibratedClassifierCV(base, method="sigmoid", cv=3))])
    pipe.fit(X, y)
    return pipe

def _ece(y: np.ndarray, p: np.ndarray) -> float:
    yp = np.clip(p, 1e-6, 1-1e-6)
    frac, mean = calibration_curve(y, yp, n_bins=10, strategy="uniform")
    counts = np.histogram(yp, bins=10, range=(0.,1.))[0]
    counts = counts[counts > 0]
    n = min(len(frac), len(counts))
    return float(np.sum((counts[:n]/counts[:n].sum()) * np.abs(frac[:n]-mean[:n])))


# ---------------------------------------------------------------------------
# Part A: Historical vig simulation on 2025-26 TEST set
# ---------------------------------------------------------------------------

def run_part_a(test_df: pd.DataFrame, feature_names: list[str],
               model: Pipeline, live_vig: float) -> dict[str, Any]:
    print(f"\n{'='*60}")
    print("PART A — 2025-26 TEST set vig simulation")
    print(f"{'='*60}")
    print(f"TEST rows: {len(test_df):,}  |  Vig: {live_vig:.4f}")

    y_test = test_df["y_target"].astype(int).to_numpy()
    X_test = _impute(test_df[feature_names].to_numpy(dtype=float))
    p_test = model.predict_proba(X_test)[:, 1]

    brier = float(brier_score_loss(y_test, p_test))
    ece   = _ece(y_test, p_test)
    auc   = float(roc_auc_score(y_test, p_test))

    print(f"\nModel metrics:")
    print(f"  Brier: {brier:.4f}  (null: {NULL_BRIER:.4f}, Δ: {NULL_BRIER-brier:+.4f})")
    print(f"  ECE:   {ece:.4f}  |  AUC-ROC: {auc:.4f}")

    half_spread = live_vig / 2.0
    mip = 0.50                # market_implied_prob = 0.50 (conservative null)
    edge = p_test - mip

    yes_bets = (edge > EDGE_THRESHOLD_YES + half_spread)
    no_bets  = (edge < EDGE_THRESHOLD_NO  - half_spread)
    n_yes, n_no = int(yes_bets.sum()), int(no_bets.sum())
    n_pass = len(p_test) - n_yes - n_no

    yes_ask = mip + half_spread
    no_ask  = (1 - mip) + half_spread
    pnl_yes = np.where(yes_bets, np.where(y_test == 1, 1 - yes_ask, -yes_ask), 0)
    pnl_no  = np.where(no_bets,  np.where(y_test == 0, 1 - no_ask,  -no_ask),  0)
    total_pnl = float((pnl_yes + pnl_no).sum())
    n_bets = n_yes + n_no
    ev = total_pnl / n_bets if n_bets > 0 else 0.0
    win_yes = int((yes_bets & (y_test == 1)).sum())
    win_no  = int((no_bets  & (y_test == 0)).sum())
    win_rate = (win_yes + win_no) / n_bets if n_bets > 0 else 0.0

    print(f"\nBet simulation (mip=0.50, vig={live_vig:.3f}):")
    print(f"  YES: {n_yes:,}  NO: {n_no:,}  PASS: {n_pass:,}")
    print(f"  Total P&L: {total_pnl:+.2f}  ({n_bets} bets)")
    print(f"  EV/bet: {ev:+.4f}  |  Win rate: {win_rate:.1%}")
    print(f"\n  EXP-004 baseline: EV {EXP004_EV_PER_BET:+.4f} | Win {EXP004_WIN_RATE:.1%} | Test set: {EXP004_TEST_SET}")
    ev_change = ev - EXP004_EV_PER_BET
    print(f"  Δ EV vs EXP-004: {ev_change:+.4f}")

    return {
        "part": "A", "test_rows": len(test_df),
        "brier": round(brier,6), "ece": round(ece,6), "auc_roc": round(auc,6),
        "brier_improvement": round(NULL_BRIER-brier,6),
        "vig": round(live_vig,4), "bets_yes": n_yes, "bets_no": n_no,
        "bets_pass": n_pass, "total_pnl": round(total_pnl,4),
        "ev_per_bet": round(ev,6), "win_rate": round(win_rate,4),
        "exp004_ev_per_bet": EXP004_EV_PER_BET,
        "delta_ev_vs_exp004": round(ev_change,6),
    }


# ---------------------------------------------------------------------------
# Part B: Live market alignment (today's playoff games)
# ---------------------------------------------------------------------------

def run_part_b(df: pd.DataFrame, feature_names: list[str],
               model: Pipeline, snapshot: object) -> dict[str, Any]:
    print(f"\n{'='*60}")
    print("PART B — Live market alignment (today's playoff games)")
    print(f"{'='*60}")

    df["game_date"] = pd.to_datetime(df["game_date"])
    df["y_target"] = _build_target(df)
    usable = df[df["y_target"].notna() & df["temporal_cutoff"].notna()].copy()
    test_df = usable[usable["train_test_label"] == "TEST"]

    latest = (test_df.sort_values("game_date")
                     .groupby("player_id").last().reset_index())

    live_markets = snapshot.markets
    print(f"Live KXNBAPTS markets: {len(live_markets)}")

    bets, found = [], []
    for _, row in latest.iterrows():
        player_name = str(row.get("player_name", ""))
        last_name = player_name.split()[-1] if player_name else ""
        first_init = player_name[0] if player_name else ""

        player_mkts = [
            m for m in live_markets
            if last_name.upper() in m.player_name.upper()
            and first_init.upper() in m.player_name.upper()
            and m.status == "active" and m.has_live_quotes
        ]
        if not player_mkts:
            continue
        found.append(player_name)

        pts_mean = float(row.get(f"pts_l{FEATURE_WINDOW}_mean", np.nan))
        if np.isnan(pts_mean):
            continue

        closest = min(player_mkts, key=lambda m: abs(m.threshold - pts_mean))
        feat_row = row[feature_names].to_frame().T
        X = _impute(feat_row.to_numpy(dtype=float))
        p_est = float(model.predict_proba(X)[0, 1])

        mid  = closest.mid_price
        half = closest.half_spread
        edge = p_est - mid - half
        direction = ("YES" if edge > EDGE_THRESHOLD_YES
                     else "NO" if edge < EDGE_THRESHOLD_NO else "PASS")

        prf_primary = int(row.get("prf_primary", 0)) if "prf_primary" in row.index else None
        # Infer dominant archetype from one-hot columns
        prf_label = None
        for i in range(1, 16):
            col = f"prf_w{i:02d}"
            if col in row.index and float(row.get(col, 0)) > 0.5:
                prf_label = f"PRF-{i}"
                break

        print(f"\n  {player_name}")
        print(f"    pts_l10_mean: {pts_mean:.1f}  |  PRF: {prf_label or 'unknown'}")
        print(f"    Market: {closest.title}  |  mid={mid:.3f}  vig={closest.vig:.3f}")
        print(f"    p_estimate: {p_est:.3f}  |  edge: {edge:+.3f}  →  {direction}")

        bets.append({
            "player_name": player_name, "player_id": int(row.get("player_id", 0)),
            "prf": prf_label, "pts_l10_mean": round(pts_mean,2),
            "kalshi_ticker": closest.ticker, "kalshi_threshold": closest.threshold,
            "mid_price": round(mid,4), "vig": round(closest.vig,4),
            "p_estimate": round(p_est,4), "edge": round(edge,4), "direction": direction,
        })

    if not found:
        print("  No cohort players with live-quoted markets found.")
    actionable = [b for b in bets if b["direction"] != "PASS"]
    print(f"\n  Players matched: {len(found)}  |  Bets actionable: {len(actionable)}")

    return {
        "part": "B", "live_markets_fetched": len(live_markets),
        "cohort_players_matched": len(found), "bets": bets,
        "actionable_count": len(actionable),
        "has_actionable": len(actionable) > 0,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger = AuditLogger(OUTPUT_DIR / "audit_exp010.jsonl", min_severity="DEBUG")

    print(f"\n{'='*60}")
    print(f"EXP-010: EV Re-estimation — L1+L2 Refreshed Model")
    print(f"Session:  {SESSION_ID}")
    print(f"Model:    78 features (31 quant + 47 qual, QS-002 backdated)")
    print(f"Test set: 2025-26 regular season")
    print(f"{'='*60}\n")

    if os.environ.get("BOT_C4_ACTIVE"):
        print("FATAL: BOT_C4_ACTIVE set.", file=sys.stderr); sys.exit(1)

    if not FEATURE_CSV.exists():
        print(f"ERROR: {FEATURE_CSV} not found — run EXP-005 first.", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # 1. Load + enrich feature matrix
    # ------------------------------------------------------------------
    df = pd.read_csv(FEATURE_CSV)
    print(f"[DATA] {len(df):,} rows")

    qs = QualitativeSignalStore(logger=logger, snapshot_id=SNAPSHOT_ID)
    if not qs.load_ds01_snapshot(QS_CSV, QS_ID, session_id=SESSION_ID):
        print("ERROR: QS load failed", file=sys.stderr); sys.exit(1)

    ok, df_q = qs.enrich_features(df, session_id=SESSION_ID)
    if not ok:
        print("ERROR: enrich failed", file=sys.stderr); sys.exit(1)

    qual_names  = qs.get_qualitative_feature_names()
    quant_names = [c for c in df_q.columns
                   if c not in _NON_FEATURE_BASE and c not in set(qual_names)]
    feature_names = quant_names + qual_names
    print(f"[FEATURES] {len(feature_names)} total ({len(quant_names)} quant + {len(qual_names)} qual)")

    # ------------------------------------------------------------------
    # 2. Build target + splits
    # ------------------------------------------------------------------
    df_q["y_target"] = _build_target(df_q)
    usable = df_q[df_q["y_target"].notna() & df_q["temporal_cutoff"].notna()].copy()
    train_df = usable[usable["train_test_label"] == "TRAIN"].copy()
    test_df  = usable[usable["train_test_label"] == "TEST"].copy()
    print(f"[SPLIT] TRAIN {len(train_df):,} | TEST {len(test_df):,}")

    # ------------------------------------------------------------------
    # 3. Fit on TRAIN (L1+L2, 78 features)
    # ------------------------------------------------------------------
    print("\n[MODEL] Fitting on TRAIN...")
    X_tr = _impute(train_df[feature_names].to_numpy(dtype=float))
    y_tr = train_df["y_target"].astype(int).to_numpy()
    model = _fit(X_tr, y_tr)
    print("[MODEL] Fit complete.")

    # ------------------------------------------------------------------
    # 4. DS-02 connectivity (optional — Part A runs offline if unavailable)
    # ------------------------------------------------------------------
    print("\n[DS-02] Connecting to Kalshi API...")
    ds02_online, snapshot, live_vig = False, None, MEASURED_VIG_20260528
    quoted_markets: list[Any] = []

    try:
        client = KalshiMarketClient.from_env()
        ok, status = client.check_connectivity()
        if ok:
            print(f"  exchange_active: {status['exchange_active']}  trading_active: {status['trading_active']}")
            ok2, snapshot = client.fetch_player_points_markets()
            if ok2 and snapshot.markets:
                quoted = [m for m in snapshot.markets if m.has_live_quotes]
                if quoted:
                    import numpy as _np
                    live_vig = float(_np.median([m.vig for m in quoted]))
                    avg_vig  = float(_np.mean([m.vig for m in quoted]))
                    print(f"  Live vig — median: {live_vig:.4f}  avg: {avg_vig:.4f}  ({len(quoted)} quoted markets)")
                    quoted_markets = quoted
                    ds02_online = True
                    print(f"  Sample markets ({min(5, len(snapshot.markets))}):")
                    for m in snapshot.markets[:5]:
                        ps = f"mid={m.mid_price:.3f} vig={m.vig:.3f}" if m.has_live_quotes else "no quotes"
                        print(f"    {m.title:<40} {ps}")
                else:
                    print(f"  No live quotes. Using MEASURED_VIG_20260528={MEASURED_VIG_20260528}")
                    ds02_online = True
            else:
                print(f"  Market fetch failed. Part A offline. Part B skipped.")
        else:
            print(f"  Connectivity failed: {status}")
    except EnvironmentError as e:
        print(f"  {e}")

    if not ds02_online:
        print(f"\n  [DS-02 OFFLINE] Using MEASURED_VIG_20260528={MEASURED_VIG_20260528}")
        print(f"  Run on hotel wifi or mobile hotspot for Part B.")

    # ------------------------------------------------------------------
    # 5. Run parts
    # ------------------------------------------------------------------
    results_a = run_part_a(test_df.copy(), feature_names, model, live_vig)

    if ds02_online and snapshot is not None and snapshot.markets:
        results_b = run_part_b(df_q.copy(), feature_names, model, snapshot)
    else:
        print(f"\n{'='*60}")
        print("PART B — SKIPPED (DS-02 offline)")
        print(f"{'='*60}")
        results_b = {
            "part": "B", "status": "SKIPPED",
            "reason": "DS-02 unavailable — run on hotel wifi or mobile hotspot",
        }

    # ------------------------------------------------------------------
    # 6. Summary
    # ------------------------------------------------------------------
    print(f"\n{'='*60}")
    print("EXP-010 SUMMARY")
    print(f"{'='*60}")
    print(f"  Model:   78 features (L1+L2: 31 quant + 47 qual)")
    print(f"  TEST:    2025-26 regular season ({results_a['test_rows']:,} rows)")
    print(f"  EV/bet:  {results_a['ev_per_bet']:+.4f}  (EXP-004: {EXP004_EV_PER_BET:+.4f})")
    print(f"  Δ EV:    {results_a['delta_ev_vs_exp004']:+.4f} vs EXP-004 baseline")
    if results_b.get("status") == "SKIPPED":
        print(f"  Part B:  SKIPPED")
    else:
        print(f"  Part B:  {results_b['cohort_players_matched']} players matched  |  {results_b['actionable_count']} actionable")

    # ------------------------------------------------------------------
    # 7. Save
    # ------------------------------------------------------------------
    out = {
        "exp_id": EXP_ID, "session_id": SESSION_ID, "run_at": _utc_now(),
        "qs_id": QS_ID, "feature_count": len(feature_names),
        "ds02_online": ds02_online, "live_vig": round(live_vig,4),
        "vig_source": "live_DS02" if ds02_online and quoted_markets else f"MEASURED_VIG_20260528",
        "part_a": results_a, "part_b": results_b,
        "exp004_comparison": {
            "ev_per_bet": EXP004_EV_PER_BET,
            "test_set": EXP004_TEST_SET,
            "brier_model": EXP004_BRIER_MODEL,
        },
    }
    out_path = OUTPUT_DIR / "EXP-010_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults saved: {out_path}")


if __name__ == "__main__":
    main()
