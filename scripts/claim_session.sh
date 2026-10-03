#!/usr/bin/env bash
# ============================================================================
# claim_session.sh — atomic concurrent-session claim (GG-082 hardening / GG-101)
#
# Serializes session claims THROUGH origin so two blind concurrent sessions
# cannot silently reserve the same T-/GG-/ADR- number (the real 2026-07-07
# T-247 double-claim race). The claim row is committed and pushed by itself;
# if another session pushed first, we rebase onto their claim (SESSION_CLAIMS.md
# is merge=union, so both rows survive automatically) and retry the push.
#
# USAGE:  scripts/claim_session.sh "<one-line focus>" ["<T-/GG-/ADR- range or TBD>"]
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
cd "$REPO_ROOT"
CLAIMS="04_EXECUTION/SESSION_CLAIMS.md"

FOCUS="${1:-}"
RANGE="${2:-TBD}"
if [ -z "$FOCUS" ]; then
  echo "usage: claim_session.sh \"<one-line focus>\" [\"<T-/GG-/ADR- range or TBD>\"]" >&2
  exit 2
fi

# Guard: only the claims file may be mutated by this script. If other files are
# already staged, refuse — a claim must be committed on its own (CLAUDE.md Step 0).
if [ -n "$(git diff --cached --name-only)" ]; then
  echo "⚠️  You have staged changes. The claim must be committed by itself." >&2
  echo "    Unstage first:  git restore --staged ." >&2
  exit 1
fi

# Fetch ALL origin branches, not just main, so check_id_collision (GG-236)
# can see a GG-/ADR- header registered only on a pushed-but-unlanded session
# branch — the blind spot that predicted, and then still failed to prevent,
# T-513's GG-237 near-collision. main is still the only branch we rebase
# onto below; the extra remote-tracking refs are read-only collision-scan
# input, nothing merges from them.
git fetch --quiet origin '+refs/heads/*:refs/remotes/origin/*' || git fetch --quiet origin main

# GG-419: we push HEAD:main below, so every local commit not already on
# origin/main would land on main with the claim (49.1 landed 7 untested NFL
# commits this way). Refuse unless HEAD carries nothing beyond origin/main —
# then the only commit the push can add is the claim itself.
UNLANDED="$(git rev-list --count origin/main..HEAD)"
if [ "$UNLANDED" != "0" ]; then
  echo "❌ Refusing claim: HEAD has $UNLANDED commit(s) not on origin/main; pushing the claim would land them on main (GG-419)." >&2
  echo "   Claim from a clean checkout of origin/main (e.g. a fresh worktree), then return to your branch." >&2
  exit 1
fi
git pull --quiet --rebase origin main || true

# Pre-claim collision check (GG-107 root-cause fix): refuse to claim any
# T-/GG-/ADR- ID already registered in TODO_NEXT.md, SESSION_CLAIMS.md,
# DECISION_LOG.md, or (GG-236) canonically headered on an unlanded branch.
# Runs against the just-fetched/rebased state so it checks the true current
# registry, not a stale local view.
source "$SCRIPT_DIR/lib/check_id_collision.sh"
if ! check_id_collision "$RANGE" "$REPO_ROOT"; then
  echo "❌ Refusing claim: one or more IDs in \"$RANGE\" are already registered/in use (see COLLISION lines above)." >&2
  echo "   Pick IDs above the current highest-in-use (grep TODO_NEXT.md/SESSION_CLAIMS.md/DECISION_LOG.md) and retry." >&2
  exit 1
fi

STAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
ROW="$(printf '| %s | %s | %s |' "$STAMP" "$RANGE" "$FOCUS")"
printf '%s\n' "$ROW" >> "$CLAIMS"
git add "$CLAIMS"
git commit --quiet -m "Session claim: ${RANGE} — ${FOCUS}"

for attempt in 1 2 3 4 5; do
  if git push --quiet origin HEAD:main; then
    echo "✅ Claim pushed (attempt $attempt): $STAMP | $RANGE | $FOCUS"
    exit 0
  fi
  echo "… push rejected — a concurrent session pushed first. Rebasing (union-merges the claim) and retrying ($attempt/5)."
  git fetch --quiet origin '+refs/heads/*:refs/remotes/origin/*' || git fetch --quiet origin main
  git pull --quiet --rebase origin main || {
    echo "⚠️  Rebase hit a conflict outside SESSION_CLAIMS.md. Resolve manually, then: git push origin HEAD:main" >&2
    exit 1
  }
  # GG-322 / T-595: the check above ran ONCE, before our commit. The rebase we
  # just did may have brought in another session's claim for the same ID (that is
  # exactly what a rejected push means), and union-merge keeps both rows. Re-verify
  # unconditionally on EVERY retry, ignoring only our own row. On a collision,
  # take our claim back out (path-scoped to the claims file) and refuse.
  if ! check_id_collision "$RANGE" "$REPO_ROOT" "$ROW"; then
    echo "❌ Refusing claim: while the push was retrying, another session claimed an ID in \"$RANGE\" (see COLLISION lines above). Withdrawing our local claim; nothing was pushed." >&2
    git reset --soft HEAD~1
    git restore --staged -- "$CLAIMS"
    grep -vxF -- "$ROW" "$CLAIMS" > "$CLAIMS.tmp.$$" || true
    mv "$CLAIMS.tmp.$$" "$CLAIMS"
    exit 1
  fi
done
echo "⚠️  Could not push the claim after 5 attempts. Your claim commit is local — push it manually before proceeding." >&2
exit 1
