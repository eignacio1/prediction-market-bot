#!/usr/bin/env bash
# ============================================================================
# end_session_worktree.sh — retire an isolated session worktree (GG-101/T-259)
# Refuses to remove a worktree that still has uncommitted work, so isolation
# never becomes silent loss at teardown.
#
# USAGE:  scripts/end_session_worktree.sh <worktree-path>
# ============================================================================
set -euo pipefail

WT="${1:-}"
[ -n "$WT" ] || { echo "usage: end_session_worktree.sh <worktree-path>" >&2; exit 2; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
cd "$REPO_ROOT"

if [ ! -d "$WT" ]; then
  echo "⚠️  No such worktree path: $WT" >&2; exit 1
fi
if [ -n "$(git -C "$WT" status --porcelain)" ]; then
  echo "⚠️  $WT has uncommitted changes — commit & push before removing:" >&2
  git -C "$WT" status --short >&2
  exit 1
fi

BRANCH="$(git -C "$WT" rev-parse --abbrev-ref HEAD)"
git worktree remove "$WT"
echo "✅ Removed worktree: $WT"
echo "   Branch '$BRANCH' retained. After it is merged to main, delete it with:"
echo "     git branch -d $BRANCH  &&  git push origin --delete $BRANCH"
