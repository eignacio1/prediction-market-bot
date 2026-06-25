"""
PIPE-06 MLB: MLB Pre-Tip Momentum Scan
========================================
Pipeline:     PIPE-06 MLB (T3 — Pre-Tip Momentum, baseball)
Band:         T3_PRE_TIP (ExecutionBand)
Phase:        Phase 6 (paper trading)
Schedule:     Every 15 min, 20:00–03:00 UTC — two cron entries to cover midnight wrap:
                */15 20-23 * * *  (8pm–11pm UTC — most MLB game windows)
                */15 0-3  * * *   (midnight–3am UTC — late games / West Coast)
Environment:  ENV-02 (VPS) or local

Purpose:
  Reads the MLB T1 pregame context file (pregame_mlb_YYYYMMDD.json) produced by
  PIPE-06pre (run_mlb_pregame.py). Fetches current live KXMLBHIT prices from Kalshi.
  For each actionable T1 forecast, computes a momentum signal by comparing the current
  market price to the T1 snapshot price.

Momentum signal logic:
  CONFIRM  — price drifted ≥ MOMENTUM_THRESHOLD in the direction of our model
             (smart money moving with our forecast → higher confidence)
  FADE     — price drifted ≥ MOMENTUM_THRESHOLD against our forecast
             (counter-signal → reduce confidence)
  NEUTRAL  — drift < threshold (no adjustment)

Output:
  logs/t3_mlb_YYYYMMDD_HHMM.json — MLB T3 momentum-adjusted forecast report

Security (NFR-05):
  Read-only scan — never places orders. VENUE_API_KEY loaded from environment.

How to run:
  source /opt/prediction-market-bot/.env
  PYTHONPATH=src /opt/prediction-market-bot/venv/bin/python \\
      src/prediction_market_bot/run_t3_mlb_pretip.py
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

_SRC_ROOT = Path(__file__).parent.parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from prediction_market_bot.execution_bands import ExecutionBand, get_band_config

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

COMPONENT  = "PIPE-06-MLB"
BAND       = ExecutionBand.T3_PRE_TIP
BAND_CFG   = get_band_config(BAND)
SESSION_ID = f"T3-MLB-{uuid.uuid4().hex[:8].upper()}"
NOW        = datetime.now(tz=timezone.utc)
GAME_DATE  = NOW.strftime("%Y%m%d")
RUN_TIME   = NOW.strftime("%H%M")

LOG_DIR      = Path(os.environ.get("LOG_DIR", "logs"))
OUTPUT_PATH  = LOG_DIR / f"t3_mlb_{GAME_DATE}_{RUN_TIME}.json"

MOMENTUM_THRESHOLD: float = 0.025
CONFIRM_MULTIPLIER: float = 1.15
FADE_MULTIPLIER:    float = 0.75


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _load_pregame_context() -> tuple[list[dict], Path | None]:
    """Load the most recent pregame_mlb_*.json from LOG_DIR."""
    jsons = sorted(LOG_DIR.glob("pregame_mlb_*.json"), reverse=True)
    if not jsons:
        return [], None
    path = jsons[0]
    report = json.loads(path.read_text())
    return report.get("forecasts", []), path


def _write_empty_report(session_id: str, reason: str, t1_path: str = "") -> None:
    report = {
        "session_id":   session_id,
        "band":         BAND.value,
        "game_date":    GAME_DATE,
        "sport":        "mlb",
        "run_at":       _utc_now(),
        "reason":       reason,
        "t1_path":      t1_path,
        "t3_evaluated": 0,
        "confirmed":    0,
        "faded":        0,
        "neutral":      0,
        "forecasts":    [],
    }
    OUTPUT_PATH.write_text(json.dumps(report, indent=2))


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = AuditLogger(LOG_DIR / "audit_mlb.jsonl", min_severity="INFO")

    print(f"\n[PIPE-06-MLB T3] MLB pre-tip momentum scan — {GAME_DATE} {RUN_TIME}Z")
    print(f"Session:  {SESSION_ID}")
    print(f"Band:     {BAND.value} | Kelly: {BAND_CFG.kelly_fraction} | SLA: {BAND_CFG.execution_sla_s}s")

    logger.info(COMPONENT, "t3_mlb_scan_start",
                payload={"session_id": SESSION_ID, "game_date": GAME_DATE,
                         "band": BAND.value, "kelly_fraction": BAND_CFG.kelly_fraction,
                         "sport": "mlb"},
                session_id=SESSION_ID)

    # ------------------------------------------------------------------
    # 1. Load MLB T1 pregame context
    # ------------------------------------------------------------------
    all_forecasts, t1_path = _load_pregame_context()

    if t1_path is None:
        print(f"[T3-MLB] No pregame_mlb_*.json in {LOG_DIR} — PIPE-06pre has not run today. Exiting.")
        logger.info(COMPONENT, "t3_mlb_no_pregame_file",
                    payload={"log_dir": str(LOG_DIR)}, session_id=SESSION_ID)
        _write_empty_report(session_id=SESSION_ID, reason="no_pregame_file")
        sys.exit(0)

    if not all_forecasts:
        print("[T3-MLB] Pregame file has no forecasts (no KXMLBHIT markets today). Exiting.")
        _write_empty_report(session_id=SESSION_ID, reason="no_forecasts",
                            t1_path=str(t1_path))
        sys.exit(0)

    actionable = [f for f in all_forecasts if f.get("direction") != "PASS"]
    print(f"[T1-MLB] Loaded {len(all_forecasts)} forecasts from {t1_path.name} "
          f"| {len(actionable)} actionable")

    if not actionable:
        print("[T3-MLB] No actionable T1 forecasts. Exiting.")
        _write_empty_report(session_id=SESSION_ID, reason="no_actionable_t1",
                            t1_path=str(t1_path))
        sys.exit(0)

    # ------------------------------------------------------------------
    # 2. Fetch current live KXMLBHIT prices
    # ------------------------------------------------------------------
    print("[DS-02] Fetching current KXMLBHIT prices from Kalshi...")
    try:
        client = KalshiMarketClient.from_env()
        ok, status = client.check_connectivity()
        if not ok:
            logger.error(COMPONENT, "ds02_connectivity_failed",
                         payload=status, session_id=SESSION_ID)
            print(f"ERROR: DS-02 connectivity failed: {status}", file=sys.stderr)
            sys.exit(1)

        ok2, snapshot = client.fetch_player_points_markets(sport="MLB")
        if not ok2 or not snapshot.markets:
            print("[T3-MLB] No KXMLBHIT markets available. Exiting.")
            logger.info(COMPONENT, "t3_mlb_no_markets",
                        payload={"reason": "no active KXMLBHIT markets"},
                        session_id=SESSION_ID)
            _write_empty_report(session_id=SESSION_ID, reason="no_live_markets",
                                t1_path=str(t1_path))
            sys.exit(0)

        live_by_ticker = {m.ticker: m for m in snapshot.markets if m.has_live_quotes}
        print(f"  {len(snapshot.markets)} markets | {len(live_by_ticker)} with live quotes")

    except EnvironmentError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # 3. Compute momentum signals
    # ------------------------------------------------------------------
    t3_forecasts: list[dict] = []

    for fc in actionable:
        ticker     = fc.get("kalshi_ticker", "")
        t1_mid     = float(fc.get("mid_price", 0.5))
        t1_edge    = float(fc.get("edge", 0.0))
        t1_dir     = fc.get("direction", "PASS")
        t1_p_est   = float(fc.get("p_estimate", 0.5))
        threshold  = fc.get("kalshi_threshold", 0)
        player     = fc.get("player_name", "")
        player_id  = fc.get("player_id")

        current_mkt = live_by_ticker.get(ticker)
        if current_mkt is None:
            continue

        current_mid = current_mkt.mid_price
        price_drift = current_mid - t1_mid

        if t1_dir == "YES" and price_drift >= MOMENTUM_THRESHOLD:
            signal    = "CONFIRM"
            edge_adj  = t1_edge * CONFIRM_MULTIPLIER
        elif t1_dir == "NO" and price_drift <= -MOMENTUM_THRESHOLD:
            signal    = "CONFIRM"
            edge_adj  = t1_edge * CONFIRM_MULTIPLIER
        elif t1_dir == "YES" and price_drift <= -MOMENTUM_THRESHOLD:
            signal    = "FADE"
            edge_adj  = t1_edge * FADE_MULTIPLIER
        elif t1_dir == "NO" and price_drift >= MOMENTUM_THRESHOLD:
            signal    = "FADE"
            edge_adj  = t1_edge * FADE_MULTIPLIER
        else:
            signal    = "NEUTRAL"
            edge_adj  = t1_edge

        t3_fc = {
            "player_name":      player,
            "player_id":        player_id,
            "kalshi_ticker":    ticker,
            "kalshi_threshold": threshold,
            "t1_mid_price":     round(t1_mid, 4),
            "current_mid_price": round(current_mid, 4),
            "price_drift":      round(price_drift, 4),
            "momentum_signal":  signal,
            "t1_edge":          round(t1_edge, 4),
            "t3_edge_adjusted": round(edge_adj, 4),
            "t1_p_estimate":    round(t1_p_est, 4),
            "t1_direction":     t1_dir,
            "band":             BAND.value,
            "kelly_fraction":   BAND_CFG.kelly_fraction,
            "sport":            "mlb",
            "forecast_at":      _utc_now(),
        }
        t3_forecasts.append(t3_fc)

        icon = "✓" if signal == "CONFIRM" else ("✗" if signal == "FADE" else "~")
        print(f"  {icon} {player:<28} H≥{threshold}  "
              f"drift={price_drift:+.3f}  signal={signal:<8}  t3_edge={edge_adj:+.3f}")

        logger.info(COMPONENT, "t3_mlb_momentum_signal",
                    payload={k: v for k, v in t3_fc.items() if k != "forecast_at"},
                    session_id=SESSION_ID)

    # ------------------------------------------------------------------
    # 4. Write report
    # ------------------------------------------------------------------
    confirmed = [f for f in t3_forecasts if f["momentum_signal"] == "CONFIRM"]
    faded     = [f for f in t3_forecasts if f["momentum_signal"] == "FADE"]

    report = {
        "session_id":   SESSION_ID,
        "band":         BAND.value,
        "game_date":    GAME_DATE,
        "sport":        "mlb",
        "run_at":       _utc_now(),
        "t1_path":      str(t1_path),
        "t1_actionable": len(actionable),
        "t3_evaluated": len(t3_forecasts),
        "confirmed":    len(confirmed),
        "faded":        len(faded),
        "neutral":      len(t3_forecasts) - len(confirmed) - len(faded),
        "forecasts":    t3_forecasts,
    }
    OUTPUT_PATH.write_text(json.dumps(report, indent=2))

    print(f"\n[DONE] T3-MLB: {len(confirmed)} CONFIRM | {len(faded)} FADE | "
          f"{report['neutral']} NEUTRAL | {OUTPUT_PATH}")

    logger.info(COMPONENT, "t3_mlb_scan_complete",
                payload={"confirmed": len(confirmed), "faded": len(faded),
                         "t3_evaluated": len(t3_forecasts),
                         "output_path": str(OUTPUT_PATH)},
                session_id=SESSION_ID)


if __name__ == "__main__":
    main()
