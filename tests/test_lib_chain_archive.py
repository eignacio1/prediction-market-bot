"""Tests for scripts/lib_chain_archive.py's archive_chain() — GG-176 (T-447).

Covers the single-entry-chain fix: the current-status line must always be
rewritten to new_current_line, even when there's only one prior entry and
therefore nothing worth archiving.
"""
from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lib_chain_archive import archive_chain  # noqa: E402


def test_no_chain_at_all_returns_none(tmp_path):
    nav = tmp_path / "NAV.md"
    nav.write_text("# Nav\n\nSome content, no chain here.\n")
    archive = tmp_path / "ARCHIVE.md"

    result = archive_chain(nav, archive, "Heading", "**Last reviewed**: new\n", "**Earlier history**: see ARCHIVE.md\n")

    assert result is None
    assert nav.read_text() == "# Nav\n\nSome content, no chain here.\n"
    assert not archive.exists()


def test_single_entry_chain_still_rewrites_current_line(tmp_path):
    # GG-176: this is the bug. A chain of exactly one entry must still be
    # replaced with new_current_line — the pointer must advance every
    # session, not freeze the first time the chain drops to one entry.
    nav = tmp_path / "NAV.md"
    nav.write_text(
        "# Nav\n\n"
        "**Last reviewed**: T-434, 2026-08-10T23:49:00Z, stale content.\n\n"
        "Rest of file.\n"
    )
    archive = tmp_path / "ARCHIVE.md"

    result = archive_chain(
        nav, archive, "Heading",
        "**Last reviewed**: T-460, 2026-08-17T23:02:23Z, fresh content.\n",
        "**Earlier history**: see ARCHIVE.md\n",
    )

    assert result is not None
    assert result["entries_archived"] == 0
    text = nav.read_text()
    assert "T-460" in text
    assert "T-434" not in text
    assert "**Earlier history**: see ARCHIVE.md" in text
    # Nothing archived — a single entry isn't the unbounded-growth problem
    # this module exists to fix.
    assert not archive.exists()


def test_multi_entry_chain_still_archives_and_collapses(tmp_path):
    # Regression: the pre-existing multi-entry behavior (archive old
    # entries verbatim, collapse nav to one new line) must be unchanged.
    nav = tmp_path / "NAV.md"
    nav.write_text(
        "# Nav\n\n"
        "**Last reviewed**: T-440, older.\n\n"
        "**Last reviewed (prior)**: T-430, oldest.\n\n"
        "Rest of file.\n"
    )
    archive = tmp_path / "ARCHIVE.md"

    result = archive_chain(
        nav, archive, "Heading",
        "**Last reviewed**: T-460, fresh.\n",
        "**Earlier history**: see ARCHIVE.md\n",
    )

    assert result is not None
    assert result["entries_archived"] == 2
    nav_text = nav.read_text()
    assert "T-460" in nav_text
    assert "T-440" not in nav_text
    assert "T-430" not in nav_text
    assert archive.exists()
    archive_text = archive.read_text()
    assert "T-440" in archive_text
    assert "T-430" in archive_text


def test_second_call_on_already_single_entry_is_idempotent_on_content(tmp_path):
    # Calling archive_chain twice in a row with the same new_current_line
    # (simulating two sessions writing identical status) must not corrupt
    # the file or duplicate the pointer line.
    nav = tmp_path / "NAV.md"
    nav.write_text("# Nav\n\n**Last reviewed**: T-434, stale.\n\nRest.\n")
    archive = tmp_path / "ARCHIVE.md"
    current_line = "**Last reviewed**: T-460, fresh.\n"
    pointer_line = "**Earlier history**: see ARCHIVE.md\n"

    archive_chain(nav, archive, "Heading", current_line, pointer_line)
    first_pass_text = nav.read_text()

    result_second = archive_chain(nav, archive, "Heading", current_line, pointer_line)

    assert result_second is not None
    assert result_second["entries_archived"] == 0
    assert nav.read_text() == first_pass_text
    assert first_pass_text.count("**Earlier history**") == 1
