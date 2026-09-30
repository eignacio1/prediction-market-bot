"""T-595 D3 / GG-322: claim_session.sh must re-verify ID uniqueness on every push retry.

Real git, real script: a bare origin, the claimant's clone, and a rival clone. A
pre-push hook in the claimant's clone lands the rival's claim for the SAME id on
origin after the pre-claim check passed but before the push -> the push is rejected,
the retry loop rebases (union-merge keeps both rows) and, before the fix, re-pushed
a duplicate claim.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def sh(cmd, cwd, check=True):
    return subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, env=ENV, check=check, timeout=60)


def _seed(tmp: Path):
    origin, a, rival = tmp / "origin.git", tmp / "a", tmp / "rival"
    sh(f"git init -q --bare -b main {origin}", tmp)
    sh(f"git clone -q {origin} {a}", tmp, check=False)
    (a / "04_EXECUTION").mkdir()
    (a / "04_EXECUTION/SESSION_CLAIMS.md").write_text("| ts | ids | focus |\n|---|---|---|\n")
    (a / ".gitattributes").write_text("04_EXECUTION/SESSION_CLAIMS.md merge=union\n")
    (a / "scripts/lib").mkdir(parents=True)
    shutil.copy(ROOT / "scripts/claim_session.sh", a / "scripts/claim_session.sh")
    shutil.copy(ROOT / "scripts/lib/check_id_collision.sh", a / "scripts/lib/check_id_collision.sh")
    sh("git checkout -q -B main && git add -A && git commit -q -m seed && git push -q origin main", a)
    sh(f"git clone -q {origin} {rival}", tmp)
    return origin, a, rival


def test_retry_after_rejected_push_refuses_id_a_rival_claimed_meanwhile(tmp_path):
    origin, a, rival = _seed(tmp_path)
    # Rival claim, pushed from the hook (first push attempt only).
    (rival / "04_EXECUTION/SESSION_CLAIMS.md").write_text(
        (rival / "04_EXECUTION/SESSION_CLAIMS.md").read_text() + "| 2026-01-01T00:00:00Z | T-900 | rival block |\n")
    sh("git add -A && git commit -q -m rival", rival)
    hook = a / ".git/hooks/pre-push"
    marker = tmp_path / "fired"
    hook.write_text(f"#!/bin/sh\n[ -e {marker} ] && exit 0\ntouch {marker}\ngit -C {rival} push -q {origin} HEAD:main\nexit 0\n")
    hook.chmod(0o755)

    r = sh('bash scripts/claim_session.sh "mine" "T-900"', a, check=False)

    assert marker.exists(), "race was not simulated"
    assert r.returncode != 0, r.stdout + r.stderr
    assert "COLLISION: T-900" in r.stderr
    origin_claims = sh(f"git --git-dir={origin} show main:04_EXECUTION/SESSION_CLAIMS.md", tmp_path).stdout
    assert origin_claims.count("T-900") == 1 and "rival block" in origin_claims and "mine" not in origin_claims
    # our claim was withdrawn locally too: no leftover row, clean tree
    assert "mine" not in (a / "04_EXECUTION/SESSION_CLAIMS.md").read_text()
    assert sh("git status --porcelain", a).stdout.strip() == ""


def test_retry_with_no_conflicting_claim_still_succeeds(tmp_path):
    origin, a, rival = _seed(tmp_path)
    (rival / "04_EXECUTION/SESSION_CLAIMS.md").write_text(
        (rival / "04_EXECUTION/SESSION_CLAIMS.md").read_text() + "| 2026-01-01T00:00:00Z | T-901 | other block |\n")
    sh("git add -A && git commit -q -m rival", rival)
    hook = a / ".git/hooks/pre-push"
    marker = tmp_path / "fired"
    hook.write_text(f"#!/bin/sh\n[ -e {marker} ] && exit 0\ntouch {marker}\ngit -C {rival} push -q {origin} HEAD:main\nexit 0\n")
    hook.chmod(0o755)

    r = sh('bash scripts/claim_session.sh "mine" "T-900"', a, check=False)

    assert r.returncode == 0, r.stdout + r.stderr
    origin_claims = sh(f"git --git-dir={origin} show main:04_EXECUTION/SESSION_CLAIMS.md", tmp_path).stdout
    assert "T-900" in origin_claims and "T-901" in origin_claims


def test_own_row_excluded_but_identical_foreign_row_is_not():
    lib = ROOT / "scripts/lib/check_id_collision.sh"
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "04_EXECUTION").mkdir()
        row = "| 2026-01-01T00:00:00Z | T-777 | mine |"
        f = Path(d) / "04_EXECUTION/SESSION_CLAIMS.md"
        f.write_text(row + "\n")
        run = lambda ex: subprocess.run(["bash", "-c", f'source "{lib}"; check_id_collision "T-777" "{d}" "{ex}"'], capture_output=True, text=True)
        assert run(row).returncode == 0          # only our own row -> fine
        f.write_text(row + "\n| 2026-01-01T00:00:01Z | T-777 | rival |\n")
        assert run(row).returncode != 0          # someone else also holds it -> collision
