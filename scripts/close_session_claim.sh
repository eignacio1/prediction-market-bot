#!/usr/bin/env bash
# close_session_claim.sh — write this session's closure row to SESSION_CLAIMS.md ON origin/main,
# independently of whether this session's own branch ever merges.
#
# WHY THIS EXISTS (GG-186 follow-on, 2026-09-17):
#   Step 6-gen appends the closure row to SESSION_CLAIMS.md *on the session's own branch*. When the
#   branch never merges, that row never reaches origin/main — so the row whose entire job is to make
#   an unmerged branch visible is itself trapped on the unmerged branch. Observed three times in two
#   waves (T-545, T-547, T-551): all three finished, pushed, and wrote a closure row, and origin/main
#   shows no row for any of them. The next session's claims scan therefore sees nothing to clean up.
#
#   This script mirrors scripts/claim_session.sh exactly — commit the row ALONE, push straight to
#   origin/main with rebase-retry, relying on SESSION_CLAIMS.md's merge=union attribute. Claim rows
#   have always reached main this way; closure rows never did. Now they do.
#
# Usage:
#   scripts/close_session_claim.sh "<TASK_ID>" "<one-line summary>"
#
# Writes CLOSED if HEAD is an ancestor of origin/main, otherwise "MERGED: NO — branch <name>
# awaiting merge". It never lies about the state and never fails the session: a push that cannot
# land prints loudly and exits nonzero, but the row is already committed locally either way.
set -euo pipefail

TASK_ID="${1:-}"
SUMMARY="${2:-}"
if [[ -z "$TASK_ID" || -z "$SUMMARY" ]]; then
  echo "usage: scripts/close_session_claim.sh \"<TASK_ID>\" \"<one-line summary>\"" >&2
  exit 2
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
CLAIMS="04_EXECUTION/SESSION_CLAIMS.md"
cd "$REPO_ROOT"

git fetch --quiet origin main 2>/dev/null || true

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
HEAD_SHORT="$(git rev-parse --short HEAD)"
NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

if git merge-base --is-ancestor HEAD origin/main 2>/dev/null; then
  STATE="CLOSED — merge confirmed, HEAD (${HEAD_SHORT}) is ancestor of origin/main"
  echo "MERGE_CHECK: YES — writing CLOSED row."
else
  STATE="MERGED: NO — branch \`${BRANCH}\` awaiting merge (HEAD ${HEAD_SHORT} not on origin/main)"
  echo "MERGE_CHECK: NO — writing an honest 'MERGED: NO' row. This is the point: the row reaches"
  echo "              origin/main even though your branch has not, so the stray is visible."
fi

printf '| %s | %s | %s — %s |\n' "$NOW" "$TASK_ID" "$STATE" "$SUMMARY" >> "$CLAIMS"

# Commit the row ALONE — never sweep other work into this commit (Step 0d / GG-101).
git add "$CLAIMS"
git commit --quiet -m "Session close: ${TASK_ID} — ${STATE%% —*}"

for attempt in 1 2 3 4 5; do
  if git push --quiet origin HEAD:main; then
    echo "✅ Closure row for ${TASK_ID} is on origin/main."
    exit 0
  fi
  echo "… push rejected — a concurrent session pushed first. Rebasing (union-merges the row) and retrying ($attempt/5)."
  git fetch --quiet origin main
  git pull --quiet --rebase origin main || {
    echo "⚠️  Rebase hit a conflict outside ${CLAIMS}. Resolve manually, then: git push origin HEAD:main" >&2
    exit 1
  }
done

echo "⚠️  Could not push the closure row to origin/main after 5 attempts. It IS committed locally." >&2
echo "    Report this to the operator — do not end the session claiming the row landed." >&2
exit 1
