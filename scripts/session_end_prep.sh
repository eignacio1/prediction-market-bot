#!/usr/bin/env bash
# ============================================================================
# session_end_prep.sh — precompute "what happened this session" (Fix 2,
# session-end protocol tiering plan, 2026-07-24)
#
# WHY: session_delta.sh answers "what changed since I last read the nav
# files" at session START. Nothing answered the symmetric question at
# session END — "what did THIS session actually do" — so /session-end had
# to be reconstructed by hand from memory/scrollback every time, which is
# slow and burns tokens re-deriving facts already sitting in git.
#
# This script computes that fresh against live git state in one call:
#   1. Commits made this session (base_ref..HEAD)
#   2. Files touched + diff --stat
#   3. Whether any src/ path changed (drives the MICRO/STANDARD tier call)
#   4. "decisions_logged: false" hits (CLAUDE.md Step 1, re-run so a session
#      doesn't have to re-grep by hand at close-out)
#   5. Any full-suite pytest summary line ("N passed, M skipped, K failed")
#      this session already logged in DECISION_LOG.md — a lightweight proxy
#      for "test-count delta" that does NOT re-run the suite itself (this
#      script must stay cheap; re-running ~2800 tests here would defeat the
#      whole point of a fast prep step).
#   6. This session's own SESSION_CLAIMS.md row, if any (reminder of what was
#      claimed, for the close-out narrative).
#   7. A suggested tier: MICRO if no src/ paths changed (doc/governance-only
#      session), STANDARD otherwise. This is a SUGGESTION only — the session
#      itself makes the final call per session-end.md's routing criteria.
#
# This script does NOT touch, weaken, or substitute for Step 0/Step 1A or
# any worktree/claim/guard mechanic (GG-101/GG-082) — those remain mandatory
# and untiered regardless of what this script reports. See CLAUDE.md Hard
# Rule 10 / Step 0.
#
# Usage: scripts/session_end_prep.sh [base_ref]
#   base_ref — defaults to `git merge-base HEAD origin/main`, which is the
#   correct "session start point" for any branch created by
#   new_session_worktree.sh (always forked fresh from origin/main).
# ============================================================================
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"

BASE_REF="${1:-}"
if [ -z "$BASE_REF" ]; then
    git fetch --quiet origin main 2>/dev/null || true
    BASE_REF="$(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD main 2>/dev/null || echo "")"
    if [ -z "$BASE_REF" ]; then
        echo "ERROR: could not determine a base ref (no origin/main or main reachable)." >&2
        echo "Pass one explicitly: scripts/session_end_prep.sh <ref>" >&2
        exit 1
    fi
fi

if ! git rev-parse --verify --quiet "${BASE_REF}^{commit}" >/dev/null; then
    echo "ERROR: '$BASE_REF' is not a valid git ref in this repo." >&2
    exit 1
fi

BRANCH="$(git rev-parse --abbrev-ref HEAD)"

echo "================================================================"
echo "SESSION END PREP — $(git rev-parse --short "$BASE_REF") ($BASE_REF) -> HEAD ($(git rev-parse --short HEAD))"
echo "Branch: $BRANCH"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "This is a SUGGESTION/precompute step only — it does not replace Step"
echo "0/1A or any worktree/claim/guard mechanic (Hard Rule 10, GG-101/GG-082)."
echo "================================================================"

echo ""
echo "--- 1. Commits this session ---"
COMMIT_LIST="$(git --no-pager log --oneline "$BASE_REF"..HEAD 2>/dev/null)"
if [ -z "$COMMIT_LIST" ]; then
    echo "(no commits yet on this branch since $BASE_REF)"
else
    printf '%s\n' "$COMMIT_LIST"
fi
COMMIT_COUNT=0
[ -n "$COMMIT_LIST" ] && COMMIT_COUNT="$(printf '%s\n' "$COMMIT_LIST" | wc -l | tr -d ' ')"

echo ""
echo "--- 2. Files touched + diff --stat ---"
DIFFSTAT="$(git --no-pager diff --stat "$BASE_REF"..HEAD 2>/dev/null)"
if [ -z "$DIFFSTAT" ]; then
    echo "(no file changes since $BASE_REF)"
else
    echo "$DIFFSTAT"
fi

echo ""
echo "--- 3. src/ touched? (drives tier suggestion) ---"
SRC_CHANGED="$(git --no-pager diff --name-only "$BASE_REF"..HEAD -- 'src/' 2>/dev/null)"
if [ -z "$SRC_CHANGED" ]; then
    echo "NO  — no src/ paths changed this session."
    TIER_SUGGESTION="MICRO"
else
    echo "YES — src/ paths changed:"
    printf '%s\n' "$SRC_CHANGED" | sed 's/^/    /'
    TIER_SUGGESTION="STANDARD"
fi

echo ""
echo "--- 4. 'Decisions logged: false' hits (CLAUDE.md Step 1) ---"
DOC_DEBT="$(grep -rn "^\*\*Decisions logged:\*\* false" \
    "02_ARCHITECTURE_DESIGN/" "08_MODEL_RISK_GOVERNANCE/" "01_SPEC/" 2>/dev/null)"
if [ -z "$DOC_DEBT" ]; then
    echo "CLEAN — no unlogged strategic decisions found."
else
    echo "$DOC_DEBT"
fi

echo ""
echo "--- 5. Full-suite test summary logged this session (proxy for test-count delta) ---"
if [ -f "03_DECISIONS/DECISION_LOG/DECISION_LOG.md" ]; then
    SESSION_TEST_LINES="$(git --no-pager diff "$BASE_REF"..HEAD -- "03_DECISIONS/DECISION_LOG/DECISION_LOG.md" 2>/dev/null \
        | grep -E '^\+.*[0-9]+ passed.*[0-9]+ skipped.*[0-9]+ failed' | sed 's/^+//' || true)"
    if [ -n "$SESSION_TEST_LINES" ]; then
        echo "$SESSION_TEST_LINES" | sed 's/^/    /'
    else
        echo "(no full-suite pytest summary line added to DECISION_LOG.md this session — run the suite"
        echo " before close-out if src/ or tests/ changed, and log the result.)"
    fi
else
    echo "(DECISION_LOG.md not found)"
fi

echo ""
echo "--- 6. This session's own SESSION_CLAIMS.md row ---"
if [ -f "04_EXECUTION/SESSION_CLAIMS.md" ]; then
    # claim_session.sh never writes the branch name into the row itself (rows are
    # "| timestamp | range | focus |") — matching on $BRANCH directly either never
    # hits (real session/<ts>-<slug> branches) or, on 'main', spuriously matches the
    # substring "main" anywhere in decades of unrelated free-text rows (GG-139).
    # Session branches follow session/<YYYYMMDDTHHMMSSZ>-<slug>; convert that
    # timestamp to the row's ISO format and match on it instead — it's unique.
    CLAIM_TS="$(echo "$BRANCH" | grep -oE '[0-9]{8}T[0-9]{6}Z' | sed -E 's/^([0-9]{4})([0-9]{2})([0-9]{2})T([0-9]{2})([0-9]{2})([0-9]{2})Z$/\1-\2-\3T\4:\5:\6Z/' || true)"
    if [ -n "$CLAIM_TS" ]; then
        CLAIM_ROW="$(grep -F "$CLAIM_TS" 04_EXECUTION/SESSION_CLAIMS.md 2>/dev/null || true)"
        if [ -n "$CLAIM_ROW" ]; then
            echo "$CLAIM_ROW"
        else
            echo "(no SESSION_CLAIMS.md row found matching this session's timestamp '$CLAIM_TS' — confirm claim_session.sh was run at start.)"
        fi
    else
        echo "(branch '$BRANCH' doesn't match session/<timestamp>-<slug> — no reliable per-session match possible."
        echo " Showing last 2 SESSION_CLAIMS.md rows for reference instead:)"
        tail -2 04_EXECUTION/SESSION_CLAIMS.md
    fi
else
    echo "(SESSION_CLAIMS.md not found)"
fi

echo ""
echo "--- 7. Suggested tier: $TIER_SUGGESTION ---"
echo "    ($COMMIT_COUNT commit(s), src/ changed: $([ "$TIER_SUGGESTION" = STANDARD ] && echo yes || echo no))"
echo "    This is a suggestion for session-end.md's routing step, not a decision —"
echo "    Step 0/1A and all worktree/claim/guard mechanics apply regardless of tier."

echo ""
echo "================================================================"
echo "END SESSION END PREP"
echo "================================================================"
