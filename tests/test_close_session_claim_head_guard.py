"""GG-451: close_session_claim.sh must not land a feature branch's commits on main.

Mirrors test_claim_session_head_guard.py (GG-419). Real git, real script, temp bare origin.
A branch carrying an extra commit must be refused before anything is written or pushed; a
branch level with origin/main pushes only the closure row.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def sh(cmd, cwd, check=True):
    return subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, env=ENV, check=check, timeout=60)


def _seed(tmp: Path):
    origin, a = tmp / "origin.git", tmp / "a"
    sh(f"git init -q --bare -b main {origin}", tmp)
    sh(f"git clone -q {origin} {a}", tmp, check=False)
    (a / "04_EXECUTION").mkdir()
    (a / "04_EXECUTION/SESSION_CLAIMS.md").write_text("| ts | ids | focus |\n|---|---|---|\n")
    (a / ".gitattributes").write_text("04_EXECUTION/SESSION_CLAIMS.md merge=union\n")
    (a / "scripts").mkdir()
    (a / "scripts/close_session_claim.sh").write_text((ROOT / "scripts/close_session_claim.sh").read_text())
    sh("git checkout -q -B main && git add -A && git commit -q -m seed && git push -q origin main", a)
    return origin, a


def test_feature_branch_with_extra_commit_is_refused_and_main_untouched(tmp_path):
    origin, a = _seed(tmp_path)
    before = sh(f"git --git-dir={origin} rev-parse main", tmp_path).stdout.strip()
    sh("git checkout -q -b feature && echo x > feature.txt && git add feature.txt && git commit -q -m feature-work", a)

    r = sh('bash scripts/close_session_claim.sh "T-1" "done"', a, check=False)

    assert r.returncode != 0, r.stdout + r.stderr
    assert "GG-451" in r.stderr
    assert sh(f"git --git-dir={origin} rev-parse main", tmp_path).stdout.strip() == before
    assert sh(f"git --git-dir={origin} log --format=%s main", tmp_path).stdout.count("feature-work") == 0
    # nothing was written, committed or left dirty locally
    assert sh("git log -1 --format=%s", a).stdout.strip() == "feature-work"
    assert sh("git status --porcelain", a).stdout.strip() == ""


def test_branch_level_with_origin_main_pushes_only_the_closure_row(tmp_path):
    origin, a = _seed(tmp_path)
    before = sh(f"git --git-dir={origin} rev-parse main", tmp_path).stdout.strip()
    sh("git checkout -q -b session", a)

    r = sh('bash scripts/close_session_claim.sh "T-1" "done"', a, check=False)

    assert r.returncode == 0, r.stdout + r.stderr
    new = sh(f"git --git-dir={origin} rev-list {before}..main", tmp_path).stdout.split()
    assert len(new) == 1
    files = sh(f"git --git-dir={origin} show --name-only --format= main", tmp_path).stdout.split()
    assert files == ["04_EXECUTION/SESSION_CLAIMS.md"]
