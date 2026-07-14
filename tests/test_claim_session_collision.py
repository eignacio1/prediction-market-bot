"""Tests for scripts/lib/check_id_collision.sh — GG-107 root-cause fix (T-355).

check_id_collision() is a pure/offline bash function (no git network calls),
sourced by claim_session.sh before it appends a new SESSION_CLAIMS.md row.
These tests source the lib directly against synthetic registry files in a
tmp dir, so the collision check is exercised without touching a live remote.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

LIB = Path(__file__).parent.parent / "scripts" / "lib" / "check_id_collision.sh"


def _make_registries(tmp_path: Path, todo_next: str = "", session_claims: str = "", decision_log: str = "") -> None:
    execution = tmp_path / "04_EXECUTION"
    execution.mkdir(parents=True, exist_ok=True)
    (execution / "TODO_NEXT.md").write_text(todo_next)
    (execution / "SESSION_CLAIMS.md").write_text(session_claims)

    decisions = tmp_path / "03_DECISIONS" / "DECISION_LOG"
    decisions.mkdir(parents=True, exist_ok=True)
    (decisions / "DECISION_LOG.md").write_text(decision_log)


def _run_check(tmp_path: Path, range_str: str) -> subprocess.CompletedProcess:
    script = f'''
set -euo pipefail
source "{LIB}"
check_id_collision "{range_str}" "{tmp_path}"
'''
    return subprocess.run(
        ["bash", "-c", script], capture_output=True, text=True, timeout=10
    )


def test_rejects_id_already_registered_in_todo_next(tmp_path):
    _make_registries(tmp_path, todo_next="## T-352 — SECRETS_HANDLING.md rotation cadence — OPEN\n")

    result = _run_check(tmp_path, "T-352")

    assert result.returncode != 0
    assert "COLLISION: T-352" in result.stderr
    assert "TODO_NEXT.md" in result.stderr


def test_rejects_id_already_claimed_in_session_claims(tmp_path):
    _make_registries(
        tmp_path,
        session_claims="| 2026-07-12T17:19:01Z | GG-116, T-351, T-352, T-353 | Window 3 close-out audit |\n",
    )

    result = _run_check(tmp_path, "T-353")

    assert result.returncode != 0
    assert "COLLISION: T-353" in result.stderr
    assert "SESSION_CLAIMS.md" in result.stderr


def test_rejects_id_referenced_in_decision_log(tmp_path):
    _make_registries(tmp_path, decision_log="| 2026-07-12 | GG-107 | ... |\n")

    result = _run_check(tmp_path, "GG-107")

    assert result.returncode != 0
    assert "COLLISION: GG-107" in result.stderr
    assert "DECISION_LOG.md" in result.stderr


def test_allows_fresh_unused_id(tmp_path):
    _make_registries(
        tmp_path,
        todo_next="## T-100 — unrelated, already-complete task\n",
        session_claims="| 2026-07-01T00:00:00Z | T-100 | old unrelated claim |\n",
    )

    result = _run_check(tmp_path, "T-9001")

    assert result.returncode == 0
    assert result.stderr == ""


def test_no_ids_in_range_is_a_noop_pass(tmp_path):
    _make_registries(tmp_path, todo_next="## T-100 — something\n")

    result = _run_check(tmp_path, "TBD")

    assert result.returncode == 0


def test_partial_id_does_not_false_positive(tmp_path):
    # T-3520 must not collide with a claim for T-352 (substring, not exact token).
    _make_registries(tmp_path, todo_next="## T-352 — SECRETS_HANDLING.md rotation cadence — OPEN\n")

    result = _run_check(tmp_path, "T-3520")

    assert result.returncode == 0
    assert result.stderr == ""


def test_rejects_taken_id_matching_this_session_own_t354_t355_claim(tmp_path):
    # Regression check mirroring the real event this session hit: T-354/T-355
    # were claimed earlier this session (SESSION_CLAIMS.md row below), so a
    # second attempt to claim either must be rejected.
    _make_registries(
        tmp_path,
        session_claims=(
            "| 2026-07-14T04:32:23Z | T-354,T-355,GG-107 | UNWIND_PLAN Window B: "
            "T-354 prune crash-residue branches/worktrees, T-355 fix claim_session.sh "
            "ID-collision root cause (GG-107) |\n"
        ),
    )

    result = _run_check(tmp_path, "T-354,T-355")

    assert result.returncode != 0
    assert "COLLISION: T-354" in result.stderr
    assert "COLLISION: T-355" in result.stderr
