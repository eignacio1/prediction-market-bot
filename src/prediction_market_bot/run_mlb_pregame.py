"""
PIPE-06pre: MLB Pre-Game Context Generator
===========================================
Pipeline:     PIPE-06pre (read-only — no orders, no capital)
Phase:        Phase 6 (paper trading)
Schedule:     Cron: 16:30 UTC daily (12:30pm ET — before first MLB game at 18:00 UTC)
Environment:  ENV-02 (VPS) or local

Steps:
  1. Load mlb_v1_model.joblib (per-threshold pipelines, feature_names, col_medians)
  2. Load exp_output/MLB/mlb_feature_matrix.csv → latest-row-per-player
  3. Fetch tonight's live starting pitchers via MLB Stats API (SP overlay)
  4. Fetch ALL live KXMLBHIT markets from Kalshi
  5. For each player with active quoted KXMLBHIT markets:
     a. Look up player row in feature CSV (name-normalised)
     b. Build feature vector with live SP override
     c. Run per-threshold pipeline (thresholds 1, 2)
     d. Calibrate probability and compute edge
  6. Write logs/pregame_mlb_YYYYMMDD.json

Output format (mirrors NBA pregame_YYYYMMDD.json — T3 + T4 depend on this):
  {
    "session_id": ..., "game_date": ..., "run_at": ..., "model_version": ...,
    "markets_fetched": N, "players_matched": N, "markets_logged": N, "actionable": N,
    "forecasts": [
      {"player_id": N, "player_name": ..., "kalshi_ticker": ..., "kalshi_threshold": N,
       "p_estimate": 0.NN, "h_l10_mean": N.N, "mid_price": ..., "edge": ..., "direction": ...}
    ]
  }

T3 and T4 read this file to know which players have active markets, what the
model's T1 probability is (p_estimate = p_t1 for T4 Bayesian updates), and which
Kalshi tickers to poll during the game.

Security (NFR-05):
  Read-only — writes pregame JSON only. Never places orders.
  VENUE_API_KEY loaded from environment.

How to run:
  source /opt/prediction-market-bot/.env
  PYTHONPATH=src /opt/prediction-market-bot/venv/bin/python \\
      src/prediction_market_bot/run_mlb_pregame.py
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

_SRC_ROOT = Path(__file__).parent.parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from prediction_market_bot.c1_signal_ingestion.data_contracts import MLB_FEATURE_CSV_CONTRACT
from prediction_market_bot.c1_signal_ingestion.mlb_ingestion import MLBIngestionClient
from prediction_market_bot.c1_signal_ingestion.mlb_pitcher_stats_store import (
    MLBPitcherStatsStore,
)
from prediction_market_bot.c1_signal_ingestion.validators import (
    DataContractViolation,
    assert_contract,
)
from prediction_market_bot.c3_forecasting.calibration import calibrate_probability
from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient, SERIES_MLB_PLAYER_HITS
from prediction_market_bot.c5_execution.market_mapper import normalize_player_name
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

COMPONENT  = "PIPE-06pre"
SESSION_ID = f"PG-MLB-{uuid.uuid4().hex[:8].upper()}"

# Today's games — T3 and T4 need context for live + upcoming games today
GAME_DATE     = datetime.now(tz=timezone.utc).strftime("%Y%m%d")
GAME_DATE_ISO = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")

MODEL_PATH  = Path("models/mlb_v1_model.joblib")
FEATURE_CSV = Path("exp_output/MLB/mlb_feature_matrix.csv")
SNAPSHOT_ID = "SNAP-MLB-PREGAME"
LOG_DIR     = Path(os.environ.get("LOG_DIR", "logs"))
OUTPUT_PATH = LOG_DIR / f"pregame_mlb_{GAME_DATE}.json"

EDGE_YES = 0.02
EDGE_NO  = -0.02

_MODEL_THRESHOLDS: frozenset[int] = frozenset({1, 2})

_NON_FEATURE_MLB: frozenset[str] = frozenset({
    "player_id", "player_name", "team_abbreviation", "game_id", "game_date",
    "season", "season_type", "matchup", "opponent_team_abbr",
    "snapshot_id", "feature_run_id", "feature_version",
    "temporal_cutoff", "train_test_label", "ingestion_run_id", "ingested_at",
    "ab", "h", "doubles", "triples", "hr", "rbi", "bb", "k", "hbp", "sf",
    "y_target", "game_date_dt",
    "threshold",
})

_SP_OVERRIDE_FIELDS = frozenset({
    "opp_sp_era_l5", "opp_sp_k9_l5", "opp_sp_bb9_l5", "opp_sp_is_known"
})


# ---------------------------------------------------------------------------
# Helpers (mirrored from run_mlb_paper_trade.py — shared logic)
# ---------------------------------------------------------------------------


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _impute(X: np.ndarray, medians: np.ndarray) -> np.ndarray:
    X = X.copy().astype(float)
    mask = np.isnan(X)
    X[mask] = np.take(medians, np.where(mask)[1])
    return X


def _safe_int(v: object) -> int | None:
    if v is None:
        return None
    try:
        f = float(v)  # type: ignore[arg-type]
        if np.isnan(f):
            return None
        return int(f)
    except (TypeError, ValueError):
        return None


def _build_mlb_feature_vector(
    row: pd.Series,
    feature_names: list[str],
    col_medians: np.ndarray,
    sp_override: dict | None = None,
) -> np.ndarray:
    vals: list[float] = []
    for col in feature_names:
        if sp_override is not None and col in _SP_OVERRIDE_FIELDS:
            v = sp_override.get(col)
            vals.append(float(v) if v is not None else np.nan)
        elif col in row.index:
            v = row[col]
            vals.append(float(v) if pd.notna(v) else np.nan)
        else:
            vals.append(np.nan)
    return _impute(np.array([vals], dtype=float), col_medians)


def _build_live_sp_override(
    today_iso: str,
    latest_df: pd.DataFrame,
    client: MLBIngestionClient,
    logger: AuditLogger,
    session_id: str,
) -> dict[int, dict]:
    ok, starters = client.fetch_game_starters(today_iso, session_id)
    if not ok or not starters:
        return {}

    team_to_game: dict[int, tuple[int, bool]] = {}
    for game_pk, info in starters.items():
        htid = _safe_int(info.get("home_team_id"))
        atid = _safe_int(info.get("away_team_id"))
        if htid is not None:
            team_to_game[htid] = (game_pk, True)
        if atid is not None:
            team_to_game[atid] = (game_pk, False)

    sp_ids_needed: set[int] = set()
    player_sp_map: dict[int, int | None] = {}
    player_sp_known: dict[int, bool] = {}

    for _, row in latest_df.iterrows():
        pid = _safe_int(row.get("player_id"))
        tid = _safe_int(row.get("team_id"))
        if pid is None or tid is None or tid not in team_to_game:
            continue
        game_pk, is_home = team_to_game[tid]
        sp_key = "away_sp_id" if is_home else "home_sp_id"
        sp_id = _safe_int(starters[game_pk].get(sp_key))
        known = sp_id is not None
        player_sp_map[pid] = sp_id
        player_sp_known[pid] = known
        if known:
            sp_ids_needed.add(sp_id)  # type: ignore[arg-type]

    if not player_sp_map:
        return {}

    pitcher_store = MLBPitcherStatsStore()
    current_season = str(date.today().year)
    for sp_id in sp_ids_needed:
        ok_p, df_p = client.fetch_pitcher_game_log(sp_id, current_season, session_id=session_id)
        if ok_p and df_p is not None and not df_p.empty:
            pitcher_store.add_pitcher_log(sp_id, df_p)

    logger.info(
        COMPONENT, "live_sp_overlay_fetched",
        payload={"n_games": len(starters), "n_players_mapped": len(player_sp_map),
                 "n_sp_fetched": len(sp_ids_needed)},
        session_id=session_id,
    )

    result: dict[int, dict] = {}
    for pid, sp_id in player_sp_map.items():
        is_known = player_sp_known.get(pid, False)
        era = pitcher_store.get_era_l5(sp_id, today_iso) if sp_id is not None else None
        k9  = pitcher_store.get_k_per_9_l5(sp_id, today_iso) if sp_id is not None else None
        bb9 = pitcher_store.get_bb_per_9_l5(sp_id, today_iso) if sp_id is not None else None
        result[pid] = {
            "opp_sp_era_l5":  era,
            "opp_sp_k9_l5":   k9,
            "opp_sp_bb9_l5":  bb9,
            "opp_sp_is_known": 1.0 if is_known else 0.0,
        }
    return result


def _write_empty_report() -> None:
    report = {
        "session_id": SESSION_ID, "game_date": GAME_DATE, "run_at": _utc_now(),
        "sport": "mlb", "markets_fetched": 0, "players_matched": 0,
        "markets_logged": 0, "actionable": 0, "forecasts": [],
    }
    OUTPUT_PATH.write_text(json.dumps(report, indent=2))
    print(f"[DONE] Empty report written: {OUTPUT_PATH}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = AuditLogger(LOG_DIR / "audit_mlb.jsonl", min_severity="INFO")

    print(f"\n[PIPE-06pre] MLB Pregame context — {GAME_DATE}")
    print(f"Session:  {SESSION_ID}")
    print(f"Output:   {OUTPUT_PATH}")

    logger.info(COMPONENT, "pregame_mlb_run_start",
                payload={"session_id": SESSION_ID, "game_date": GAME_DATE, "sport": "mlb"},
                session_id=SESSION_ID, snapshot_id=SNAPSHOT_ID)

    # ------------------------------------------------------------------
    # 1. Load model
    # ------------------------------------------------------------------
    if not MODEL_PATH.exists():
        print(f"ERROR: {MODEL_PATH} not found — run scripts/train_mlb_model.py first.",
              file=sys.stderr)
        sys.exit(1)

    artifact       = joblib.load(MODEL_PATH)
    pipelines      = artifact["pipelines"]
    feature_names: list[str]  = artifact["feature_names"]
    col_medians: np.ndarray   = artifact["col_medians"]
    model_version: str        = artifact["model_version"]
    sport_label: str          = artifact.get("sport", "mlb")

    if sport_label.lower() != "mlb":
        print(f"ERROR: Model artifact sport='{sport_label}' — expected 'mlb'.", file=sys.stderr)
        sys.exit(1)

    print(f"[MODEL] {model_version} | sport={sport_label} | {len(feature_names)} features")

    # ------------------------------------------------------------------
    # 2. Load feature CSV → latest-row-per-player lookup
    # ------------------------------------------------------------------
    if not FEATURE_CSV.exists():
        print(f"ERROR: {FEATURE_CSV} not found — run scripts/generate_mlb_features.py first.",
              file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(FEATURE_CSV, low_memory=False)

    # ------------------------------------------------------------------
    # T-212 — Data contract validation (structural: schema, cardinality,
    # freshness). Supersedes the ad hoc freshness-only guard that mirrored
    # T-193 in PIPE-05 — this also catches column drift and row-count
    # collapse/explosion, not just staleness. GG-059.
    # ------------------------------------------------------------------
    try:
        contract_result = assert_contract(
            df,
            MLB_FEATURE_CSV_CONTRACT,
            audit=logger,
            pipeline_id=COMPONENT,
            session_id=SESSION_ID,
            snapshot_id=SNAPSHOT_ID,
        )
    except DataContractViolation as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    for _w in contract_result.warnings():
        print(f"  [WARN] {_w.check_type}: {_w.reason}", file=sys.stderr)

    df["game_date_dt"] = pd.to_datetime(df["game_date"], errors="coerce")
    latest = df.sort_values("game_date_dt").groupby("player_id").last().reset_index()

    _max_game_date = df["game_date_dt"].max()
    _csv_age_days = (datetime.now(tz=timezone.utc).date() - _max_game_date.date()).days
    print(f"[FEATURE CSV] {len(df)} rows | {len(latest)} players | "
          f"latest game_date: {_max_game_date.date()} ({_csv_age_days} days ago)")

    cohort_lookup: dict[str, pd.Series] = {}
    for _, row in latest.iterrows():
        norm = normalize_player_name(str(row.get("player_name", "")))
        cohort_lookup[norm] = row

    print(f"[DATA] {len(latest)} players | most recent game: {df['game_date'].max()}")

    # ------------------------------------------------------------------
    # 3. Build live SP overlay (T-187G pattern)
    # ------------------------------------------------------------------
    mlb_client = MLBIngestionClient(logger, SNAPSHOT_ID)
    sp_override_by_player: dict[int, dict] = {}
    try:
        sp_override_by_player = _build_live_sp_override(
            today_iso=GAME_DATE_ISO,
            latest_df=latest,
            client=mlb_client,
            logger=logger,
            session_id=SESSION_ID,
        )
        print(f"[SP OVERLAY] Live SP stats fetched for {len(sp_override_by_player)} players")
    except Exception as e:
        logger.warning(COMPONENT, "live_sp_overlay_failed",
                       payload={"error": str(e)}, session_id=SESSION_ID)
        print(f"[SP OVERLAY] Failed — falling back to historical SP stats: {e}")

    # ------------------------------------------------------------------
    # 4. Fetch live KXMLBHIT markets
    # ------------------------------------------------------------------
    print("[DS-02] Fetching live KXMLBHIT markets...")
    try:
        client = KalshiMarketClient.from_env()
        ok, status = client.check_connectivity()
        if not ok:
            logger.error(COMPONENT, "ds02_connectivity_failed",
                         payload=status, session_id=SESSION_ID)
            print(f"ERROR: DS-02 connectivity failed: {status}", file=sys.stderr)
            sys.exit(1)
        print(f"  Exchange active: {status['exchange_active']}")

        ok2, snapshot = client.fetch_player_points_markets(series_ticker=SERIES_MLB_PLAYER_HITS)
        if not ok2 or not snapshot.markets:
            print("  No KXMLBHIT markets available. No games today or pre-market.")
            logger.info(COMPONENT, "no_mlb_markets_today",
                        payload={"reason": "no active KXMLBHIT markets"},
                        session_id=SESSION_ID)
            _write_empty_report()
            sys.exit(0)

        live = snapshot.markets
        quoted = [m for m in live if m.has_live_quotes]
        if quoted:
            avg_vig = float(np.mean([m.vig for m in quoted]))
            print(f"  {len(live)} markets | {len(quoted)} quoted | avg vig {avg_vig:.4f}")
        else:
            print(f"  {len(live)} markets — no live quotes yet (pre-market).")

    except EnvironmentError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # 5. Compute forecasts — market-first
    # ------------------------------------------------------------------
    forecasts: list[dict] = []

    markets_by_player: dict[str, list] = defaultdict(list)
    for m in live:
        if m.status == "active" and m.has_live_quotes:
            markets_by_player[m.player_name].append(m)

    print(f"  {len(markets_by_player)} players in live markets | "
          f"{sum(len(v) for v in markets_by_player.values())} market/threshold pairs")

    for kalshi_player_name, player_mkts in markets_by_player.items():
        norm = normalize_player_name(kalshi_player_name)
        row = cohort_lookup.get(norm)

        if row is None:
            logger.info(COMPONENT, "player_not_in_feature_csv",
                        payload={"player": kalshi_player_name, "norm": norm},
                        session_id=SESSION_ID)
            print(f"  [SKIP] {kalshi_player_name} — not in feature CSV (no MLB fallback lookup)")
            continue

        player_id = int(row.get("player_id", 0))
        h_l10_mean = float(row.get("h_l10_mean", np.nan)) if "h_l10_mean" in row.index else float("nan")
        ba_l10 = float(row.get("ba_l10", np.nan)) if "ba_l10" in row.index else float("nan")

        sp_override = sp_override_by_player.get(player_id)
        X = _build_mlb_feature_vector(
            row=row,
            feature_names=feature_names,
            col_medians=col_medians,
            sp_override=sp_override,
        )

        for mkt in player_mkts:
            thr = int(mkt.threshold)
            if thr not in _MODEL_THRESHOLDS:
                continue

            p_raw = float(pipelines[thr].predict_proba(X)[0, 1])
            p_calibrated = calibrate_probability(p_raw, sport="mlb")

            mid   = mkt.mid_price
            half  = mkt.half_spread
            gross_edge = p_calibrated - mid - half
            kalshi_fee = 0.07 * mid * (1.0 - mid)
            edge       = gross_edge - kalshi_fee

            direction = ("YES" if edge > EDGE_YES else "NO" if edge < EDGE_NO else "PASS")

            print(f"  {kalshi_player_name:<28} H≥{thr}  "
                  f"p={p_calibrated:.3f}  mid={mid:.3f}  edge={edge:+.3f}  → {direction}")

            fc = {
                "player_name": kalshi_player_name,
                "player_id": player_id,
                "h_l10_mean": round(h_l10_mean, 3) if not np.isnan(h_l10_mean) else None,
                "ba_l10": round(ba_l10, 4) if not np.isnan(ba_l10) else None,
                "kalshi_ticker": mkt.ticker,
                "kalshi_threshold": thr,
                "mid_price": round(mid, 4),
                "vig": round(mkt.vig, 4),
                "p_estimate": round(p_calibrated, 4),
                "p_estimate_raw": round(p_raw, 4),
                "gross_edge": round(gross_edge, 4),
                "kalshi_fee": round(kalshi_fee, 6),
                "edge": round(edge, 4),
                "direction": direction,
                "model_version": model_version,
                "forecast_at": _utc_now(),
            }
            forecasts.append(fc)

            logger.info(COMPONENT, "forecast_emitted",
                        payload={k: v for k, v in fc.items() if k != "forecast_at"},
                        session_id=SESSION_ID, snapshot_id=SNAPSHOT_ID)

    # ------------------------------------------------------------------
    # 6. Write report
    # ------------------------------------------------------------------
    players_matched = len({f["player_id"] for f in forecasts})
    actionable = [f for f in forecasts if f["direction"] != "PASS"]
    report = {
        "session_id": SESSION_ID,
        "game_date": GAME_DATE,
        "game_date_iso": GAME_DATE_ISO,
        "run_at": _utc_now(),
        "sport": "mlb",
        "model_version": model_version,
        "markets_fetched": len(live),
        "players_matched": players_matched,
        "markets_logged": len(forecasts),
        "actionable": len(actionable),
        "forecasts": forecasts,
    }
    OUTPUT_PATH.write_text(json.dumps(report, indent=2))

    print(f"\n[DONE] {players_matched} players | {len(forecasts)} markets | "
          f"{len(actionable)} actionable | {OUTPUT_PATH}")

    logger.info(COMPONENT, "pregame_mlb_run_complete",
                payload={"players_matched": players_matched,
                         "markets_logged": len(forecasts),
                         "actionable": len(actionable),
                         "output_path": str(OUTPUT_PATH)},
                session_id=SESSION_ID, snapshot_id=SNAPSHOT_ID)


if __name__ == "__main__":
    main()
