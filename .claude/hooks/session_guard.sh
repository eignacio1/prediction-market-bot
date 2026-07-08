#!/usr/bin/env bash
# ============================================================================
# session_guard.sh — concurrent-session safety guard (GG-082 / GG-101 / T-259)
#
# Run at session start (after claiming) AND before every commit into a shared
# tree. Surfaces the four things that cause concurrent-session contamination:
#   (a) whether you are isolated (own branch/worktree) or in the shared main tree
#   (b) HEAD vs origin/main drift (must re-sync before trusting shared-doc text)
#   (c) other sessions' recent claims
#   (d) foreign uncommitted changes you could accidentally sweep into a commit
#
# Non-destructive: reads only. Never modifies the tree.
# ============================================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
cd "$REPO_ROOT"

echo "================ SESSION GUARD ================"
BR="$(git rev-parse --abbrev-ref HEAD)"
echo "worktree : $REPO_ROOT"
echo "branch   : $BR"
if [ "$BR" = "main" ]; then
  echo "!!  On 'main' — this is likely the SHARED tree. For concurrent work, prefer:"
  echo "      scripts/new_session_worktree.sh \"<focus>\""
  echo "    In a shared tree, NEVER 'git add -A' / 'git commit -a'. Commit only your"
  echo "    own files, path-scoped (git commit <file1> <file2> ...). (GG-101)"
else
  echo "OK  Isolated branch — worktree-isolated from other sessions."
fi

echo "--- HEAD vs origin/main ---"
if git fetch --quiet origin main 2>/dev/null; then
  LOCAL="$(git rev-parse HEAD)"
  REMOTE="$(git rev-parse origin/main 2>/dev/null || echo none)"
  if [ "$LOCAL" = "$REMOTE" ]; then
    echo "OK  up to date with origin/main"
  else
    echo "!!  HEAD != origin/main. Re-sync before trusting any shared-doc narrative (Hard Rule 10)."
    echo "    behind by:"
    git --no-pager log --oneline "$LOCAL..$REMOTE" 2>/dev/null | head -5 || true
  fi
else
  echo "(fetch failed — offline? treat shared-doc narratives as possibly stale)"
fi

echo "--- Other sessions' recent claims (tail SESSION_CLAIMS.md) ---"
[ -f 04_EXECUTION/SESSION_CLAIMS.md ] && tail -6 04_EXECUTION/SESSION_CLAIMS.md

echo "--- Uncommitted changes in THIS tree ---"
if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
  echo "OK  clean working tree"
else
  echo "!!  Uncommitted changes present. In a SHARED tree, some may belong to a"
  echo "    CONCURRENT session — commit ONLY your own files, path-scoped. Do not"
  echo "    stash / reset --hard / checkout -- / clean another session's work. (GG-101)"
  git --no-pager status --short
fi
echo "=============================================="
