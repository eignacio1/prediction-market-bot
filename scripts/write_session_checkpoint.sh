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
# USAGE: scripts/write_session_checkpoint.sh
#   Writes the short SHA of current HEAD to 04_EXECUTION/.last_session_checkpoint.
#   Caller (session-end.md Step 6) is responsible for committing the result
#   in the same path-scoped commit as the SESSION_HANDOFF file.
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
cd "$REPO_ROOT"

CHECKPOINT_FILE="04_EXECUTION/.last_session_checkpoint"
SHA="$(git rev-parse --short HEAD)"

echo "$SHA" > "$CHECKPOINT_FILE"
echo "Checkpoint written: $CHECKPOINT_FILE -> $SHA"
