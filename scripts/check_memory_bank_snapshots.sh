#!/usr/bin/env bash
# ============================================================================
# check_memory_bank_snapshots.sh — MEMORY_BANK snapshot-count guard (T-334/E1)
#
# Enforces the "one authoritative snapshot, older ones archived" rule against
# THREE independent chains/fields in 11_MEMORY_HANDOFF/MEMORY_BANK.md that
# have each exhibited the same accumulate-and-never-prune failure mode:
#   1. "## Current State Snapshot (...)" headers (Project state section)
#   2. "**Last reviewed" lines (Project Identity section, near the top) —
#      discovered independently, after chain 1 was already fixed, as a
#      9-entry chain going back to 2026-07-05 that the original version of
#      this script did not cover, and which re-accumulated a SECOND time
#      (55 more entries, fixed 2026-07-24) before this script gained the
#      length/anti-pattern checks below to catch that regression earlier.
#   3. "## Compass OS Health (...)" headers — same header-per-entry pattern
#      as #1, added to this script's coverage 2026-07-24 (previously
#      uncovered entirely; found only via a manual audit pass, not a guard).
# When a session writes a new entry in any of these, the prior authoritative
# block must be moved verbatim into 11_MEMORY_HANDOFF/MEMORY_BANK_ARCHIVE.md,
# not left in place with a "(superseded)"/"(prior)" marker — that pattern is
# what let all three chains grow unreconciled and required manual
# consolidation passes (T-334, then again 2026-07-24) to fix.
# See DECISION_LOG.md 2026-07-11 (T-334).
#
# Header-COUNT checks alone miss a second failure mode: a single-header field
# (Current State Snapshot / Compass OS Health) can stay at count==1 while its
# one line grows without bound via an embedded "*(Previous, as of ...)*" /
# "Prior pointer — " / "Prior freshness pointer" phrase instead of a proper
# archive cutover — this is exactly what happened before the first T-334 pass
# (count==1 the whole time; the line itself became the growing blob). Two
# additional checks below catch this: a per-line length threshold, and a
# direct grep for those anti-pattern phrases anywhere in the file.
#
# Non-destructive: reads only. Exit code 0 always (this is a WARN, not a
# blocking check) unless run with --strict, in which case it exits 1 on any
# violation so it can be wired into a pre-commit hook later if desired.
# ============================================================================
set -uo pipefail

STRICT=0
[ "${1:-}" = "--strict" ] && STRICT=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
MB="$REPO_ROOT/11_MEMORY_HANDOFF/MEMORY_BANK.md"

if [ ! -f "$MB" ]; then
  echo "check_memory_bank_snapshots: $MB not found — skipping"
  exit 0
fi

VIOLATION=0

check_chain() {
  local label="$1" pattern="$2" fix_hint="$3"
  local header_lines count
  header_lines="$(grep -n "$pattern" "$MB")"
  count=0
  [ -n "$header_lines" ] && count="$(printf '%s\n' "$header_lines" | wc -l | tr -d ' ')"

  echo "--- $label count: $count ---"

  if [ "$count" -le 1 ]; then
    echo "OK  exactly one (or zero) $label header — rule satisfied."
    return 0
  fi

  VIOLATION=1
  echo "!!  $count $label headers found — the rule is 'one authoritative entry,"
  echo "    older ones archived' (T-334). Found:"
  printf '%s\n' "$header_lines" | while IFS= read -r h; do
    echo "      $h"
  done
  echo "    Fix: $fix_hint"

  # Flag same-day duplicates specifically — this is the GG-082 conflation mode
  # (two concurrent sessions on the same date each writing their own entry
  # instead of consolidating into one). Only look at the date immediately
  # following the header marker (first ~150 chars of each line) — these are
  # long free-text lines that mention many other dates in prose further in,
  # and scanning the whole line produces false "same-day" hits on unrelated
  # dates mentioned in the narrative body.
  local dates entry_date
  dates=""
  while IFS= read -r h; do
    entry_date="$(printf '%s' "$h" | cut -c1-150 | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1)"
    [ -n "$entry_date" ] && dates="$dates$entry_date"$'\n'
  done <<HEREDOC_LINES
$header_lines
HEREDOC_LINES
  dates="$(printf '%s' "$dates" | sort | uniq -c | awk '$1 > 1 {print $2}')"
  if [ -n "$dates" ]; then
    echo "!!  Same-day duplicates detected for: $(printf '%s' "$dates" | tr '\n' ' ')"
    echo "    This is the recurring GG-082 narrative-conflation pattern — consolidate now."
  fi
}

check_chain "Current State Snapshot" "^## Current State Snapshot" \
  "keep only the newest as authoritative; move the rest verbatim into 11_MEMORY_HANDOFF/MEMORY_BANK_ARCHIVE.md (reverse-chronological, newest archived entry first) rather than leaving them marked '(superseded)' in place."

check_chain "Last reviewed" "^\*\*Last reviewed" \
  "keep only the current '**Last reviewed:**' line, pointing at the Current State Snapshot section for detail; move every '(prior)'/'(prior, prior)'/'Prior —'/'Earlier —' entry verbatim into 11_MEMORY_HANDOFF/MEMORY_BANK_ARCHIVE.md rather than letting the chain keep growing."

check_chain "Compass OS Health" "^## Compass OS Health" \
  "keep only the newest as authoritative; move the rest verbatim into 11_MEMORY_HANDOFF/MEMORY_BANK_ARCHIVE.md's 'Compass OS Health chain' section rather than leaving them marked '(superseded)'/'Previous, as of' in place."

# --- Check 4: per-line length threshold on the single-header fields ---
# Catches the "count stays 1 but the line itself becomes the blob" failure
# mode that header-count checks alone cannot see. 3000 chars is comfortably
# above the healthy post-cutover size (~900-1300 chars observed 2026-07-24 for
# both fields) and well below what an unpruned multi-entry blob reaches.
LENGTH_THRESHOLD=3000
check_line_length() {
  local label="$1" pattern="$2"
  local ln len
  ln="$(grep -n "$pattern" "$MB" | head -1 | cut -d: -f1)"
  [ -z "$ln" ] && return 0
  len="$(sed -n "${ln}p" "$MB" | wc -c | tr -d ' ')"
  echo "--- $label line length: $len chars (line $ln) ---"
  if [ "$len" -gt "$LENGTH_THRESHOLD" ]; then
    VIOLATION=1
    echo "!!  $label's single line is $len chars (> ${LENGTH_THRESHOLD} threshold) — even though"
    echo "    the header count is 1, the line itself may be growing as an inline blob"
    echo "    again (the pre-T-334 failure mode). Check for embedded 'Prior pointer —'"
    echo "    / '(Previous, as of ...)' phrases and cut over to a dated archive header"
    echo "    if found."
  else
    echo "OK  under the ${LENGTH_THRESHOLD}-char threshold."
  fi
}
check_line_length "Current State Snapshot" "^## Current State Snapshot"
check_line_length "Compass OS Health" "^## Compass OS Health"

# --- Check 5: anti-pattern phrase scan ---
# These exact phrases are how both blob fields grew silently before T-334:
# instead of cutting to a new dated "## ... (DATE...)" archive header, a
# session appended "Prior pointer — ..." / "Prior freshness pointer(s) — ..."
# / "*(Previous, as of DATE...)*" inline onto the live line. Any hit means
# the anti-pattern has recurred, regardless of header count or line length.
ANTI_PATTERNS=("Prior pointer — " "Prior freshness pointer" "*(Previous, as of ")
echo "--- Anti-pattern phrase scan ---"
ANTI_HIT=0
for phrase in "${ANTI_PATTERNS[@]}"; do
  hits="$(grep -Fn "$phrase" "$MB" || true)"
  if [ -n "$hits" ]; then
    ANTI_HIT=1
    VIOLATION=1
    echo "!!  Found anti-pattern phrase '$phrase':"
    printf '%s\n' "$hits" | sed 's/^/      /' | cut -c1-160
  fi
done
if [ "$ANTI_HIT" -eq 0 ]; then
  echo "OK  no anti-pattern phrases found."
fi

if [ "$STRICT" -eq 1 ] && [ "$VIOLATION" -eq 1 ]; then
  exit 1
fi
exit 0
