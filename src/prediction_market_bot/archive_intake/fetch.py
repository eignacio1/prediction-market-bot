"""Fetch the archive read-only at a pinned commit.  Never pushes."""
from __future__ import annotations

import subprocess
from pathlib import Path

ARCHIVE_REPO = "eignacio1/sports-intel-archive"


def _git(args: list[str], cwd: Path | None = None) -> str:
    out = subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)
    return out.stdout.strip()


def ensure_clone(dest: Path, sha: str, url: str | None = None) -> str:
    """Make ``dest`` a shallow checkout of exactly ``sha``; return the SHA.

    ``url`` defaults to the private GitHub repo over the operator's existing git
    credentials.  Raises if the checked-out commit is not ``sha`` (pinning).
    """
    dest = Path(dest)
    url = url or f"https://github.com/{ARCHIVE_REPO}.git"
    if not (dest / ".git").exists():
        dest.mkdir(parents=True, exist_ok=True)
        _git(["init", "-q"], dest)
        _git(["remote", "add", "origin", url], dest)
    _git(["fetch", "-q", "--depth", "1", "origin", sha], dest)
    _git(["-c", "advice.detachedHead=false", "checkout", "-q", "--detach", "FETCH_HEAD"], dest)
    head = _git(["rev-parse", "HEAD"], dest)
    if head != sha:
        raise RuntimeError(f"archive pin mismatch: wanted {sha}, got {head}")
    return head
