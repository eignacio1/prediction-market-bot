"""
PIPE-06: T3 Pre-Tip Momentum Scan
===================================
Pipeline:     PIPE-06 (T3 Execution Band — Pre-Tip Momentum)
Band:         T3_PRE_TIP (ExecutionBand)
Phase:        Phase 7 (buildable on current cron infrastructure)
Schedule:     Every 15 min, 20:00–03:00 UTC (cron: */15 20-23,0-3 * * *); extended per T-084 for late 10pm ET games
Environment:  ENV-02 (VPS — same as PIPE-02)

Purpose:
  Reads the T1 forecast output (pregame_YYYYMMDD.json) produced by PIPE-02.
  Fetches current live Kalshi prices via VenueRouter.
  For each forecast player, computes a momentum signal by comparing the
  current market price to the T1 forecast-time price.

Momentum signal logic:
  CONFIRM  — price drifted ≥ MOMENTUM_THRESHOLD in the direction of our model
             (smart money moving with our forecast → increase confidence)
  FADE     — price drifted ≥ MOMENTUM_THRESHOLD against our forecast
             (counter-signal → reduce position size)
  NEUTRAL  — price unchanged or drift < threshold (no adjustment)

Band adjustments (from BAND_CONFIGS):
  T3 kelly_fraction = 0.10 (half of T1's 0.25)
  T3 max_compute_ms = 500ms (no historical data loaded)
  T3 execution_sla_s = 300s (5 min window before tip-off)

Output:
  logs/t3_YYYYMMDD_HHMM.json — T3 momentum-adjusted forecast report

Security (NFR-05):
  VENUE_API_KEY loaded from environment only. BOT_C4_ACTIVE must NOT be set.

How to run:
  # On VPS (ENV-02):
  source /opt/prediction-market-bot/.env
  PYTHONPATH=/opt/prediction-market-bot/src \\
      /opt/prediction-market-bot/venv/bin/python \\
      /opt/prediction-market-bot/src/prediction_market_bot/run_t3_pretip.py
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

from prediction_market_bot.c5_execution.venue_router import VenueRouter
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from prediction_market_bot.execution_bands import ExecutionBand, get_band_config

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

COMPONENT   = "PIPE-06"
BAND        = ExecutionBand.T3_PRE_TIP
BAND_CFG    = get_band_config(BAND)
SESSION_ID  = f"T3-{uuid.uuid4().hex[:8].upper()}"
NOW         = datetime.now(tz=timezone.utc)
GAME_DATE   = NOW.strftime("%Y%m%d")
RUN_TIME    = NOW.strftime("%H%M")

LOG_DIR     = Path(os.environ.get("LOG_DIR", "logs"))
T1_REPORT   = LOG_DIR / f"pregame_{GAME_DATE}.json"
OUTPUT_PATH = LOG_DIR / f"t3_{GAME_DATE}_{RUN_TIME}.json"

# Minimum price drift to register a momentum signal
MOMENTUM_THRESHOLD: float = 0.025

# Multipliers applied to T1 edge based on momentum signal
CONFIRM_MULTIPLIER: float = 1.15     # Price moved with us → higher confidence
FADE_MULTIPLIER:    float = 0.75     # Price moved against us → lower confidence


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = AuditLogger(LOG_DIR / "audit.jsonl", min_severity="INFO")

    print(f"\n[PIPE-06 T3] Pre-tip momentum scan — {GAME_DATE} {RUN_TIME}Z")
    print(f"Session:  {SESSION_ID}")
    print(f"Band:     {BAND.value} | Kelly: {BAND_CFG.kelly_fraction} | SLA: {BAND_CFG.execution_sla_s}s")

    logger.info(COMPONENT, "t3_scan_start",
                payload={"session_id": SESSION_ID, "game_date": GAME_DATE,
                         "band": BAND.value, "kelly_fraction": BAND_CFG.kelly_fraction},
                session_id=SESSION_ID)

    # ------------------------------------------------------------------
    # 1. Load T1 forecast report
    # ------------------------------------------------------------------
    if not T1_REPORT.exists():
        print(f"[T3] No T1 report found at {T1_REPORT} — PIPE-02 has not run today. Exiting.")
        logger.info(COMPONENT, "t3_no_t1_report",
                    payload={"path": str(T1_REPORT)}, session_id=SESSION_ID)
        _write_empty_report(session_id=SESSION_ID, reason="no_t1_report")
        sys.exit(0)

    t1_report = json.loads(T1_REPORT.read_text())
    t1_forecasts = t1_report.get("forecasts", [])

    if not t1_forecasts:
        print("[T3] T1 report has no forecasts (no markets today). Exiting.")
        _write_empty_report(session_id=SESSION_ID, reason="no_t1_forecasts")
        sys.exit(0)

    actionable_t1 = [f for f in t1_forecasts if f.get("direction") != "PASS"]
    print(f"[T1] Loaded {len(t1_forecasts)} forecasts | {len(actionable_t1)} actionable from T1")

    # ------------------------------------------------------------------
    # 2. Fetch current live prices via VenueRouter
    # ------------------------------------------------------------------
    print("[DS-02] Fetching current prices via VenueRouter...")
    try:
        router = VenueRouter.from_env()
        ok, snapshot = router.fetch_all_markets()
        if not ok or not snapshot.markets:
            print("[T3] No markets available from VenueRouter. Exiting.")
            logger.info(COMPONENT, "t3_no_markets",
                        payload={"venues": router.active_venues}, session_id=SESSION_ID)
            _write_empty_report(session_id=SESSION_ID, reason="no_live_markets")
            sys.exit(0)
        print(f"  {len(snapshot.markets)} markets | venues: {router.active_venues}")
    except EnvironmentError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # 3. Compute momentum signals
    # ------------------------------------------------------------------
    t3_forecasts = []

    for fc in actionable_t1:
        player_name = fc.get("player_name", "")
        t1_ticker   = fc.get("kalshi_ticker", "")
        t1_mid      = float(fc.get("mid_price", 0.5))
        t1_edge     = float(fc.get("edge", 0.0))
        t1_dir      = fc.get("direction", "PASS")
        t1_p_est    = float(fc.get("p_estimate", 0.5))
        threshold   = fc.get("kalshi_threshold", 0)

        # Find current price for same ticker
        current_market = next(
            (m for m in snapshot.markets if m.ticker == t1_ticker), None
        )
        if current_market is None:
            # Market may have closed; skip
            continue

        current_mid = current_market.mid_price
        price_drift = current_mid - t1_mid   # positive = price went up

        # Momentum signal
        if t1_dir == "YES" and price_drift >= MOMENTUM_THRESHOLD:
            signal = "CONFIRM"
            edge_adj = t1_edge * CONFIRM_MULTIPLIER
        elif t1_dir == "NO" and price_drift <= -MOMENTUM_THRESHOLD:
            signal = "CONFIRM"
            edge_adj = t1_edge * CONFIRM_MULTIPLIER
        elif t1_dir == "YES" and price_drift <= -MOMENTUM_THRESHOLD:
            signal = "FADE"
            edge_adj = t1_edge * FADE_MULTIPLIER
        elif t1_dir == "NO" and price_drift >= MOMENTUM_THRESHOLD:
            signal = "FADE"
            edge_adj = t1_edge * FADE_MULTIPLIER
        else:
            signal = "NEUTRAL"
            edge_adj = t1_edge

        t3_fc = {
            "player_name":      player_name,
            "kalshi_ticker":    t1_ticker,
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
            "venue":            current_market.venue,
            "forecast_at":      _utc_now(),
        }
        t3_forecasts.append(t3_fc)

        status_icon = "✓" if signal == "CONFIRM" else ("✗" if signal == "FADE" else "~")
        print(f"  {status_icon} {player_name:<28} drift={price_drift:+.3f}  signal={signal:<8} t3_edge={edge_adj:+.3f}")

        logger.info(COMPONENT, "t3_momentum_signal",
                    payload={k: v for k, v in t3_fc.items() if k != "forecast_at"},
                    session_id=SESSION_ID)

    # ------------------------------------------------------------------
    # 4. Write report
    # ------------------------------------------------------------------
    confirmed = [f for f in t3_forecasts if f["momentum_signal"] == "CONFIRM"]
    faded     = [f for f in t3_forecasts if f["momentum_signal"] == "FADE"]

    report = {
        "session_id":       SESSION_ID,
        "band":             BAND.value,
        "game_date":        GAME_DATE,
        "run_at":           _utc_now(),
        "t1_report_path":   str(T1_REPORT),
        "t1_actionable":    len(actionable_t1),
        "t3_evaluated":     len(t3_forecasts),
        "confirmed":        len(confirmed),
        "faded":            len(faded),
        "neutral":          len(t3_forecasts) - len(confirmed) - len(faded),
        "forecasts":        t3_forecasts,
    }
    OUTPUT_PATH.write_text(json.dumps(report, indent=2))

    print(f"\n[DONE] T3: {len(confirmed)} CONFIRM | {len(faded)} FADE | "
          f"{report['neutral']} NEUTRAL | report: {OUTPUT_PATH}")

    logger.info(COMPONENT, "t3_scan_complete",
                payload={"confirmed": len(confirmed), "faded": len(faded),
                         "output_path": str(OUTPUT_PATH)},
                session_id=SESSION_ID)


def _write_empty_report(session_id: str, reason: str) -> None:
    report = {
        "session_id":    session_id,
        "band":          BAND.value,
        "game_date":     GAME_DATE,
        "run_at":        _utc_now(),
        "reason":        reason,
        "t3_evaluated":  0,
        "confirmed":     0,
        "faded":         0,
        "neutral":       0,
        "forecasts":     [],
    }
    OUTPUT_PATH.write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    if os.environ.get("BOT_C4_ACTIVE"):
        print("FATAL: BOT_C4_ACTIVE is set. PIPE-06 does not place orders.", file=sys.stderr)
        sys.exit(1)
    main()
