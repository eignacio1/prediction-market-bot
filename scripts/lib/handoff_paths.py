#!/usr/bin/env python3
"""W117.4: resolve SESSION_HANDOFF files whether live or archived.

Handoffs older than 7 days live under 11_MEMORY_HANDOFF/archive/<YYYY-MM>/. Anything that
cites a handoff by its bare filename must still resolve it, so every lookup goes through here.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HANDOFF_DIR = REPO_ROOT / "11_MEMORY_HANDOFF"
ARCHIVE_DIR = HANDOFF_DIR / "archive"
GLOB = "SESSION_HANDOFF_*.md"


def live_handoffs(handoff_dir: Path = HANDOFF_DIR) -> list[Path]:
    return sorted(handoff_dir.glob(GLOB))


def archived_handoffs(archive_dir: Path = ARCHIVE_DIR) -> list[Path]:
    return sorted(archive_dir.glob(f"*/{GLOB}"))


def all_handoffs(handoff_dir: Path = HANDOFF_DIR) -> list[Path]:
    return live_handoffs(handoff_dir) + archived_handoffs(handoff_dir / "archive")


def resolve_handoff(name: str, handoff_dir: Path = HANDOFF_DIR) -> Path | None:
    """Return the path of the handoff with this filename (live first, then archive), or None."""
    base = Path(name).name
    live = handoff_dir / base
    if live.is_file():
        return live
    for path in archived_handoffs(handoff_dir / "archive"):
        if path.name == base:
            return path
    return None
