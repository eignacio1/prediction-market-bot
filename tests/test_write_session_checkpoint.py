"""Tests for scripts/write_session_checkpoint.sh (T-369; format updated GG-103).

Prior to this script, .last_session_checkpoint was written by a single raw
`git rev-parse` line inline in session-end.md Step 6, with nothing checking
it ran. These tests exercise the wrapper against a synthetic git repo so the
write behavior is verified without touching the real project's checkpoint.

GG-103 (2026-07-15) changed the file from a single overwritten SHA to an
append-only log (`checkpoint<TAB>timestamp<TAB>slug` per row, `merge=union`
in `.gitattributes`) so two sessions closing concurrently both survive
instead of one clobbering the other's pointer. The wrapper now APPENDS.

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


def _run(tmp_path: Path, slug: str | None = None) -> subprocess.CompletedProcess:
    cmd = ["bash", str(tmp_path / "scripts" / "write_session_checkpoint.sh")]
    if slug is not None:
        cmd.append(slug)
    return subprocess.run(
        cmd, cwd=tmp_path, capture_output=True, text=True, timeout=10,
    )


def _last_row(repo: Path) -> list[str]:
    lines = (repo / "04_EXECUTION" / ".last_session_checkpoint").read_text().strip().splitlines()
    return lines[-1].split("\t")


def test_appends_current_head_short_sha(tmp_path):
    repo = _init_repo(tmp_path)
    expected_sha = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()

    result = _run(repo)

    assert result.returncode == 0
    sha, ts, slug = _last_row(repo)
    assert sha == expected_sha
    assert slug == "session-end"
    assert expected_sha in result.stdout


def test_appends_without_clobbering_prior_rows(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "04_EXECUTION" / ".last_session_checkpoint").write_text("deadbeef\tunknown\tprior-session\n")

    # Advance HEAD past the prior row.
    (repo / "README.md").write_text("second commit\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "second"], cwd=repo, check=True)
    expected_sha = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()

    result = _run(repo, "my-slug")

    assert result.returncode == 0
    lines = (repo / "04_EXECUTION" / ".last_session_checkpoint").read_text().strip().splitlines()
    assert lines[0] == "deadbeef\tunknown\tprior-session"
    sha, ts, slug = lines[-1].split("\t")
    assert sha == expected_sha
    assert slug == "my-slug"


def test_creates_execution_dir_parent_not_required_when_present(tmp_path):
    # 04_EXECUTION already exists from _init_repo; confirm no error if the
    # checkpoint file itself does not pre-exist (first-ever write).
    repo = _init_repo(tmp_path)
    checkpoint_path = repo / "04_EXECUTION" / ".last_session_checkpoint"
    assert not checkpoint_path.exists()

    result = _run(repo)

    assert result.returncode == 0
    assert checkpoint_path.exists()
