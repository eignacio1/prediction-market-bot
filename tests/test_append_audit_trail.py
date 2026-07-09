"""Tests for scripts/append_audit_trail.py — T-300 (A2), ADR-0041.

Covers: append correctness (structural equivalence to a hand-written
AuditLogger.log() entry for the same event, per the A2 gate), the
schema-rejection path, and concurrent-append safety (many threads
appending through the same log_type produce exactly that many valid,
uncorrupted JSON lines with an accurate total byte count).
"""
from __future__ import annotations

import json
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import append_audit_trail as aat
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger


@pytest.fixture(autouse=True)
def _reset_registry(tmp_path, monkeypatch):
    """Point every log_type at an isolated tmp file and clear cached loggers."""
    for key in list(aat.LOG_TYPE_PATHS):
        monkeypatch.setitem(aat.LOG_TYPE_PATHS, key, str(tmp_path / f"{key}.jsonl"))
    aat._loggers.clear()
    aat._write_locks.clear()
    yield
    aat._loggers.clear()
    aat._write_locks.clear()


def _read_lines(path: Path) -> list[dict]:
    with path.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


# ── append correctness ───────────────────────────────────────────────────────


def test_append_returns_receipt_only():
    result = aat.append_audit_trail(
        "system", {"component": "C6", "event_type": "test_event", "payload": {"k": "v"}}
    )
    assert set(result.keys()) == {"status", "bytes_written"}
    assert result["status"] == "ok"
    assert result["bytes_written"] > 0


def test_append_writes_structurally_identical_entry_to_hand_written_logger():
    """Gate: output byte-identical in structure to a hand-written log entry
    for the same event — i.e. the same field set, same values for the
    fields under the caller's control, modulo the two fields (timestamp,
    event_id) that AuditLogger itself generates per-call and can never be
    equal across two separate calls by construction."""
    path = Path(aat.LOG_TYPE_PATHS["mlb"])

    aat.append_audit_trail(
        "mlb",
        {
            "component": "C4",
            "event_type": "risk_eval_pass",
            "payload": {"edge": 0.05},
            "session_id": "SESSION-TEST",
            "severity": "INFO",
        },
    )
    via_tool = _read_lines(path)[0]

    hand_logger = AuditLogger(log_path=path, min_severity="DEBUG")
    hand_logger.log(
        component="C4",
        event_type="risk_eval_pass",
        payload={"edge": 0.05},
        session_id="SESSION-TEST",
        severity="INFO",
    )
    via_hand = _read_lines(path)[1]

    assert via_tool.keys() == via_hand.keys()
    for key in via_tool:
        if key in ("timestamp", "event_id"):
            continue
        assert via_tool[key] == via_hand[key], key


def test_append_routes_to_correct_log_type_path():
    aat.append_audit_trail("mlb_t4", {"component": "C6", "event_type": "t4_cycle"})
    aat.append_audit_trail("system", {"component": "C6", "event_type": "system_event"})

    t4_path = Path(aat.LOG_TYPE_PATHS["mlb_t4"])
    system_path = Path(aat.LOG_TYPE_PATHS["system"])

    assert len(_read_lines(t4_path)) == 1
    assert _read_lines(t4_path)[0]["event_type"] == "t4_cycle"
    assert len(_read_lines(system_path)) == 1
    assert _read_lines(system_path)[0]["event_type"] == "system_event"


def test_bytes_written_matches_actual_line_length():
    path = Path(aat.LOG_TYPE_PATHS["system"])
    result = aat.append_audit_trail("system", {"component": "C6", "event_type": "sized_event"})
    assert result["bytes_written"] == path.stat().st_size


# ── schema rejection path ────────────────────────────────────────────────────


def test_rejects_missing_component():
    result = aat.append_audit_trail("system", {"event_type": "no_component"})
    assert result["status"] == "rejected"
    assert result["bytes_written"] == 0
    assert "component" in result["reason"]


def test_rejects_missing_event_type():
    result = aat.append_audit_trail("system", {"component": "C6"})
    assert result["status"] == "rejected"
    assert "event_type" in result["reason"]


def test_rejects_unknown_log_type():
    result = aat.append_audit_trail("nba_t4_does_not_exist", {"component": "C6", "event_type": "x"})
    assert result["status"] == "rejected"
    assert "log_type" in result["reason"]


def test_rejects_field_not_accepted_by_c6_schema():
    result = aat.append_audit_trail(
        "system", {"component": "C6", "event_type": "x", "api_key": "sk-live-secret"}
    )
    assert result["status"] == "rejected"
    assert "api_key" in result["reason"]


def test_rejects_non_dict_inner_payload():
    result = aat.append_audit_trail(
        "system", {"component": "C6", "event_type": "x", "payload": "not-a-dict"}
    )
    assert result["status"] == "rejected"


def test_rejects_invalid_severity():
    result = aat.append_audit_trail(
        "system", {"component": "C6", "event_type": "x", "severity": "CATASTROPHIC"}
    )
    assert result["status"] == "rejected"
    assert "severity" in result["reason"]


def test_rejected_call_does_not_touch_disk():
    path = Path(aat.LOG_TYPE_PATHS["system"])
    aat.append_audit_trail("system", {"event_type": "missing_component"})
    assert not path.exists()


# ── concurrent-append safety ─────────────────────────────────────────────────


def test_concurrent_appends_produce_exactly_n_valid_lines():
    path = Path(aat.LOG_TYPE_PATHS["mlb_t4"])
    n_threads = 40
    results: list[dict] = [None] * n_threads  # type: ignore[list-item]

    def _worker(i: int) -> None:
        results[i] = aat.append_audit_trail(
            "mlb_t4", {"component": "C6", "event_type": "concurrent_test", "payload": {"i": i}}
        )

    threads = [threading.Thread(target=_worker, args=(i,)) for i in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert all(r["status"] == "ok" for r in results)

    lines = _read_lines(path)
    assert len(lines) == n_threads
    seen_is = sorted(line["payload"]["i"] for line in lines)
    assert seen_is == list(range(n_threads))

    total_bytes_claimed = sum(r["bytes_written"] for r in results)
    assert total_bytes_claimed == path.stat().st_size


def test_concurrent_appends_across_log_types_do_not_interfere():
    n_per_type = 15
    log_types = ["system", "mlb", "mlb_t4"]
    results: dict[str, list[dict]] = {lt: [] for lt in log_types}
    lock = threading.Lock()

    def _worker(log_type: str, i: int) -> None:
        r = aat.append_audit_trail(log_type, {"component": "C6", "event_type": "x", "payload": {"i": i}})
        with lock:
            results[log_type].append(r)

    threads = [
        threading.Thread(target=_worker, args=(lt, i))
        for lt in log_types
        for i in range(n_per_type)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    for lt in log_types:
        path = Path(aat.LOG_TYPE_PATHS[lt])
        assert len(_read_lines(path)) == n_per_type
        assert all(r["status"] == "ok" for r in results[lt])
