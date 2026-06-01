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
echo ""
echo "PORTFOLIO:"
python3 - <<'EOF'
import json, os
path = 'logs/paper_portfolio.json'
try:
    with open(path) as f:
        d = json.load(f)
    open_pos   = len(d.get('open_positions', []))
    closed_pos = len(d.get('closed_positions', []))
    bankroll   = d.get('bankroll_usd', 'unknown')
    initial    = d.get('initial_bankroll_usd', 1000.0)
    pnl        = d.get('total_realized_pnl', 0.0)
    realized_dd = max(0.0, -pnl) / initial
    print(f'  Bankroll: ${bankroll:.2f} | Open: {open_pos} | Resolved: {closed_pos}/30 (G6) | Realized drawdown: {realized_dd:.1%} | P&L: ${pnl:+.2f}')
except Exception as e:
    print(f'  Could not read portfolio: {e}')
EOF

echo ""
echo "============================================================"
echo "MANDATORY BEFORE ANY IMPLEMENTATION WORK:"
echo "  Complete ARE WE COMPROMISED? (CLAUDE.md Q1-Q6)"
echo "  Q6 is non-negotiable: what are you actually worried about?"
echo "============================================================"
