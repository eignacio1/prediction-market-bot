"""
PIPE-05: T2 Same-Day Injury/Lineup Overlay
============================================
Pipeline:     PIPE-05 (T2 Execution Band — Same-Day)
Band:         T2_SAME_DAY (ExecutionBand)
Phase:        Phase 7 (requires injury data source — T-075)
Schedule:     17:00 UTC daily on game days (cron: 0 17 * * *)
Environment:  ENV-02 (VPS — same as PIPE-02)

Purpose:
  Applies an injury and lineup adjustment overlay on top of the T1 forecast.
  Runs 4-6 hours before tipoff when lineups are being confirmed.
  Adjusts p_estimate for players whose usage share changes materially
  due to teammate absences or confirmed load management.

Band configuration (from BAND_CONFIGS):
  T2 kelly_fraction = 0.20 (slightly below T1's 0.25 — injury data adds uncertainty)
  T2 max_compute_ms = 5,000ms
  T2 execution_sla_s = 1,800s (30 min window)

STATUS: SKELETON — Injury data source (DS-04) not yet provisioned.
  T-075 (Strategy B feature enhancement) will add injury flags to C2.
  Until DS-04 is registered:
    - Pipeline runs and reads T1 forecasts
    - Injury overlay is a TODO stub (returns T1 forecasts unchanged)
    - Output is written as t2_YYYYMMDD.json for monitoring

TODO (T-075):
  [ ] Register injury/availability data source as DS-04 in DATA_REQUIREMENTS.md
  [ ] Add injury_flag, teammate_out_flag, usage_adjustment features to C2
  [ ] Implement _apply_injury_overlay() using nba_api PlayerAvailability
      or third-party injury feed
  [ ] Add to FEATURE_VERSION 1.3.0

Security (NFR-05):
  VENUE_API_KEY loaded from environment only. BOT_C4_ACTIVE must NOT be set.
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

from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from prediction_market_bot.execution_bands import ExecutionBand, get_band_config

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

COMPONENT   = "PIPE-05"
BAND        = ExecutionBand.T2_SAME_DAY
BAND_CFG    = get_band_config(BAND)
SESSION_ID  = f"T2-{uuid.uuid4().hex[:8].upper()}"
GAME_DATE   = datetime.now(tz=timezone.utc).strftime("%Y%m%d")

LOG_DIR     = Path(os.environ.get("LOG_DIR", "logs"))
T1_REPORT   = LOG_DIR / f"pregame_{GAME_DATE}.json"
OUTPUT_PATH = LOG_DIR / f"t2_{GAME_DATE}.json"

# Usage share adjustment applied when a key teammate is confirmed out
# (stub value — calibrate once DS-04 injury data is integrated)
TEAMMATE_OUT_USAGE_BOOST: float = 0.04   # +4% scoring probability boost


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = AuditLogger(LOG_DIR / "audit.jsonl", min_severity="INFO")

    print(f"\n[PIPE-05 T2] Same-day injury overlay — {GAME_DATE}")
    print(f"Session:  {SESSION_ID}")
    print(f"Band:     {BAND.value} | Kelly: {BAND_CFG.kelly_fraction} | STATUS: SKELETON (T-075)")

    logger.info(COMPONENT, "t2_run_start",
                payload={"session_id": SESSION_ID, "game_date": GAME_DATE,
                         "band": BAND.value, "status": "skeleton"},
                session_id=SESSION_ID)

    # ------------------------------------------------------------------
    # 1. Load T1 forecast
    # ------------------------------------------------------------------
    if not T1_REPORT.exists():
        print(f"[T2] No T1 report at {T1_REPORT}. Exiting.")
        _write_empty_report(SESSION_ID, "no_t1_report")
        sys.exit(0)

    t1_report   = json.loads(T1_REPORT.read_text())
    t1_forecasts = t1_report.get("forecasts", [])

    if not t1_forecasts:
        print("[T2] T1 report has no forecasts. Exiting.")
        _write_empty_report(SESSION_ID, "no_t1_forecasts")
        sys.exit(0)

    print(f"[T1] Loaded {len(t1_forecasts)} forecasts from {T1_REPORT.name}")

    # ------------------------------------------------------------------
    # 2. Injury overlay (STUB — T-075)
    # ------------------------------------------------------------------
    # TODO (T-075): Replace this stub with real injury data from DS-04.
    # Steps:
    #   a. Fetch PlayerAvailability from nba_api (or DS-04 injury feed)
    #   b. For each player in t1_forecasts:
    #      - Check if key usage-share teammates are listed as OUT
    #      - If yes: apply TEAMMATE_OUT_USAGE_BOOST to p_estimate
    #      - If player themselves is QUESTIONABLE: reduce kelly_fraction to 0.05
    #      - If player themselves is OUT: remove from t2_forecasts entirely
    #   c. Log all adjustments to C6 with event_type='t2_injury_adjustment'
    #
    # For now: pass T1 forecasts through unchanged with T2 band tag

    t2_forecasts = []
    for fc in t1_forecasts:
        t2_fc = {
            **fc,
            "band":           BAND.value,
            "kelly_fraction": BAND_CFG.kelly_fraction,
            "injury_overlay": "not_applied",   # TODO: replace with DS-04 result
            "t2_p_estimate":  fc.get("p_estimate"),
            "t2_edge":        fc.get("edge"),
        }
        t2_forecasts.append(t2_fc)

    print(f"[T2] Injury overlay: STUB (DS-04 not yet registered — T-075)")
    print(f"[T2] {len(t2_forecasts)} forecasts passed through with T2 band tag")

    # ------------------------------------------------------------------
    # 3. Write report
    # ------------------------------------------------------------------
    report = {
        "session_id":      SESSION_ID,
        "band":            BAND.value,
        "game_date":       GAME_DATE,
        "run_at":          _utc_now(),
        "t1_report_path":  str(T1_REPORT),
        "t1_count":        len(t1_forecasts),
        "t2_count":        len(t2_forecasts),
        "injury_overlay":  "stub_t075_pending",
        "forecasts":       t2_forecasts,
    }
    OUTPUT_PATH.write_text(json.dumps(report, indent=2))

    print(f"[DONE] Report: {OUTPUT_PATH}")

    logger.info(COMPONENT, "t2_run_complete",
                payload={"t2_count": len(t2_forecasts), "output_path": str(OUTPUT_PATH),
                         "injury_overlay": "stub"},
                session_id=SESSION_ID)


def _write_empty_report(session_id: str, reason: str) -> None:
    report = {
        "session_id": session_id, "band": BAND.value,
        "game_date": GAME_DATE, "run_at": _utc_now(),
        "reason": reason, "t2_count": 0, "forecasts": [],
    }
    OUTPUT_PATH.write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    if os.environ.get("BOT_C4_ACTIVE"):
        print("FATAL: BOT_C4_ACTIVE is set. PIPE-05 does not place orders.", file=sys.stderr)
        sys.exit(1)
    main()
