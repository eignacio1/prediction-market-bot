#!/usr/bin/env bash
# sweep_stray_branches.sh — report every session branch that is not an ancestor of origin/main,
# and (opt-in, --execute) clean up the opposite case: local branches that ARE fully landed but
# still sitting around undeleted, plus stale worktree administrative metadata.
#
# The NOT-LANDED report above the "---" is still REPORT ONLY — never merges, never deletes, always
# exits 0. A stray unlanded branch is the operator's routing decision (it becomes a Deliverable 0 in
# a queue block), NOT work for whichever session happens to notice it — Hard Rule 11. Do not
# "helpfully" land someone else's branch because this printed it.
#
# The landed-branch cleanup added below it (T-570, 2026-09-23) is the mirror case: a LOCAL branch
# that IS an ancestor of origin/main (its work already landed) but was never deleted. That is pure
# filing, not adjudication — deleting a branch whose content is already on main discards nothing.
# Default is still report-only; pass --execute to actually delete. Only ever `git branch -d`
# (refuses automatically on anything not safely merged) — NEVER `-D`. `git worktree prune` is run
# unconditionally in both modes: it only removes administrative metadata for a worktree directory
# that no longer exists on disk, never a branch or a live worktree's files, so there is no unsafe
# "would prune" state worth gating behind --execute.
#
# Usage: scripts/sweep_stray_branches.sh [max_age_days] [--execute]   (default max_age_days=30, 0 = no age filter)
set -uo pipefail

MAX_AGE_DAYS=30
EXECUTE=0
for arg in "$@"; do
  case "$arg" in
    --execute) EXECUTE=1 ;;
    *) MAX_AGE_DAYS="$arg" ;;
  esac
done
cd "$(git rev-parse --show-toplevel)"

echo "=== stray-branch sweep — $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
if git fetch --quiet origin '+refs/heads/*:refs/remotes/origin/*' 2>/dev/null; then
  echo "fetched origin — ancestor checks below are against live origin/main"
else
  echo "⚠️  COULD NOT FETCH. origin/main is frozen at whatever a prior fetch left."
  echo "    A 'NOT LANDED' line below may be false. 'LANDED' is still trustworthy."
fi
echo "origin/main = $(git rev-parse --short origin/main 2>/dev/null || echo UNKNOWN)"
echo

NOW_S=$(date -u +%s)
FOUND=0
while read -r ref; do
  [ -z "$ref" ] && continue
  case "$ref" in */origin/main|*/origin/HEAD) continue;; esac
  git merge-base --is-ancestor "$ref" origin/main 2>/dev/null && continue

  tip=$(git rev-parse --short "$ref" 2>/dev/null) || continue
  n=$(git rev-list --count origin/main.."$ref" 2>/dev/null || echo "?")
  ts=$(git log -1 --format=%ct "$ref" 2>/dev/null || echo "$NOW_S")
  age_d=$(( (NOW_S - ts) / 86400 ))
  if [ "$MAX_AGE_DAYS" != "0" ] && [ "$age_d" -gt "$MAX_AGE_DAYS" ]; then continue; fi

  FOUND=$((FOUND+1))
  printf 'NOT LANDED  %2s commits  %3sd old  tip=%s  %s\n' "$n" "$age_d" "$tip" "${ref#refs/remotes/}"
done < <(git for-each-ref --format='%(refname)' refs/remotes/origin 2>/dev/null)

echo
if [ "$FOUND" -eq 0 ]; then
  echo "CLEAN — no unlanded session branch newer than ${MAX_AGE_DAYS}d."
else
  echo "${FOUND} unlanded branch(es). If one of them is YOURS, land it now — that is Step 8."
  echo "If it is not yours: report it in the SESSION_HANDOFF and the operator digest. Do NOT merge it."
  echo "Caveat: a branch whose content landed under different SHAs (rebase/cherry-pick/squash) still"
  echo "reads NOT LANDED here. Check whether its gap/task is already resolved on main before flagging."
fi

echo
echo "=== landed local branches — cleanup ($([ "$EXECUTE" = "1" ] && echo EXECUTE || echo report-only)) ==="
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
LOCAL_FOUND=0
while read -r ref; do
  [ -z "$ref" ] && continue
  branch="${ref#refs/heads/}"
  [ "$branch" = "main" ] && continue
  git merge-base --is-ancestor "$ref" origin/main 2>/dev/null || continue

  LOCAL_FOUND=$((LOCAL_FOUND+1))
  if [ "$branch" = "$CURRENT_BRANCH" ]; then
    echo "SKIP (currently checked out here)   $branch"
    continue
  fi
  if [ "$EXECUTE" = "1" ]; then
    if out=$(git branch -d "$branch" 2>&1); then
      echo "DELETED (landed, git branch -d)   $branch"
    else
      echo "SKIP (git branch -d refused -- investigate before forcing)   $branch : $out"
    fi
  else
    echo "LANDED, not yet deleted   $branch   (would run: git branch -d $branch)"
  fi
done < <(git for-each-ref --format='%(refname)' refs/heads 2>/dev/null)

if [ "$LOCAL_FOUND" -eq 0 ]; then
  echo "CLEAN — no landed local branches pending deletion."
elif [ "$EXECUTE" != "1" ]; then
  echo "${LOCAL_FOUND} landed local branch(es) found. Re-run with --execute to delete (git branch -d only, never -D)."
fi

echo
echo "=== worktree prune ==="
# Always safe, both modes: only removes admin metadata for worktrees whose directory is already
# gone from disk. Never touches a branch or a live worktree's files.
git worktree prune -v 2>&1 || true

exit 0
