#!/usr/bin/env bash
# ============================================================================
# check_future_timestamps.sh — audit-trail integrity check
#
# WHY: this project's institutional memory (DECISION_LOG.md, SESSION_CLAIMS.md,
# governance-gap timelines) depends on timestamps being trustworthy for
# reconstructing "what happened when." A 2026-07-15 efficiency review found
# SESSION_CLAIMS.md rows timestamped ahead of what looked like the current
# session clock — traced to a timezone-display artifact (env context showing
# a Pacific-time date string one calendar day behind the real UTC clock used
# to stamp entries), NOT a real defect. That review is exactly the kind of
# thing this script should catch automatically instead of a human tracing it
# by hand every time: flag anything stamped meaningfully ahead of the real
# system UTC clock at the moment the check runs, so a genuine clock-skew bug
# (a real one, not a display artifact) doesn't go unnoticed.
#
# USAGE:  scripts/check_future_timestamps.sh [--tolerance-min N]
#   --tolerance-min N   allow up to N minutes of clock drift before flagging
#                       (default 15 — generous enough to absorb normal
#                       git-fetch/commit latency, tight enough to catch a
#                       real skew of hours or days)
#
# Checks:
#   1. SESSION_CLAIMS.md — every row's leading ISO-8601 timestamp
#   2. Last N days of git log commit timestamps (author date)
#
# Exit code: 0 if clean, 1 if any future-dated entry found (beyond tolerance).
# This is a read-only diagnostic — it does not modify any file.
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
cd "$REPO_ROOT"

TOLERANCE_MIN=15
if [ "${1:-}" = "--tolerance-min" ]; then
  TOLERANCE_MIN="${2:-15}"
fi

NOW_EPOCH="$(date -u +%s)"
TOLERANCE_SEC=$(( TOLERANCE_MIN * 60 ))
FOUND_ISSUE=0

echo "================================================================"
echo "TIMESTAMP INTEGRITY CHECK"
echo "Real system UTC now: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Tolerance: ${TOLERANCE_MIN} minutes"
echo "================================================================"

echo ""
echo "--- 1. SESSION_CLAIMS.md row timestamps ---"
CLAIMS="04_EXECUTION/SESSION_CLAIMS.md"
if [ -f "$CLAIMS" ]; then
  while IFS= read -r line; do
    ts="$(printf '%s' "$line" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z' | head -1 || true)"
    [ -z "$ts" ] && continue
    ts_epoch="$(date -u -d "$ts" +%s 2>/dev/null || date -u -j -f "%Y-%m-%dT%H:%M:%SZ" "$ts" +%s 2>/dev/null || echo "")"
    [ -z "$ts_epoch" ] && continue
    delta=$(( ts_epoch - NOW_EPOCH ))
    if [ "$delta" -gt "$TOLERANCE_SEC" ]; then
      echo "  !! FUTURE-DATED ROW (+$(( delta / 60 )) min ahead): $ts"
      echo "     $line" | cut -c1-160
      FOUND_ISSUE=1
    fi
  done < "$CLAIMS"
else
  echo "  (SESSION_CLAIMS.md not found — skipped)"
fi
[ "$FOUND_ISSUE" -eq 0 ] && echo "  clean — no SESSION_CLAIMS.md row exceeds tolerance"

echo ""
echo "--- 2. Recent commit author-date check (last 50 commits) ---"
COMMIT_ISSUE=0
while IFS= read -r commit_line; do
  sha="${commit_line%% *}"
  ts_epoch="${commit_line#* }"
  delta=$(( ts_epoch - NOW_EPOCH ))
  if [ "$delta" -gt "$TOLERANCE_SEC" ]; then
    echo "  !! FUTURE-DATED COMMIT (+$(( delta / 60 )) min ahead): $sha ($(git show -s --format=%ad --date=iso-strict "$sha"))"
    COMMIT_ISSUE=1
    FOUND_ISSUE=1
  fi
done < <(git log -50 --format="%H %at")
[ "$COMMIT_ISSUE" -eq 0 ] && echo "  clean — no recent commit exceeds tolerance"

echo ""
echo "================================================================"
if [ "$FOUND_ISSUE" -eq 0 ]; then
  echo "RESULT: clean."
  exit 0
else
  echo "RESULT: future-dated entries found beyond tolerance — investigate before"
  echo "trusting sequence-of-events reconstructions from the flagged file(s)."
  echo "Note: a flagged entry is not automatically a bug — check for a"
  echo "timezone-display mismatch (local-time string vs. UTC clock) before"
  echo "assuming genuine clock skew. See ADR/DECISION_LOG note, 2026-07-15."
  exit 1
fi
