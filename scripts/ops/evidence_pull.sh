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
  # Live append-only ledgers keep growing between the copy and the hash. For those, verify the Mac copy is an exact
  # BYTE PREFIX of the box file (box hashes only the first <mac size> bytes); the rows appended since arrive next run.
  PREFIX=""; REAL=""
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    sz=$(stat -f %z "$DEST/data/$f" 2>/dev/null) || { REAL="$REAL$f"$'\n'; continue; }
    bh=$("${SSH[@]}" "cd '$ROOT' && head -c $sz -- '$f' | sha256sum" 2>/dev/null | cut -d' ' -f1)
    mh=$(shasum -a 256 "$DEST/data/$f" | cut -d' ' -f1)
    if [ -n "$bh" ] && [ "$bh" = "$mh" ] && [[ "$f" == *.jsonl || "$f" == *.log ]]; then PREFIX="$PREFIX$f"$'\n'; else REAL="$REAL$f"$'\n'; fi
  done <<< "$BAD2"
  if [ -n "$REAL" ]; then
    log "MISMATCH after retry: $(printf %s "$REAL" | grep -c .) file(s):"; printf %s "$REAL" | head -40
    printf '{"utc":"%s","files":%s,"ok":false,"mismatch":%s}\n' "$STAMP" "$N" "$(printf %s "$REAL" | grep -c .)" > "$DEST/LAST_RUN.json"
    exit 1
  fi
  if [ -n "$PREFIX" ]; then
    log "$(printf %s "$PREFIX" | grep -c .) live append-only ledger(s) verified as exact byte-prefix of the box file (rows added since copy come next run):"; printf %s "$PREFIX"
    printf %s "$PREFIX" > "$MAN/${STAMP}_prefix_verified.txt"
    # manifests: drop those paths from both sides (they are covered by the prefix check above)
    for side in box mac; do
      python3 - "$MAN/${STAMP}_${side}.sha256" "$MAN/${STAMP}_prefix_verified.txt" <<'PY'
import sys
skip=set(open(sys.argv[2]).read().split("\n"))
keep=[l for l in open(sys.argv[1]) if l.rstrip("\n").split(" ",1)[-1] not in skip]
open(sys.argv[1],"w").writelines(keep)
PY
    done
  else
    # retried files now agree: splice their fresh hashes into the manifests (do not rehash 5k files while appenders move)
    for side in box mac; do
      python3 - "$MAN/${STAMP}_${side}.sha256" "$TMP/retry_${side}.sha256" <<'PY'
import sys
new={l.rstrip("\n").split(" ",1)[1]:l for l in open(sys.argv[2]) if " " in l}
out=[new.pop(l.rstrip("\n").split(" ",1)[1],l) if l.rstrip("\n").split(" ",1)[1] in new else l for l in open(sys.argv[1])]
open(sys.argv[1],"w").writelines(sorted(out,key=lambda l:l.split(" ",1)[1]))
PY
    done
  fi
fi
cmp -s "$MAN/${STAMP}_box.sha256" "$MAN/${STAMP}_mac.sha256" || { log "MISMATCH: manifests differ after retry"; exit 1; }
# W120.3: keep the Mac copy compressed - drop a plain file only when its .gz decompresses to the same bytes (Mac side only).
SZ0="$(du -sh "$DEST" | cut -f1)"
if [ "${EVIDENCE_NO_COMPACT:-0}" != "1" ]; then
  python3 "$HERE/evidence_compact.py" "$DEST/data" || log "evidence_compact reported a kept-both or failed file (see above); the pull itself is verified"
fi
SZ="$(du -sh "$DEST" | cut -f1)"
printf '{"utc":"%s","files":%s,"ok":true,"mismatch":0,"prefix_verified":%s,"size":"%s"}\n' "$STAMP" "$N" "$(printf %s "${PREFIX:-}" | grep -c . || true)" "$SZ" > "$DEST/LAST_RUN.json"
log "OK: $N files, manifests match on both sides, $DEST = $SZ (before compaction $SZ0)"
