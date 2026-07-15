#!/usr/bin/env bash
# ============================================================================
# write_session_checkpoint.sh — wrap the .last_session_checkpoint write (T-369)
#
# Prior to this script, the checkpoint pointer that powers ADR-0041's
# delta-first retrieval (scripts/session_delta.sh) was written by a single
# raw `git rev-parse --short HEAD > 04_EXECUTION/.last_session_checkpoint`
# line buried inside .claude/commands/session-end.md Step 6, with nothing
# checking it actually ran. A skipped Step 6 silently degrades the *next*
# session back to the full-read fallback with no visible symptom at the time
# it happens. This wrapper is the single place that write happens, so
# session_guard.sh's staleness check (below) has one script to trust instead
# of re-deriving the write logic itself.
#
# Format updated GG-103 (2026-07-15, reconciliation merge of PR #25/#26):
# the file is now an APPEND-ONLY log (checkpoint<TAB>timestamp<TAB>slug per
# row, merge=union in .gitattributes) instead of a single overwritten SHA,
# so two sessions closing concurrently both survive instead of one
# clobbering the other's pointer. session-start.md/session_guard.sh read
# only the LAST line.
#
# USAGE: scripts/write_session_checkpoint.sh [slug]
#   Appends "<short-SHA-of-HEAD>\t<UTC-timestamp>\t<slug>" to
#   04_EXECUTION/.last_session_checkpoint. `slug` defaults to "session-end"
#   if omitted. Caller (session-end.md Step 6) is responsible for committing
#   the result in the same path-scoped commit as the SESSION_HANDOFF file.
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
cd "$REPO_ROOT"

CHECKPOINT_FILE="04_EXECUTION/.last_session_checkpoint"
SHA="$(git rev-parse --short HEAD)"
SLUG="${1:-session-end}"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

printf '%s\t%s\t%s\n' "$SHA" "$TS" "$SLUG" >> "$CHECKPOINT_FILE"
echo "Checkpoint appended: $CHECKPOINT_FILE -> $SHA ($TS, $SLUG)"
