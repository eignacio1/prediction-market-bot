#!/usr/bin/env bash
# ============================================================================
# session_guard.sh — concurrent-session safety guard (GG-082 / GG-101 / T-259 / T-335)
#
# Run at session start (after claiming) AND before every commit into a shared
# tree. Surfaces the five things that cause concurrent-session contamination:
#   (a) whether you are isolated (own branch/worktree) or in the shared main tree
#   (b) HEAD vs origin/main drift (must re-sync before trusting shared-doc text)
#   (c) other sessions' recent claims, and whether that adds up to a live
#       GG-101 near-miss (this session on shared main + another session
#       claimed work in roughly the same window)
#   (d) foreign uncommitted changes you could accidentally sweep into a commit
#   (e) MEMORY_BANK.md snapshot-count hygiene (T-334)
#
# Isolated worktrees (scripts/new_session_worktree.sh) are the DEFAULT way to
# start a session, not a conditional recommendation — see CLAUDE.md Step 0a.
# Only skip it if you have first confirmed, via this script, that no other
# session is plausibly active in the shared tree right now.
#
# Modes:
#   (no args)             informational — reads only, never modifies the tree,
#                          always exits 0.
#   --guard-destructive    same reads, but exits 1 (refuses) if run on 'main'
#                          with uncommitted changes present. Run this before
#                          any destructive git op (reset --hard, checkout --,
#                          clean -fd, stash without -u accounting) in a shared
#                          tree — a non-zero exit means STOP, the uncommitted
#                          state may belong to a concurrent session (GG-101).
# ============================================================================
set -uo pipefail

MODE="${1:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
cd "$REPO_ROOT"

echo "================ SESSION GUARD ================"
BR="$(git rev-parse --abbrev-ref HEAD)"
echo "worktree : $REPO_ROOT"
echo "branch   : $BR"
if [ "$BR" = "main" ]; then
  echo "!!  On 'main' — this is likely the SHARED tree. Isolated worktrees are the"
  echo "    DEFAULT session launch (CLAUDE.md Step 0a), not just a suggestion:"
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

echo "--- Checkpoint staleness (T-369; format GG-103, 2026-07-15 — append-only, read LAST line only) ---"
CHECKPOINT_FILE="04_EXECUTION/.last_session_checkpoint"
if [ -s "$CHECKPOINT_FILE" ]; then
  CKPT_SHA="$(tail -n 1 "$CHECKPOINT_FILE" | cut -f1 | tr -d '[:space:]')"
  if git cat-file -e "${CKPT_SHA}^{commit}" 2>/dev/null; then
    CKPT_BEHIND="$(git rev-list --count "${CKPT_SHA}..HEAD" 2>/dev/null || echo "?")"
    CKPT_AGE_SEC="$(( $(date +%s) - $(git show -s --format=%ct "$CKPT_SHA" 2>/dev/null || echo "$(date +%s)") ))"
    CKPT_AGE_DAYS="$(( CKPT_AGE_SEC / 86400 ))"
    if [ "$CKPT_BEHIND" != "?" ] && [ "$CKPT_BEHIND" -gt 20 ] 2>/dev/null || [ "$CKPT_AGE_DAYS" -gt 3 ] 2>/dev/null; then
      echo "!!  STALE: checkpoint $CKPT_SHA is $CKPT_BEHIND commit(s) / ${CKPT_AGE_DAYS}d behind HEAD."
      echo "    session_delta.sh's Tier 1 diff will be large or the fallback full-read"
      echo "    path may be more reliable. A prior session likely skipped session-end.md"
      echo "    Step 6 (scripts/write_session_checkpoint.sh). Warn-only — not blocking."
    else
      echo "OK  checkpoint $CKPT_SHA is $CKPT_BEHIND commit(s) / ${CKPT_AGE_DAYS}d behind HEAD."
    fi
  else
    echo "!!  checkpoint SHA '$CKPT_SHA' not found in this tree's history (shallow clone or corrupt pointer)."
  fi
else
  echo "!!  no checkpoint file at $CHECKPOINT_FILE — first session, or it was never written."
fi

echo "--- Other sessions' recent claims (tail SESSION_CLAIMS.md) ---"
[ -f 04_EXECUTION/SESSION_CLAIMS.md ] && tail -6 04_EXECUTION/SESSION_CLAIMS.md

RECENT_OTHER_CLAIMS=0
if [ "$BR" = "main" ] && [ -f 04_EXECUTION/SESSION_CLAIMS.md ] && command -v python3 >/dev/null 2>&1; then
  RECENT_OTHER_CLAIMS="$(python3 - <<'PYEOF'
import re, sys
from datetime import datetime, timezone, timedelta

WINDOW_HOURS = 6
now = datetime.now(timezone.utc)
count = 0
pat = re.compile(r'\|\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?Z)')
try:
    with open("04_EXECUTION/SESSION_CLAIMS.md") as f:
        for line in f:
            m = pat.match(line.strip())
            if not m:
                continue
            ts_str = m.group(1)
            if len(ts_str) == 17:  # no seconds, e.g. 2026-07-06T23:50Z
                ts_str = ts_str[:-1] + ":00Z"
            try:
                ts = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            if now - ts <= timedelta(hours=WINDOW_HOURS):
                count += 1
except FileNotFoundError:
    pass
print(count)
PYEOF
)"
fi

if [ "$BR" = "main" ] && [ "${RECENT_OTHER_CLAIMS:-0}" -ge 2 ] 2>/dev/null; then
  echo "!!  GG-101 NEAR-MISS: $RECENT_OTHER_CLAIMS session claims in the last 6h AND"
  echo "    this session is on shared 'main' — another session may be concurrently"
  echo "    active in this same physical tree right now. A shared git op (stash,"
  echo "    reset, checkout, clean) here could destroy that session's uncommitted"
  echo "    work with no recovery (GG-101, 2026-07-08 near-miss). Strongly prefer"
  echo "    switching to an isolated worktree before doing anything further:"
  echo "      scripts/new_session_worktree.sh \"<focus>\""
fi

echo "--- Uncommitted changes in THIS tree ---"
DIRTY=0
if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
  echo "OK  clean working tree"
else
  DIRTY=1
  echo "!!  Uncommitted changes present. In a SHARED tree, some may belong to a"
  echo "    CONCURRENT session — commit ONLY your own files, path-scoped. Do not"
  echo "    stash / reset --hard / checkout -- / clean another session's work. (GG-101)"
  git --no-pager status --short
fi

echo "--- MEMORY_BANK snapshot hygiene (T-334) ---"
if [ -x scripts/check_memory_bank_snapshots.sh ]; then
  bash scripts/check_memory_bank_snapshots.sh
else
  echo "(scripts/check_memory_bank_snapshots.sh not found or not executable — skipped)"
fi

echo "--- Timestamp integrity (T-372) ---"
if [ -x scripts/check_future_timestamps.sh ]; then
  bash scripts/check_future_timestamps.sh || true
else
  echo "(scripts/check_future_timestamps.sh not found or not executable — skipped)"
fi

echo "=============================================="

if [ "$MODE" = "--guard-destructive" ] && [ "$BR" = "main" ] && [ "$DIRTY" -eq 1 ]; then
  echo "REFUSED: --guard-destructive on 'main' with uncommitted changes present."
  echo "Resolve (commit path-scoped, or confirm the changes are genuinely yours)"
  echo "before running any destructive git operation here. (GG-101)"
  exit 1
fi
