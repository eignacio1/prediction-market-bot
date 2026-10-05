#!/usr/bin/env bash
# W55.3b / GG-470: refresh the MLB games cache from a machine Stats API does not throttle, then push it to the VPS.
# Run from the operator Mac (repo root) at least once a day; the shadow runner refuses a cache older than 26h.
# Fail-closed: any step failing leaves the VPS cache untouched (scp to .tmp, then atomic mv).
set -euo pipefail
cd "$(dirname "$0")/.."
VPS="${VPS_HOST:-prediction-market-vps}"; REMOTE=/opt/prediction-market-bot/exp_output/MLB_GAME/cache_w47
C=exp_output/MLB_GAME/cache_w47; mkdir -p "$C"
[ -f "$C/games.parquet" ] || scp "$VPS:$REMOTE/games.parquet" "$C/games.parquet"     # one-time seed
PYTHONPATH=src:. python3 scripts/fetch_mlb_game_history.py --recent --season "$(date -u +%Y)" \
  --base "$C/games.parquet" --out "$C/games_current.parquet"
scp "$C/games_current.parquet" "$VPS:$REMOTE/games_current.parquet.tmp"
scp "$C/games_current.meta.json" "$VPS:$REMOTE/games_current.meta.json.tmp"
ssh "$VPS" "cd $REMOTE && mv games_current.parquet.tmp games_current.parquet && mv games_current.meta.json.tmp games_current.meta.json"
echo "synced $(cat "$C/games_current.meta.json")"
