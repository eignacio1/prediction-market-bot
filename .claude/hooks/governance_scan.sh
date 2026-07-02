#!/bin/bash
# Governance scan — runs before every model response in this project.
# Output is injected into model context. Model cannot skip what it sees.

PROJECT="/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
cd "$PROJECT" 2>/dev/null || exit 0

echo "============================================================"
echo "GOVERNANCE SCAN — $(date '+%Y-%m-%d %H:%M')"
echo "============================================================"

# --- Stub scan ---
echo ""
echo "STUB SCAN (src/):"
python3 - <<'EOF'
import os, re
hits = []
for root, dirs, files in os.walk('src'):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            try:
                with open(path) as fh:
                    for i, line in enumerate(fh, 1):
                        if re.search(r'# stub|# placeholder|# TBD|# todo', line, re.IGNORECASE):
                            hits.append(f'  {path}:{i}: {line.strip()}')
            except:
                pass
if hits:
    print(f'  {len(hits)} stub(s) found:')
    for h in hits:
        print(h)
else:
    print('  CLEAN — no stubs found')
EOF

# --- Open governance gaps ---
echo ""
echo "OPEN GOVERNANCE GAPS:"
OPEN=$(grep "| OPEN" "03_DECISIONS/GOVERNANCE_GAP_LOG.md" 2>/dev/null | grep -v "OPEN / IN PROGRESS" | grep -v "template")
if [ -z "$OPEN" ]; then
    echo "  CLEAN — no open gaps"
else
    echo "$OPEN" | while read -r line; do echo "  $line"; done
fi

# --- Hard limits snapshot ---
echo ""
echo "HARD LIMITS (risk.py):"
grep -n "max_\|_HARD_LIMITS\|MIN_EDGE\|DEFAULT_KELLY" "src/prediction_market_bot/c4_risk_engine/risk.py" 2>/dev/null \
  | grep -v "^.*#.*NOTE\|removed\|deleted" \
  | grep "float\|:\s*{" \
  | head -10 \
  | while read -r line; do echo "  $line"; done

# --- Portfolio quick state ---
# GG-033/T-171: the git-tracked logs/paper_portfolio*.json files are stale snapshots;
# the live books are written by cron on the VPS. Fetch the VPS copies (cached 10 min
# so this hook stays fast).
#
# GG-070: NBA (paper_portfolio.json) and MLB (paper_portfolio_mlb.json) are SEPARATE,
# ISOLATED ledgers/bankroll pools — NOT the same book. NBA is frozen/dark (off-season,
# tabled per standing operator directive) at an already-known, already-adjudicated
# negative balance (GG-034/GG-037 — this is historical fact, not a live risk signal).
# MLB is the current ACTIVE G6 pool. Both are printed below, explicitly labeled, so
# no session ever again has to spend tokens re-deriving which figure is which
# (this cost ~20k tokens once already — do not repeat that investigation).
echo ""
for SPORT_PAIR in "mlb:paper_portfolio_mlb.json:MLB (ACTIVE)" "nba:paper_portfolio.json:NBA (DARK/FROZEN — historical, not live risk)"; do
    SPORT_KEY="${SPORT_PAIR%%:*}"
    REST="${SPORT_PAIR#*:}"
    FILE="${REST%%:*}"
    TAG="${REST#*:}"
    CACHE="logs/.vps_portfolio_cache_${SPORT_KEY}.json"
    CACHE_MAX_AGE=600
    fetch_needed=1
    if [ -f "$CACHE" ]; then
        age=$(( $(date +%s) - $(stat -f %m "$CACHE" 2>/dev/null || echo 0) ))
        [ "$age" -lt "$CACHE_MAX_AGE" ] && fetch_needed=0
    fi
    if [ "$fetch_needed" -eq 1 ]; then
        if ssh -o ConnectTimeout=3 -o BatchMode=yes prediction-market-vps \
             "cat /opt/prediction-market-bot/logs/${FILE}" > "$CACHE.tmp" 2>/dev/null \
           && python3 -c "import json; json.load(open('$CACHE.tmp'))" 2>/dev/null; then
            mv "$CACHE.tmp" "$CACHE"
        else
            rm -f "$CACHE.tmp"
        fi
    fi
    python3 - "$CACHE" "logs/${FILE}" "$TAG" <<'EOF'
import json, os, sys, time

cache, local, tag = sys.argv[1], sys.argv[2], sys.argv[3]

if os.path.exists(cache):
    path = cache
    age_min = (time.time() - os.path.getmtime(cache)) / 60
    label = f'PORTFOLIO — {tag} (VPS LIVE BOOK, fetched {age_min:.0f} min ago):'
else:
    path = local
    label = f'PORTFOLIO — {tag} (LOCAL GIT SNAPSHOT — STALE, VPS unreachable — see GG-033/T-171):'
print(label)
try:
    with open(path) as f:
        d = json.load(f)
    open_list  = d.get('open_positions', [])
    open_pos   = len(open_list)
    deployed   = sum(float(p.get('size_usd', 0)) for p in open_list)
    closed_pos = len(d.get('closed_positions', []))
    bankroll   = d.get('bankroll_usd', 'unknown')
    initial    = d.get('initial_bankroll_usd', 1000.0)
    pnl        = d.get('total_realized_pnl', 0.0)
    realized_dd = max(0.0, -pnl) / initial
    print(f'  Bankroll: ${bankroll:.2f} | Open: {open_pos} (${deployed:.2f} deployed) | '
          f'Resolved: {closed_pos}/30 (G6) | Realized drawdown: {realized_dd:.1%} | P&L: ${pnl:+.2f}')
except Exception as e:
    print(f'  Could not read portfolio: {e}')
echo_blank = ''
EOF
    echo ""
done

echo ""
echo "============================================================"
echo "MANDATORY BEFORE ANY IMPLEMENTATION WORK:"
echo "  Complete ARE WE COMPROMISED? (CLAUDE.md Q1-Q6)"
echo "  Q6 is non-negotiable: what are you actually worried about?"
echo "============================================================"
