"""
EXP-015: T3 Analytical Backtest — Pre-Tip Momentum Signal Simulation
=====================================================================
Experiment ID:   EXP-015
Phase:           Phase 7 (T3 band validation — HYP-008)
Status:          OFFLINE RUNNER — 2026-05-29

Purpose:
    Analytical simulation of the T3 momentum signal using the EXP-005 TEST set.
    Quantifies the EV impact of the T3 CONFIRM/FADE/NEUTRAL filter relative to
    the T1-only baseline (EXP-010: EV +$0.0958/bet, 871 bets, kelly=0.25).

    The Kelly tradeoff:
        T3 CONFIRM: edge × 1.15 at kelly=0.10
        T1-only:    edge × 1.0  at kelly=0.25
        Effective ratio per CONFIRM bet = (0.10 × 1.15) / 0.25 = 0.46

    HYP-008 gate: EV_T3/EV_T1 > 0.90 OR confirm-signal win_rate > 0.66

Simulation design:
    - Synthetic price drifts drawn from N(0, drift_std) for each bet
    - T3 signal assigned per run_t3_pretip.py lines 165–178 logic
    - P6 orchestrator rules applied per execution_bands_orchestrator._apply_t3_rules()
    - NEUTRAL: proceed at T1 Kelly (0.25) — no T3 signal → T1 unchanged
    - CONFIRM: proceed at T3 Kelly (0.10) with CONFIRM_MULTIPLIER edge boost
    - FADE:    HOLD — no bet placed

How to run:
    PYTHONPATH=src python3 src/prediction_market_bot/run_exp015.py

Security (NFR-05):
    No API keys. BOT_C4_ACTIVE must NOT be set.
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

from prediction_market_bot.c2_feature_store.qualitative_store import (
    QualitativeSignalStore,
)
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from prediction_market_bot.execution_bands import ExecutionBand, get_band_config
from typing import Any

EXP_ID     = "EXP-015"
SESSION_ID = f"EXP-015-{uuid.uuid4().hex[:8].upper()}"

FEATURE_CSV  = Path("exp_output/EXP-005/EXP-005_feature_matrix.csv")
QS_CSV       = Path("qualitative_data/pam_v4/QS-2026-05-28-002_classifications.csv")
QS_ID        = "QS-2026-05-28-002"
SNAPSHOT_ID  = "SNAP-2026-05-28-002"
OUTPUT_DIR   = Path("exp_output/EXP-015")

# Band Kelly fractions from execution_bands.py (single source of truth)
T1_KELLY = get_band_config(ExecutionBand.T1_MULTI_DAY).kelly_fraction   # 0.25
T3_KELLY = get_band_config(ExecutionBand.T3_PRE_TIP).kelly_fraction     # 0.10

# T3 momentum constants matching run_t3_pretip.py
MOMENTUM_THRESHOLD: float = 0.025
CONFIRM_MULTIPLIER: float = 1.15
FADE_MULTIPLIER:    float = 0.75

# Simulation grid
DRIFT_STD_VALUES = [0.010, 0.015, 0.020, 0.025, 0.030]
N_SIMULATIONS    = 10_000
RANDOM_SEED      = 42

# HYP-008 gates
EV_RATIO_GATE  = 0.90
WIN_RATE_GATE  = 0.66

# Backtest parameters matching EXP-010
FEATURE_WINDOW      = 10
NULL_BRIER          = 0.2500
MEASURED_VIG        = 0.030
MIP                 = 0.50     # market implied probability (conservative null)
EDGE_THRESHOLD_YES  =  0.02
EDGE_THRESHOLD_NO   = -0.02

_PRUNED_V110 = {
    "season_type_is_playoffs", "days_since_last_game", "b2b_flag",
    "load_games_l7d", "eri_prev_hot", "eri_prev_cold", "eri_consec_cold_games",
}
_NON_FEATURE_BASE = {
    "player_id", "player_name", "team_id", "team_abbreviation",
    "game_id", "game_date", "season", "season_type",
    "min", "pts", "reb", "ast", "stl", "blk", "tov", "pf",
    "fgm", "fga", "fg_pct", "fg3m", "fg3a", "fg3_pct", "ftm", "fta", "ft_pct", "plus_minus",
    "snapshot_id", "ingestion_run_id", "ingested_at",
    "temporal_cutoff", "feature_run_id", "feature_version", "train_test_label", "y_target",
    "prf_primary", "prf_secondary", "prf_hybrid_weight",
} | _PRUNED_V110


# ---------------------------------------------------------------------------
# Helpers (copied from run_exp010.py — pattern used by all exp runners)
# ---------------------------------------------------------------------------


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _build_target(df: pd.DataFrame) -> pd.Series:
    col = f"pts_l{FEATURE_WINDOW}_mean"
    if col not in df.columns or "pts" not in df.columns:
        return pd.Series([np.nan] * len(df), index=df.index)
    pts = pd.to_numeric(df["pts"], errors="coerce")
    pm  = pd.to_numeric(df[col], errors="coerce")
    t   = (pts >= pm).astype("Int8")
    t[pts.isna() | pm.isna()] = pd.NA  # type: ignore[call-overload]  # pandas-stubs: no NAType overload for bool-mask key
    return t


def _impute(X: np.ndarray) -> np.ndarray:
    X   = X.copy().astype(float)
    med = np.nanmedian(X, axis=0)
    med = np.where(np.isnan(med), 0.0, med)
    mask = np.isnan(X)
    X[mask] = np.take(med, np.where(mask)[1])
    return X


def _fit_model(X: np.ndarray, y: np.ndarray) -> Pipeline:
    base = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000,
                               random_state=42, class_weight="balanced")
    pipe = Pipeline([("sc", StandardScaler()),
                     ("clf", CalibratedClassifierCV(base, method="sigmoid", cv=3))])
    pipe.fit(X, y)
    return pipe


def _ece(y: np.ndarray, p: np.ndarray) -> float:
    yp = np.clip(p, 1e-6, 1 - 1e-6)
    frac, mean = calibration_curve(y, yp, n_bins=10, strategy="uniform")
    counts = np.histogram(yp, bins=10, range=(0., 1.))[0]
    counts = counts[counts > 0]
    n = min(len(frac), len(counts))
    return float(np.sum((counts[:n] / counts[:n].sum()) * np.abs(frac[:n] - mean[:n])))


# ---------------------------------------------------------------------------
# EXP-015 core functions
# ---------------------------------------------------------------------------


def load_test_bets(
    feature_csv: Path,
    qs_csv: Path,
    qs_id: str,
    logger: AuditLogger,
) -> list[dict[str, Any]]:
    """
    Refit LR on TRAIN, score TEST set, return actionable bets.

    Mirrors run_part_a() from run_exp010.py.  Each bet record:
        {player_name, p_estimate, mid_price, edge, direction, y_target}

    Only YES and NO bets are returned (PASS bets excluded).
    """
    df = pd.read_csv(feature_csv)

    qs = QualitativeSignalStore(logger=logger, snapshot_id=SNAPSHOT_ID)
    if not qs.load_ds01_snapshot(qs_csv, qs_id, session_id=SESSION_ID):
        raise RuntimeError("QS load failed")
    ok, df_q = qs.enrich_features(df, session_id=SESSION_ID)
    if not ok:
        raise RuntimeError("QS enrich failed")

    qual_names  = qs.get_qualitative_feature_names()
    quant_names = [c for c in df_q.columns
                   if c not in _NON_FEATURE_BASE and c not in set(qual_names)]
    feature_names = quant_names + qual_names

    df_q["y_target"] = _build_target(df_q)
    usable   = df_q[df_q["y_target"].notna() & df_q["temporal_cutoff"].notna()].copy()
    train_df = usable[usable["train_test_label"] == "TRAIN"].copy()
    test_df  = usable[usable["train_test_label"] == "TEST"].copy()

    X_tr = _impute(train_df[feature_names].to_numpy(dtype=float))
    y_tr = train_df["y_target"].astype(int).to_numpy()
    model = _fit_model(X_tr, y_tr)

    y_test = test_df["y_target"].astype(int).to_numpy()
    X_test = _impute(test_df[feature_names].to_numpy(dtype=float))
    p_test = model.predict_proba(X_test)[:, 1]

    half_spread = MEASURED_VIG / 2.0
    edge_arr    = p_test - MIP

    bets = []
    for i in range(len(test_df)):
        edge = float(edge_arr[i])
        if edge > EDGE_THRESHOLD_YES + half_spread:
            direction = "YES"
        elif edge < EDGE_THRESHOLD_NO - half_spread:
            direction = "NO"
        else:
            continue  # PASS — not actionable
        row = test_df.iloc[i]
        bets.append({
            "player_name": str(row.get("player_name", "")),
            "p_estimate":  round(float(p_test[i]), 6),
            "mid_price":   MIP,
            "edge":        round(edge, 6),
            "direction":   direction,
            "y_target":    int(y_test[i]),
        })

    return bets


def simulate_t3_signal(
    bet: dict[str, Any],
    drift_std: float,
    rng: np.random.Generator,
) -> str:
    """
    Draw a synthetic price drift and assign CONFIRM / FADE / NEUTRAL.

    Mirrors T3 momentum logic from run_t3_pretip.py lines 165–178.
    A positive drift means the market price rose (smart money on YES).
    """
    price_drift = float(rng.normal(0, drift_std))
    direction   = bet["direction"]

    if direction == "YES" and price_drift >= MOMENTUM_THRESHOLD:
        return "CONFIRM"
    if direction == "NO"  and price_drift <= -MOMENTUM_THRESHOLD:
        return "CONFIRM"
    if direction == "YES" and price_drift <= -MOMENTUM_THRESHOLD:
        return "FADE"
    if direction == "NO"  and price_drift >= MOMENTUM_THRESHOLD:
        return "FADE"
    return "NEUTRAL"


def compute_outcome_ev(bet: dict[str, Any], signal: str) -> dict[str, Any]:
    """
    Apply P6 multi-band rules (from execution_bands_orchestrator._apply_t3_rules)
    to a single bet+signal.  Returns EV metrics relative to T1 baseline.

    P6 rules implemented here:
      CONFIRM  → PROCEED at T3_KELLY; |edge| boosted by CONFIRM_MULTIPLIER
      FADE     → HOLD; no bet placed; EV = 0
      NEUTRAL  → PROCEED at T1_KELLY; T3 made no difference; full T1 sizing

    edge_applied is always positive (|edge| × multiplier) — sign is absorbed into
    direction so EV = kelly × edge_applied is always non-negative for actionable bets.
    """
    edge      = float(bet["edge"])
    abs_edge  = abs(edge)   # YES edge > 0; NO edge < 0; abs_edge = |edge|
    direction = bet["direction"]
    y_target  = int(bet["y_target"])

    half_spread = MEASURED_VIG / 2.0
    yes_ask     = MIP + half_spread
    no_ask      = (1 - MIP) + half_spread

    if signal == "CONFIRM":
        kelly_applied       = T3_KELLY
        edge_applied        = abs_edge * CONFIRM_MULTIPLIER
        # EV ratio vs T1: (T3_KELLY × CONFIRM_MULTIPLIER) / T1_KELLY = 0.46 historically.
        # ADR-0048 (2026-07-29) zeroed T1_KELLY; ratio to a zero baseline is undefined,
        # not 0.46 — report 0.0 rather than divide by zero.
        position_size_ratio = (
            0.0 if T1_KELLY == 0.0
            else round((T3_KELLY * CONFIRM_MULTIPLIER) / T1_KELLY, 4)
        )
    elif signal == "FADE":
        kelly_applied       = 0.0
        edge_applied        = 0.0
        position_size_ratio = 0.0
    else:  # NEUTRAL — T3 had no information; T1 proceeds at full sizing
        kelly_applied       = T1_KELLY
        edge_applied        = abs_edge
        position_size_ratio = 1.0

    expected_value = kelly_applied * edge_applied

    if signal == "FADE":
        outcome_pnl = 0.0
    elif direction == "YES":
        outcome_pnl = kelly_applied * (1 - yes_ask if y_target == 1 else -yes_ask)
    else:  # NO
        outcome_pnl = kelly_applied * (1 - no_ask if y_target == 0 else -no_ask)

    return {
        "signal":              signal,
        "kelly_applied":       round(kelly_applied, 4),
        "edge_applied":        round(edge_applied, 4),
        "position_size_ratio": round(position_size_ratio, 4),
        "expected_value":      round(expected_value, 6),
        "outcome_pnl":         round(outcome_pnl, 6),
    }


def run_monte_carlo(
    test_bets: list[dict[str, Any]],
    drift_std: float,
    n_sims: int,
    rng: np.random.Generator,
) -> dict[str, Any]:
    """
    Run N_SIMULATIONS of synthetic T3 signal draws and aggregate EV metrics.

    Vectorised: generates (n_sims × n_bets) drift matrix in one call.
    """
    n_bets = len(test_bets)

    directions = np.array([b["direction"] for b in test_bets])
    y_targets  = np.array([int(b["y_target"]) for b in test_bets])
    edges      = np.array([float(b["edge"]) for b in test_bets])
    abs_edges  = np.abs(edges)  # always positive; |p_est - MIP|

    # Shape (n_sims, n_bets)
    drifts   = rng.normal(0, drift_std, (n_sims, n_bets))
    yes_mask = (directions == "YES")   # (n_bets,) broadcast to (n_sims, n_bets)

    confirm_mat = (yes_mask & (drifts >= MOMENTUM_THRESHOLD)) | \
                  (~yes_mask & (drifts <= -MOMENTUM_THRESHOLD))
    fade_mat    = (yes_mask & (drifts <= -MOMENTUM_THRESHOLD)) | \
                  (~yes_mask & (drifts >= MOMENTUM_THRESHOLD))
    neutral_mat = ~confirm_mat & ~fade_mat

    # EV per bet per simulation (using abs_edges so YES and NO bets both contribute positively)
    # NEUTRAL: proceeds at T1_KELLY → same EV as T1 baseline → EV ratio = 1.0 for neutral bets
    t3_ev_mat = (
        confirm_mat * (T3_KELLY * CONFIRM_MULTIPLIER * abs_edges) +
        neutral_mat * (T1_KELLY * abs_edges)
        # fade contributes 0
    )
    t3_ev_per_sim  = t3_ev_mat.mean(axis=1)              # (n_sims,)
    t1_ev_baseline = float((T1_KELLY * abs_edges).mean()) # scalar — always > 0

    ev_ratio_per_sim = (t3_ev_per_sim / t1_ev_baseline
                        if t1_ev_baseline > 0 else np.zeros(n_sims))

    # Win vector: True when the bet outcome is correct
    win_vec = ((yes_mask) & (y_targets == 1)) | ((~yes_mask) & (y_targets == 0))  # (n_bets,)

    confirm_total_per_sim = confirm_mat.sum(axis=1)
    confirm_wins_per_sim  = (confirm_mat & win_vec).sum(axis=1)
    total_confirm         = int(confirm_total_per_sim.sum())
    total_confirm_wins    = int(confirm_wins_per_sim.sum())
    confirm_win_rate      = total_confirm_wins / total_confirm if total_confirm > 0 else 0.0

    fade_total_per_sim = fade_mat.sum(axis=1)
    fade_wins_per_sim  = (fade_mat & win_vec).sum(axis=1)
    total_fade         = int(fade_total_per_sim.sum())
    total_fade_wins    = int(fade_wins_per_sim.sum())
    faded_miss_rate    = total_fade_wins / total_fade if total_fade > 0 else 0.0

    return {
        "drift_std":         drift_std,
        "confirm_rate":      float(confirm_mat.mean()),
        "fade_rate":         float(fade_mat.mean()),
        "neutral_rate":      float(neutral_mat.mean()),
        "ev_per_bet_mean":   float(t3_ev_per_sim.mean()),
        "ev_ratio":          float(ev_ratio_per_sim.mean()),
        "size_efficiency":   round(T3_KELLY * CONFIRM_MULTIPLIER / T1_KELLY, 4),  # 0.46
        "faded_miss_rate":   float(faded_miss_rate),
        "confirm_win_rate":  float(confirm_win_rate),
    }


def run_analytical_sensitivity(
    test_bets: list[dict[str, Any]],
    drift_std_values: list[float],
    n_sims: int,
    seed: int,
) -> pd.DataFrame:
    """Run run_monte_carlo over the full DRIFT_STD_VALUES grid."""
    rng  = np.random.default_rng(seed)
    rows = [run_monte_carlo(test_bets, dstd, n_sims, rng) for dstd in drift_std_values]
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger = AuditLogger(OUTPUT_DIR / "audit_exp015.jsonl", min_severity="DEBUG")

    if os.environ.get("BOT_C4_ACTIVE"):
        print("FATAL: BOT_C4_ACTIVE set.", file=sys.stderr); sys.exit(1)

    print(f"\n{'='*60}")
    print(f"EXP-015: T3 Analytical Backtest — Momentum Signal Simulation")
    print(f"Session:    {SESSION_ID}")
    print(f"HYP-008:    EV_T3/EV_T1 > {EV_RATIO_GATE} OR confirm win_rate > {WIN_RATE_GATE}")
    print(f"T1 Kelly:   {T1_KELLY}  |  T3 Kelly: {T3_KELLY}  |  CONFIRM×: {CONFIRM_MULTIPLIER}")
    print(f"{'='*60}\n")

    if not FEATURE_CSV.exists():
        print(f"ERROR: {FEATURE_CSV} not found — run EXP-005 first.", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # 1. Load test bets (refit LR on TRAIN, score TEST)
    # ------------------------------------------------------------------
    print("[DATA] Loading and scoring TEST set...")
    test_bets = load_test_bets(FEATURE_CSV, QS_CSV, QS_ID, logger)
    n_bets = len(test_bets)
    n_yes  = sum(1 for b in test_bets if b["direction"] == "YES")
    n_no   = sum(1 for b in test_bets if b["direction"] == "NO")
    actual_win_rate = sum(
        1 for b in test_bets
        if (b["direction"] == "YES" and b["y_target"] == 1) or
           (b["direction"] == "NO"  and b["y_target"] == 0)
    ) / n_bets if n_bets > 0 else 0.0
    print(f"  {n_bets} actionable bets  |  YES: {n_yes}  NO: {n_no}  |  T1 win rate: {actual_win_rate:.1%}")

    # ------------------------------------------------------------------
    # 2. Primary Monte Carlo run at drift_std=0.020
    # ------------------------------------------------------------------
    print(f"\n[MC] Primary run: drift_std=0.020, n_sims={N_SIMULATIONS:,}")
    rng_primary = np.random.default_rng(RANDOM_SEED)
    primary = run_monte_carlo(test_bets, drift_std=0.020, n_sims=N_SIMULATIONS, rng=rng_primary)

    print(f"  CONFIRM: {primary['confirm_rate']:.1%}  FADE: {primary['fade_rate']:.1%}  "
          f"NEUTRAL: {primary['neutral_rate']:.1%}")
    print(f"  EV ratio (T3/T1): {primary['ev_ratio']:.4f}")
    print(f"  CONFIRM win rate: {primary['confirm_win_rate']:.1%}  "
          f"(T1 baseline: {actual_win_rate:.1%})")
    print(f"  Faded miss rate:  {primary['faded_miss_rate']:.1%}")

    # ------------------------------------------------------------------
    # 3. Full sensitivity grid
    # ------------------------------------------------------------------
    print(f"\n[MC] Sensitivity grid over {DRIFT_STD_VALUES}...")
    sensitivity = run_analytical_sensitivity(test_bets, DRIFT_STD_VALUES, N_SIMULATIONS, RANDOM_SEED)

    print(f"\n  {'drift_std':>10}  {'confirm%':>9}  {'fade%':>7}  "
          f"{'ev_ratio':>9}  {'confirm_wr':>11}  {'faded_miss':>11}")
    print("  " + "-" * 65)
    for _, row in sensitivity.iterrows():
        print(f"  {row['drift_std']:.3f}       {row['confirm_rate']:.1%}     "
              f"  {row['fade_rate']:.1%}    {row['ev_ratio']:.4f}    "
              f"   {row['confirm_win_rate']:.1%}        {row['faded_miss_rate']:.1%}")

    # ------------------------------------------------------------------
    # 4. Breakeven confirm_rate
    # ------------------------------------------------------------------
    # Solve: confirm_rate × (T3_K × CONFIRM_MULT / T1_K) + (1 - confirm_rate - fade_rate) × 1.0 = 1.0
    # With fade_rate = confirm_rate (symmetric drift): solve for confirm_rate
    confirm_factor = (T3_KELLY * CONFIRM_MULTIPLIER) / T1_KELLY  # 0.46
    # confirm × 0.46 + (1 - 2×confirm) × 1.0 = 1.0
    # 0.46×c + 1 - 2c = 1.0 → c(0.46 - 2) = 0 → c = 0
    # That's always at 0 for any EV — breakeven is trivially when confirm & fade rates = 0
    # More meaningful: at what confirm_rate (with fade_rate = 0) does EV ratio = 0.90?
    # confirm × 0.46 + (1 - confirm) × 1.0 = 0.90
    # 0.46c + 1 - c = 0.90 → -0.54c = -0.10 → c = 0.1852
    breakeven_confirm_rate = (1.0 - EV_RATIO_GATE) / (1.0 - confirm_factor)

    print(f"\n[BREAKEVEN] Confirm rate needed for EV_ratio ≥ {EV_RATIO_GATE} "
          f"(assuming fade_rate=0): {breakeven_confirm_rate:.1%}")

    # ------------------------------------------------------------------
    # 5. HYP-008 verdict
    # ------------------------------------------------------------------
    primary_ev_ratio   = primary["ev_ratio"]
    primary_confirm_wr = primary["confirm_win_rate"]

    hyp_ev_pass   = primary_ev_ratio > EV_RATIO_GATE
    hyp_wr_pass   = primary_confirm_wr > WIN_RATE_GATE
    hyp_confirmed = hyp_ev_pass or hyp_wr_pass

    if hyp_confirmed:
        hyp_verdict = "CONFIRMED"
        hyp_icon    = "🟢"
    else:
        hyp_verdict = "FALSIFIED"
        hyp_icon    = "🔴"

    print(f"\n{'='*60}")
    print(f"HYP-008 VERDICT: {hyp_icon} {hyp_verdict}")
    print(f"{'='*60}")
    print(f"  EV ratio gate    (> {EV_RATIO_GATE}): {primary_ev_ratio:.4f} → {'PASS' if hyp_ev_pass else 'FAIL'}")
    print(f"  Win rate gate    (> {WIN_RATE_GATE:.0%}): {primary_confirm_wr:.1%} → {'PASS' if hyp_wr_pass else 'FAIL'}")
    if not hyp_confirmed:
        print(f"\n  Implication: T3 CONFIRM filter reduces EV materially.")
        print(f"  T3 most useful as a gate (FADE → block), not a confidence booster.")

    # ------------------------------------------------------------------
    # 6. Save
    # ------------------------------------------------------------------
    out = {
        "exp_id":     EXP_ID,
        "session_id": SESSION_ID,
        "run_at":     _utc_now(),
        "hyp_id":     "HYP-008",
        "hyp_verdict": hyp_verdict,
        "parameters": {
            "t1_kelly":           T1_KELLY,
            "t3_kelly":           T3_KELLY,
            "confirm_multiplier": CONFIRM_MULTIPLIER,
            "fade_multiplier":    FADE_MULTIPLIER,
            "momentum_threshold": MOMENTUM_THRESHOLD,
            "n_simulations":      N_SIMULATIONS,
            "random_seed":        RANDOM_SEED,
            "drift_std_values":   DRIFT_STD_VALUES,
        },
        "test_set": {
            "n_bets":        n_bets,
            "n_yes":         n_yes,
            "n_no":          n_no,
            "t1_win_rate":   round(actual_win_rate, 4),
        },
        "primary_run_drift020": primary,
        "breakeven_confirm_rate": round(breakeven_confirm_rate, 4),
        "sensitivity_grid":       sensitivity.to_dict(orient="records"),
        "gates": {
            "ev_ratio_gate":     EV_RATIO_GATE,
            "win_rate_gate":     WIN_RATE_GATE,
            "ev_ratio_achieved": round(primary_ev_ratio, 4),
            "confirm_wr_achieved": round(primary_confirm_wr, 4),
        },
    }
    out_path = OUTPUT_DIR / "EXP-015_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults saved: {out_path}")


if __name__ == "__main__":
    main()
