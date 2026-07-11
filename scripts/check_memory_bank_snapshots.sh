#!/usr/bin/env bash
# ============================================================================
# check_memory_bank_snapshots.sh — MEMORY_BANK snapshot-count guard (T-334/E1)
#
# Enforces the "one authoritative snapshot, older ones archived" rule against
# TWO independent chains in 11_MEMORY_HANDOFF/MEMORY_BANK.md that have both
# exhibited the same accumulate-and-never-prune failure mode:
#   1. "## Current State Snapshot (...)" headers (Project state section)
#   2. "**Last reviewed" lines (Project Identity section, near the top) —
#      discovered independently, after chain 1 was already fixed, as a
#      9-entry chain going back to 2026-07-05 that the original version of
#      this script did not cover.
# When a session writes a new entry in either chain at session-end, the
# prior authoritative block must be moved verbatim into
# 11_MEMORY_HANDOFF/MEMORY_BANK_ARCHIVE.md, not left in place with a
# "(superseded)"/"(prior)" marker — that pattern is what let both chains grow
# unreconciled and required a manual consolidation pass (T-334) to fix.
# See DECISION_LOG.md 2026-07-11 (T-334).
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

if [ "$STRICT" -eq 1 ] && [ "$VIOLATION" -eq 1 ]; then
  exit 1
fi
exit 0
