#!/usr/bin/env bash
# ============================================================================
# new_session_worktree.sh — isolated concurrent-session launcher
# Resolves GG-101 / T-259 (shared-working-tree concurrent-session risk).
#
# WHY: Every terminal session previously ran `cd` into the SAME physical git
# working tree on `main`. A git op in one session (stash / reset --hard /
# checkout -- / clean -fd) can touch another session's UNCOMMITTED files.
# SESSION_CLAIMS.md made sessions VISIBLE but did not ISOLATE them.
#
# This creates a dedicated `git worktree` + short-lived branch, checked out
# from a freshly-fetched origin/main. Two sessions launched this way have
# physically separate checkouts — one cannot clobber the other's files.
#
# USAGE:  scripts/new_session_worktree.sh "short-focus-slug"
# EXAMPLE: scripts/new_session_worktree.sh gg095-brier-ladder
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
cd "$REPO_ROOT"

SLUG="${1:-session}"
SLUG="$(printf '%s' "$SLUG" | tr '[:upper:] ' '[:lower:]-' | tr -cd '[:alnum:]-' | cut -c1-40)"
[ -n "$SLUG" ] || SLUG="session"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BRANCH="session/${STAMP}-${SLUG}"

WT_PARENT="$(dirname "$REPO_ROOT")/PM-worktrees"
WT_PATH="${WT_PARENT}/${STAMP}-${SLUG}"

echo "==> Fetching origin/main (isolation always starts from a fresh base) ..."
git fetch --quiet origin main

mkdir -p "$WT_PARENT"
echo "==> Creating isolated worktree"
echo "    path   : $WT_PATH"
echo "    branch : $BRANCH  (from origin/main)"
git worktree add -b "$BRANCH" "$WT_PATH" origin/main >/dev/null

cat <<EOF

✅ Isolated session worktree ready.

  cd "$WT_PATH"

Then, inside it:
  • You are on your own branch  $BRANCH  — a physically separate checkout.
  • Run the CLAUDE.md session-start protocol (Step 0 first):
        scripts/claim_session.sh "<one-line focus>" "<T-/GG-/ADR- range or TBD>"
        bash .claude/hooks/session_guard.sh
  • Commit early and often — do not accumulate large uncommitted state.
  • When done:
        git push -u origin "$BRANCH"     # then fast-forward-merge / PR into main
        scripts/end_session_worktree.sh "$WT_PATH"

Concurrent sessions launched this way CANNOT stash/reset/clobber each other.
(GG-101 / T-259)
EOF
