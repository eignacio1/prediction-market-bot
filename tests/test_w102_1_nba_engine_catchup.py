"""W102.1: attempt trace + stale-arm catch-up (known-answer tests, no network, no pandas)."""
import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from prediction_market_bot.nba_engine import attempts as A, catchup as C

NOW = datetime(2026, 11, 5, 0, 0, tzinfo=timezone.utc)


def _arms(tmp_path):
    return {n: ("mod_" + n, tmp_path / n) for n in ("v1", "v2", "v3")}


def _status(d: Path, ts: datetime):
    d.mkdir(parents=True, exist_ok=True)
    (d / "status.json").write_text(json.dumps({"as_of": ts.isoformat()}))


def test_attempt_ok_leaves_no_unfinished(tmp_path):
    with A.attempt("v2", tmp_path):
        pass
    assert [r["event"] for r in A.read_attempts(tmp_path)] == ["start", "end"]
    assert A.unfinished(tmp_path) == []


def test_killed_run_is_a_start_without_end(tmp_path):
    A._append(tmp_path / "attempts.jsonl", dict(event="start", arm="v3", pid=7, ts="t"))   # SIGKILL: no end written
    u = A.unfinished(tmp_path)
    assert len(u) == 1 and u[0]["arm"] == "v3" and u[0]["pid"] == 7


def test_exception_is_recorded_and_propagates(tmp_path):
    with pytest.raises(ValueError):
        with A.attempt("v1", tmp_path):
            raise ValueError("x")
    assert A.read_attempts(tmp_path)[-1]["outcome"] == "error"
    assert A.unfinished(tmp_path) == []


def test_torn_last_line_is_ignored(tmp_path):
    (tmp_path / "attempts.jsonl").write_text('{"event":"start","arm":"v1","pid":1,"ts":"t"}\n{"event":"en')
    assert len(A.read_attempts(tmp_path)) == 1


def test_stale_arms_known_answer(tmp_path):
    arms = _arms(tmp_path)
    _status(tmp_path / "v1", NOW - timedelta(minutes=3))      # fresh
    _status(tmp_path / "v2", NOW - timedelta(minutes=13))     # stale (> 12)
    # v3 has no status at all -> stale
    assert C.stale_arms(NOW, arms) == ["v2", "v3"]


def test_fresh_everywhere_spawns_nothing(tmp_path, monkeypatch):
    arms = _arms(tmp_path)
    for n in arms:
        _status(tmp_path / n, NOW - timedelta(minutes=1))
    monkeypatch.setattr(C, "ARMS", arms)
    calls = []
    assert C.main([], now=NOW, spawn=lambda m, r: calls.append(m) or 0) == 0
    assert calls == []


def test_killed_arm_is_retried_once_and_traced(tmp_path):
    arms = _arms(tmp_path)
    rcs = iter([-9, 0])
    out = C.run_arm("v2", "raw", arms=arms, spawn=lambda m, r: next(rcs))
    assert out == "ok_after_retry"
    ends = [r for r in A.read_attempts(tmp_path / "v2") if r["event"] == "end"]
    assert [e["returncode"] for e in ends] == [-9, 0]


def test_normal_error_exit_is_not_retried(tmp_path):
    arms = _arms(tmp_path)
    n = []
    out = C.run_arm("v3", "raw", arms=arms, spawn=lambda m, r: n.append(1) or 1)
    assert out == "error" and len(n) == 1


def test_two_kills_end_killed(tmp_path):
    arms = _arms(tmp_path)
    assert C.run_arm("v1", "raw", arms=arms, spawn=lambda m, r: -9) == "killed"


def test_timeout_counts_as_killed(tmp_path):
    arms = _arms(tmp_path)

    def boom(m, r):
        raise subprocess.TimeoutExpired("x", 1)
    assert C.run_arm("v1", "raw", arms=arms, spawn=boom) == "killed"
