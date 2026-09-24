#!/usr/bin/env python3
"""retire_resolved_gaps.py — move resolved-class entries from GOVERNANCE_GAP_LOG.md
into GOVERNANCE_GAP_LOG_ARCHIVE.md, verbatim, whole-entry, idempotently.

T-570 (2026-09-23), Deliverable 1 of the retirement-mechanism task: "make retirement
a machine step instead of a person remembering." This script FILES entries already
marked resolved -- it never judges whether work is done, never edits a Status token,
and never touches an entry classified as still-open. Adjudication happens in
GOVERNANCE_GAP_LOG.md itself, by whoever sets the Status line; this script only
relocates what is already marked resolved-class, byte-for-byte.

SAFE BY DEFAULT. Running with no flags only REPORTS what would move -- nothing is
written anywhere. Writing requires --apply AND explicit --out-src/--out-archive
destination paths; --apply with no output paths refuses rather than silently
defaulting to overwriting the live files. To retire the real log, pass --apply
--out-src 03_DECISIONS/GOVERNANCE_GAP_LOG.md --out-archive
03_DECISIONS/GOVERNANCE_GAP_LOG_ARCHIVE.md explicitly -- this session, that
invocation is intentionally never made; every run here targets copies.

Resolved-class classification -- the whole safety margin, get this list right.
A Status token counts as resolved-class iff it starts with the literal word
"RESOLVED" or the literal phrase "CLOSED-AS-ARTIFACT", followed by a non-letter
or end-of-string. This is a PREFIX match, not a substring search, specifically so
it does NOT catch the STAY tokens (open work, must never be archived):
    PARTIALLY RESOLVED
    PARTIAL RESOLVE
    LIKELY RESOLVED
    IN PROGRESS
    PLAN ACCEPTED
    ACCEPTED UNCERTAINTY
    WATCH ITEM
None of these begin with "RESOLVED" or "CLOSED-AS-ARTIFACT", so the prefix anchor
excludes all seven without a negative lookahead or a stay-token blocklist that could
itself drift out of date. Compound/dated resolved variants confirmed against the real
live log (2026-09-23) that must still match:
    RESOLVED
    RESOLVED (2026-09-11)
    RESOLVED 2026-08-28 (T-502)
    RESOLVED (2026-09-11, code+migration)
    RESOLVED (2026-09-11, code+migration) · ACTIVATED (2026-09-15, ...)   [GG-271]
    CLOSED-AS-ARTIFACT
A full-paragraph resolved Status value also matches -- the regex only anchors the
start of the token, so it does not care how long the rest of the line is.

Entry extraction reuses generate_operator_console.py's proven header-slice algorithm:
find every real `### GG-NNN` header (excluding the Gap Registration Template's
example header, which matches the header pattern but is not a real gap), slice each
entry from its header's start index to the next header's start index (or EOF),
verbatim. This is the same technique already relied on for the live console, not a
new, unproven parser.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SRC = ROOT / "03_DECISIONS" / "GOVERNANCE_GAP_LOG.md"
DEFAULT_ARCHIVE = ROOT / "03_DECISIONS" / "GOVERNANCE_GAP_LOG_ARCHIVE.md"

HEADER_RE = re.compile(r"^### (GG-\d+) — (.+)$", re.M)
STATUS_RE = re.compile(r"^\*\*Status:\*\* (.+?) · \*\*Severity:\*\* (.+)$", re.M)

# Prefix match, not substring -- see module docstring for why this excludes every
# known stay token without needing a blocklist.
RESOLVED_CLASS_RE = re.compile(r"^(RESOLVED|CLOSED-AS-ARTIFACT)(?:[^A-Za-z]|$)")

STAY_TOKENS_FOR_REFERENCE = (
    "PARTIALLY RESOLVED",
    "PARTIAL RESOLVE",
    "LIKELY RESOLVED",
    "IN PROGRESS",
    "PLAN ACCEPTED",
    "ACCEPTED UNCERTAINTY",
    "WATCH ITEM",
)


def is_resolved_class(token: str) -> bool:
    """True iff the captured Status token is resolved-class (see module docstring)."""
    return bool(RESOLVED_CLASS_RE.match(token.strip()))


def parse_entries(text: str) -> list[dict]:
    """Whole, verbatim `### GG-NNN ...` entry blocks. Same slice algorithm as
    generate_operator_console.py's parse_entries() -- reused deliberately, not
    reinvented."""
    starts = [(m.start(), m.group(1), m.group(2)) for m in HEADER_RE.finditer(text)]
    starts = [s for s in starts if re.match(r"GG-\d+$", s[1])]  # exclude template
    starts.append((len(text), None, None))
    entries = []
    for i in range(len(starts) - 1):
        s, gid, title = starts[i]
        e = starts[i + 1][0]
        block = text[s:e]
        m = STATUS_RE.search(block)
        token, sev = (m.group(1), m.group(2)) if m else ("UNKNOWN", "UNSPECIFIED")
        entries.append({
            "id": gid,
            "title": title,
            "token": token,
            "severity": sev,
            "block": block,
            "resolved_class": is_resolved_class(token),
        })
    return entries


def preamble(text: str) -> str:
    """Everything before the first real GG-NNN header -- front matter, the Gap
    Registration Template, etc. Never touched by the move."""
    m = re.search(r"^### GG-\d+ — ", text, re.M)
    return text[: m.start()] if m else text


def plan_move(src_text: str, archive_text: str) -> tuple[list[dict], list[dict], list[str]]:
    """Returns (to_move, to_stay, warnings) without writing anything."""
    entries = parse_entries(src_text)
    to_move = [e for e in entries if e["resolved_class"]]
    to_stay = [e for e in entries if not e["resolved_class"]]

    warnings = []
    archive_ids = set(m.group(1) for m in HEADER_RE.finditer(archive_text))
    for e in to_move:
        if e["id"] in archive_ids:
            warnings.append(
                f"{e['id']}: already present in archive by id -- SKIPPING this move "
                f"to avoid a duplicate (idempotency guard; investigate before re-running "
                f"--apply, this should only happen if the archive was hand-edited or a "
                f"prior --apply partially landed)"
            )
    # Recompute to_move/to_stay honoring the duplicate guard.
    skip_ids = {w.split(":", 1)[0] for w in warnings}
    final_move = [e for e in to_move if e["id"] not in skip_ids]
    final_stay = to_stay + [e for e in to_move if e["id"] in skip_ids]
    return final_move, final_stay, warnings


def render_report(to_move: list[dict], to_stay: list[dict], warnings: list[str]) -> str:
    lines = []
    lines.append(f"=== retire_resolved_gaps.py — dry-run report ===")
    lines.append(f"resolved-class entries that WOULD move: {len(to_move)}")
    lines.append(f"stay-class entries remaining live: {len(to_stay)}")
    lines.append("")
    if to_move:
        lines.append("-- WOULD MOVE (verbatim, whole entry) --")
        for e in to_move:
            lines.append(f"  {e['id']:<10} status={e['token']!r:<70} severity={e['severity']}")
    else:
        lines.append("-- WOULD MOVE -- none")
    lines.append("")
    if warnings:
        lines.append("-- WARNINGS --")
        for w in warnings:
            lines.append(f"  !! {w}")
        lines.append("")
    lines.append("-- STAY (sample of stay-class tokens actually observed, for spot-check) --")
    seen_tokens = []
    for e in to_stay:
        t = e["token"].strip()
        if t not in seen_tokens:
            seen_tokens.append(t)
    for t in sorted(seen_tokens)[:40]:
        lines.append(f"  {t}")
    if len(seen_tokens) > 40:
        lines.append(f"  ... and {len(seen_tokens) - 40} more distinct stay tokens")
    return "\n".join(lines)


def apply_move(src_text: str, archive_text: str, to_move: list[dict], to_stay: list[dict]) -> tuple[str, str]:
    """Builds new src/archive text. Pure function -- caller decides where to write."""
    new_src = preamble(src_text) + "".join(e["block"] for e in to_stay)
    if to_move:
        sep = "" if archive_text.endswith("\n\n") else ("\n" if archive_text.endswith("\n") else "\n\n")
        new_archive = archive_text + sep + "".join(e["block"] for e in to_move)
    else:
        new_archive = archive_text
    return new_src, new_archive


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--src", type=Path, default=DEFAULT_SRC, help="live-log-shaped file to read (default: real live log -- read-only unless --apply)")
    p.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE, help="archive-shaped file to read (default: real archive -- read-only unless --apply)")
    p.add_argument("--apply", action="store_true", help="actually write. Requires --out-src and --out-archive.")
    p.add_argument("--out-src", type=Path, default=None, help="where to write the post-move src (required with --apply)")
    p.add_argument("--out-archive", type=Path, default=None, help="where to write the post-move archive (required with --apply)")
    args = p.parse_args()

    if not args.src.exists():
        print(f"ERROR: {args.src} not found", file=sys.stderr)
        return 1
    if not args.archive.exists():
        print(f"ERROR: {args.archive} not found", file=sys.stderr)
        return 1

    src_text = args.src.read_text()
    archive_text = args.archive.read_text()

    to_move, to_stay, warnings = plan_move(src_text, archive_text)
    print(render_report(to_move, to_stay, warnings))

    if not args.apply:
        print("\n(dry-run only -- nothing written. Pass --apply --out-src ... --out-archive ... to write.)")
        return 0

    if args.out_src is None or args.out_archive is None:
        print(
            "\nERROR: --apply requires both --out-src and --out-archive to be given "
            "explicitly. Refusing to guess a destination.",
            file=sys.stderr,
        )
        return 2

    new_src, new_archive = apply_move(src_text, archive_text, to_move, to_stay)
    args.out_src.write_text(new_src)
    args.out_archive.write_text(new_archive)
    print(f"\nWROTE {args.out_src} ({len(to_stay)} entries retained)")
    print(f"WROTE {args.out_archive} ({len(to_move)} entries appended)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
