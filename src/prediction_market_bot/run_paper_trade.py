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
  4. Fetch live Kalshi KXNBAPTS markets (DS-02)
  5. For each cohort player with active market:
     a. Generate p_estimate
     b. Route through C4 RiskEngine (Kelly sizing, hard limits)
     c. If APPROVED: record paper order via PaperTrader
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
from datetime import datetime, timezone
from pathlib import Path

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

from prediction_market_bot.c2_feature_store.qualitative_store import QualitativeSignalStore
from prediction_market_bot.c4_risk_engine.risk import RiskEngine
from prediction_market_bot.c5_execution.complement_lock_scanner import ComplementLockScanner
from prediction_market_bot.c7_monitoring.monitor import SystemMonitor
from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient
from prediction_market_bot.c5_execution.paper_trader import PaperTrader
from prediction_market_bot.execution_bands import BAND_REGISTRY, get_band_config, ExecutionBand
from prediction_market_bot.c5_execution.venue_router import VenueRouter
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from prediction_market_bot.c3_forecasting.game_state_model import _poisson_cdf

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SESSION_ID = f"PT-{uuid.uuid4().hex[:8].upper()}"
GAME_DATE  = datetime.now(tz=timezone.utc).strftime("%Y%m%d")

MODEL_PATH    = Path("models/prod_model.joblib")
FEATURE_CSV   = Path("exp_output/EXP-005/EXP-005_feature_matrix.csv")
QS_CSV        = Path("qualitative_data/pam_v4/QS-2026-05-28-002_classifications.csv")
QS_ID         = "QS-2026-05-28-002"
SNAPSHOT_ID   = "SNAP-2026-05-28-002"
LOG_DIR       = Path(os.environ.get("LOG_DIR", str(_SRC_ROOT / "logs")))
PORTFOLIO_PATH = LOG_DIR / "paper_portfolio.json"
REPORT_PATH   = LOG_DIR / f"paper_{GAME_DATE}.json"

EDGE_YES = 0.02
EDGE_NO  = -0.02
FEATURE_WINDOW = 10

# ADR-0010: T1 band Kelly fraction (0.10). Read from execution_bands so that any
# future ADR updating the band config automatically propagates here.
T1_KELLY = get_band_config(ExecutionBand.T1_MULTI_DAY).kelly_fraction

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
    engine   = RiskEngine(logger=logger, snapshot_id=SNAPSHOT_ID, bankroll=bankroll,
                          kelly_fraction=T1_KELLY)
    daily_loss = _state.get("current_daily_loss", 0.0)
    _initial_bankroll = _state.get("initial_bankroll_usd", 1000.0)
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
    # 6. Generate forecasts + C4 evaluation + paper orders
    # ------------------------------------------------------------------
    orders, passes = [], []

    for _, row in latest.iterrows():
        player_name = str(row.get("player_name", ""))
        player_id   = int(row.get("player_id", 0))
        last_name   = player_name.split()[-1] if player_name else ""
        first_init  = player_name[0].upper() if player_name else ""

        player_mkts = [
            m for m in snap.markets
            if last_name.upper() in m.player_name.upper()
            and first_init in m.player_name.upper()
            and m.status == "active"
            and m.has_live_quotes
        ]
        if not player_mkts:
            continue

        pts_mean = float(row.get(f"pts_l{FEATURE_WINDOW}_mean", np.nan))
        if np.isnan(pts_mean):
            continue

        # Compute features once per player; LR p_est used for C6 logging only.
        X = _impute(
            np.array([[row[c] if c in row.index else np.nan for c in feature_names]], dtype=float),
            col_medians,
        )
        p_est = float(pipeline.predict_proba(X)[0, 1])

        for mkt in player_mkts:
            # Idempotency: skip if already holding an open position on this ticker
            _open_tickers = {p["kalshi_ticker"] for p in trader.get_state().get("open_positions", [])}
            if mkt.ticker in _open_tickers:
                print(f"  [IDEMPOTENCY] SKIP {player_name} — {mkt.ticker} already in portfolio "
                      f"({len(_open_tickers)} open tickers; portfolio: {PORTFOLIO_PATH})")
                continue

            # T-129 Path B: threshold-specific probability via Poisson(pts_l10_mean).
            # LR p_est is player-level (no kalshi_threshold feature) → same value for
            # all thresholds → phantom edge at extremes (GG-008). Poisson CDF gives the
            # correct per-threshold estimate without retraining the model.
            thresh_int = int(mkt.threshold)
            p_threshold = 1.0 - _poisson_cdf(thresh_int - 1, pts_mean)

            mid   = mkt.mid_price
            half  = mkt.half_spread
            edge  = p_threshold - mid - half
            direction = ("YES" if edge > EDGE_YES else "NO" if edge < EDGE_NO else "PASS")

            # Route through C4 risk engine
            forecast_rec = {
                "forecast_id": f"FCST-{uuid.uuid4().hex[:8].upper()}",
                "p_estimate": p_threshold,
                "p_estimate_lr": p_est,
                "market_implied_prob": mid,
                "edge": edge,
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
                ok_pos, pos = trader.open_position(
                    approval=approval,
                    player_name=player_name,
                    player_id=player_id,
                    kalshi_ticker=mkt.ticker,
                    kalshi_threshold=mkt.threshold,
                    mid_price=mid,
                    vig=mkt.vig,
                    game_date=_ticker_to_game_date(mkt.ticker),
                    session_id=SESSION_ID,
                )
                size = approval.get("approved_size", 0)
                print(f"  BET  {player_name:<22} {direction:<4}  ${size:.2f}  "
                      f"edge={edge:+.3f}  p={p_threshold:.3f}  mkt={mkt.threshold}+ pts")
                if pos:
                    orders.append(pos)
                    _state = trader.get_state()
                    bankroll = _state["bankroll_usd"]
                    _initial_bankroll = _state.get("initial_bankroll_usd", 1000.0)
                    _realized_loss = max(0.0, -_state.get("total_realized_pnl", 0.0))
                    current_drawdown_pct = _realized_loss / _initial_bankroll if _initial_bankroll > 0 else 0.0
                    engine = RiskEngine(logger=logger, snapshot_id=SNAPSHOT_ID, bankroll=bankroll,
                                       kelly_fraction=T1_KELLY)
                    daily_loss += size if edge < 0 else 0
            else:
                reason = approval.get("rejection_reason", "unknown")
                if direction != "PASS":
                    passes.append({"player": player_name, "direction": direction,
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
