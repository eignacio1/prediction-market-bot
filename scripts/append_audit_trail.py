#!/usr/bin/env python3
"""
T-300 (A2) — Disk-backed audit/log writer, receipt-only return
ADR-0041 | Window A: context/token optimization infra

CONTEXT
-------
A Claude Code session writing a governance event today has to read the target
log file back (fully or in part) to confirm the write landed, which pulls Tier 1
log content into the conversation's context window for no reason — the write
itself is already durable once C6's AuditLogger.log() returns True. Per
ADR-0041 (Tier 1: never cull governance lineage from disk, only from what a
session loads into context), the fix is a thin wrapper that appends through
the existing, already-tested C6 AuditLogger and hands back a receipt
({status, bytes_written}) instead of the entry it just wrote.

This module does not reimplement append-only writing, redaction, severity
filtering, or the traceability-chain warning — all of that stays owned by
`c6_audit_logger.audit_logger.AuditLogger`. It adds exactly two things on top:
a pre-write schema-conformance check, and a receipt-only return contract.

LOG TYPE REGISTRY
-----------------
`log_type` selects which on-disk C6 audit log a call targets. The registry
below mirrors the paths already in production use (grepped from every
`AuditLogger(...)` call site as of 2026-07-09) rather than inventing new
paths — adding a new sport/band's audit log is a one-line registry entry,
not a new writer.
"""

from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any

from prediction_market_bot.c6_audit_logger.audit_logger import (
    SEVERITY_LEVELS,
    AuditLogger,
)

# ---------------------------------------------------------------------------
# Log type registry — path is relative to repo root / cwd, matching every
# existing AuditLogger(...) call site's own convention (LOG_DIR / "....jsonl").
# ---------------------------------------------------------------------------

LOG_TYPE_PATHS: dict[str, str] = {
    "system": os.environ.get("BOT_AUDIT_LOG_PATH", "logs/audit.jsonl"),
    "mlb": "logs/audit_mlb.jsonl",
    "mlb_t4": "logs/audit_mlb_t4.jsonl",
    "mlb_t4_edge_decisions": "logs/audit_mlb_t4_edge_decisions.jsonl",
    "mlb_edge_decisions": "logs/audit_mlb_edge_decisions.jsonl",
}

_REQUIRED_KEYS = frozenset({"component", "event_type"})
_LOG_KWARG_KEYS = frozenset(
    {
        "payload",
        "session_id",
        "snapshot_id",
        "feature_run_id",
        "forecast_id",
        "risk_eval_id",
        "order_id",
        "severity",
    }
)

_registry_lock = threading.Lock()
_loggers: dict[str, AuditLogger] = {}
_write_locks: dict[str, threading.Lock] = {}


class SchemaConformanceError(ValueError):
    """Raised (and converted to a rejected receipt) when payload fails the C6 schema check."""


def _get_logger_and_lock(log_type: str) -> tuple[AuditLogger, threading.Lock]:
    if log_type not in LOG_TYPE_PATHS:
        raise SchemaConformanceError(
            f"unknown log_type {log_type!r}; registered types: {sorted(LOG_TYPE_PATHS)}"
        )
    with _registry_lock:
        logger = _loggers.get(log_type)
        if logger is None:
            logger = AuditLogger(log_path=LOG_TYPE_PATHS[log_type], min_severity="DEBUG")
            _loggers[log_type] = logger
            _write_locks[log_type] = threading.Lock()
        return logger, _write_locks[log_type]


def _check_schema(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise SchemaConformanceError("payload must be a dict")
    missing = _REQUIRED_KEYS - payload.keys()
    if missing:
        raise SchemaConformanceError(f"payload missing required C6 fields: {sorted(missing)}")
    unknown = set(payload.keys()) - _REQUIRED_KEYS - _LOG_KWARG_KEYS
    if unknown:
        raise SchemaConformanceError(f"payload has fields C6 AuditLogger.log() does not accept: {sorted(unknown)}")
    inner_payload = payload.get("payload")
    if inner_payload is not None and not isinstance(inner_payload, dict):
        raise SchemaConformanceError("payload['payload'] must be a dict if present")
    severity = payload.get("severity")
    if severity is not None and severity not in SEVERITY_LEVELS:
        raise SchemaConformanceError(f"payload['severity'] must be one of {SEVERITY_LEVELS}, got {severity!r}")


def append_audit_trail(log_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    """
    Append one structured C6 audit entry to the on-disk log selected by
    log_type. Returns a receipt only — {status, bytes_written} — never the
    entry or log body, per ADR-0041.

    Parameters
    ----------
    log_type:
        Key into LOG_TYPE_PATHS selecting which physical audit log to append to.
    payload:
        Must contain 'component' and 'event_type' (required C6 fields). May
        also contain any of: payload (dict), session_id, snapshot_id,
        feature_run_id, forecast_id, risk_eval_id, order_id, severity.
        This is the same keyword surface as AuditLogger.log() — nothing new
        is invented here.

    Returns
    -------
    dict with keys:
        status: "ok" | "rejected" | "write_failed"
        bytes_written: int (0 unless status == "ok")
        reason: str (present only when status != "ok")
    """
    try:
        _check_schema(payload)
        logger, write_lock = _get_logger_and_lock(log_type)
    except SchemaConformanceError as exc:
        return {"status": "rejected", "bytes_written": 0, "reason": str(exc)}

    path = Path(LOG_TYPE_PATHS[log_type])

    log_kwargs = {k: v for k, v in payload.items() if k in _LOG_KWARG_KEYS}

    # Held for the full before-size / write / after-size sequence so this
    # call's own bytes_written is accurate under concurrent same-process
    # callers targeting the same log_type. AuditLogger.log() has its own
    # internal lock guaranteeing line-level append integrity regardless;
    # this outer lock exists only to make the byte-delta receipt correct,
    # not to re-guard the write itself.
    with write_lock:
        before = path.stat().st_size if path.exists() else 0
        ok = logger.log(
            component=payload["component"],
            event_type=payload["event_type"],
            **log_kwargs,
        )
        if not ok:
            return {"status": "write_failed", "bytes_written": 0, "reason": "AuditLogger.log() returned False"}
        after = path.stat().st_size

    return {"status": "ok", "bytes_written": after - before}
