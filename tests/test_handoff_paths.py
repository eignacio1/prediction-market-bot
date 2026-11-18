"""W117.4: handoff lookups find live and archived SESSION_HANDOFF files."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts" / "lib"))

from handoff_paths import all_handoffs, archived_handoffs, live_handoffs, resolve_handoff  # noqa: E402


def _make(root: Path) -> Path:
    (root / "archive" / "2026-10").mkdir(parents=True)
    (root / "SESSION_HANDOFF_20261117_A.md").write_text("live")
    (root / "archive" / "2026-10" / "SESSION_HANDOFF_20261003_OLD.md").write_text("old")
    (root / "MEMORY_BANK.md").write_text("not a handoff")
    return root


def test_live_and_archived_are_listed_separately(tmp_path):
    root = _make(tmp_path)
    assert [p.name for p in live_handoffs(root)] == ["SESSION_HANDOFF_20261117_A.md"]
    assert [p.name for p in archived_handoffs(root / "archive")] == ["SESSION_HANDOFF_20261003_OLD.md"]
    assert len(all_handoffs(root)) == 2


def test_resolve_finds_archived_by_bare_name(tmp_path):
    root = _make(tmp_path)
    found = resolve_handoff("SESSION_HANDOFF_20261003_OLD.md", root)
    assert found is not None and found.parent.name == "2026-10"


def test_resolve_prefers_live_and_accepts_old_path_form(tmp_path):
    root = _make(tmp_path)
    assert resolve_handoff("11_MEMORY_HANDOFF/SESSION_HANDOFF_20261117_A.md", root) == root / "SESSION_HANDOFF_20261117_A.md"


def test_resolve_missing_returns_none(tmp_path):
    root = _make(tmp_path)
    assert resolve_handoff("SESSION_HANDOFF_nope.md", root) is None


def test_real_repo_cited_handoff_resolves():
    # The TENSIONS evidence cites this file; it was archived by the W117.4 move.
    assert resolve_handoff("SESSION_HANDOFF_20261015T0025Z_W73_1.md") is not None
