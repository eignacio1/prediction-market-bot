"""
PIPE-03: Paper Trading Pipeline
=================================
Pipeline:     PIPE-03 (Full simulated decision cycle)
Phase:        Phase 6 (ENV-02 — paper trading)
Schedule:     Cron: 21:30 UTC daily (replaces PIPE-02 once activated)
Environment:  ENV-02 — BOT_ENV=paper required; no real capital

Steps:
  1. Verify ENV-02 (BOT_ENV=paper); activate C4 in-process
  2. Resolve any open positions from previous game days (nba_api)
  3. Load serialized model + qualitative enrichment
  4. Fetch ALL live Kalshi KXNBAPTS markets (DS-02, paginated)
  5. For each player with active market (market-first, not cohort-first):
     a. Cohort players: EXP-005 feature vector + Poisson CDF (Path B)
     b. Non-cohort players: dynamic nba_api pts_l10_mean + Poisson CDF only
     c. Route through C4 RiskEngine (Kelly sizing, hard limits, reserve gate)
     d. If APPROVED and reserve mandate satisfied: record paper order
  6. Log everything to C6; write paper_YYYYMMDD.json report
  7. Print portfolio summary

Security:
  BOT_C4_ACTIVE is set in-process only after BOT_ENV=paper is verified.
  If VENUE_PRIVATE_KEY_PATH is set, orders fire to Kalshi demo (ADR-0008).
  If VENUE_PRIVATE_KEY_PATH is unset, PaperTrader runs local-only (degraded mode).
  BOT_C4_ACTIVE must NOT be set externally in ENV-02's .env.

How to run:
  source /opt/prediction-market-bot/.env
  BOT_ENV=paper PYTHONPATH=src /opt/prediction-market-bot/venv/bin/python \\
      src/prediction_market_bot/run_paper_trade.py
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

import requests

import joblib
import numpy as np
import pandas as pd

_SRC_ROOT = Path(__file__).parent.parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

# Verify ENV-02 before importing anything else
if os.environ.get("BOT_ENV", "").lower() != "paper":
    print("FATAL: PIPE-03 requires BOT_ENV=paper. Set BOT_ENV=paper in your .env.", file=sys.stderr)
    sys.exit(1)

# Activate C4 in-process (paper trading; verified ENV-02 above)
os.environ["BOT_C4_ACTIVE"] = "true"

from collections import defaultdict

from prediction_market_bot.c1_signal_ingestion.ingestion import (
    NBAIngestionClient,
    SEASON_TYPE_REGULAR,
)
from prediction_market_bot.c1_signal_ingestion.team_stats_store import TeamStatsStore
from prediction_market_bot.c2_feature_store.qualitative_store import QualitativeSignalStore
from prediction_market_bot.c3_forecasting.game_state_model import (
    _poisson_cdf,
    opp_adjusted_lambda,
    parse_ticker_opponent,
)
from prediction_market_bot.c4_risk_engine.risk import RiskEngine
from prediction_market_bot.c5_execution.complement_lock_scanner import ComplementLockScanner
from prediction_market_bot.c5_execution.market_mapper import normalize_player_name
from prediction_market_bot.c7_monitoring.monitor import SystemMonitor
from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient
from prediction_market_bot.c5_execution.paper_trader import PaperTrader
from prediction_market_bot.execution_bands import BAND_REGISTRY, get_band_config, ExecutionBand
from prediction_market_bot.c5_execution.venue_router import VenueRouter
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from prediction_market_bot.t3_signal_loader import load_t3_signals, T3_MAX_STALENESS_S

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SESSION_ID    = f"PT-{uuid.uuid4().hex[:8].upper()}"
GAME_DATE     = datetime.now(tz=timezone.utc).strftime("%Y%m%d")
GAME_DATE_ISO = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")

MODEL_PATH    = Path("models/prod_model.joblib")
FEATURE_CSV   = Path("exp_output/EXP-005/EXP-005_feature_matrix.csv")
QS_CSV        = Path("qualitative_data/pam_v4/QS-2026-05-28-002_classifications.csv")
QS_ID         = "QS-2026-05-28-002"
SNAPSHOT_ID   = "SNAP-2026-05-28-002"
LOG_DIR       = Path(os.environ.get("LOG_DIR", str(_SRC_ROOT / "logs")))
PORTFOLIO_PATH = LOG_DIR / "paper_portfolio.json"
REPORT_PATH   = LOG_DIR / f"paper_{GAME_DATE}.json"
TEAM_STATS_CACHE = LOG_DIR / f"team_stats_cache_{GAME_DATE}.json"

EDGE_YES = 0.02
EDGE_NO  = -0.02
FEATURE_WINDOW = 10
RESERVE_MANDATE_PCT = float(os.environ.get("RESERVE_MANDATE_PCT", "0.40"))  # batch reserve gate; override in .env for paper testing (e.g. 0.20 with T4 VIRTUAL)
MIN_BET_T1_PAPER = float(os.environ.get("MIN_BET_T1_PAPER", "1.0"))  # paper-mode min bet floor; mirrors MIN_BET_T4_PAPER=1.0; live uses risk.py MIN_BET_USD=10.0
DYNAMIC_FETCH_SEASON = "2025-26"  # current NBA season for non-cohort player stat lookup

# ADR-0010: T1 band Kelly fraction (0.10). Read from execution_bands so that any
# future ADR updating the band config automatically propagates here.
T1_KELLY = get_band_config(ExecutionBand.T1_MULTI_DAY).kelly_fraction

# T3 momentum overlay multipliers — must stay in sync with run_t3_pretip.py
T3_CONFIRM_MULTIPLIER: float = 1.15
T3_FADE_MULTIPLIER:    float = 0.75

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


def _ticker_to_game_date(ticker: str) -> str:
    """Parse game date from Kalshi ticker. KXNBAPTS-26MAY30SASOKC-... -> 2026-05-30."""
    import re
    m = re.search(r"-([0-9]{2})([A-Z]{3})([0-9]{2})", ticker)
    if m:
        try:
            from datetime import datetime as _dt
            return _dt.strptime(f"20{m.group(1)}{m.group(2)}{m.group(3)}", "%Y%b%d").strftime("%Y-%m-%d")
        except ValueError:
            pass
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")


def _build_target(df: pd.DataFrame) -> pd.Series:
    col = f"pts_l{FEATURE_WINDOW}_mean"
    if col not in df.columns or "pts" not in df.columns:
        return pd.Series([np.nan]*len(df), index=df.index)
    pts = pd.to_numeric(df["pts"], errors="coerce")
    pm  = pd.to_numeric(df[col], errors="coerce")
    t   = (pts >= pm).astype("Int8")
    t[pts.isna() | pm.isna()] = pd.NA
    return t

def _impute(X: np.ndarray, medians: np.ndarray) -> np.ndarray:
    X = X.copy().astype(float)
    mask = np.isnan(X)
    X[mask] = np.take(medians, np.where(mask)[1])
    return X


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = AuditLogger(LOG_DIR / "audit.jsonl", min_severity="INFO")

    # Kalshi client — loads RSA key if VENUE_PRIVATE_KEY_PATH is set (ADR-0008)
    try:
        kalshi_client = KalshiMarketClient.from_env()
        signing_ready = kalshi_client.has_signing_key()
    except Exception as e:
        kalshi_client = None
        signing_ready = False
        logger.warning("PIPE-03", "kalshi_client_init_failed",
                       payload={"error": str(e)}, session_id=SESSION_ID)

    trader = PaperTrader(PORTFOLIO_PATH, logger, kalshi_client=kalshi_client)

    print(f"\n[PIPE-03] Paper trading — {GAME_DATE}")
    print(f"Session:  {SESSION_ID}")
    print(f"BOT_ENV:  {os.environ.get('BOT_ENV')}  |  C4: ACTIVE")
    print(f"Kalshi:   {'LIVE ORDERS (demo)' if signing_ready else 'local-only (no RSA key)'}")

    logger.info("PIPE-03", "paper_run_start",
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
            logger.warning("PIPE-03", "band_registry_violation",
                           payload={"violation": v}, session_id=SESSION_ID)
    else:
        print("[BAND_REGISTRY] OK — no violations")

    # ------------------------------------------------------------------
    # 1. Resolve yesterday's open positions
    # ------------------------------------------------------------------
    portfolio = trader.get_state()
    n_open = len(portfolio.get("open_positions", []))
    if n_open > 0:
        print(f"\n[RESOLVE] {n_open} open position(s) from previous games...")
        ok, resolved = trader.resolve_pending(session_id=SESSION_ID)
        if resolved:
            for r in resolved:
                sign = "+" if r["pnl"] >= 0 else ""
                print(f"  {r['player_name']:<22} {r['outcome']:<5}  pts={r['actual_pts']:.0f} vs {r['kalshi_threshold']}+  P&L={sign}{r['pnl']:.2f}")
        else:
            print("  No positions resolved yet (game results not available or no past games).")
    else:
        print("\n[RESOLVE] No open positions to resolve.")

    # ------------------------------------------------------------------
    # 2. Load model
    # ------------------------------------------------------------------
    if not MODEL_PATH.exists():
        print(f"ERROR: {MODEL_PATH} not found — run train_and_save_model.py first.", file=sys.stderr)
        sys.exit(1)

    artifact     = joblib.load(MODEL_PATH)
    pipeline     = artifact["pipeline"]
    feature_names = artifact["feature_names"]
    col_medians  = artifact["col_medians"]
    model_version = artifact["model_version"]
    print(f"\n[MODEL] {model_version} | {len(feature_names)} features")

    # ------------------------------------------------------------------
    # 3. Load + enrich features
    # ------------------------------------------------------------------
    if not FEATURE_CSV.exists():
        print(f"ERROR: {FEATURE_CSV} not found.", file=sys.stderr); sys.exit(1)

    df = pd.read_csv(FEATURE_CSV)
    qs = QualitativeSignalStore(logger=logger, snapshot_id=SNAPSHOT_ID)
    if not qs.load_ds01_snapshot(QS_CSV, QS_ID, session_id=SESSION_ID):
        print("ERROR: QS load failed.", file=sys.stderr); sys.exit(1)
    ok, df_q = qs.enrich_features(df, session_id=SESSION_ID)
    if not ok:
        print("ERROR: QS enrich failed.", file=sys.stderr); sys.exit(1)

    df_q["game_date_dt"] = pd.to_datetime(df_q["game_date"], errors="coerce")
    latest = df_q.sort_values("game_date_dt").groupby("player_id").last().reset_index()

    # ------------------------------------------------------------------
    # 4. Initialize C4 Risk Engine
    # ------------------------------------------------------------------
    _state   = trader.get_state()
    bankroll = _state["bankroll_usd"]
    _initial_bankroll = _state.get("initial_bankroll_usd", 1000.0)
    engine   = RiskEngine(logger=logger, snapshot_id=SNAPSHOT_ID, bankroll=bankroll,
                          kelly_fraction=T1_KELLY, initial_bankroll=_initial_bankroll,
                          min_bet_usd=MIN_BET_T1_PAPER)
    daily_loss = _state.get("current_daily_loss", 0.0)
    # Stale-date guard (mirrors run_t4_live.py a300a51): current_daily_loss is stamped
    # by close_position at resolution time; a prior game night's value must not gate today.
    if _state.get("daily_loss_date", "") != date.today().isoformat():
        daily_loss = 0.0
    # Bug H fix: drawdown is realized losses only — open stakes are not losses
    _realized_loss = max(0.0, -_state.get("total_realized_pnl", 0.0))
    current_drawdown_pct = _realized_loss / _initial_bankroll if _initial_bankroll > 0 else 0.0

    print(f"[C4] Bankroll ${bankroll:.2f} | Daily loss ${daily_loss:.2f} | Drawdown {current_drawdown_pct:.1%}")

    # ------------------------------------------------------------------
    # 5. Fetch live markets via VenueRouter (kalshi_only default until T-077)
    # ------------------------------------------------------------------
    print("[DS-02] Fetching live KXNBAPTS markets via VenueRouter...")
    try:
        router       = VenueRouter.from_env()
        connectivity = router.check_all_connectivity()
        kalshi_ok, kalshi_stat = connectivity.get("kalshi", (False, {}))
        if not kalshi_ok:
            logger.error("PIPE-03", "ds02_failed", payload=kalshi_stat, session_id=SESSION_ID)
            print(f"ERROR: DS-02 (Kalshi) unavailable: {kalshi_stat}", file=sys.stderr)
            sys.exit(1)

        ok2, snap = router.fetch_all_markets()
        if not ok2 or not snap.markets:
            print("  No KXNBAPTS markets available. No games today or pre-market.")
            _write_report([], bankroll, trader)
            sys.exit(0)

        quoted = [m for m in snap.markets if m.has_live_quotes]
        if quoted:
            avg_vig = np.mean([m.vig for m in quoted])
            print(f"  {len(snap.markets)} markets | {len(quoted)} quoted | "
                  f"avg vig {avg_vig:.4f} | venues: {router.active_venues}")
        else:
            print(f"  {len(snap.markets)} markets — no live quotes yet. | venues: {router.active_venues}")

        _scan_and_log_locks(snap.markets, router.active_venues, logger, SESSION_ID)
    except EnvironmentError as e:
        print(f"ERROR: {e}", file=sys.stderr); sys.exit(1)

    # ------------------------------------------------------------------
    # T-162/GG-024: Abort bet placement if any NBA game for GAME_DATE is
    # already in progress. Late crons firing mid-game produce anti-informed
    # bets against a market that has already repriced to live state.
    # ------------------------------------------------------------------
    _ESPN_SB = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
    try:
        _sb_r = requests.get(
            _ESPN_SB,
            params={"dates": GAME_DATE},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        _sb_events = _sb_r.json().get("events", [])
        _in_progress = [
            e["id"] for e in _sb_events
            if e.get("status", {}).get("type", {}).get("name") == "STATUS_IN_PROGRESS"
        ]
        if _in_progress:
            print(f"[PIPE-03] Game(s) in progress {_in_progress} — aborting bet placement (T-162/GG-024)")
            logger.info(
                "PIPE-03", "paper_run_skipped_game_in_progress",
                payload={"game_ids": _in_progress, "session_id": SESSION_ID},
                session_id=SESSION_ID,
            )
            _write_report([], bankroll, trader)
            sys.exit(0)
    except Exception as _exc:
        print(f"[PIPE-03] ESPN game-state check failed ({_exc}) — proceeding")

    # ------------------------------------------------------------------
    # 6. Generate forecasts + C4 evaluation + paper orders (market-first)
    #
    # Iterates over ALL live Kalshi markets (not just the EXP-005 cohort).
    # For cohort players: uses EXP-005 feature vector + Poisson CDF (Path B).
    # For non-cohort players: fetches pts_l10_mean from nba_api dynamically,
    #   then Poisson CDF only (p_estimate_lr = None in C6 log).
    # ------------------------------------------------------------------
    orders, passes = [], []

    # Build O(1) cohort lookup by normalized player name
    cohort_lookup: dict[str, pd.Series] = {}
    for _, row in latest.iterrows():
        norm = normalize_player_name(str(row.get("player_name", "")))
        cohort_lookup[norm] = row

    # Group active quoted markets by Kalshi player name
    markets_by_player: dict[str, list] = defaultdict(list)
    for m in snap.markets:
        if m.status == "active" and m.has_live_quotes:
            markets_by_player[m.player_name].append(m)

    print(f"  {len(markets_by_player)} players in live markets | "
          f"{sum(len(v) for v in markets_by_player.values())} market/threshold pairs")

    # Ingester + cache for non-cohort dynamic stat fetch (rate-limited by C1 throttle)
    _ingester = NBAIngestionClient(logger=logger, snapshot_id=SNAPSHOT_ID)
    _pts_cache: dict[str, float] = {}

    # ------------------------------------------------------------------
    # 5a. Load opponent defensive stats store (ADR-0015)
    # PIPE-02 writes the cache ~5 min earlier; load from it if present.
    # Falls back to fresh build; falls back to raw λ if both fail.
    # ------------------------------------------------------------------
    team_store: TeamStatsStore | None = None
    if TEAM_STATS_CACHE.exists():
        try:
            _cache_data = json.loads(TEAM_STATS_CACHE.read_text())
            team_store = TeamStatsStore.from_cache_dict(_cache_data)
            print(f"[TSS] Loaded {len(team_store)} teams from cache (ADR-0015)")
            logger.info("PIPE-03", "team_stats_store_cache_hit",
                        payload={"teams": len(team_store), "cache": str(TEAM_STATS_CACHE)},
                        session_id=SESSION_ID)
        except Exception as _ce:
            logger.warning("PIPE-03", "team_stats_cache_load_failed",
                           payload={"error": str(_ce)}, session_id=SESSION_ID)
    if team_store is None or len(team_store) == 0:
        print("[TSS] Cache miss — building fresh team stats store...")
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
            print(f"[TSS] Built fresh: {_tss_ok}/{len(teams)} teams loaded (ADR-0015)")
            logger.info("PIPE-03", "team_stats_store_built",
                        payload={"teams_loaded": _tss_ok, "teams_total": len(teams)},
                        session_id=SESSION_ID)
        except Exception as _tss_err:
            logger.warning("PIPE-03", "team_stats_store_build_failed",
                           payload={"error": str(_tss_err)}, session_id=SESSION_ID)
            print(f"[TSS] Build failed — using raw λ (fallback): {_tss_err}")

    # T-134/GG-012/GG-013: emit ERROR when TSS resolves to 0 teams — suppresses silent adj_λ failures
    if team_store is None or len(team_store) == 0:
        logger.error("PIPE-03", "team_stats_store_empty",
                     payload={"note": "adj_λ inactive — all bets use raw pts_l10_mean; check API access or GHA cache"},
                     session_id=SESSION_ID)
        print("[TSS] WARNING: 0 teams loaded — adj_λ (ADR-0015) inactive this run")

    # T3 momentum overlay: load PIPE-06 signals once, before the player loop.
    # Absent or stale report → empty dict → every ticker lookup returns "NEUTRAL"
    # → edge unchanged → pure T1 path. Non-contamination guarantee.
    t3_signals = load_t3_signals(LOG_DIR, GAME_DATE)
    if t3_signals:
        _t3_confirm = sum(1 for s in t3_signals.values() if s == "CONFIRM")
        _t3_fade    = sum(1 for s in t3_signals.values() if s == "FADE")
        print(f"[T3] {len(t3_signals)} momentum signals — "
              f"{_t3_confirm} CONFIRM / {_t3_fade} FADE")
        logger.info("PIPE-03", "t3_signals_loaded",
                    payload={"count": len(t3_signals),
                             "confirm": _t3_confirm, "fade": _t3_fade},
                    session_id=SESSION_ID)
    else:
        print("[T3] No T3 signals (PIPE-06 not run or stale) — pure T1 path")

    _reserve_halted = False

    for kalshi_player_name, player_mkts in markets_by_player.items():
        if _reserve_halted:
            break

        norm = normalize_player_name(kalshi_player_name)

        # --- Resolve player stats ---
        row = cohort_lookup.get(norm)
        if row is not None:
            player_id = int(row.get("player_id", 0))
            pts_mean = float(row.get(f"pts_l{FEATURE_WINDOW}_mean", np.nan))
            X = _impute(
                np.array([[row[c] if c in row.index else np.nan for c in feature_names]], dtype=float),
                col_medians,
            )
            p_est_lr: float | None = float(pipeline.predict_proba(X)[0, 1])
        else:
            # Non-cohort: dynamic nba_api fetch (Poisson path only — no LR model)
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

        if np.isnan(pts_mean):
            continue

        # Resolve opponent once per player (same game for all their thresholds)
        _opp_team = parse_ticker_opponent(player_mkts[0].ticker) if player_mkts else None

        for mkt in player_mkts:
            if _reserve_halted:
                break

            # Idempotency: skip if already holding a successfully placed open position on this
            # ticker. Positions with kalshi_order_status starting "failed:" are transient
            # placement failures (503/429) — they don't block a retry on the next cron run.
            _open_tickers = {
                p["kalshi_ticker"]
                for p in trader.get_state().get("open_positions", [])
                if not str(p.get("kalshi_order_status", "")).startswith("failed:")
            }
            if mkt.ticker in _open_tickers:
                print(f"  [IDEMPOTENCY] SKIP {kalshi_player_name} — {mkt.ticker} already open")
                continue

            # T-129 Path B: Poisson CDF with opponent-adjusted λ (ADR-0015)
            thresh_int = int(mkt.threshold)
            adj_lam = opp_adjusted_lambda(pts_mean, mkt.ticker, team_store, GAME_DATE_ISO)
            p_threshold = 1.0 - _poisson_cdf(thresh_int - 1, adj_lam)

            mid  = mkt.mid_price
            half = mkt.half_spread
            gross_edge = p_threshold - mid - half
            kalshi_fee = 0.07 * mid * (1.0 - mid)  # ADR-0016 taker fee
            edge = gross_edge - kalshi_fee           # net-of-fee edge (T1 base)
            t1_edge   = edge
            t3_signal = t3_signals.get(mkt.ticker, "NEUTRAL")
            if t3_signal == "CONFIRM":
                edge = t1_edge * T3_CONFIRM_MULTIPLIER
            elif t3_signal == "FADE":
                edge = t1_edge * T3_FADE_MULTIPLIER
            if t3_signal != "NEUTRAL":
                logger.info("PIPE-03", "t3_edge_overlay",
                            payload={"ticker": mkt.ticker, "signal": t3_signal,
                                     "t1_edge": round(t1_edge, 6),
                                     "adj_edge": round(edge, 6)},
                            session_id=SESSION_ID)
            direction = ("YES" if edge > EDGE_YES else "NO" if edge < EDGE_NO else "PASS")

            forecast_rec = {
                "forecast_id": f"FCST-{uuid.uuid4().hex[:8].upper()}",
                "p_estimate": p_threshold,
                "p_estimate_lr": p_est_lr,
                "market_implied_prob": mid,
                "gross_edge": gross_edge,
                "kalshi_fee": round(kalshi_fee, 6),
                "edge": edge,                      # T3-adjusted net-of-fee (C4 gates on this)
                "t1_edge": round(t1_edge, 6),      # raw T1 edge pre-overlay (EXP-018 isolation)
                "t3_signal": t3_signal,
                "recommended_direction": direction,
            }
            ok_c4, approval = engine.evaluate_forecast(
                forecast_record=forecast_rec,
                current_daily_loss=daily_loss,
                current_drawdown_pct=current_drawdown_pct,
                session_id=SESSION_ID,
            )

            status = approval.get("approval_status", "UNKNOWN")

            if status == "KILL_SWITCH":
                logger.critical("PIPE-03", "kill_switch_from_c4",
                                payload=approval, session_id=SESSION_ID)
                print(f"  KILL SWITCH triggered by C4 — halting PIPE-03.", file=sys.stderr)
                sys.exit(1)

            if status == "APPROVED":
                approved_size = approval.get("approved_size", 0)

                # Batch reserve gate: block if this bet would drop bankroll below 40% floor
                if bankroll - approved_size < RESERVE_MANDATE_PCT * _initial_bankroll:
                    reserve_floor = RESERVE_MANDATE_PCT * _initial_bankroll
                    print(f"  [RESERVE GATE] BATCH HALT — "
                          f"${bankroll:.2f} - ${approved_size:.2f} = "
                          f"${bankroll - approved_size:.2f} < ${reserve_floor:.2f} floor. "
                          f"No further bets.")
                    logger.warning("PIPE-03", "reserve_mandate_batch_halt",
                                   payload={"bankroll": bankroll,
                                            "proposed_size": approved_size,
                                            "reserve_floor": reserve_floor,
                                            "player": kalshi_player_name,
                                            "ticker": mkt.ticker},
                                   session_id=SESSION_ID)
                    _reserve_halted = True
                    break

                approval = {
                    **approval,
                    "model_p": float(forecast_rec["p_estimate"]),
                    "edge": float(forecast_rec["edge"]),           # net-of-fee
                    "gross_edge": float(forecast_rec["gross_edge"]),  # pre-fee (for paper_trader annotation)
                    "t3_signal": forecast_rec.get("t3_signal", "NEUTRAL"),  # EXP-018 isolation
                    "t1_edge": forecast_rec.get("t1_edge", forecast_rec["gross_edge"]),  # pre-T3 raw edge
                }
                ok_pos, pos = trader.open_position(
                    approval=approval,
                    player_name=kalshi_player_name,
                    player_id=player_id,
                    kalshi_ticker=mkt.ticker,
                    kalshi_threshold=mkt.threshold,
                    mid_price=mid,
                    vig=mkt.vig,
                    game_date=_ticker_to_game_date(mkt.ticker),
                    session_id=SESSION_ID,
                )
                dyn_tag = "  [dyn]" if p_est_lr is None else ""
                t3_tag  = f"  [T3:{t3_signal}]" if t3_signal != "NEUTRAL" else ""
                print(f"  BET  {kalshi_player_name:<22} {direction:<4}  ${approved_size:.2f}  "
                      f"edge={edge:+.3f}  p={p_threshold:.3f}  mkt={mkt.threshold}+ pts{dyn_tag}{t3_tag}")
                if pos:
                    orders.append(pos)
                    _state = trader.get_state()
                    bankroll = _state["bankroll_usd"]
                    _initial_bankroll = _state.get("initial_bankroll_usd", 1000.0)
                    _realized_loss = max(0.0, -_state.get("total_realized_pnl", 0.0))
                    current_drawdown_pct = _realized_loss / _initial_bankroll if _initial_bankroll > 0 else 0.0
                    engine = RiskEngine(logger=logger, snapshot_id=SNAPSHOT_ID, bankroll=bankroll,
                                       kelly_fraction=T1_KELLY, initial_bankroll=_initial_bankroll,
                                       min_bet_usd=MIN_BET_T1_PAPER)
                    # daily_loss is loaded from portfolio.current_daily_loss (close_position accumulates
                    # realized losses). Do NOT add bet stakes here — NO bets have edge<0 by convention
                    # and the old line 558 incorrectly accumulated all NO stakes as daily losses.
            else:
                reason = approval.get("rejection_reason", "unknown")
                if direction != "PASS":
                    passes.append({"player": kalshi_player_name, "direction": direction,
                                   "edge": round(edge, 3), "reason": reason})

    # ------------------------------------------------------------------
    # 7. Summary
    # ------------------------------------------------------------------
    summary = trader.summary()
    print(f"\n[SUMMARY]")
    print(f"  Bets placed today:  {len(orders)}")
    print(f"  Rejected by C4:     {len(passes)}")
    print(f"  Bankroll:           ${summary['bankroll_usd']:.2f}")
    print(f"  Total realized P&L: ${summary['total_realized_pnl']:+.2f}")
    print(f"  Open positions:     {summary['open_positions']}")
    print(f"  Closed positions:   {summary['closed_positions']}")
    if summary["win_rate"] is not None:
        print(f"  Win rate:           {summary['win_rate']:.1%}")
    print(f"  Realized drawdown:  {summary['realized_drawdown_pct']:.1f}%")
    print(f"  Deployed (stakes):  {summary['deployed_pct']:.1f}%")

    _write_report(orders, summary["bankroll_usd"], trader)

    SystemMonitor(logger=logger, snapshot_id=SNAPSHOT_ID, session_id=SESSION_ID).check_portfolio_pnl(
        total_realized_pnl=summary["total_realized_pnl"],
        initial_bankroll=summary["initial_bankroll_usd"],
        session_id=SESSION_ID,
    )

    logger.info("PIPE-03", "paper_run_complete",
                payload={"bets_placed": len(orders), "rejected": len(passes),
                         "bankroll": summary["bankroll_usd"],
                         "total_pnl": summary["total_realized_pnl"]},
                session_id=SESSION_ID, snapshot_id=SNAPSHOT_ID)


def _scan_and_log_locks(
    markets: list,
    active_venues: list,
    logger: AuditLogger,
    session_id: str,
) -> None:
    """Detection-only. APR-0010 not signed. Only runs when ≥2 venues are active."""
    if len(active_venues) < 2:
        return
    scanner = ComplementLockScanner(
        fee_per_contract=0.030,
        min_net_profit=0.001,
        require_cross_venue=True,
    )
    opportunities = scanner.scan_snapshot(markets)
    for opp in opportunities:
        logger.info(
            "PIPE-03",
            "lock_detected",
            payload={
                "player_name":    opp.player_name,
                "threshold":      opp.threshold,
                "buy_yes_venue":  opp.buy_yes_venue,
                "buy_no_venue":   opp.buy_no_venue,
                "net_profit":     opp.net_profit,
                "governance":     "detection_only_APR-0010_required",
            },
            session_id=session_id,
        )
    logger.info(
        "PIPE-03",
        "lock_scan_complete",
        payload={"opportunities_found": len(opportunities), "venues": active_venues},
        session_id=session_id,
    )


def _write_report(orders: list, bankroll: float, trader: PaperTrader) -> None:
    summary = trader.summary()
    report = {
        "session_id": SESSION_ID, "game_date": GAME_DATE, "run_at": _utc_now(),
        "bets_placed": len(orders), "portfolio": summary, "orders": orders,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2))
    print(f"\n[DONE] Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
