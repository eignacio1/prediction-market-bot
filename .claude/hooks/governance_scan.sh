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

# --- Clean-logic provenance (T-320/T-321) ---
# G6 progress language should reference clean_n (bets resolved entirely under
# CURRENT_LOGIC_EPOCH), not raw_n, since raw_n includes bets contaminated by
# GG-077/GG-087 write-path bugs closed 2026-07-05. See src/prediction_market_bot/
# logic_epoch.py for the epoch-boundary table and why GG-100 is excluded.
echo ""
echo "CLEAN-LOGIC PROVENANCE (T-320/T-321 — raw_n vs clean_n per band):"
CACHE_T4M="logs/.vps_portfolio_cache_mlb_t4.json"
CACHE_MAX_AGE=600
fetch_needed=1
if [ -f "$CACHE_T4M" ]; then
    age=$(( $(date +%s) - $(stat -f %m "$CACHE_T4M" 2>/dev/null || echo 0) ))
    [ "$age" -lt "$CACHE_MAX_AGE" ] && fetch_needed=0
fi
if [ "$fetch_needed" -eq 1 ]; then
    if ssh -o ConnectTimeout=3 -o BatchMode=yes prediction-market-vps \
         "cat /opt/prediction-market-bot/logs/paper_portfolio_mlb_t4.json" > "$CACHE_T4M.tmp" 2>/dev/null \
       && python3 -c "import json; json.load(open('$CACHE_T4M.tmp'))" 2>/dev/null; then
        mv "$CACHE_T4M.tmp" "$CACHE_T4M"
    else
        rm -f "$CACHE_T4M.tmp"
    fi
fi
python3 - "logs/.vps_portfolio_cache_mlb.json" "logs/paper_portfolio_mlb.json" "$CACHE_T4M" "logs/paper_portfolio_mlb_t4.json" <<'EOF'
import json, os, sys

mlb_cache, mlb_local, t4m_cache, t4m_local = sys.argv[1:5]

sys.path.insert(0, "src")
try:
    from prediction_market_bot.logic_epoch import CURRENT_LOGIC_EPOCH
except Exception:
    CURRENT_LOGIC_EPOCH = None

def _load(cache, local):
    path = cache if os.path.exists(cache) else local
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None

def _band_counts(portfolio, band):
    closed = portfolio.get('closed_positions', []) if portfolio else []
    rows = [p for p in closed if p.get('band') == band]
    raw_n = len(rows)
    clean_n = sum(1 for p in rows if p.get('logic_epoch') == CURRENT_LOGIC_EPOCH)
    return raw_n, clean_n

if CURRENT_LOGIC_EPOCH is None:
    print('  Could not import logic_epoch — skipping clean_n breakdown')
else:
    mlb = _load(mlb_cache, mlb_local)
    t4m = _load(t4m_cache, t4m_local)
    parts = []
    if mlb is not None:
        for band in ('T1', 'T2'):
            raw_n, clean_n = _band_counts(mlb, band)
            parts.append(f'MLB {band}: raw_n={raw_n} clean_n={clean_n}')
    else:
        parts.append('MLB T1/T2: portfolio unavailable')
    if t4m is not None:
        raw_n, clean_n = _band_counts(t4m, 'T4M-PROJ')
        parts.append(f'MLB T4M-PROJ: raw_n={raw_n} clean_n={clean_n}')
    else:
        parts.append('MLB T4M-PROJ: portfolio unavailable')
    print('  ' + ', '.join(parts) + '.')
    print('  (clean_n = resolved under CURRENT_LOGIC_EPOCH; G6 progress language should cite clean_n, not raw_n.)')
EOF

# --- Sample adequacy: clean_n vs n* per band (T-323/T-338, GG-004) ---
# n* is the variance-derived sample needed for 95% power to distinguish
# edge>0 from edge=0 (one-sided, alpha=0.05) — not the flat 30/150/500
# heuristic. See 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T338_CLEAN_N_VS_N_STAR_MEMO.md.
echo ""
echo "SAMPLE ADEQUACY (T-338 — clean_n vs n* per band):"
python3 scripts/build_t4_resolved_ledger.py --portfolio "$CACHE_T4M" \
    --out logs/t4_mlb_resolved_ledger.jsonl >/dev/null 2>&1
python3 - <<'EOF'
import sys
from pathlib import Path
sys.path.insert(0, "scripts")
try:
    from run_power_calc import run_all_bands
    results = run_all_bands(
        Path("logs/.vps_portfolio_cache_mlb.json"),
        Path("logs/t4_mlb_resolved_ledger.jsonl"),
        0.05, 0.95,
    )
except Exception as e:
    print(f'  Could not compute power calc: {e}')
    results = None
if results:
    parts = []
    for band, r in results.items():
        if r["status"] in ("INSUFFICIENT_DATA", "NO_POSITIVE_EFFECT"):
            parts.append(f"[{band}] clean_n={r['clean_n']} {r['status'].lower()}")
            continue
        eta = f"{r['eta_weeks']:.1f}wk" if r["eta_weeks"] is not None else "unknown"
        flag = " IMMATURE" if r.get("cadence_immature") else ""
        parts.append(
            f"[{band}] clean_n={r['clean_n']}/n*={r['n_star']} "
            f"(needs {r['gap_to_n_star']} more) ETA~{eta}{flag}"
        )
    print("  " + "  |  ".join(parts))
    print("  (n* = 95%-power sample vs flat GG-004 heuristic; ETA provisional until cadence "
          "span >= 14d. See T338_CLEAN_N_VS_N_STAR_MEMO.md.)")
EOF

echo ""
echo "============================================================"
echo "MANDATORY BEFORE ANY IMPLEMENTATION WORK:"
echo "  Complete ARE WE COMPROMISED? (CLAUDE.md Q1-Q6)"
echo "  Q6 is non-negotiable: what are you actually worried about?"
echo "============================================================"
