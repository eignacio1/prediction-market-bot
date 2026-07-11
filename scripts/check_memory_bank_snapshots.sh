#!/usr/bin/env bash
# ============================================================================
# check_memory_bank_snapshots.sh — MEMORY_BANK snapshot-count guard (T-334/E1)
#
# Enforces the "one authoritative snapshot, older ones archived" rule:
# 11_MEMORY_HANDOFF/MEMORY_BANK.md must contain exactly one
# "## Current State Snapshot (...)" header. When a session writes a new one
# at session-end, the prior authoritative block must be moved verbatim into
# 11_MEMORY_HANDOFF/MEMORY_BANK_ARCHIVE.md, not left in place with a
# "(superseded by ... above)" marker — that pattern is what let two
# same-day 2026-07-11 snapshots go unreconciled and required a manual
# consolidation pass (T-334) to fix. See DECISION_LOG.md 2026-07-11 (T-334).
#
# Non-destructive: reads only. Exit code 0 always (this is a WARN, not a
# blocking check) unless run with --strict, in which case it exits 1 on
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

HEADER_LINES="$(grep -n "^## Current State Snapshot" "$MB")"
COUNT=0
[ -n "$HEADER_LINES" ] && COUNT="$(printf '%s\n' "$HEADER_LINES" | wc -l | tr -d ' ')"

echo "--- MEMORY_BANK snapshot count: $COUNT ---"

if [ "$COUNT" -le 1 ]; then
  echo "OK  exactly one (or zero) Current State Snapshot header — rule satisfied."
  exit 0
fi

echo "!!  $COUNT Current State Snapshot headers found — the rule is 'one authoritative"
echo "    snapshot, older ones archived' (T-334). Found:"
printf '%s\n' "$HEADER_LINES" | while IFS= read -r h; do
  echo "      $h"
done
echo "    Fix: keep only the newest as authoritative; move the rest verbatim into"
echo "    11_MEMORY_HANDOFF/MEMORY_BANK_ARCHIVE.md (reverse-chronological, newest"
echo "    archived entry first) rather than leaving them marked '(superseded)' in place."

# Flag same-day duplicates specifically — this is the GG-082 conflation mode
# (two concurrent sessions on the same date each writing their own block
# instead of consolidating into one).
DATES="$(printf '%s\n' "$HEADER_LINES" | grep -oE '\([0-9]{4}-[0-9]{2}-[0-9]{2}' | sort | uniq -c | awk '$1 > 1 {print $2}')"
if [ -n "$DATES" ]; then
  echo "!!  Same-day duplicates detected for: $(echo "$DATES" | tr -d '(' | tr '\n' ' ')"
  echo "    This is the recurring GG-082 narrative-conflation pattern — consolidate now."
fi

if [ "$STRICT" -eq 1 ]; then
  exit 1
fi
exit 0
