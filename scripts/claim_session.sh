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

git fetch --quiet origin main
git pull --quiet --rebase origin main || true

STAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf '| %s | %s | %s |\n' "$STAMP" "$RANGE" "$FOCUS" >> "$CLAIMS"
git add "$CLAIMS"
git commit --quiet -m "Session claim: ${RANGE} — ${FOCUS}"

for attempt in 1 2 3 4 5; do
  if git push --quiet origin HEAD:main; then
    echo "✅ Claim pushed (attempt $attempt): $STAMP | $RANGE | $FOCUS"
    exit 0
  fi
  echo "… push rejected — a concurrent session pushed first. Rebasing (union-merges the claim) and retrying ($attempt/5)."
  git fetch --quiet origin main
  git pull --quiet --rebase origin main || {
    echo "⚠️  Rebase hit a conflict outside SESSION_CLAIMS.md. Resolve manually, then: git push origin HEAD:main" >&2
    exit 1
  }
done
echo "⚠️  Could not push the claim after 5 attempts. Your claim commit is local — push it manually before proceeding." >&2
exit 1
