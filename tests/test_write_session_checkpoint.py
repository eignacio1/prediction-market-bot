"""Tests for scripts/write_session_checkpoint.sh (T-369).

Prior to this script, .last_session_checkpoint was written by a single raw
`git rev-parse` line inline in session-end.md Step 6, with nothing checking
it ran. These tests exercise the wrapper against a synthetic git repo so the
write behavior is verified without touching the real project's checkpoint.

The script resolves its own repo root from its own script location
(SCRIPT_DIR -> `git rev-parse --show-toplevel`), NOT from the caller's cwd —
so invoking the real script path directly against a tmp_path repo would
silently write into *this* repo's real checkpoint file instead of the
synthetic one. To isolate correctly (same pattern as
test_session_guard_checkpoint_staleness.py), each test copies the script
into the synthetic repo under scripts/ and runs that copy.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

REAL_SCRIPT = Path(__file__).parent.parent / "scripts" / "write_session_checkpoint.sh"


def _init_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)

    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(REAL_SCRIPT, scripts_dir / "write_session_checkpoint.sh")

    (tmp_path / "04_EXECUTION").mkdir(parents=True, exist_ok=True)
    (tmp_path / "README.md").write_text("init\n")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)
    return tmp_path


def _run(tmp_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(tmp_path / "scripts" / "write_session_checkpoint.sh")],
        cwd=tmp_path, capture_output=True, text=True, timeout=10,
    )


def test_writes_current_head_short_sha(tmp_path):
    repo = _init_repo(tmp_path)
    expected_sha = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()

    result = _run(repo)

    assert result.returncode == 0
    checkpoint = (repo / "04_EXECUTION" / ".last_session_checkpoint").read_text().strip()
    assert checkpoint == expected_sha
    assert expected_sha in result.stdout


def test_overwrites_stale_prior_checkpoint(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "04_EXECUTION" / ".last_session_checkpoint").write_text("deadbeef\n")

    # Advance HEAD past the stale pointer.
    (repo / "README.md").write_text("second commit\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "second"], cwd=repo, check=True)
    expected_sha = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()

    result = _run(repo)

    assert result.returncode == 0
    checkpoint = (repo / "04_EXECUTION" / ".last_session_checkpoint").read_text().strip()
    assert checkpoint == expected_sha
    assert checkpoint != "deadbeef"


def test_creates_execution_dir_parent_not_required_when_present(tmp_path):
    # 04_EXECUTION already exists from _init_repo; confirm no error if the
    # checkpoint file itself does not pre-exist (first-ever write).
    repo = _init_repo(tmp_path)
    checkpoint_path = repo / "04_EXECUTION" / ".last_session_checkpoint"
    assert not checkpoint_path.exists()

    result = _run(repo)

    assert result.returncode == 0
    assert checkpoint_path.exists()
