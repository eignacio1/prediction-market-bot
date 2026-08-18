#!/usr/bin/env bash
# session_end_timer.sh — GG-182's PENDING assertion, landed (T-455).
#
# WHY: a model cannot observe context/usage capacity in-band — there is no
# counter to read for the thing that actually ran out on 2026-08-14. Wall
# clock and word counts ARE observable. This script gives session-end a
# RECEIVED SIGNAL instead of a remembered rule: run `start` once at Step 0,
# `check` before the two expensive artifacts (DECISION_LOG, SESSION_HANDOFF),
# and `wordcheck` on any capped block. The verdict string is the point — a
# model that reads "BUDGET EXCEEDED, TRUNCATE NOW" behaves differently than
# one silently computing minutes against a cap it has to recall.
#
# State lives in logs/ (gitignored) — one file per checkout/worktree, so
# concurrent sessions in separate worktrees never collide (GG-101 pattern).
#
# USAGE:
#   scripts/session_end_timer.sh start
#   scripts/session_end_timer.sh check
#   scripts/session_end_timer.sh wordcheck <label> <cap>   # text on stdin
#   scripts/session_end_timer.sh merge-check   # GG-186/T-462: HEAD ancestor of origin/main?
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
STATE_FILE="$REPO_ROOT/logs/session_end_timer_state"
BUDGET_MIN=10

cmd="${1:-}"

case "$cmd" in
  start)
    mkdir -p "$REPO_ROOT/logs"
    now_iso="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    date -u +%s > "$STATE_FILE"
    echo "session_end_timer: START recorded ($now_iso)"
    ;;
  check)
    if [ ! -f "$STATE_FILE" ]; then
      echo "session_end_timer: NO START RECORDED — run 'start' at Step 0 first. Treating as OVER BUDGET (unknown elapsed is not safe to assume small)."
      exit 1
    fi
    start_epoch="$(cat "$STATE_FILE")"
    now_epoch="$(date -u +%s)"
    elapsed_s=$(( now_epoch - start_epoch ))
    elapsed_m=$(( elapsed_s / 60 ))
    if [ "$elapsed_m" -ge "$BUDGET_MIN" ]; then
      echo "session_end_timer: ELAPSED ${elapsed_m}m — BUDGET EXCEEDED, TRUNCATE NOW (session-end.md Truncation Path)"
      exit 1
    else
      echo "session_end_timer: ELAPSED ${elapsed_m}m — WITHIN BUDGET (<=${BUDGET_MIN}m)"
    fi
    ;;
  wordcheck)
    label="${2:?usage: session_end_timer.sh wordcheck <label> <cap>  (text on stdin)}"
    cap="${3:?usage: session_end_timer.sh wordcheck <label> <cap>  (text on stdin)}"
    words=$(wc -w | tr -d ' ')
    if [ "$words" -gt "$cap" ]; then
      echo "session_end_timer: ${label} = ${words} words — OVER cap (${cap})"
      exit 1
    else
      echo "session_end_timer: ${label} = ${words} words — PASS (cap ${cap})"
    fi
    ;;
  merge-check)
    # GG-186/T-462: the executable assertion behind session-end.md Step 8's
    # closure-row gate. "CLOSED" may only be written once this prints YES —
    # this is what makes "closed" and "on origin/main" the same fact instead
    # of two facts that can silently drift apart (T-456 x2, T-458, T-460).
    git fetch --quiet origin main 2>/dev/null || true
    branch="$(git rev-parse --abbrev-ref HEAD)"
    head_short="$(git rev-parse --short HEAD)"
    if git merge-base --is-ancestor HEAD origin/main 2>/dev/null; then
      echo "MERGE_CHECK: YES — HEAD (${head_short}) is an ancestor of origin/main"
    else
      echo "MERGE_CHECK: NO — branch ${branch} (HEAD ${head_short}) is NOT yet an ancestor of origin/main"
      exit 1
    fi
    ;;
  *)
    echo "usage: session_end_timer.sh {start|check|wordcheck <label> <cap>|merge-check}" >&2
    exit 2
    ;;
esac
