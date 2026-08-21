#!/usr/bin/env python3
"""
gg_id_uniqueness_check.py — GG-199/GG-162 class: detect duplicate "### GG-NNN"
ids across GOVERNANCE_GAP_LOG.md (and its archive).

Why this exists: CLAUDE.md Step 3's structural check compares header count vs.
"**Status:**" line count -- that check passes cleanly even on a duplicate id,
because both counters increment together for the duplicate row (GG-162: no
atomic reservation for GG-numbers, unlike T-numbers). Three real concurrent-
claim collisions have hit this exact defect: GG-187 claimed by both T-465 and
T-466 twelve seconds apart (2026-08-18), and GG-197 claimed concurrently by
T-473 and T-479 (2026-08-21, commit 05ed07e) -- inside a batch explicitly
trying to pre-allocate numbers. This checks both the live log and the archive
combined, since a number could be reused against an already-resolved/archived
id, which a live-log-only check would never see.
"""
from __future__ import annotations

import re
from collections import Counter

_ID_RE = re.compile(r"^### (GG-[0-9]+)")


def find_duplicate_ids(*texts: str) -> list[str]:
    """Return sorted duplicate GG-NNN ids found across all given file texts."""
    counts: Counter[str] = Counter()
    for text in texts:
        for line in text.splitlines():
            m = _ID_RE.match(line)
            if m:
                counts[m.group(1)] += 1
    dups = sorted(
        (gid for gid, n in counts.items() if n > 1),
        key=lambda gid: int(gid.split("-")[1]),
    )
    return dups


def main(argv=None):
    import sys
    from pathlib import Path

    argv = argv if argv is not None else sys.argv[1:]
    paths = [Path(a) for a in argv] or [
        Path("03_DECISIONS/GOVERNANCE_GAP_LOG.md"),
        Path("03_DECISIONS/GOVERNANCE_GAP_LOG_ARCHIVE.md"),
    ]
    texts = [p.read_text() for p in paths if p.exists()]
    dups = find_duplicate_ids(*texts)
    if dups:
        print(
            "  *** GG-199-CLASS ALERT: duplicate GG-NNN id(s) detected -- the header==status-line"
        )
        print(
            "      parity check CANNOT see this (both counters increment together per duplicate)."
        )
        print("      Renumber one immediately -- do not let two gaps share an id (GG-162 class;")
        print("      GG-187 x2 + GG-197 already hit this):")
        for d in dups:
            print(f"        - {d}")
        return 1
    print("  OK -- no duplicate GG-NNN ids across live log + archive")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
