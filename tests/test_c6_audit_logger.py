"""
Tests for src/prediction_market_bot/c6_audit_logger/audit_logger.py

Coverage areas:
  - AuditLogger.__init__: creates parent directories; rejects invalid min_severity
  - AuditLogger.log: writes valid JSONL; returns True on success; returns False on IOError
  - Severity filtering: events below min_severity threshold are silently dropped (True)
  - Payload redaction: api_key, password, token, secret → [REDACTED]
  - Traceability chain: chain_warning inserted when all anchors absent on non-DEBUG
  - Convenience wrappers: info, warning, error, critical, debug delegate correctly
  - AuditLogger.from_env: reads BOT_AUDIT_LOG_PATH and BOT_ENV
  - Thread safety: multiple concurrent writes all succeed
  - JSONL format: each line is valid JSON with required top-level fields
"""

from __future__ import annotations

import json
import sys
import threading
from pathlib import Path
from unittest.mock import patch

import pytest

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from prediction_market_bot.c6_audit_logger.audit_logger import (
    AUDIT_LOG_ENV_VAR,
    AuditLogger,
    _redact_payload,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_REQUIRED_LOG_FIELDS = {
    "timestamp", "event_id", "component", "event_type", "severity",
    "session_id", "snapshot_id", "feature_run_id", "forecast_id",
    "risk_eval_id", "order_id", "payload",
}


def _read_jsonl(path: Path) -> list[dict]:
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestAuditLoggerInit:
    @pytest.mark.unit
    def test_creates_parent_directory(self, tmp_path):
        log_path = tmp_path / "subdir" / "nested" / "audit.jsonl"
        logger = AuditLogger(log_path=log_path)
        assert log_path.parent.exists()

    @pytest.mark.unit
    def test_invalid_min_severity_raises(self, tmp_path):
        with pytest.raises(ValueError, match="min_severity"):
            AuditLogger(log_path=tmp_path / "audit.jsonl", min_severity="INVALID")

    @pytest.mark.unit
    def test_valid_min_severities_accepted(self, tmp_path):
        for sev in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            logger = AuditLogger(log_path=tmp_path / f"audit_{sev}.jsonl", min_severity=sev)
            assert logger is not None


# ---------------------------------------------------------------------------
# Basic write
# ---------------------------------------------------------------------------


class TestAuditLoggerWrite:
    @pytest.mark.unit
    def test_log_returns_true_on_success(self, tmp_path):
        logger = AuditLogger(tmp_path / "audit.jsonl")
        result = logger.log("C1", "test_event", {"key": "value"}, session_id="SID-001")
        assert result is True

    @pytest.mark.unit
    def test_log_writes_valid_jsonl(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path)
        logger.log("C2", "feature_computed", {"rows": 100}, session_id="SID-001")
        entries = _read_jsonl(log_path)
        assert len(entries) == 1
        assert entries[0]["component"] == "C2"
        assert entries[0]["event_type"] == "feature_computed"

    @pytest.mark.unit
    def test_log_contains_all_required_fields(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path)
        logger.log("C3", "forecast_emitted", {}, snapshot_id="SNAP-TEST")
        entries = _read_jsonl(log_path)
        for field in _REQUIRED_LOG_FIELDS:
            assert field in entries[0], f"Field '{field}' missing from log entry"

    @pytest.mark.unit
    def test_log_appends_multiple_entries(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path)
        for i in range(5):
            logger.log("C1", f"event_{i}", {}, session_id="SID-001")
        entries = _read_jsonl(log_path)
        assert len(entries) == 5

    @pytest.mark.unit
    def test_log_preserves_session_id(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path)
        logger.log("C4", "risk_eval", {}, session_id="SID-XYZ")
        entry = _read_jsonl(log_path)[0]
        assert entry["session_id"] == "SID-XYZ"

    @pytest.mark.unit
    def test_log_preserves_snapshot_id(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path)
        logger.log("C2", "feature_run", {}, snapshot_id="SNAP-2026-05-27-001")
        entry = _read_jsonl(log_path)[0]
        assert entry["snapshot_id"] == "SNAP-2026-05-27-001"

    @pytest.mark.unit
    def test_log_severity_stored_correctly(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path)
        logger.log("C1", "evt", {}, severity="WARNING", session_id="S1")
        entry = _read_jsonl(log_path)[0]
        assert entry["severity"] == "WARNING"

    @pytest.mark.unit
    def test_log_event_id_is_unique(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path)
        for _ in range(10):
            logger.log("C1", "evt", {}, session_id="S1")
        entries = _read_jsonl(log_path)
        event_ids = [e["event_id"] for e in entries]
        assert len(set(event_ids)) == 10, "event_ids must all be unique"

    @pytest.mark.unit
    def test_log_unknown_severity_coerced_to_error(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path)
        # Unknown severity should be treated as ERROR, not raise
        result = logger.log("C1", "evt", {}, severity="BOGUS", session_id="S1")
        assert result is True
        entry = _read_jsonl(log_path)[0]
        assert entry["severity"] == "ERROR"


# ---------------------------------------------------------------------------
# Write failure → returns False
# ---------------------------------------------------------------------------


class TestWriteFailure:
    @pytest.mark.unit
    def test_ioerror_returns_false(self, tmp_path):
        logger = AuditLogger(tmp_path / "audit.jsonl")
        with patch(
            "prediction_market_bot.c6_audit_logger.audit_logger.jsonlines.open",
            side_effect=IOError("disk full"),
        ):
            result = logger.log("C1", "test_event", {}, session_id="S1")
        assert result is False

    @pytest.mark.unit
    def test_permission_error_returns_false(self, tmp_path):
        logger = AuditLogger(tmp_path / "audit.jsonl")
        with patch(
            "prediction_market_bot.c6_audit_logger.audit_logger.jsonlines.open",
            side_effect=PermissionError("access denied"),
        ):
            result = logger.log("C1", "test_event", {}, session_id="S1")
        assert result is False

    @pytest.mark.unit
    def test_write_failure_prints_to_stderr(self, tmp_path, capsys):
        logger = AuditLogger(tmp_path / "audit.jsonl")
        with patch(
            "prediction_market_bot.c6_audit_logger.audit_logger.jsonlines.open",
            side_effect=IOError("no space"),
        ):
            logger.log("C1", "test_event", {}, session_id="S1")
        captured = capsys.readouterr()
        assert "AUDIT LOGGER WRITE FAILURE" in captured.err


# ---------------------------------------------------------------------------
# Severity filtering
# ---------------------------------------------------------------------------


class TestSeverityFiltering:
    @pytest.mark.unit
    def test_debug_filtered_at_info_threshold(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path, min_severity="INFO")
        result = logger.log("C1", "debug_event", {}, severity="DEBUG", session_id="S1")
        # Filtered events return True (not a write failure)
        assert result is True
        # File should have no entries
        if log_path.exists():
            entries = _read_jsonl(log_path)
            assert len(entries) == 0

    @pytest.mark.unit
    def test_info_passes_at_info_threshold(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path, min_severity="INFO")
        logger.log("C1", "info_event", {}, severity="INFO", session_id="S1")
        entries = _read_jsonl(log_path)
        assert len(entries) == 1

    @pytest.mark.unit
    def test_warning_filtered_at_error_threshold(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path, min_severity="ERROR")
        result = logger.log("C1", "warn_event", {}, severity="WARNING", session_id="S1")
        assert result is True
        if log_path.exists():
            entries = _read_jsonl(log_path)
            assert len(entries) == 0

    @pytest.mark.unit
    def test_critical_always_passes(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path, min_severity="CRITICAL")
        logger.log("C1", "crit_event", {}, severity="CRITICAL", session_id="S1")
        entries = _read_jsonl(log_path)
        assert len(entries) == 1


# ---------------------------------------------------------------------------
# Payload redaction
# ---------------------------------------------------------------------------


class TestPayloadRedaction:
    @pytest.mark.unit
    def test_api_key_redacted(self):
        result = _redact_payload({"api_key": "sk-secret123", "rows": 10})
        assert result["api_key"] == "[REDACTED]"
        assert result["rows"] == 10

    @pytest.mark.unit
    def test_password_redacted(self):
        result = _redact_payload({"password": "hunter2"})
        assert result["password"] == "[REDACTED]"

    @pytest.mark.unit
    def test_token_redacted(self):
        result = _redact_payload({"token": "abc123"})
        assert result["token"] == "[REDACTED]"

    @pytest.mark.unit
    def test_nested_secret_redacted(self):
        result = _redact_payload({"config": {"api_secret": "xyz", "timeout": 30}})
        assert result["config"]["api_secret"] == "[REDACTED]"
        assert result["config"]["timeout"] == 30

    @pytest.mark.unit
    def test_case_insensitive_redaction(self):
        result = _redact_payload({"API_KEY": "exposed"})
        assert result["API_KEY"] == "[REDACTED]"

    @pytest.mark.unit
    def test_non_sensitive_keys_preserved(self):
        result = _redact_payload({"player_id": 2544, "rows": 100})
        assert result["player_id"] == 2544
        assert result["rows"] == 100

    @pytest.mark.unit
    def test_redacted_payload_in_log(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path)
        logger.log("C1", "evt", {"api_key": "secret", "rows": 5}, session_id="S1")
        entry = _read_jsonl(log_path)[0]
        assert entry["payload"]["api_key"] == "[REDACTED]"
        assert entry["payload"]["rows"] == 5


# ---------------------------------------------------------------------------
# Traceability chain warning
# ---------------------------------------------------------------------------


class TestTraceabilityChain:
    @pytest.mark.unit
    def test_chain_warning_when_no_anchors(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path)
        # Non-DEBUG event with no chain anchors → warning inserted
        logger.log("C1", "orphaned_event", {}, severity="INFO")
        entry = _read_jsonl(log_path)[0]
        assert "_chain_warning" in entry

    @pytest.mark.unit
    def test_no_chain_warning_with_session_id(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path)
        logger.log("C1", "ok_event", {}, session_id="SID-001", severity="INFO")
        entry = _read_jsonl(log_path)[0]
        assert "_chain_warning" not in entry

    @pytest.mark.unit
    def test_no_chain_warning_for_debug(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path, min_severity="DEBUG")
        logger.log("C1", "debug_evt", {}, severity="DEBUG")
        entry = _read_jsonl(log_path)[0]
        assert "_chain_warning" not in entry


# ---------------------------------------------------------------------------
# Convenience wrappers
# ---------------------------------------------------------------------------


class TestConvenienceWrappers:
    @pytest.mark.unit
    def test_info_writes_info_severity(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path)
        result = logger.info("C1", "info_evt", {}, session_id="S1")
        assert result is True
        entry = _read_jsonl(log_path)[0]
        assert entry["severity"] == "INFO"

    @pytest.mark.unit
    def test_warning_writes_warning_severity(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path)
        logger.warning("C2", "warn_evt", {}, session_id="S1")
        entry = _read_jsonl(log_path)[0]
        assert entry["severity"] == "WARNING"

    @pytest.mark.unit
    def test_error_writes_error_severity(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path)
        logger.error("C3", "err_evt", {}, session_id="S1")
        entry = _read_jsonl(log_path)[0]
        assert entry["severity"] == "ERROR"

    @pytest.mark.unit
    def test_critical_writes_critical_severity(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path)
        logger.critical("C4", "crit_evt", {}, session_id="S1")
        entry = _read_jsonl(log_path)[0]
        assert entry["severity"] == "CRITICAL"

    @pytest.mark.unit
    def test_debug_filtered_at_info_threshold_via_wrapper(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path, min_severity="INFO")
        result = logger.debug("C1", "dbg_evt", {}, session_id="S1")
        assert result is True
        if log_path.exists():
            entries = _read_jsonl(log_path)
            assert len(entries) == 0


# ---------------------------------------------------------------------------
# from_env factory
# ---------------------------------------------------------------------------


class TestFromEnv:
    @pytest.mark.unit
    def test_from_env_uses_audit_log_path(self, tmp_path, monkeypatch):
        log_path = str(tmp_path / "env_audit.jsonl")
        monkeypatch.setenv(AUDIT_LOG_ENV_VAR, log_path)
        monkeypatch.setenv("BOT_ENV", "research")
        logger = AuditLogger.from_env()
        assert logger._path == Path(log_path)

    @pytest.mark.unit
    def test_from_env_research_sets_debug(self, tmp_path, monkeypatch):
        monkeypatch.setenv(AUDIT_LOG_ENV_VAR, str(tmp_path / "audit.jsonl"))
        monkeypatch.setenv("BOT_ENV", "research")
        logger = AuditLogger.from_env()
        # Research env → min_severity=DEBUG → DEBUG rank = 0
        from prediction_market_bot.c6_audit_logger.audit_logger import _SEVERITY_RANK
        assert logger._min_rank == _SEVERITY_RANK["DEBUG"]

    @pytest.mark.unit
    def test_from_env_non_research_sets_info(self, tmp_path, monkeypatch):
        monkeypatch.setenv(AUDIT_LOG_ENV_VAR, str(tmp_path / "audit.jsonl"))
        monkeypatch.setenv("BOT_ENV", "staging")
        logger = AuditLogger.from_env()
        from prediction_market_bot.c6_audit_logger.audit_logger import _SEVERITY_RANK
        assert logger._min_rank == _SEVERITY_RANK["INFO"]


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------


class TestThreadSafety:
    @pytest.mark.unit
    def test_concurrent_writes_all_succeed(self, tmp_path):
        log_path = tmp_path / "threaded.jsonl"
        logger = AuditLogger(log_path)
        results = []

        def write_10():
            for i in range(10):
                ok = logger.log("C1", f"evt_{i}", {"i": i}, session_id="THREAD-TEST")
                results.append(ok)

        threads = [threading.Thread(target=write_10) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All 50 writes should succeed
        assert all(results), f"Some writes failed: {results.count(False)} failures"
        entries = _read_jsonl(log_path)
        assert len(entries) == 50
