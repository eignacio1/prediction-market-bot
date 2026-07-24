#!/usr/bin/env bash
# ============================================================================
# archive_todo_next.sh — move completed TODO_NEXT.md sections into
# MEMORY_BANK_ARCHIVE.md's "TODO_NEXT Task Archive" section (Fix 4,
# session-end protocol tiering plan, 2026-07-24)
#
# WHY: T-396 (2026-07-23) did this once by hand, archiving 34 completed
# `## T-NNN` sections and leaving a note that "no standing cadence existed
# for it prior to this session (see GG-133)". One day later TODO_NEXT.md had
# already regrown past 2,000 lines with new completed sections plus a large
# legacy block never covered by the first pass — proving a one-off manual
# pass doesn't hold. This script makes the archival mechanical and repeatable
# so it can be wired into /session-end and actually recur.
#
# CLASSIFICATION (conservative by design — never risk moving live work):
#   A top-level "## " section is ARCHIVABLE only if its header line contains
#   a completion keyword (DONE / COMPLETE / COMPLETED / CLOSED / RESOLVED)
#   AND does not contain a keep-keyword (OPEN / BLOCKED / PARTIAL / PENDING /
#   IN PROGRESS / DRAFTED / SCOPED / STANDING / PRIORITY QUEUE). Keep-keywords
#   always win, even if a completion keyword is also present, e.g. "PARTIAL,
#   GG-091 remains OPEN" must stay. Nested "### " sub-headers do NOT create
#   new boundaries — a "## " section is archived or kept as one whole block,
#   matching the granularity T-396's manual pass already used.
#
#   Default output is DRY-RUN: report what would move, do not touch files.
#   Pass --apply to actually perform the move.
#
# Usage:
#   scripts/archive_todo_next.sh            # dry run, report only
#   scripts/archive_todo_next.sh --apply    # perform the archival
# ============================================================================
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"

APPLY=0
[ "${1:-}" = "--apply" ] && APPLY=1

TODO="04_EXECUTION/TODO_NEXT.md"
ARCHIVE="11_MEMORY_HANDOFF/MEMORY_BANK_ARCHIVE.md"

if [ ! -f "$TODO" ] || [ ! -f "$ARCHIVE" ]; then
    echo "ERROR: $TODO or $ARCHIVE not found." >&2
    exit 1
fi

python3 - "$TODO" "$ARCHIVE" "$APPLY" <<'PYEOF'
import sys, re, datetime

todo_path, archive_path, apply_flag = sys.argv[1], sys.argv[2], sys.argv[3] == "1"

with open(todo_path) as f:
    lines = f.readlines()

# top-level section boundaries: any line starting with "## " (not "### " or deeper)
header_idx = [i for i, l in enumerate(lines) if re.match(r"^## (?!#)", l)]

KEEP_KEYWORDS = ["OPEN", "BLOCKED", "PARTIAL", "PENDING", "IN PROGRESS",
                 "DRAFTED", "SCOPED", "STANDING", "PRIORITY QUEUE"]
DONE_KEYWORDS = ["DONE", "COMPLETE", "COMPLETED", "CLOSED", "RESOLVED"]

def classify(header_text):
    upper = header_text.upper()
    if any(kw in upper for kw in KEEP_KEYWORDS):
        return "KEEP"
    if any(kw in upper for kw in DONE_KEYWORDS):
        return "ARCHIVE"
    return "KEEP"

sections = []
for n, start in enumerate(header_idx):
    end = header_idx[n + 1] if n + 1 < len(header_idx) else len(lines)
    header_text = lines[start].rstrip("\n")
    verdict = classify(header_text)
    sections.append((start, end, header_text, verdict))

archive_sections = [s for s in sections if s[3] == "ARCHIVE"]
keep_sections = [s for s in sections if s[3] == "KEEP"]

print(f"Total top-level sections: {len(sections)}")
print(f"ARCHIVE: {len(archive_sections)}   KEEP: {len(keep_sections)}")
print()
print("--- Sections to ARCHIVE ---")
total_archived_lines = 0
for start, end, header_text, _ in archive_sections:
    n_lines = end - start
    total_archived_lines += n_lines
    print(f"  L{start+1}-{end} ({n_lines} lines): {header_text[:100]}")
print()
print("--- Sections to KEEP ---")
for start, end, header_text, _ in keep_sections:
    print(f"  L{start+1}-{end} ({end-start} lines): {header_text[:100]}")
print()
print(f"Total lines that would be archived: {total_archived_lines} / {len(lines)}")

if not apply_flag:
    print()
    print("DRY RUN ONLY — no files modified. Re-run with --apply to perform the move.")
    sys.exit(0)

if not archive_sections:
    print("Nothing to archive — no changes made.")
    sys.exit(0)

# Build the archived blob in original file order (top to bottom), preserving
# each section verbatim.
archived_blob_lines = []
for start, end, header_text, _ in archive_sections:
    archived_blob_lines.extend(lines[start:end])

today = datetime.date.today().isoformat()
today_env = "__DATE_OVERRIDE__"
note = (
    f"\n**Archived {today_env} (`scripts/archive_todo_next.sh --apply`) — "
    f"{len(archive_sections)} completed top-level sections moved verbatim "
    f"(byte-for-byte) from `04_EXECUTION/TODO_NEXT.md`, spanning "
    f"{archive_sections[0][2][:60].strip()!r} through "
    f"{archive_sections[-1][2][:60].strip()!r}. This is a mechanical, "
    f"repeatable pass — see `scripts/archive_todo_next.sh` for the "
    f"classification rule (completion keyword in header, no keep-keyword "
    f"override). Full rationale: `03_DECISIONS/DECISION_LOG/DECISION_LOG.md` "
    f"{today_env}.**\n\n---\n\n"
)
note = note.replace(today_env, today)

# Insert into MEMORY_BANK_ARCHIVE.md immediately after the existing
# "## TODO_NEXT Task Archive" header + its own intro note, i.e. right before
# the first pre-existing archived section (newest-first convention: this
# pass's content goes on top).
with open(archive_path) as f:
    archive_lines = f.readlines()

anchor_pat = re.compile(r"^## TODO_NEXT Task Archive")
anchor_idx = next((i for i, l in enumerate(archive_lines) if anchor_pat.match(l)), None)
if anchor_idx is None:
    print("ABORT: '## TODO_NEXT Task Archive' header not found in MEMORY_BANK_ARCHIVE.md")
    sys.exit(1)

# find the end of the existing intro block for that section: the next line
# that starts with "---" after anchor_idx (the separator already used by the
# T-396 pass), insert immediately after it.
sep_idx = next((i for i in range(anchor_idx + 1, len(archive_lines))
                 if archive_lines[i].startswith("---")), None)
if sep_idx is None:
    print("ABORT: could not find the '---' separator after the archive section header.")
    sys.exit(1)

insert_at = sep_idx + 1
new_archive_lines = (
    archive_lines[:insert_at]
    + [note]
    + archived_blob_lines
    + ["\n"]
    + archive_lines[insert_at:]
)
with open(archive_path, "w") as f:
    f.writelines(new_archive_lines)

# Remove archived sections from TODO_NEXT.md, keeping everything else in order.
archive_ranges = [(s[0], s[1]) for s in archive_sections]
new_todo_lines = []
i = 0
while i < len(lines):
    in_archived = False
    for start, end in archive_ranges:
        if start <= i < end:
            in_archived = True
            i = end
            break
    if in_archived:
        continue
    new_todo_lines.append(lines[i])
    i += 1

with open(todo_path, "w") as f:
    f.writelines(new_todo_lines)

print()
print(f"APPLIED: archived {len(archive_sections)} sections ({total_archived_lines} lines) "
      f"from {todo_path} into {archive_path}.")
PYEOF
