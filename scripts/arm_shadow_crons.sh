#!/usr/bin/env bash
# Arm the EXP-037 pregame-shadow crons on the VPS. RUN FROM A LOCAL SESSION (needs ssh).
#   bash scripts/arm_shadow_crons.sh [--allow <path> ...]
# Steps: (a) show incoming commits+files; (b) refuse if any changed file is outside the
# additive allowlist; (c) ff-only merge; (d) dry-run every cron line, stop on failure;
# (e) back up crontab, install BEGIN/END block idempotently, print crontab + next fires.
# Restarts NO service. Never edits any crontab line outside the EXP-037 block.
set -euo pipefail
HOST="${VPS_HOST:-prediction-market-vps}"
DIR=/opt/prediction-market-bot
CONF=deploy/cron_exp037_pregame_shadow.conf
HERE="$(cd "$(dirname "$0")" && pwd)"
HELPER="$HERE/arm_shadow_crons.py"
ALLOW=()
while [ $# -gt 0 ]; do
  case "$1" in --allow) ALLOW+=(--allow "$2"); shift 2;; *) echo "unknown arg $1" >&2; exit 2;; esac
done
R() { ssh "$HOST" "cd $DIR && $*"; }

R "git fetch origin main -q"
echo "=== (a) incoming commits ==="
R "git log --oneline HEAD..origin/main"
echo "=== changed files ==="
CHANGED="$(R "git diff --name-only HEAD origin/main")"
echo "$CHANGED"

echo "=== (b) additive allowlist ==="
printf '%s\n' "$CHANGED" | python3 "$HELPER" check-files ${ALLOW[@]+"${ALLOW[@]}"} || { echo "ABORT: nothing merged." >&2; exit 1; }

echo "=== (c) ff-only merge ==="
R "git merge --ff-only origin/main"

echo "=== (d) dry-run every cron line ==="
python3 "$HELPER" dry-cmds "$HERE/../$CONF" | while IFS= read -r c; do
  echo "--- $c"
  ssh "$HOST" "cd $DIR && $c" || { echo "ABORT: dry-run failed; crontab untouched." >&2; exit 1; }
done

echo "=== (e) install ==="
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
R "crontab -l > /root/crontab.bak.$STAMP 2>/dev/null || true; echo backup: /root/crontab.bak.$STAMP"
CUR="$(mktemp)"; NEW="$(mktemp)"
ssh "$HOST" "crontab -l 2>/dev/null || true" > "$CUR"
python3 "$HELPER" merge-crontab "$CUR" "$HERE/../$CONF" > "$NEW"
ssh "$HOST" "crontab -" < "$NEW"
echo "=== crontab -l ==="; ssh "$HOST" "crontab -l"
echo "=== next fires (UTC) ==="; python3 "$HELPER" next-fire "$HERE/../$CONF"
echo "Restarted nothing. T1 MLB cron line untouched."
