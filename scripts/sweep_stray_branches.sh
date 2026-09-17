#!/usr/bin/env bash
# sweep_stray_branches.sh — report every session branch that is not an ancestor of origin/main.
#
# REPORT ONLY. It merges nothing, deletes nothing, and always exits 0.
# A stray branch is the operator's routing decision (it becomes a Deliverable 0 in a queue block),
# NOT work for whichever session happens to notice it — Hard Rule 11. Do not "helpfully" land
# someone else's branch because this printed it.
#
# Always fetches first: an ancestor check against a stale ref produces false "not landed" calls.
# Note the asymmetry — "LANDED" is monotone and safe even on a stale ref; "NOT LANDED" is not.
#
# Usage: scripts/sweep_stray_branches.sh [max_age_days]   (default 30; 0 = no age filter)
set -uo pipefail

MAX_AGE_DAYS="${1:-30}"
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
exit 0
