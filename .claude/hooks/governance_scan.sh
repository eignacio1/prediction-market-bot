#!/bin/bash
# Fast wrapper: prints the last finished full scan with its age (<0.1s); refreshes it in the background when older than 10 min.
# For a live read: bash .claude/hooks/governance_scan_full.sh
PROJECT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." 2>/dev/null && pwd)"
[ -f "$PROJECT/03_DECISIONS/GOVERNANCE_GAP_LOG.md" ] || PROJECT="/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
cd "$PROJECT" 2>/dev/null || exit 0
mkdir -p logs
OUT="logs/.governance_scan_last.txt"; LOCK="logs/.governance_scan.lock"
REFRESH_S=600; STALE_S=7200; LOCK_MAX_S=900
mtime() { stat -c %Y "$1" 2>/dev/null || stat -f %m "$1" 2>/dev/null || echo 0; }
now=$(date +%s); age=-1
[ -s "$OUT" ] && age=$(( now - $(mtime "$OUT") ))
if [ -d "$LOCK" ] && [ $(( now - $(mtime "$LOCK") )) -gt "$LOCK_MAX_S" ]; then rmdir "$LOCK" 2>/dev/null; fi
refreshing=0
if [ "$age" -lt 0 ] || [ "$age" -gt "$REFRESH_S" ]; then
  if mkdir "$LOCK" 2>/dev/null; then
    refreshing=1
    nohup bash -c 'bash .claude/hooks/governance_scan_full.sh > logs/.governance_scan_next.txt 2>&1; mv -f logs/.governance_scan_next.txt logs/.governance_scan_last.txt; rmdir logs/.governance_scan.lock 2>/dev/null' </dev/null >/dev/null 2>&1 &
    disown 2>/dev/null
  elif [ -d "$LOCK" ]; then refreshing=1; fi
fi
if [ "$age" -lt 0 ]; then echo "GOVERNANCE SCAN — first run in progress (background); output from next prompt. Live: bash .claude/hooks/governance_scan_full.sh"; exit 0; fi
label="as of $(( age / 60 ))min ago"
[ "$age" -gt "$STALE_S" ] && label="STALE — $(( age / 3600 ))h old; do not treat as current"
[ "$refreshing" -eq 1 ] && label="$label; refresh running in background"
echo "[cached governance scan — $label]"; cat "$OUT"; exit 0
