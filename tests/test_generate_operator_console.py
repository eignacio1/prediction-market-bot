"""
Tests for scripts/generate_operator_console.py's Section 0 "Overdue for
retirement" additions (T-570, 2026-09-23): the resolved-class-first
classify() change, and the four new rollup helpers. All git/filesystem state
is synthetic (tmp_path) -- never the real repo's GOVERNANCE_GAP_LOG.md,
SESSION_CLAIMS.md, APPROVALS_REGISTER.md, or any real branch/worktree.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import generate_operator_console as goc  # noqa: E402


# ---------------------------------------------------------------------------
# classify() -- resolved-class must win over blocked/broken/accruing
# ---------------------------------------------------------------------------

def _entry(token, block=""):
    return {"id": "GG-1", "title": "t", "token": token, "severity": "LOW", "block": block}


class TestClassifyResolvedClassFirst:
    def test_resolved_routes_to_retirement_debt_even_with_blocked_field(self):
        e = _entry("RESOLVED", "**Blocked-On-Operator:** YES\n")
        assert goc.classify(e) == "retirement_debt"

    def test_closed_as_artifact_routes_to_retirement_debt(self):
        e = _entry("CLOSED-AS-ARTIFACT")
        assert goc.classify(e) == "retirement_debt"

    def test_stay_token_partially_resolved_does_not_route_to_retirement_debt(self):
        e = _entry("PARTIALLY RESOLVED")
        assert goc.classify(e) != "retirement_debt"

    def test_open_with_blocked_field_still_routes_to_blocked(self):
        e = _entry("OPEN", "**Blocked-On-Operator:** YES\n")
        assert goc.classify(e) == "blocked"

    def test_open_with_broken_field_routes_to_broken(self):
        e = _entry("OPEN", "**Actively-Broken:** YES\n")
        assert goc.classify(e) == "broken"

    def test_open_with_no_field_routes_to_accruing(self):
        e = _entry("OPEN")
        assert goc.classify(e) == "accruing"


# ---------------------------------------------------------------------------
# merged_undeleted_branches() -- mirrors sweep_stray_branches.sh's landed logic
# ---------------------------------------------------------------------------

def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    )


def _make_repo(tmp_path: Path) -> Path:
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


class TestMergedUndeletedBranches:
    def test_landed_branch_is_reported(self, tmp_path, monkeypatch):
        work = _make_repo(tmp_path)
        _git(work, "branch", "landed-branch")
        monkeypatch.chdir(work)

        assert goc.merged_undeleted_branches() == ["landed-branch"]

    def test_unmerged_branch_is_not_reported(self, tmp_path, monkeypatch):
        work = _make_repo(tmp_path)
        _git(work, "checkout", "-b", "wip-branch")
        (work / "f.txt").write_text("unmerged\n")
        _git(work, "commit", "-am", "wip")
        _git(work, "checkout", "main")
        monkeypatch.chdir(work)

        assert goc.merged_undeleted_branches() == []

    def test_main_is_never_reported(self, tmp_path, monkeypatch):
        work = _make_repo(tmp_path)
        monkeypatch.chdir(work)

        assert goc.merged_undeleted_branches() == []

    def test_currently_checked_out_landed_branch_is_excluded(self, tmp_path, monkeypatch):
        work = _make_repo(tmp_path)
        _git(work, "checkout", "-b", "landed-current")
        _git(work, "push", "origin", "landed-current")
        _git(work, "push", "origin", "landed-current:main")
        monkeypatch.chdir(work)

        assert goc.merged_undeleted_branches() == []


class TestPrunableWorktrees:
    def test_returns_list_without_crashing_on_clean_repo(self, tmp_path, monkeypatch):
        work = _make_repo(tmp_path)
        monkeypatch.chdir(work)

        assert goc.prunable_worktrees() == []

    def test_never_calls_prune_without_dash_n(self, tmp_path, monkeypatch):
        calls = []
        real_git = goc._git

        def spy(*args):
            calls.append(args)
            return real_git(*args)

        monkeypatch.setattr(goc, "_git", spy)
        work = _make_repo(tmp_path)
        monkeypatch.chdir(work)

        goc.prunable_worktrees()
        prune_calls = [c for c in calls if c[:1] == ("worktree",)]
        assert prune_calls
        assert all("-n" in c for c in prune_calls)


# ---------------------------------------------------------------------------
# accepted_without_register_row() -- thin filter over check_register_parity
# ---------------------------------------------------------------------------

class TestAcceptedWithoutRegisterRow:
    def test_no_register_file_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(goc._crp, "REGISTER", tmp_path / "nope.md")
        assert goc.accepted_without_register_row() == []

    def test_filters_to_no_row_findings_only(self, monkeypatch):
        monkeypatch.setattr(goc._crp, "REGISTER", Path(__file__))  # any existing path
        monkeypatch.setattr(
            goc._crp,
            "collect_findings",
            lambda: (
                [
                    "ADR-0001: no APPROVALS_REGISTER.md row at all (doc status: x)",
                    "ADR-0002: doc says resolved but register row still reads PENDING",
                    "ADR-0003: resolved and mentioned in APPROVALS_REGISTER.md, but has no OWN dedicated row (x)",
                ],
                3,
            ),
        )
        out = goc.accepted_without_register_row()
        assert len(out) == 2
        assert any("ADR-0001" in f for f in out)
        assert any("ADR-0003" in f for f in out)
        assert not any("ADR-0002" in f for f in out)


# ---------------------------------------------------------------------------
# unclosed_session_claims()
# ---------------------------------------------------------------------------

class TestUnclosedSessionClaims:
    def test_missing_file_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(goc, "CLAIMS", tmp_path / "nope.md")
        assert goc.unclosed_session_claims() == []

    def test_claim_without_closed_row_is_unclosed(self, tmp_path, monkeypatch):
        claims = tmp_path / "SESSION_CLAIMS.md"
        claims.write_text(
            "| ts | T/GG | note |\n"
            "|---|---|---|\n"
            "| 2026-09-23T00:00:00Z | T-570 | retirement mechanism |\n"
        )
        monkeypatch.setattr(goc, "CLAIMS", claims)
        assert goc.unclosed_session_claims() == ["T-570"]

    def test_claim_with_closed_row_is_excluded(self, tmp_path, monkeypatch):
        claims = tmp_path / "SESSION_CLAIMS.md"
        claims.write_text(
            "| ts | T/GG | note |\n"
            "|---|---|---|\n"
            "| 2026-09-01T00:00:00Z | T-563 | some work |\n"
            "| 2026-09-02T00:00:00Z | T-563 | CLOSED — merge confirmed |\n"
        )
        monkeypatch.setattr(goc, "CLAIMS", claims)
        assert goc.unclosed_session_claims() == []

    def test_parked_row_is_still_unclosed(self, tmp_path, monkeypatch):
        claims = tmp_path / "SESSION_CLAIMS.md"
        claims.write_text(
            "| ts | T/GG | note |\n"
            "|---|---|---|\n"
            "| 2026-09-01T00:00:00Z | T-569 | some work |\n"
            "| 2026-09-02T00:00:00Z | T-569 | PARKED (awaiting review) |\n"
        )
        monkeypatch.setattr(goc, "CLAIMS", claims)
        assert goc.unclosed_session_claims() == ["T-569"]

    def test_results_sorted_numerically(self, tmp_path, monkeypatch):
        claims = tmp_path / "SESSION_CLAIMS.md"
        claims.write_text(
            "| ts | T/GG | note |\n"
            "|---|---|---|\n"
            "| 2026-09-01T00:00:00Z | T-600 | x |\n"
            "| 2026-09-02T00:00:00Z | T-50 | y |\n"
        )
        monkeypatch.setattr(goc, "CLAIMS", claims)
        assert goc.unclosed_session_claims() == ["T-50", "T-600"]


# ---------------------------------------------------------------------------
# shared_tree_behind_origin() -- shared main-tree checkout drift vs origin/main
# ---------------------------------------------------------------------------

class TestSharedTreeBehindOrigin:
    def test_up_to_date_tree_reports_zero(self, tmp_path, monkeypatch):
        work = _make_repo(tmp_path)
        monkeypatch.chdir(work)
        result = goc.shared_tree_behind_origin()
        assert result is not None
        assert result["behind"] == 0

    def test_behind_tree_reports_correct_count(self, tmp_path, monkeypatch):
        work = _make_repo(tmp_path)
        origin = tmp_path / "origin.git"
        other = tmp_path / "other"
        _git(tmp_path, "clone", str(origin), str(other))
        _git(other, "config", "user.email", "test@example.com")
        _git(other, "config", "user.name", "Test")
        for i in range(3):
            (other / "f.txt").write_text(f"b{i}\n")
            _git(other, "commit", "-am", f"c{i}")
        _git(other, "push", "origin", "main")
        monkeypatch.chdir(work)
        result = goc.shared_tree_behind_origin()
        assert result is not None
        assert result["behind"] == 3

    def test_never_writes_anything_to_the_tree(self, tmp_path, monkeypatch):
        work = _make_repo(tmp_path)
        monkeypatch.chdir(work)
        before = _git(work, "status", "--porcelain").stdout
        goc.shared_tree_behind_origin()
        after = _git(work, "status", "--porcelain").stdout
        assert before == after == ""


# ---------------------------------------------------------------------------
# closed_wave_fences() -- pasteable fences left under a CLOSED wave header
# ---------------------------------------------------------------------------

class TestClosedWaveFences:
    def test_missing_file_returns_empty(self, tmp_path):
        assert goc.closed_wave_fences(tmp_path / "nope.md") == []

    def test_closed_wave_with_leftover_fence_is_reported(self, tmp_path):
        q = tmp_path / "ACTIVE_QUEUE.md"
        q.write_text(
            "## Sequencing track\n\n"
            "| **33** | CLOSED |\n\n"
            "## Wave 33 block\n\n"
            "```\nsome leftover block\n```\n"
        )
        findings = goc.closed_wave_fences(q)
        assert len(findings) == 1
        assert "Wave 33" in findings[0]

    def test_open_wave_with_fence_is_not_reported(self, tmp_path):
        q = tmp_path / "ACTIVE_QUEUE.md"
        q.write_text(
            "## Sequencing track\n\n"
            "| **36** | ACTIVE |\n\n"
            "## Wave 36 block\n\n"
            "```\nstill relevant\n```\n"
        )
        assert goc.closed_wave_fences(q) == []

    def test_closed_wave_with_no_fence_is_not_reported(self, tmp_path):
        q = tmp_path / "ACTIVE_QUEUE.md"
        q.write_text(
            "## Sequencing track\n\n"
            "| **33** | CLOSED |\n\n"
            "## Wave 33 block\n\n"
            "no fences here\n"
        )
        assert goc.closed_wave_fences(q) == []
