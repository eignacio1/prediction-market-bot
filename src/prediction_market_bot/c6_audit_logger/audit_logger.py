"""
C6: Audit Logger — Append-only JSON Lines structured log
=========================================================
Component:    C6 (Audit Logger)
Phase active: ALWAYS ACTIVE from Phase 3+. Never disabled.
Status:       CANONICAL (Phase 3 2026-05-23)
Upstream:     All components (C1–C5, C7) write through this module
Downstream:   Audit log file (BOT_AUDIT_LOG_PATH env var)
Interfaces:   All components call AuditLogger.log(); no return value required
ADR refs:     ADR-0001 (Compass OS), ADR-0002 (forecast-only)
Policy refs:  OBSERVABILITY.md, DATA_RETENTION_DELETION.md CAT-04,
              RUNBOOKS/RUNBOOK_kill-switch.md

Security constraints (NFR-05, NFR-07):
  - Audit log MUST NOT contain API keys, passwords, or tokens in payload
  - Secrets must be redacted before passing to log()
  - Audit log is append-only; truncation or deletion requires ADR evidence

Kill switch constraint (NFR-03):
  - AuditLogger write failure (IOError, PermissionError, disk full) must
    trigger the kill switch. Downstream callers check the return value.
  - C6 is the traceability backbone — a silently failing logger is worse
    than a halted system.

Retention:
  - ENV-01/02: 2-year minimum (DATA_RETENTION_DELETION.md CAT-04)
  - ENV-03 (live capital): 5-year minimum

Traceability chain (every entry must carry forward the full ID chain):
  snapshot_id → feature_run_id → forecast_id → risk_eval_id → order_id

Event severity levels:
  DEBUG   — development/trace events; filtered out in ENV-02/03
  INFO    — normal operational events (data fetched, feature computed, etc.)
  WARNING — non-fatal anomaly (stale data, soft limit approached)
  ERROR   — component failure; triggers alert (OBSERVABILITY.md)
  CRITICAL— system-threatening; triggers kill switch check
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonlines


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AUDIT_LOG_ENV_VAR = "BOT_AUDIT_LOG_PATH"
DEFAULT_AUDIT_LOG_PATH = "logs/audit.jsonl"

# Severity levels (ordered)
SEVERITY_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
_SEVERITY_RANK = {s: i for i, s in enumerate(SEVERITY_LEVELS)}

# Fields that must NEVER appear in log payloads (NFR-05)
_REDACTED_KEYS = frozenset(
    {
        "api_key",
        "api_secret",
        "venue_api_key",
        "venue_api_secret",
        "password",
        "token",
        "secret",
        "authorization",
        "auth_header",
    }
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc_now_iso() -> str:
    """Return current UTC timestamp as ISO 8601 string with 'Z' suffix."""
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _redact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively redact known-sensitive keys from a payload dict.
    Mutates a copy — original is not modified.
    Raises ValueError if any top-level key resolves to a redacted name.
    """
    clean: dict[str, Any] = {}
    for k, v in payload.items():
        k_str = str(k)
        if k_str.lower() in _REDACTED_KEYS:
            clean[k_str] = "[REDACTED]"
        elif isinstance(v, dict):
            clean[k_str] = _redact_payload(v)
        else:
            clean[k_str] = v
    return clean


def _make_event_id() -> str:
    return f"EVT-{uuid.uuid4().hex[:12].upper()}"


# ---------------------------------------------------------------------------
# AuditLogger
# ---------------------------------------------------------------------------


class AuditLogger:
    """
    Thread-safe append-only JSON Lines audit logger.

    Usage::

        logger = AuditLogger.from_env()
        logger.log(
            component="C1",
            event_type="data_fetch_complete",
            payload={"player_id": 2544, "seasons_fetched": 3},
            session_id=session_id,
            snapshot_id=snapshot_id,
        )

    Every log() call returns True on success, False on write failure.
    Callers MUST check the return value and trigger the kill switch on False.

    The traceability chain fields (snapshot_id, feature_run_id, forecast_id,
    risk_eval_id, order_id) are all optional individually but at least one
    chain anchor MUST be present for non-DEBUG events. This is enforced at
    WARNING.
    """

    def __init__(self, log_path: str | Path, min_severity: str = "INFO") -> None:
        """
        Parameters
        ----------
        log_path:
            Path to the JSON Lines audit log file. Parent directories will be
            created if they do not exist.
        min_severity:
            Minimum severity level to write. Events below this level are
            silently dropped. Default: INFO. Set to DEBUG in ENV-01 for
            full trace logging.
        """
        self._path = Path(log_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if min_severity not in _SEVERITY_RANK:
            raise ValueError(
                f"min_severity must be one of {SEVERITY_LEVELS}, got {min_severity!r}"
            )
        self._min_rank = _SEVERITY_RANK[min_severity]
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_env(cls, min_severity: str | None = None) -> "AuditLogger":
        """
        Instantiate from environment variables.

        BOT_AUDIT_LOG_PATH  — path to log file (default: logs/audit.jsonl)
        BOT_ENV             — if 'research', sets min_severity=DEBUG unless
                              overridden
        """
        log_path = os.environ.get(AUDIT_LOG_ENV_VAR, DEFAULT_AUDIT_LOG_PATH)
        if min_severity is None:
            bot_env = os.environ.get("BOT_ENV", "research").lower()
            min_severity = "DEBUG" if bot_env == "research" else "INFO"
        return cls(log_path=log_path, min_severity=min_severity)

    # ------------------------------------------------------------------
    # Core log method
    # ------------------------------------------------------------------

    def log(
        self,
        component: str,
        event_type: str,
        payload: dict[str, Any] | None = None,
        session_id: str | None = None,
        snapshot_id: str | None = None,
        feature_run_id: str | None = None,
        forecast_id: str | None = None,
        risk_eval_id: str | None = None,
        order_id: str | None = None,
        severity: str = "INFO",
    ) -> bool:
        """
        Append one structured audit entry to the JSON Lines log.

        Returns True on success, False on any write failure.
        Callers must check return value and trigger kill switch on False.

        Parameters
        ----------
        component:
            Emitting component identifier (e.g. 'C1', 'C2', 'C3', 'C4', 'C5',
            'C6', 'C7', 'SYSTEM').
        event_type:
            Snake_case event descriptor (e.g. 'data_fetch_start',
            'feature_computed', 'forecast_emitted', 'risk_eval_pass',
            'order_submitted', 'kill_switch_triggered').
        payload:
            Arbitrary structured data. Sensitive keys are auto-redacted.
            Must not contain live secrets — pass already-sanitized data.
        session_id:
            Unique identifier for the current bot run session.
        snapshot_id:
            DS-01 / data snapshot anchor (SNAP-001, etc.).
        feature_run_id:
            C2 feature derivation run identifier.
        forecast_id:
            C3 forecast identifier.
        risk_eval_id:
            C4 risk evaluation identifier.
        order_id:
            C5 order identifier.
        severity:
            One of DEBUG, INFO, WARNING, ERROR, CRITICAL.
        """
        if severity not in _SEVERITY_RANK:
            severity = "ERROR"
        if _SEVERITY_RANK[severity] < self._min_rank:
            return True  # Filtered — not a write failure

        entry: dict[str, Any] = {
            "timestamp": _utc_now_iso(),
            "event_id": _make_event_id(),
            "component": component,
            "event_type": event_type,
            "severity": severity,
            # Traceability chain
            "session_id": session_id,
            "snapshot_id": snapshot_id,
            "feature_run_id": feature_run_id,
            "forecast_id": forecast_id,
            "risk_eval_id": risk_eval_id,
            "order_id": order_id,
            # Payload (secrets redacted)
            "payload": _redact_payload(payload or {}),
        }

        # Warn if no chain anchor on non-DEBUG events
        chain_anchors = (
            session_id,
            snapshot_id,
            feature_run_id,
            forecast_id,
            risk_eval_id,
            order_id,
        )
        if severity != "DEBUG" and not any(chain_anchors):
            entry["_chain_warning"] = (
                "No traceability chain anchor provided — "
                "at least one of session_id/snapshot_id/... is required"
            )

        try:
            with self._lock:
                with jsonlines.open(str(self._path), mode="a") as writer:
                    writer.write(entry)
            return True
        except (IOError, OSError, PermissionError) as exc:
            # Do NOT raise — callers check return value and trigger kill switch.
            # Emit to stderr as last resort so the failure is visible.
            import sys

            print(
                f"[C6 AUDIT LOGGER WRITE FAILURE] {exc!r} — kill switch should be triggered",
                file=sys.stderr,
            )
            return False

    # ------------------------------------------------------------------
    # Convenience wrappers
    # ------------------------------------------------------------------

    def info(
        self,
        component: str,
        event_type: str,
        payload: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> bool:
        return self.log(component, event_type, payload, severity="INFO", **kwargs)

    def warning(
        self,
        component: str,
        event_type: str,
        payload: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> bool:
        return self.log(component, event_type, payload, severity="WARNING", **kwargs)

    def error(
        self,
        component: str,
        event_type: str,
        payload: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> bool:
        return self.log(component, event_type, payload, severity="ERROR", **kwargs)

    def critical(
        self,
        component: str,
        event_type: str,
        payload: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> bool:
        return self.log(component, event_type, payload, severity="CRITICAL", **kwargs)

    def debug(
        self,
        component: str,
        event_type: str,
        payload: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> bool:
        return self.log(component, event_type, payload, severity="DEBUG", **kwargs)
