"""
EXP-016: Playoff Generalization Ablation (T-072 / HYP-009)
===========================================================
Experiment ID:  EXP-016
Phase:          Phase 6 (T-072 — Playoff model validity)
Status:         RUNNER — 2026-05-29
Registered:     KI-008 (playoff model validity gap)

Hypothesis:
  HYP-009: The regular-season-trained model maintains Brier score within
  0.012 of its regular-season TEST performance when evaluated on playoff
  game rows.

  Rationale for 0.012 gate:
    Current edge margin = EV $0.0958/bet (EXP-010) against vig $0.030.
    Current Brier = 0.2461. A +0.012 Brier degradation would erode ~50%
    of edge, reducing EV to ~$0.048/bet — still positive but narrow.
    Beyond +0.012, the edge-to-vig ratio becomes unreliable for G6 evidence.

Design:
  - Regular season matrix: reuses EXP-005 feature matrix (same train/test
    splits; production model ancestry)
  - Playoff matrix: fresh pull via nba_api (SEASON_TYPE_PLAYOFFS);
    seasons 2021-22 through 2024-25 (complete playoff data available)
  - TRAIN: regular season rows before TRAIN_END_DATE (same as production)
  - TEST_REGULAR: regular season rows after VAL_END_DATE (same as EXP-005)
  - TEST_PLAYOFF: ALL playoff rows — fully held-out; model never trained on
    any playoff data

  Temporal integrity (TI-01): playoff rows never appear in TRAIN.
  Playoff game dates are always after their regular-season cutoff.

How to run:
  PYTHONPATH=src python3 src/prediction_market_bot/run_exp016.py

  Skip playoff data pull (use cached matrix):
  EXP016_SKIP_PULL=1 PYTHONPATH=src python3 ...

Output: exp_output/EXP-016/EXP-016_results.json

Security (NFR-05): No API keys required (nba_api is public).
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

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

from prediction_market_bot.c1_signal_ingestion.ingestion import (
    NBAIngestionClient,
    SEASON_TYPE_PLAYOFFS,
    SEASON_TYPE_REGULAR,
)
from prediction_market_bot.c2_feature_store.features import FeatureStore
from prediction_market_bot.c2_feature_store.qualitative_store import (
    QualitativeSignalStore,
    DS01_FEATURE_NAMES,
)
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from prediction_market_bot.cohort import get_player_ids_v2

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

EXP_ID      = "EXP-016"
SESSION_ID  = f"EXP-016-{uuid.uuid4().hex[:8].upper()}"
OUTPUT_DIR  = Path("exp_output/EXP-016")
PLAYOFF_CSV = OUTPUT_DIR / "EXP-016_playoff_matrix.csv"

# Regular season source — reuse EXP-005 matrix (production ancestry)
REGULAR_CSV = Path("exp_output/EXP-005/EXP-005_feature_matrix.csv")

QS_CSV      = Path("qualitative_data/pam_v4/QS-2026-05-28-002_classifications.csv")
QS_ID       = "QS-2026-05-28-002"
SNAPSHOT_ID = "SNAP-EXP-016-001"

# Playoff seasons to pull — complete data available for these
PLAYOFF_SEASONS = ["2021-22", "2022-23", "2023-24", "2024-25"]

# Must match EXP-005 splits exactly (temporal integrity TI-01)
TRAIN_END_DATE = "2024-04-14"
VAL_END_DATE   = "2025-04-13"

# Production baseline (EXP-005 / EXP-010 ancestry)
BASELINE_BRIER = 0.2461
BASELINE_ECE   = 0.0342
BASELINE_AUC   = 0.5765

# HYP-009 gate: playoff Brier degradation must be < 0.012 vs regular TEST
# Rationale: +0.012 Brier erodes ~50% of current EV margin; beyond this,
# paper results are unreliable for G6 evidence
PLAYOFF_BRIER_GATE = 0.012

PLAYER_IDS: list[int] = get_player_ids_v2()

_NON_FEATURE = {
    "player_id","player_name","team_id","team_abbreviation","game_id","game_date",
    "game_date_dt",  # Timestamp column added during split — must not be a feature
    "season","season_type","matchup","opponent_team_abbr","min","pts","reb","ast",
    "stl","blk","tov","pf","fgm","fga","fg_pct","fg3m","fg3a","fg3_pct","ftm",
    "fta","ft_pct","plus_minus","snapshot_id","ingestion_run_id","ingested_at",
    "temporal_cutoff","feature_run_id","feature_version","train_test_label","y_target",
    "prf_primary","prf_secondary","prf_hybrid_weight",
    "season_type_is_playoffs","days_since_last_game","b2b_flag","load_games_l7d",
    "eri_prev_hot","eri_prev_cold","eri_consec_cold_games",
    "is_home_game","opp_def_rating_l10_mean",
}


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _build_target(df: pd.DataFrame) -> pd.Series:
    col = "pts_l10_mean"
    pts = pd.to_numeric(df["pts"], errors="coerce")
    pm  = pd.to_numeric(df.get(col, pd.Series(dtype=float)), errors="coerce")
    t   = (pts >= pm).astype("Int8")
    t[pts.isna() | pm.isna()] = pd.NA
    return t


def _impute(X: np.ndarray) -> np.ndarray:
    X   = X.copy().astype(float)
    med = np.nanmedian(X, axis=0)
    med = np.where(np.isnan(med), 0.0, med)
    mask = np.isnan(X)
    X[mask] = np.take(med, np.where(mask)[1])
    return X


def _ece(y: np.ndarray, p: np.ndarray) -> float:
    yp = np.clip(p, 1e-6, 1 - 1e-6)
    try:
        frac, mean = calibration_curve(y, yp, n_bins=10, strategy="uniform")
    except ValueError:
        return float("nan")
    counts = np.histogram(yp, bins=10, range=(0., 1.))[0]
    counts = counts[counts > 0]
    n = min(len(frac), len(counts))
    if n == 0:
        return float("nan")
    return float(np.sum((counts[:n] / counts[:n].sum()) * np.abs(frac[:n] - mean[:n])))


def _fit_model(X_tr: np.ndarray, y_tr: np.ndarray) -> Pipeline:
    base = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000,
                              random_state=42, class_weight="balanced",
                              penalty="l2")
    pipe = Pipeline([("sc", StandardScaler()),
                     ("clf", CalibratedClassifierCV(base, method="sigmoid", cv=3))])
    pipe.fit(X_tr, y_tr)
    return pipe


# ---------------------------------------------------------------------------
# Playoff data pull
# ---------------------------------------------------------------------------

def pull_playoff_matrix(logger: AuditLogger) -> pd.DataFrame:
    """Pull playoff game logs for cohort, derive v1.2.0 features, return matrix."""
    print(f"\n[PULL] Fetching playoff logs: {len(PLAYER_IDS)} players × {len(PLAYOFF_SEASONS)} seasons...")

    ingestion = NBAIngestionClient(logger=logger, snapshot_id=SNAPSHOT_ID)
    frames: list[pd.DataFrame] = []

    for season in PLAYOFF_SEASONS:
        season_rows = 0
        for i, pid in enumerate(PLAYER_IDS, 1):
            ok, df = ingestion.fetch_player_game_log(pid, season, SEASON_TYPE_PLAYOFFS)
            if ok and not df.empty:
                frames.append(df)
                season_rows += len(df)
            if i % 15 == 0:
                print(f"  {season} [{i}/{len(PLAYER_IDS)}]")
        print(f"  {season}: {season_rows} playoff rows")

    if not frames:
        print("[PULL] WARNING: No playoff data found. Players may not have playoff games.")
        return pd.DataFrame()

    raw = pd.concat(frames, ignore_index=True)
    print(f"[PULL] {len(raw):,} total playoff player-game rows across {len(PLAYOFF_SEASONS)} seasons")

    print("[C2] Deriving v1.2.0 features on playoff rows...")
    feat_store = FeatureStore(logger=logger, snapshot_id=SNAPSHOT_ID)
    ok_f, feature_df = feat_store.compute_features_bulk(raw)
    if not ok_f or feature_df.empty:
        raise RuntimeError("Feature derivation failed on playoff data")
    print(f"[C2] {len(feature_df):,} playoff feature rows")

    return feature_df


# ---------------------------------------------------------------------------
# QS enrichment (same as production)
# ---------------------------------------------------------------------------

def enrich_qs(df: pd.DataFrame, logger: AuditLogger) -> pd.DataFrame:
    qs = QualitativeSignalStore(logger=logger, snapshot_id=SNAPSHOT_ID)
    if not qs.load_ds01_snapshot(QS_CSV, QS_ID, session_id=SESSION_ID):
        raise RuntimeError("QS load failed")
    ok, enriched = qs.enrich_features(df, session_id=SESSION_ID)
    if not ok:
        raise RuntimeError("QS enrich failed")
    return enriched


# ---------------------------------------------------------------------------
# Evaluation helper
# ---------------------------------------------------------------------------

def _evaluate_set(
    label: str,
    model: Pipeline,
    feature_names: list[str],
    df: pd.DataFrame,
) -> dict:
    df = df.copy()
    df["y_target"] = _build_target(df)
    df = df.dropna(subset=["y_target"])
    if len(df) < 30:
        print(f"  [{label}] Insufficient rows ({len(df)}) — skipping")
        return {"label": label, "n": len(df), "brier": None, "ece": None, "auc": None}

    available = [c for c in feature_names if c in df.columns]
    missing   = [c for c in feature_names if c not in df.columns]
    X = np.array([[row[c] if c in df.columns else np.nan
                   for c in feature_names]
                  for _, row in df.iterrows()], dtype=float)
    X = _impute(X)
    y = df["y_target"].astype(int).values
    p = model.predict_proba(X)[:, 1]

    brier = float(brier_score_loss(y, p))
    ece   = _ece(y, p)
    try:
        auc = float(roc_auc_score(y, p))
    except ValueError:
        auc = float("nan")

    null_brier = float(brier_score_loss(y, np.full_like(p, y.mean())))

    print(f"  [{label}]  n={len(df):,}  Brier {brier:.4f}  "
          f"(Δ vs null: +{null_brier - brier:.4f})  "
          f"ECE {ece:.4f}  AUC {auc:.4f}")
    if missing:
        print(f"    Warning: {len(missing)} features missing → NaN-imputed")

    return {
        "label":      label,
        "n":          len(df),
        "brier":      brier,
        "null_brier": null_brier,
        "delta_vs_null": null_brier - brier,
        "ece":        ece,
        "auc":        auc,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger = AuditLogger(Path("logs/audit.jsonl"), min_severity="INFO")
    Path("logs").mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print(f"{EXP_ID}: Playoff Generalization Ablation (HYP-009 / T-072)")
    print(f"Session:  {SESSION_ID}")
    print(f"Baseline: Brier {BASELINE_BRIER} | ECE {BASELINE_ECE}")
    print(f"Gate:     Playoff Δ Brier < {PLAYOFF_BRIER_GATE} vs regular TEST")
    print("=" * 65)

    # ------------------------------------------------------------------
    # 1. Load regular season matrix (EXP-005 ancestry)
    # ------------------------------------------------------------------
    if not REGULAR_CSV.exists():
        print(f"ERROR: {REGULAR_CSV} not found — run run_exp005.py first.", file=sys.stderr)
        sys.exit(1)

    print(f"\n[REGULAR] Loading regular season matrix from {REGULAR_CSV}...")
    reg_df = pd.read_csv(REGULAR_CSV)
    reg_df = enrich_qs(reg_df, logger)
    reg_df["game_date_dt"] = pd.to_datetime(reg_df["game_date"], errors="coerce")
    print(f"[REGULAR] {len(reg_df):,} rows")

    # ------------------------------------------------------------------
    # 2. Pull or load playoff matrix
    # ------------------------------------------------------------------
    skip_pull = os.environ.get("EXP016_SKIP_PULL", "").strip() == "1"

    if skip_pull and PLAYOFF_CSV.exists():
        print(f"\n[PLAYOFF] Loading cached matrix from {PLAYOFF_CSV}...")
        play_df = pd.read_csv(PLAYOFF_CSV)
        play_df = enrich_qs(play_df, logger)
    else:
        play_df = pull_playoff_matrix(logger)
        if not play_df.empty:
            play_df.to_csv(PLAYOFF_CSV, index=False)
            print(f"[PLAYOFF] Cached: {PLAYOFF_CSV}")
            play_df = enrich_qs(play_df, logger)

    if play_df.empty:
        print("\nWARNING: No playoff data available. HYP-009 is INCONCLUSIVE.")
        _write_results(
            {"verdict": "INCONCLUSIVE", "reason": "no_playoff_data"},
            {}, {}, {}, [], logger
        )
        return

    play_df["game_date_dt"] = pd.to_datetime(play_df["game_date"], errors="coerce")
    print(f"[PLAYOFF] {len(play_df):,} playoff rows across {play_df['season'].nunique()} seasons")

    # ------------------------------------------------------------------
    # 3. Build feature list (shared between regular + playoff; v1.2.0)
    # ------------------------------------------------------------------
    all_cols  = set(reg_df.columns) | set(play_df.columns)
    feat_cols = sorted(c for c in all_cols if c not in _NON_FEATURE)

    # ------------------------------------------------------------------
    # 4. Train on regular season TRAIN split
    # ------------------------------------------------------------------
    train_df = reg_df[reg_df["game_date_dt"] <= pd.Timestamp(TRAIN_END_DATE)].copy()
    train_df["y_target"] = _build_target(train_df)
    train_df = train_df.dropna(subset=["y_target"])

    X_tr = np.array([[row[c] if c in train_df.columns else np.nan
                       for c in feat_cols]
                      for _, row in train_df.iterrows()], dtype=float)
    X_tr = _impute(X_tr)
    y_tr = train_df["y_target"].astype(int).values

    print(f"\n[MODEL] Training on regular season TRAIN ({len(train_df):,} rows, {len(feat_cols)} features)...")
    model = _fit_model(X_tr, y_tr)
    print("[MODEL] Fit complete.")

    # ------------------------------------------------------------------
    # 5. Evaluate on regular season TEST (same as production benchmark)
    # ------------------------------------------------------------------
    reg_test_df = reg_df[reg_df["game_date_dt"] > pd.Timestamp(VAL_END_DATE)].copy()
    print(f"\n[EVAL] Regular season TEST ({len(reg_test_df):,} rows):")
    reg_result = _evaluate_set("regular_TEST", model, feat_cols, reg_test_df)

    # ------------------------------------------------------------------
    # 6. Evaluate on all playoff rows (fully held-out)
    # ------------------------------------------------------------------
    print(f"\n[EVAL] Playoff rows by season:")
    playoff_by_season = []
    for season in PLAYOFF_SEASONS:
        season_df = play_df[play_df["season"] == season].copy()
        if len(season_df) >= 30:
            r = _evaluate_set(f"playoffs_{season}", model, feat_cols, season_df)
            playoff_by_season.append(r)

    print(f"\n[EVAL] All playoff rows ({len(play_df):,} rows):")
    playoff_all_result = _evaluate_set("playoffs_ALL", model, feat_cols, play_df)

    # ------------------------------------------------------------------
    # 7. HYP-009 verdict
    # ------------------------------------------------------------------
    reg_brier  = reg_result.get("brier")
    play_brier = playoff_all_result.get("brier")

    if reg_brier is None or play_brier is None:
        verdict = "INCONCLUSIVE"
        delta   = None
        verdict_detail = "insufficient data for one or both sets"
    else:
        delta = play_brier - reg_brier
        if delta < PLAYOFF_BRIER_GATE:
            verdict = "CONFIRMED"
        else:
            verdict = "FALSIFIED"

    print("\n" + "=" * 65)
    print(f"HYP-009 RESULT: {verdict}")
    if reg_brier is not None:
        print(f"  Regular TEST Brier:  {reg_brier:.4f}")
    if play_brier is not None:
        print(f"  Playoff ALL Brier:   {play_brier:.4f}")
    if delta is not None:
        print(f"  Δ (playoff - regular): {delta:+.4f}  (gate: < {PLAYOFF_BRIER_GATE})")
    if verdict == "CONFIRMED":
        print(f"  Model generalizes to playoffs within acceptable degradation.")
        print(f"  Paper bets during playoffs are valid G6 evidence.")
    elif verdict == "FALSIFIED":
        print(f"  Playoff degradation exceeds edge margin. Paper bets during playoffs")
        print(f"  should be weighted less heavily in G6 evidence. Register KI-008.")
    print("=" * 65)

    _write_results(
        {"verdict": verdict, "delta": delta,
         "reg_brier": reg_brier, "playoff_brier": play_brier,
         "gate": PLAYOFF_BRIER_GATE},
        reg_result, playoff_all_result,
        {"train_rows": len(train_df), "reg_test_rows": len(reg_test_df),
         "playoff_rows": len(play_df), "features": len(feat_cols)},
        playoff_by_season,
        logger,
    )


def _write_results(
    verdict: dict,
    reg_result: dict,
    playoff_result: dict,
    metadata: dict,
    by_season: list,
    logger: AuditLogger,
) -> None:
    results = {
        "exp_id":          EXP_ID,
        "session_id":      SESSION_ID,
        "run_at":          _utc_now(),
        "hypothesis":      "HYP-009",
        "verdict":         verdict,
        "regular_test":    reg_result,
        "playoff_all":     playoff_result,
        "playoff_by_season": by_season,
        "metadata":        metadata,
        "baseline":        {
            "brier": BASELINE_BRIER, "ece": BASELINE_ECE, "auc": BASELINE_AUC,
            "source": "EXP-005/EXP-010",
        },
    }
    out = OUTPUT_DIR / "EXP-016_results.json"
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nResults saved: {out}")


if __name__ == "__main__":
    main()
