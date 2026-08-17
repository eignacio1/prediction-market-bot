#!/usr/bin/env python3
"""
lib_chain_archive.py — collapse a nav file's stacked "**Last reviewed**"
narrative chain down to one current-status line, archiving the rest verbatim.

Implements ADR-0044 (Governance-Entry Splitting: Current-Status Line +
Linked Immutable History) mechanically, for T-430 (session-end cost fix).

Why this exists: TODO_NEXT.md, MEMORY_BANK.md, and PLAN.md each grow one
`**Last reviewed (prior):**` paragraph per session, unbounded (GG-132 names
this for MEMORY_BANK.md; the same defect was confirmed present, unflagged,
in TODO_NEXT.md and PLAN.md during T-430's diagnosis). ADR-0044 already
specifies the fix (one live line + full history moved verbatim to a linked
append-only file) but until now applying it required a manual, model-authored
edit every session — which is itself part of the cost this fix removes.

This module makes the collapse a mechanical, zero-model-authorship operation
that session-end tooling can call on every close-out, for every tier.

Nothing is deleted. The full text of every collapsed entry is preserved
byte-for-byte in the archive file (ADR-0044 requires "lossless and verifiable"
moves) — this script satisfies that by construction, not by review.
"""
from __future__ import annotations

import re
from pathlib import Path

CHAIN_RE = re.compile(r"^\*\*Last reviewed")


POINTER_RE = re.compile(r"^\*\*Earlier history")


def _find_chain_span(lines: list[str]) -> tuple[int, int] | None:
    """Return (start_idx, end_idx) inclusive of the contiguous
    '**Last reviewed...' chain, or None if no such chain exists.

    end_idx additionally absorbs a pre-existing '**Earlier history**'
    pointer line if one immediately follows the chain (allowing blank
    lines in between) — that old pointer's text gets archived along with
    the chain it was already summarizing, so the caller can always emit
    exactly one fresh pointer afterward instead of stacking a second one
    next to it.
    """
    indices = [i for i, line in enumerate(lines) if CHAIN_RE.match(line)]
    if not indices:
        return None
    start, end = indices[0], indices[-1]
    probe = end + 1
    while probe < len(lines) and lines[probe].strip() == "":
        probe += 1
    if probe < len(lines) and POINTER_RE.match(lines[probe]):
        end = probe
    return start, end


def archive_chain(
    nav_path: Path,
    archive_path: Path,
    archive_heading: str,
    new_current_line: str,
    pointer_line: str,
) -> dict | None:
    """Collapse nav_path's Last-reviewed chain to `new_current_line`,
    archiving the full prior chain verbatim into archive_path under
    `## {archive_heading}` (newest-first, prepended).

    Returns a dict describing what happened, or None if there was no chain
    at all to update (nothing written in that case).

    GG-176: a chain of exactly one entry has nothing worth *archiving* (a
    single line isn't the unbounded-growth problem this module exists to
    fix), but it still gets *rewritten* to new_current_line — the pointer
    must always advance to reflect the session that just ran, even when
    there's no prior history to move out of the nav file. The original
    code returned None (no write at all) in this case, which meant the
    current-status line silently froze the first time a nav file reached
    exactly one chain entry — see GG-176 / TODO_NEXT.md T-447.
    """
    nav_lines = nav_path.read_text().splitlines(keepends=True)
    span = _find_chain_span(nav_lines)
    if span is None:
        return None
    start, end = span
    chain_text = "".join(nav_lines[start : end + 1])
    n_entries = sum(1 for l in nav_lines[start : end + 1] if CHAIN_RE.match(l))

    archived = False
    if n_entries > 1:
        # --- archive the full chain verbatim, newest-first ---
        heading_marker = f"## {archive_heading}"
        if archive_path.exists():
            archive_text = archive_path.read_text()
        else:
            archive_text = f"# Archive\n\n{heading_marker}\n\n"

        if heading_marker in archive_text:
            head, rest = archive_text.split(heading_marker, 1)
            # insert right after the heading line, before any prior archived batch
            rest_lines = rest.splitlines(keepends=True)
            insert_at = 0
            # skip the newline(s) immediately after the heading
            while insert_at < len(rest_lines) and rest_lines[insert_at].strip() == "":
                insert_at += 1
            new_rest = (
                "".join(rest_lines[:insert_at])
                + f"\n<!-- archived from {nav_path.name}, {n_entries} entries -->\n"
                + chain_text
                + "\n"
                + "".join(rest_lines[insert_at:])
            )
            new_archive_text = head + heading_marker + new_rest
        else:
            new_archive_text = (
                archive_text.rstrip("\n")
                + f"\n\n{heading_marker}\n\n"
                + f"<!-- archived from {nav_path.name}, {n_entries} entries -->\n"
                + chain_text
                + "\n"
            )
        archive_path.write_text(new_archive_text)
        archived = True

    # --- collapse the nav file span to the new single line — always, even
    # when there was only one entry to begin with (nothing archived above,
    # but the pointer still must advance to this session's current line).
    replacement = [new_current_line.rstrip("\n") + "\n"]
    next_line = nav_lines[end + 1] if end + 1 < len(nav_lines) else ""
    if not next_line.strip().startswith("**Earlier history"):
        replacement.append(pointer_line.rstrip("\n") + "\n")

    new_nav_lines = nav_lines[:start] + replacement + nav_lines[end + 1 :]
    nav_path.write_text("".join(new_nav_lines))

    return {
        "nav_file": str(nav_path),
        "archive_file": str(archive_path) if archived else None,
        "entries_archived": n_entries if archived else 0,
    }
