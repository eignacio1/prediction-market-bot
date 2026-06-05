"""
PIPE-02: Pre-Game Live Inference Runner
========================================
Pipeline:     PIPE-02 (Live Inference — no orders)
Phase:        Phase 6 (paper trading prep / ENV-02)
Schedule:     Cron: 21:30 UTC daily (~90 min before 7pm ET NBA games)
Environment:  ENV-02 (VPS with datacenter IP — passes Kalshi CloudFront WAF)

Steps:
  1. Load serialized production model (models/prod_model.joblib)
  2. Fetch ALL live KXNBAPTS markets from Kalshi DS-02 (paginated)
  3. For each player with an active quoted market (market-first):
     a. If in EXP-005 cohort: load feature vector, LR p_estimate, Poisson CDF per threshold
     b. If not in cohort: fetch pts_l10_mean from nba_api dynamically, Poisson CDF only
     c. Compute edge = p_threshold - kalshi_mid - half_spread
     d. Recommend YES / NO / PASS
  4. Log all forecasts to C6 audit log
  5. Write edge report to logs/pregame_YYYYMMDD.json
  6. Exit 0 (no markets today is not an error)

Security (NFR-05):
  VENUE_API_KEY loaded from environment only. Never logged.
  Read-only — writes pregame JSON and team_stats_cache; never places orders.

How to run:
  # On VPS (ENV-02):
  source /opt/prediction-market-bot/.env
  PYTHONPATH=/opt/prediction-market-bot/src \\
      /usr/local/bin/python3.11 \\
      /opt/prediction-market-bot/src/prediction_market_bot/run_pregame.py

  # Or via cron (see deploy/cron.conf)
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

_SRC_ROOT = Path(__file__).parent.parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from collections import defaultdict

from prediction_market_bot.c1_signal_ingestion.ingestion import (
    NBAIngestionClient,
    SEASON_TYPE_REGULAR,
)
from prediction_market_bot.c1_signal_ingestion.team_stats_store import TeamStatsStore
from prediction_market_bot.c2_feature_store.qualitative_store import QualitativeSignalStore
from prediction_market_bot.c3_forecasting.game_state_model import opp_adjusted_lambda, parse_ticker_opponent
from prediction_market_bot.c3_forecasting.shadow_forecaster import ShadowForecaster
from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient
from prediction_market_bot.c5_execution.market_mapper import normalize_player_name
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from prediction_market_bot.execution_bands import BAND_REGISTRY

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

COMPONENT   = "PIPE-02"
SESSION_ID  = f"PG-{uuid.uuid4().hex[:8].upper()}"
GAME_DATE     = datetime.now(tz=timezone.utc).strftime("%Y%m%d")
GAME_DATE_ISO = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")

MODEL_PATH   = Path("models/prod_model.joblib")
MODEL_META   = Path("models/prod_model_meta.json")
FEATURE_CSV  = Path("exp_output/EXP-005/EXP-005_feature_matrix.csv")
QS_CSV       = Path("qualitative_data/pam_v4/QS-2026-05-28-002_classifications.csv")
QS_ID        = "QS-2026-05-28-002"
SNAPSHOT_ID  = "SNAP-2026-05-28-002"
LOG_DIR      = Path(os.environ.get("LOG_DIR", "logs"))
OUTPUT_PATH  = LOG_DIR / f"pregame_{GAME_DATE}.json"
TEAM_STATS_CACHE = LOG_DIR / f"team_stats_cache_{GAME_DATE}.json"

EDGE_YES =  0.02
EDGE_NO  = -0.02
FEATURE_WINDOW = 10
DYNAMIC_FETCH_SEASON = "2025-26"  # current NBA season for non-cohort player stat lookup

_NON_FEATURE = {
    "player_id","player_name","team_id","team_abbreviation",
    "game_id","game_date","season","season_type",
    "min","pts","reb","ast","stl","blk","tov","pf",
    "fgm","fga","fg_pct","fg3m","fg3a","fg3_pct","ftm","fta","ft_pct","plus_minus",
    "snapshot_id","ingestion_run_id","ingested_at",
    "temporal_cutoff","feature_run_id","feature_version","train_test_label","y_target",
    "prf_primary","prf_secondary","prf_hybrid_weight",
    "season_type_is_playoffs","days_since_last_game","b2b_flag","load_games_l7d",
    "eri_prev_hot","eri_prev_cold","eri_consec_cold_games",
}


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

def _impute(X: np.ndarray, medians: np.ndarray) -> np.ndarray:
    X = X.copy().astype(float)
    mask = np.isnan(X)
    X[mask] = np.take(medians, np.where(mask)[1])
    return X


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = AuditLogger(LOG_DIR / "audit.jsonl", min_severity="INFO")

    print(f"\n[PIPE-02] Pre-game inference — {GAME_DATE}")
    print(f"Session:  {SESSION_ID}")

    logger.info(COMPONENT, "pregame_run_start",
                payload={"session_id": SESSION_ID, "game_date": GAME_DATE},
                session_id=SESSION_ID, snapshot_id=SNAPSHOT_ID)

    # ------------------------------------------------------------------
    # Band registry startup validation (pre-G6 requirement)
    # Violations are WARNINGS only — SKELETON/BLOCKED are expected states
    # ------------------------------------------------------------------
    band_violations = BAND_REGISTRY.validate()
    if band_violations:
        for v in band_violations:
            print(f"[BAND_REGISTRY] WARNING: {v}")
            logger.warning(COMPONENT, "band_registry_violation",
                           payload={"violation": v}, session_id=SESSION_ID)
    else:
        print("[BAND_REGISTRY] OK — no violations")

    # ------------------------------------------------------------------
    # 1. Load serialized model
    # ------------------------------------------------------------------
    if not MODEL_PATH.exists():
        msg = f"Model not found: {MODEL_PATH}. Run train_and_save_model.py first."
        logger.error(COMPONENT, "model_not_found",
                     payload={"path": str(MODEL_PATH)}, session_id=SESSION_ID)
        print(f"ERROR: {msg}", file=sys.stderr)
        sys.exit(1)

    artifact = joblib.load(MODEL_PATH)
    pipeline       = artifact["pipeline"]
    feature_names  = artifact["feature_names"]
    col_medians    = artifact["col_medians"]
    model_version  = artifact["model_version"]
    print(f"[MODEL] {model_version} | {len(feature_names)} features")

    # T-119: Model version hash guard (ADR-0009)
    # Verify loaded artifact matches prod_model_meta.json to detect silent substitution.
    if MODEL_META.exists():
        _meta = json.loads(MODEL_META.read_text())
        _expected = _meta.get("model_version")
        if _expected and model_version != _expected:
            logger.error(COMPONENT, "model_version_mismatch",
                         payload={"expected": _expected, "actual": model_version},
                         session_id=SESSION_ID)
            print(f"FATAL: model_version_mismatch — expected={_expected} got={model_version}",
                  file=sys.stderr)
            sys.exit(1)
        print(f"[MODEL] version guard OK — {model_version}")

    # Shadow model (ADR-0009) — optional parallel inference, C6-only output
    shadow = ShadowForecaster(logger=logger, snapshot_id=SNAPSHOT_ID)
    if shadow.available:
        print(f"[SHADOW] {shadow.model_version} loaded — shadow inference active")
    else:
        print("[SHADOW] No shadow model found — production only")

    # ------------------------------------------------------------------
    # 2. Load static feature matrix + QS enrichment
    # ------------------------------------------------------------------
    if not FEATURE_CSV.exists():
        logger.error(COMPONENT, "feature_csv_missing",
                     payload={"path": str(FEATURE_CSV)}, session_id=SESSION_ID)
        print(f"ERROR: {FEATURE_CSV} not found.", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(FEATURE_CSV)
    qs = QualitativeSignalStore(logger=logger, snapshot_id=SNAPSHOT_ID)
    if not qs.load_ds01_snapshot(QS_CSV, QS_ID, session_id=SESSION_ID):
        print("ERROR: QS load failed.", file=sys.stderr); sys.exit(1)
    ok, df_q = qs.enrich_features(df, session_id=SESSION_ID)
    if not ok:
        print("ERROR: QS enrichment failed.", file=sys.stderr); sys.exit(1)

    df_q["game_date_dt"] = pd.to_datetime(df_q["game_date"], errors="coerce")
    latest = (df_q.sort_values("game_date_dt")
                  .groupby("player_id").last().reset_index())
    print(f"[DATA] {len(latest)} players | most recent game: {df_q['game_date'].max()}")

    # ------------------------------------------------------------------
    # 3. Fetch live Kalshi markets
    # ------------------------------------------------------------------
    print("[DS-02] Fetching live KXNBAPTS markets...")
    try:
        client = KalshiMarketClient.from_env()
        ok, status = client.check_connectivity()
        if not ok:
            logger.error(COMPONENT, "ds02_connectivity_failed",
                         payload=status, session_id=SESSION_ID)
            print(f"ERROR: DS-02 connectivity failed: {status}", file=sys.stderr)
            sys.exit(1)
        print(f"  Exchange active: {status['exchange_active']}")

        ok2, snapshot = client.fetch_player_points_markets()
        if not ok2 or not snapshot.markets:
            print("  No KXNBAPTS markets available. No games today or pre-market.")
            logger.info(COMPONENT, "no_markets_today",
                        payload={"reason": "no active KXNBAPTS markets"},
                        session_id=SESSION_ID)
            _write_empty_report()
            sys.exit(0)

        live = snapshot.markets
        quoted = [m for m in live if m.has_live_quotes]
        if quoted:
            avg_vig = float(np.mean([m.vig for m in quoted]))
            print(f"  {len(live)} markets | {len(quoted)} quoted | avg vig {avg_vig:.4f}")
        else:
            print(f"  {len(live)} markets fetched — no live quotes yet (pre-market).")

    except EnvironmentError as e:
        print(f"ERROR: {e}", file=sys.stderr); sys.exit(1)

    # ------------------------------------------------------------------
    # 4. Compute edges — market-first (all live players, not just cohort)
    #
    # Cohort players: use EXP-005 feature vector + Poisson CDF (Path B).
    # Non-cohort players: fetch pts_l10_mean from nba_api dynamically,
    #   Poisson CDF only (p_estimate = None in report).
    # ------------------------------------------------------------------
    from prediction_market_bot.c3_forecasting.game_state_model import _poisson_cdf

    forecasts = []

    # Build cohort lookup by normalized name
    cohort_lookup: dict[str, pd.Series] = {}
    for _, row in latest.iterrows():
        norm = normalize_player_name(str(row.get("player_name", "")))
        cohort_lookup[norm] = row

    # Group active quoted markets by Kalshi player name
    markets_by_player: dict[str, list] = defaultdict(list)
    for m in live:
        if m.status == "active" and m.has_live_quotes:
            markets_by_player[m.player_name].append(m)

    print(f"  {len(markets_by_player)} players in live markets | "
          f"{sum(len(v) for v in markets_by_player.values())} market/threshold pairs")

    _ingester = NBAIngestionClient(logger=logger, snapshot_id=SNAPSHOT_ID)
    _pts_cache: dict[str, float] = {}

    # ------------------------------------------------------------------
    # 4a. Build opponent defensive stats store (ADR-0015)
    # Pre-populated cache (GitHub Actions tss_daily_sync, GG-013 fix) takes
    # priority. Falls back to API build if absent; raw λ if both fail.
    # ------------------------------------------------------------------
    team_store: TeamStatsStore | None = None
    _cache_loaded = False
    if TEAM_STATS_CACHE.exists():
        try:
            _cache_data = json.loads(TEAM_STATS_CACHE.read_text())
            if _cache_data:
                team_store = TeamStatsStore.from_cache_dict(_cache_data)
                _tss_ok = len(team_store)
                _cache_loaded = True
                print(f"[TSS] Loaded from pre-populated cache: {_tss_ok} teams (ADR-0015)")
                logger.info(COMPONENT, "team_stats_store_loaded",
                            payload={"teams_loaded": _tss_ok, "source": "pre_populated_cache"},
                            session_id=SESSION_ID, snapshot_id=SNAPSHOT_ID)
        except Exception as _ce:
            logger.warning(COMPONENT, "team_stats_cache_load_failed",
                           payload={"error": str(_ce)}, session_id=SESSION_ID)
    if not _cache_loaded:
        try:
            teams = NBAIngestionClient.get_all_teams()
            store = TeamStatsStore()
            _tss_ok = 0
            for _team in teams:
                _ok, _df = _ingester.fetch_team_game_log(
                    team_id=_team["id"],
                    season=DYNAMIC_FETCH_SEASON,
                    session_id=SESSION_ID,
                )
                if _ok and not _df.empty:
                    store.add_team_log(_team["abbreviation"], _df)
                    _tss_ok += 1
            team_store = store
            print(f"[TSS] Team stats store: {_tss_ok}/{len(teams)} teams loaded (ADR-0015)")
            logger.info(COMPONENT, "team_stats_store_built",
                        payload={"teams_loaded": _tss_ok, "teams_total": len(teams)},
                        session_id=SESSION_ID, snapshot_id=SNAPSHOT_ID)
            # Cache for PIPE-03 (runs ~5 min after PIPE-02)
            try:
                TEAM_STATS_CACHE.write_text(json.dumps(store.to_cache_dict()))
                print(f"[TSS] Cache written: {TEAM_STATS_CACHE}")
            except Exception as _ce:
                logger.warning(COMPONENT, "team_stats_cache_write_failed",
                               payload={"error": str(_ce)}, session_id=SESSION_ID)
        except Exception as _tss_err:
            logger.warning(COMPONENT, "team_stats_store_build_failed",
                           payload={"error": str(_tss_err)}, session_id=SESSION_ID)
            print(f"[TSS] Build failed — using raw λ (fallback): {_tss_err}")

    for kalshi_player_name, player_mkts in markets_by_player.items():
        norm = normalize_player_name(kalshi_player_name)

        row = cohort_lookup.get(norm)
        if row is not None:
            player_id = int(row.get("player_id", 0))
            pts_mean = float(row.get(f"pts_l{FEATURE_WINDOW}_mean", np.nan))
            X = np.array([[row[c] if c in row.index else np.nan for c in feature_names]], dtype=float)
            X = _impute(X, col_medians)
            p_est_lr: float | None = float(pipeline.predict_proba(X)[0, 1])
            p_shadow = shadow.predict_shadow(row, session_id=SESSION_ID) if shadow.available else None
        else:
            if norm in _pts_cache:
                pts_mean = _pts_cache[norm]
            else:
                nba_id = NBAIngestionClient.get_player_id_by_name(kalshi_player_name)
                if nba_id is None:
                    print(f"  [SKIP] {kalshi_player_name} — not in cohort, nba_api lookup failed")
                    continue
                ok_f, gl_df = _ingester.fetch_player_game_log(
                    player_id=nba_id,
                    season=DYNAMIC_FETCH_SEASON,
                    season_type=SEASON_TYPE_REGULAR,
                    session_id=SESSION_ID,
                )
                if not ok_f or gl_df.empty:
                    print(f"  [SKIP] {kalshi_player_name} — dynamic fetch returned no data")
                    continue
                gl_df["_gd"] = pd.to_datetime(gl_df["game_date"], errors="coerce")
                pts_mean = float(gl_df.sort_values("_gd").tail(10)["pts"].mean())
                _pts_cache[norm] = pts_mean
            player_id = 0
            p_est_lr = None
            p_shadow = None

        if np.isnan(pts_mean):
            continue

        # Resolve opponent once per player (same game for all their thresholds)
        _opp_team = parse_ticker_opponent(player_mkts[0].ticker) if player_mkts else None

        for mkt in player_mkts:
            mid  = mkt.mid_price
            half = mkt.half_spread
            thresh_int = int(mkt.threshold)
            adj_lam = opp_adjusted_lambda(pts_mean, mkt.ticker, team_store, GAME_DATE_ISO)
            p_threshold = 1.0 - _poisson_cdf(thresh_int - 1, adj_lam)
            gross_edge = p_threshold - mid - half
            kalshi_fee = round(0.07 * mid * (1.0 - mid), 6)  # ADR-0016 taker fee
            edge = gross_edge - kalshi_fee                     # net-of-fee edge
            direction = ("YES" if edge > EDGE_YES else "NO" if edge < EDGE_NO else "PASS")

            dyn_tag = " [dyn]" if p_est_lr is None else ""
            opp_tag = f" opp={_opp_team} λ={adj_lam:.1f}" if team_store and _opp_team else ""
            print(f"  {kalshi_player_name:<28} thr={mkt.threshold:>3}  "
                  f"p={p_threshold:.3f}  mid={mid:.3f}  edge={edge:+.3f}  → {direction}{dyn_tag}{opp_tag}")

            fc = {
                "player_name": kalshi_player_name, "player_id": player_id,
                "pts_l10_mean": round(pts_mean, 2),
                "opp_team": _opp_team,
                "opp_adj_lambda": round(adj_lam, 3),
                "kalshi_ticker": mkt.ticker,
                "kalshi_threshold": mkt.threshold,
                "mid_price": round(mid, 4), "vig": round(mkt.vig, 4),
                "p_estimate": round(p_threshold, 4),
                "gross_edge": round(gross_edge, 4),
                "kalshi_fee": kalshi_fee,
                "edge": round(edge, 4),
                "p_estimate_lr": round(p_est_lr, 4) if p_est_lr is not None else None,
                "direction": direction,
                "model_version": model_version,
                "shadow_p_estimate": round(p_shadow, 4) if p_shadow is not None else None,
                "shadow_model_version": shadow.model_version if shadow.available else None,
                "forecast_at": _utc_now(),
            }
            forecasts.append(fc)

            logger.info(COMPONENT, "forecast_emitted",
                        payload={k: v for k, v in fc.items() if k != "forecast_at"},
                        session_id=SESSION_ID, snapshot_id=SNAPSHOT_ID)

    # ------------------------------------------------------------------
    # 5. Write report
    # ------------------------------------------------------------------
    players_matched = len({f["player_id"] for f in forecasts})
    actionable = [f for f in forecasts if f["direction"] != "PASS"]
    report = {
        "session_id": SESSION_ID, "game_date": GAME_DATE, "run_at": _utc_now(),
        "model_version": model_version,
        "shadow_model_version": shadow.model_version if shadow.available else None,
        "markets_fetched": len(live),
        "players_matched": players_matched,
        "markets_logged": len(forecasts),
        "actionable": len(actionable),
        "forecasts": forecasts,
    }
    OUTPUT_PATH.write_text(json.dumps(report, indent=2))

    print(f"\n[DONE] {players_matched} players | {len(forecasts)} markets | {len(actionable)} actionable | report: {OUTPUT_PATH}")

    logger.info(COMPONENT, "pregame_run_complete",
                payload={"players_matched": players_matched,
                         "markets_logged": len(forecasts),
                         "actionable": len(actionable),
                         "output_path": str(OUTPUT_PATH)},
                session_id=SESSION_ID, snapshot_id=SNAPSHOT_ID)


def _write_empty_report() -> None:
    report = {
        "session_id": SESSION_ID, "game_date": GAME_DATE, "run_at": _utc_now(),
        "markets_fetched": 0, "players_matched": 0, "actionable": 0, "forecasts": [],
    }
    OUTPUT_PATH.write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
