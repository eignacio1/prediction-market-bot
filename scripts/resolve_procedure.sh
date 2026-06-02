#!/usr/bin/env bash
# resolve_procedure.sh — T-109 standing procedure automation
# ============================================================
# Runs the full post-game resolution pipeline locally.
# Must run locally (VPS 403 blocks stats.nba.com).
# Scheduled via launchctl (macOS) — see scripts/com.predbot.resolve.plist
#
# Step 1: Resolve open paper positions using nba_api (local only)
# Step 2: Sync pregame files from VPS for EXP-017 data accumulation
#         (may fail on work wifi — non-fatal; syncs separately when on home network)
# Step 3: Report G6 evidence count

set -euo pipefail

PROJ_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHONPATH="$PROJ_ROOT/src"
PYTHON="$PROJ_ROOT/.venv311/bin/python3"
LOG_DIR="$PROJ_ROOT/logs"
LOG_FILE="$LOG_DIR/resolve_auto.log"
TIMESTAMP="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] === T-109 resolve procedure ===" | tee -a "$LOG_FILE"

# --- Step 1: Resolve open positions (requires nba_api; must be local) ---
echo "[$TIMESTAMP] Step 1: run_resolve_local.py" | tee -a "$LOG_FILE"
BOT_ENV=paper PYTHONPATH="$PYTHONPATH" "$PYTHON" \
    "$PROJ_ROOT/src/prediction_market_bot/run_resolve_local.py" \
    2>&1 | tee -a "$LOG_FILE"

STEP1_EXIT="${PIPESTATUS[0]}"
if [[ "$STEP1_EXIT" -ne 0 ]]; then
    echo "[$TIMESTAMP] WARNING: Step 1 exited $STEP1_EXIT — check log" | tee -a "$LOG_FILE"
fi

# --- Step 2: Sync pregame files from VPS (non-fatal on network failure) ---
echo "[$TIMESTAMP] Step 2: fetch_kalshi_prices.py --portfolio" | tee -a "$LOG_FILE"
PYTHONPATH="$PYTHONPATH" "$PYTHON" \
    "$PROJ_ROOT/src/prediction_market_bot/fetch_kalshi_prices.py" --portfolio \
    2>&1 | tee -a "$LOG_FILE" || {
    echo "[$TIMESTAMP] WARNING: Step 2 failed (work wifi? VPS unreachable?) — will retry on next run" | tee -a "$LOG_FILE"
}

# --- Step 3: G6 evidence count ---
echo "[$TIMESTAMP] Step 3: G6 evidence count" | tee -a "$LOG_FILE"
PORTFOLIO="$PROJ_ROOT/logs/paper_portfolio.json"
if [[ -f "$PORTFOLIO" ]]; then
    CLOSED=$(python3 -c "
import json, sys
d = json.load(open('$PORTFOLIO'))
closed = d.get('closed_positions', [])
tickers = set(p.get('kalshi_ticker','') for p in closed)
print(f'Closed positions: {len(closed)} | Unique markets: {len(tickers)} / 66 (APR-0017 floor)')
" 2>/dev/null || echo "  (parse error)")
    echo "[$TIMESTAMP] $CLOSED" | tee -a "$LOG_FILE"
else
    echo "[$TIMESTAMP] Portfolio not found — no bets resolved yet" | tee -a "$LOG_FILE"
fi

echo "[$TIMESTAMP] === Done ===" | tee -a "$LOG_FILE"
