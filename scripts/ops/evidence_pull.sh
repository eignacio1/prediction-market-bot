#!/usr/bin/env bash
# W119.4 / B-103: verified copy of the box's un-recapturable evidence to this Mac. Run ON THE MAC.
# Box side is READ-ONLY (rsync sender + sha256sum reads). Nothing is ever deleted on either side (no --delete).
# After the copy: sha256 of every file on BOTH sides, compared. Any mismatch (after one re-copy of just those files) -> exit 1.
# Usage: scripts/ops/evidence_pull.sh [--dest DIR] [--host ALIAS] [--root BOXDIR]
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST="${EVIDENCE_HOST:-prediction-market-vps}"
ROOT="${EVIDENCE_BOX_ROOT:-/opt/prediction-market-bot}"
DEST="${EVIDENCE_DEST:-$HOME/PredictionMarketEvidence}"
while [ $# -gt 0 ]; do case "$1" in
  --dest) DEST="$2"; shift 2;; --host) HOST="$2"; shift 2;; --root) ROOT="$2"; shift 2;;
  *) echo "unknown arg $1" >&2; exit 2;; esac; done
SSH=(ssh -o BatchMode=yes -o ConnectTimeout=20 -o ServerAliveInterval=30 "$HOST")
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
MAN="$DEST/_manifests"; mkdir -p "$DEST/data" "$MAN"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
log(){ echo "[evidence_pull $(date -u +%H:%M:%SZ)] $*"; }

# 1. file list, built on the box (read-only find over the allowlist)
PATHS="$(grep -vE '^\s*(#|$)' "$HERE/evidence_paths.txt" | tr '\n' ' ')"
"${SSH[@]}" "cd '$ROOT' && for p in $PATHS; do find \$p -type f ! -name '*.tmp' ! -name '*.lock' ! -name '*.gz.tmp' 2>/dev/null; done | sort -u" > "$TMP/files.txt" || { log "FAIL: could not list files on box"; exit 3; }
N=$(wc -l < "$TMP/files.txt" | tr -d ' ')
[ "$N" -gt 0 ] || { log "FAIL: box returned 0 files"; exit 3; }
log "box lists $N files"

copy(){ rsync -a --partial -z --files-from="$1" -e "ssh -o BatchMode=yes -o ServerAliveInterval=30" "$HOST:$ROOT/" "$DEST/data/"; }
# 2. copy (pull only)
copy "$TMP/files.txt"; RC=$?
[ $RC -eq 0 ] || [ $RC -eq 24 ] || { log "FAIL: rsync exit $RC"; exit 4; }   # 24 = source file vanished (the box compressed it mid-run); the retry below re-lists

hash_box(){ "${SSH[@]}" "cd '$ROOT' && xargs -d '\n' sha256sum 2>/dev/null" < "$1" | sed 's/  / /' | sort -k2; }
hash_mac(){ (cd "$DEST/data" && tr '\n' '\0' < "$1" | xargs -0 shasum -a 256 2>/dev/null) | sed 's/  / /' | sort -k2; }

# 3. manifests on both sides, compared
hash_box "$TMP/files.txt" > "$MAN/${STAMP}_box.sha256"
hash_mac "$TMP/files.txt" > "$MAN/${STAMP}_mac.sha256"
diff_files(){ diff "$1" "$2" | grep '^[<>]' | awk '{print $3}' | sort -u; }
BAD="$(diff_files "$MAN/${STAMP}_box.sha256" "$MAN/${STAMP}_mac.sha256")"
if [ -n "$BAD" ]; then
  log "$(echo "$BAD" | wc -l | tr -d ' ') file(s) differ on first pass (live appenders or files compressed mid-run); re-copying just those"
  echo "$BAD" > "$TMP/retry.txt"
  copy "$TMP/retry.txt" >/dev/null 2>&1
  hash_box "$TMP/retry.txt" > "$TMP/retry_box.sha256"; hash_mac "$TMP/retry.txt" > "$TMP/retry_mac.sha256"
  BAD2="$(diff_files "$TMP/retry_box.sha256" "$TMP/retry_mac.sha256")"
  # a file the box no longer has under that name (compressed since listing) is reported, not hidden
  if [ -n "$BAD2" ]; then
    log "MISMATCH after retry: $(echo "$BAD2" | wc -l | tr -d ' ') file(s):"; echo "$BAD2" | head -40
    printf '{"utc":"%s","files":%s,"ok":false,"mismatch":%s}\n' "$STAMP" "$N" "$(echo "$BAD2" | wc -l | tr -d ' ')" > "$DEST/LAST_RUN.json"
    exit 1
  fi
  hash_box "$TMP/files.txt" > "$MAN/${STAMP}_box.sha256"; hash_mac "$TMP/files.txt" > "$MAN/${STAMP}_mac.sha256"
fi
cmp -s "$MAN/${STAMP}_box.sha256" "$MAN/${STAMP}_mac.sha256" || { log "MISMATCH: manifests differ after retry"; exit 1; }
SZ="$(du -sh "$DEST" | cut -f1)"
printf '{"utc":"%s","files":%s,"ok":true,"mismatch":0,"size":"%s"}\n' "$STAMP" "$N" "$SZ" > "$DEST/LAST_RUN.json"
log "OK: $N files, manifests match on both sides, $DEST = $SZ"
