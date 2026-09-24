"""
Tests for scripts/sweep_stray_branches.sh's new landed-local-branch cleanup +
worktree prune (T-570 Deliverable 4a, 2026-09-23).

These run the REAL script (subprocess) against a synthetic git repo built
fresh under tmp_path -- a bare "origin" plus a working clone -- so no real
repo branch, worktree, or the actual GOVERNANCE_GAP_LOG.md is ever touched.
The pre-existing NOT-LANDED report section (unchanged by this deliverable)
is exercised incidentally as a regression guard, not the focus here.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "scripts" / "sweep_stray_branches.sh"


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    )


def _make_repo(tmp_path: Path) -> Path:
    """Bare 'origin' + a working clone with an initial commit on main, pushed."""
    origin = tmp_path / "origin.git"
    work = tmp_path / "work"
    _git(tmp_path, "init", "--bare", "-b", "main", str(origin))
    _git(tmp_path, "clone", str(origin), str(work))
    _git(work, "config", "user.email", "test@example.com")
    _git(work, "config", "user.name", "Test")
    (work / "f.txt").write_text("initial\n")
    _git(work, "add", "f.txt")
    _git(work, "commit", "-m", "initial")
    _git(work, "push", "origin", "main")
    return work


def _run(work: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        cwd=work,
        capture_output=True,
        text=True,
    )


def test_landed_local_branch_reported_but_not_deleted_by_default(tmp_path):
    work = _make_repo(tmp_path)
    _git(work, "branch", "landed-branch")  # ancestor of main -- fully "landed"

    result = _run(work)

    assert result.returncode == 0
    assert "LANDED, not yet deleted   landed-branch" in result.stdout
    assert "1 landed local branch(es) found" in result.stdout
    branches = _git(work, "branch", "--list", "landed-branch").stdout
    assert "landed-branch" in branches  # untouched


def test_execute_deletes_landed_branch_with_dash_d(tmp_path):
    work = _make_repo(tmp_path)
    _git(work, "branch", "landed-branch")

    result = _run(work, "--execute")

    assert result.returncode == 0
    assert "DELETED (landed, git branch -d)   landed-branch" in result.stdout
    branches = _git(work, "branch", "--list", "landed-branch").stdout
    assert "landed-branch" not in branches


def test_execute_never_force_deletes_unmerged_branch(tmp_path):
    work = _make_repo(tmp_path)
    _git(work, "checkout", "-b", "wip-branch")
    (work / "f.txt").write_text("unmerged change\n")
    _git(work, "commit", "-am", "unmerged work")
    _git(work, "checkout", "main")
    # wip-branch has a commit not reachable from origin/main -- not landed.

    result = _run(work, "--execute")

    assert result.returncode == 0
    # Not an ancestor of origin/main, so it must never appear in the landed
    # cleanup section, and git branch -D must never be invoked on it.
    assert "wip-branch" not in "\n".join(
        line for line in result.stdout.splitlines() if "landed local" in line.lower() or "DELETED" in line
    )
    branches = _git(work, "branch", "--list", "wip-branch").stdout
    assert "wip-branch" in branches  # still present, untouched


def test_currently_checked_out_landed_branch_is_skipped_not_deleted(tmp_path):
    work = _make_repo(tmp_path)
    _git(work, "checkout", "-b", "landed-current")
    _git(work, "push", "origin", "landed-current")
    _git(work, "push", "origin", "landed-current:main")  # fast-forward main to include it
    # Now landed-current == origin/main, and it is the checked-out branch.

    result = _run(work, "--execute")

    assert result.returncode == 0
    assert "SKIP (currently checked out here)   landed-current" in result.stdout
    branches = _git(work, "branch", "--list", "landed-current").stdout
    assert "landed-current" in branches


def test_main_branch_never_offered_for_cleanup(tmp_path):
    work = _make_repo(tmp_path)

    result = _run(work)

    assert "not yet deleted   main" not in result.stdout
    assert "DELETED" not in result.stdout


def test_worktree_prune_section_runs_without_error(tmp_path):
    work = _make_repo(tmp_path)

    result = _run(work)

    assert result.returncode == 0
    assert "=== worktree prune ===" in result.stdout


def test_clean_message_when_no_landed_local_branches(tmp_path):
    work = _make_repo(tmp_path)  # only "main" exists locally

    result = _run(work)

    assert result.returncode == 0
    assert "CLEAN — no landed local branches pending deletion." in result.stdout


def test_default_mode_label_is_report_only_not_execute(tmp_path):
    work = _make_repo(tmp_path)

    result = _run(work)

    assert "landed local branches — cleanup (report-only)" in result.stdout


def test_execute_mode_label_switches_to_execute(tmp_path):
    work = _make_repo(tmp_path)

    result = _run(work, "--execute")

    assert "landed local branches — cleanup (EXECUTE)" in result.stdout


def test_max_age_days_positional_still_works_alongside_execute_flag(tmp_path):
    work = _make_repo(tmp_path)
    _git(work, "branch", "landed-branch")

    result = _run(work, "0", "--execute")

    assert result.returncode == 0
    assert "DELETED (landed, git branch -d)   landed-branch" in result.stdout
