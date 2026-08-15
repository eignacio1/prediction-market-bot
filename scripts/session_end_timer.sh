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
  *)
    echo "usage: session_end_timer.sh {start|check|wordcheck <label> <cap>}" >&2
    exit 2
    ;;
esac
