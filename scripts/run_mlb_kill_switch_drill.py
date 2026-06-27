"""
MLB Kill Switch Drill — T-197 / TC-007 / NFR-03

Mirrors the NBA drill pattern (run 2026-05-28, SES-DRILL-20260528-001).
Instantiates SystemMonitor against the MLB audit log and runs the in-process
kill switch drill.  Measures halt_time_ms and asserts SLA (≤60,000ms).

Pass criteria (mirrors G5 NBA pattern, applied to MLB-G1):
  - result.passed_sla is True
  - Kill event appears in audit_mlb.jsonl
  - result.halt_time_ms reported and written to drill_audit.jsonl

Usage:
  BOT_ENV=paper PYTHONPATH=src python3 scripts/run_mlb_kill_switch_drill.py
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

_SRC_ROOT = Path(__file__).parent.parent / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

os.environ.setdefault("BOT_ENV", "paper")

from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from prediction_market_bot.c7_monitoring.monitor import SystemMonitor

LOG_DIR      = Path(os.environ.get("LOG_DIR", str(_SRC_ROOT / "logs")))
SESSION_ID   = f"SES-MLB-DRILL-{datetime.now(timezone.utc).strftime('%Y%m%d')}-001"
SNAPSHOT_ID  = "SNAP-MLB-DRILL-T197"
OPERATOR     = "Earl Ignacio"
TC_REF       = "TC-007"
NFR_REF      = "NFR-03"


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    audit_path = LOG_DIR / "audit_mlb.jsonl"
    drill_log  = LOG_DIR / "drill_audit.jsonl"

    print(f"\n[MLB DRILL] Kill switch drill — TC-007 / NFR-03")
    print(f"Session:    {SESSION_ID}")
    print(f"Audit log:  {audit_path}")
    print(f"Drill log:  {drill_log}")

    logger = AuditLogger(audit_path, min_severity="INFO")
    monitor = SystemMonitor(
        logger=logger,
        snapshot_id=SNAPSHOT_ID,
        session_id=SESSION_ID,
    )

    print("\n[DRILL] Triggering kill switch...")
    result = monitor.run_kill_switch_drill(
        operator=OPERATOR,
        session_id=SESSION_ID,
    )

    sla_status = "PASS" if result.passed_sla else "FAIL"
    print(f"\n[DRILL] Result:")
    print(f"  kill_switch_id:  {result.kill_switch_id}")
    print(f"  halt_time_ms:    {result.halt_time_ms:.3f}")
    print(f"  passed_sla:      {result.passed_sla}  [{sla_status}]")
    print(f"  sla_threshold:   60,000ms")

    apr_record = {
        "timestamp":       datetime.now(timezone.utc).isoformat(),
        "session_id":      SESSION_ID,
        "snapshot_id":     SNAPSHOT_ID,
        "sport":           "MLB",
        "gate":            "MLB-G1",
        "drill_type":      "kill_switch",
        "tc_ref":          TC_REF,
        "nfr_ref":         NFR_REF,
        "operator":        OPERATOR,
        "kill_switch_id":  result.kill_switch_id,
        "halt_time_ms":    result.halt_time_ms,
        "passed_sla":      result.passed_sla,
        "sla_threshold_ms": 60000,
        "result":          sla_status,
    }

    with open(drill_log, "a") as fh:
        fh.write(json.dumps(apr_record) + "\n")
    print(f"\n[DRILL] APR record written to {drill_log}")

    if not result.passed_sla:
        print(f"\n[DRILL] FAIL — halt_time_ms={result.halt_time_ms:.3f} exceeds SLA (60,000ms)",
              file=sys.stderr)
        sys.exit(1)

    print(f"\n[DRILL] MLB kill switch drill PASSED — TC-007 SLA satisfied.")


if __name__ == "__main__":
    main()
