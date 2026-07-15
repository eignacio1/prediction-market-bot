"""Tests for session_guard.sh's checkpoint-staleness check (T-369).

session_guard.sh resolves its own repo root from its own script location
(SCRIPT_DIR -> `git rev-parse --show-toplevel`), so to exercise it in
isolation these tests copy the real script into a synthetic git repo under
.claude/hooks/ and run it from there — the copy's REPO_ROOT then resolves to
the synthetic repo, not the real project, with no risk to the real
.last_session_checkpoint or SESSION_CLAIMS.md.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

REAL_SCRIPT = Path(__file__).parent.parent / ".claude" / "hooks" / "session_guard.sh"


def _init_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)

    hooks_dir = tmp_path / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(REAL_SCRIPT, hooks_dir / "session_guard.sh")

    (tmp_path / "04_EXECUTION").mkdir(parents=True, exist_ok=True)
    (tmp_path / "README.md").write_text("init\n")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)
    return tmp_path


def _commit(repo: Path, msg: str) -> str:
    (repo / "README.md").write_text(msg + "\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", msg], cwd=repo, check=True)
    return subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()


def _run_guard(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(repo / ".claude" / "hooks" / "session_guard.sh")],
        cwd=repo, capture_output=True, text=True, timeout=20,
    )


def test_missing_checkpoint_file_warns(tmp_path):
    repo = _init_repo(tmp_path)

    result = _run_guard(repo)

    assert "no checkpoint file at" in result.stdout


def test_fresh_checkpoint_reports_ok(tmp_path):
    repo = _init_repo(tmp_path)
    head_sha = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()
    (repo / "04_EXECUTION" / ".last_session_checkpoint").write_text(head_sha + "\n")

    result = _run_guard(repo)

    assert "OK  checkpoint" in result.stdout
    assert "0 commit(s)" in result.stdout


def test_far_behind_checkpoint_warns_stale(tmp_path):
    repo = _init_repo(tmp_path)
    stale_sha = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()
    (repo / "04_EXECUTION" / ".last_session_checkpoint").write_text(stale_sha + "\n")

    # Advance HEAD 25 commits past the recorded checkpoint (> 20-commit threshold).
    for i in range(25):
        _commit(repo, f"commit {i}")

    result = _run_guard(repo)

    assert "STALE" in result.stdout
    assert "25 commit(s)" in result.stdout


def test_unknown_checkpoint_sha_warns(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "04_EXECUTION" / ".last_session_checkpoint").write_text("0000000\n")

    result = _run_guard(repo)

    assert "not found in this tree's history" in result.stdout
