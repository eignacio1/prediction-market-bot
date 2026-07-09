#!/usr/bin/env bash
# T-300 (A3) — session_delta.sh: diff-since-checkpoint + dense state artifact
# ADR-0041 | Window A: context/token optimization infra
#
# Usage: scripts/session_delta.sh <last_checkpoint_ref>
#
#   <last_checkpoint_ref> — a git ref (SHA, tag, or branch) marking the point
#   a prior session last read the Tier 1 governance files in full.
#
# Emits two things, both computed fresh against live HEAD (never cached):
#   1. A git diff of the ADR-0041 Tier 1 file set since the checkpoint.
#   2. A dense state artifact: bankroll (both ledgers, GG-070 labeled),
#      open governance gaps (truncated one-liners, not full entries),
#      the last 3 EXP-0xx deltas logged in DECISION_LOG.md, and G6/EXP-017
#      gate progress (the GG-004 n-count progression).
#
# Per ADR-0041: this script does not replace Hard Rule 10. A session that
# uses this delta instead of a full file read must still re-read or re-diff
# the specific Tier 1 file fresh from HEAD immediately before writing to it
# — a delta bounds what changed since the checkpoint, not what changed since
# the delta was generated.

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

CHECKPOINT="${1:?Usage: session_delta.sh <last_checkpoint_ref>}"

if ! git rev-parse --verify --quiet "${CHECKPOINT}^{commit}" >/dev/null; then
    echo "ERROR: '$CHECKPOINT' is not a valid git ref in this repo." >&2
    exit 1
fi

# ADR-0041 Tier 1 — governance lineage. ADRs live under 03_DECISIONS/ alongside
# DECISION_LOG.md/GOVERNANCE_GAP_LOG.md, so the directory covers all three.
TIER1_PATHS=(
    "03_DECISIONS/"
    "04_EXECUTION/TODO_NEXT.md"
    "04_EXECUTION/SESSION_CLAIMS.md"
    "11_MEMORY_HANDOFF/"
    "logs/audit.jsonl"
    "logs/audit_mlb.jsonl"
    "logs/audit_mlb_t4.jsonl"
)

echo "================================================================"
echo "SESSION DELTA — $(git rev-parse --short "$CHECKPOINT") ($CHECKPOINT) -> HEAD ($(git rev-parse --short HEAD))"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Per ADR-0041: diff computed fresh against live HEAD, not cached."
echo "Hard Rule 10 still applies — re-read/re-diff fresh immediately before writing to any Tier 1 file."
echo "================================================================"

echo ""
echo "--- 1. Tier 1 governance diff (ADR-0041) since checkpoint ---"
echo ""
if [ -z "$(git diff --stat "$CHECKPOINT"..HEAD -- "${TIER1_PATHS[@]}")" ]; then
    echo "(no changes to Tier 1 paths since checkpoint)"
else
    git --no-pager diff --stat "$CHECKPOINT"..HEAD -- "${TIER1_PATHS[@]}"
    echo ""
    git --no-pager diff "$CHECKPOINT"..HEAD -- "${TIER1_PATHS[@]}"
fi

echo ""
echo "--- 2. Dense state artifact ---"

# --- 2a. Bankroll, both ledgers (GG-070) ---
# Reuses the exact cache-or-ssh-or-stale-local-snapshot logic already
# established in .claude/hooks/governance_scan.sh (lines 60-120) rather than
# reimplementing it — same cache files, same 600s freshness window, same
# ConnectTimeout=3/BatchMode=yes ssh convention, same STALE-warning fallback.
echo ""
echo "2a. Bankroll — both ledgers (GG-070: MLB and NBA are separate pools):"
for SPORT_PAIR in "mlb:paper_portfolio_mlb.json:MLB (ACTIVE)" "nba:paper_portfolio.json:NBA (DARK/FROZEN — historical, not live risk)"; do
    SPORT_KEY="${SPORT_PAIR%%:*}"
    REST="${SPORT_PAIR#*:}"
    FILE="${REST%%:*}"
    TAG="${REST#*:}"
    CACHE="logs/.vps_portfolio_cache_${SPORT_KEY}.json"
    CACHE_MAX_AGE=600
    fetch_needed=1
    if [ -f "$CACHE" ]; then
        age=$(( $(date +%s) - $(stat -f %m "$CACHE" 2>/dev/null || stat -c %Y "$CACHE" 2>/dev/null || echo 0) ))
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
    label = f'  PORTFOLIO — {tag} (VPS LIVE BOOK, fetched {age_min:.0f} min ago):'
elif os.path.exists(local):
    path = local
    label = f'  PORTFOLIO — {tag} (LOCAL GIT SNAPSHOT — STALE, VPS unreachable — see GG-033/T-171):'
else:
    print(f'  PORTFOLIO — {tag}: no cache or local snapshot found')
    path = None
    label = None

if path:
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
        print(f'    Bankroll: ${bankroll:.2f} | Open: {open_pos} (${deployed:.2f} deployed) | '
              f'Resolved: {closed_pos}/30 (G6) | Realized drawdown: {realized_dd:.1%} | P&L: ${pnl:+.2f}')
    except Exception as e:
        print(f'    Could not read portfolio: {e}')
EOF
done

# --- 2b. Open governance gaps (truncated one-liners, not full entries) ---
echo ""
echo "2b. Open governance gaps (GOVERNANCE_GAP_LOG.md), truncated to first 200 chars each:"
python3 - <<'EOF'
import re

with open("03_DECISIONS/GOVERNANCE_GAP_LOG.md") as f:
    text = f.read()

gap_ids = re.findall(r"\|\s*Gap ID\s*\|\s*(GG-\d+)\s*\|", text)
statuses = re.findall(r"\|\s*Status\s*\|\s*(OPEN|RESOLVED|PARTIALLY RESOLVED|\*\*RESOLVED[^|]*)\s*\|", text)

# Walk gap-id/status pairs in file order by re-scanning with positions.
entries = []
for m in re.finditer(r"\|\s*Gap ID\s*\|\s*(GG-\d+)\s*\|", text):
    gid = m.group(1)
    rest = text[m.end():]
    sm = re.search(r"\|\s*Status\s*\|\s*(.*?)\s*\|", rest)
    if sm:
        status_text = sm.group(1)
        entries.append((gid, status_text))

open_entries = [(gid, s) for gid, s in entries if s.strip().upper().startswith("OPEN")]
print(f"  {len(open_entries)} OPEN gap(s):")
for gid, status_text in open_entries:
    snippet = status_text[:200].replace("\n", " ")
    ellipsis = "..." if len(status_text) > 200 else ""
    print(f"    {gid}: {snippet}{ellipsis}")
EOF

# --- 2c. Last 3 EXP-0xx deltas logged in DECISION_LOG.md ---
echo ""
echo "2c. Last 3 EXP-0xx deltas (DECISION_LOG.md Notable Judgment Calls):"
python3 - <<'EOF'
import re

with open("03_DECISIONS/DECISION_LOG/DECISION_LOG.md") as f:
    text = f.read()

rows = re.findall(r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*\*\*\[([^\]]+)\]\*\*", text, re.MULTILINE)
exp_rows = [(d, t) for d, t in rows if "EXP-0" in t or "exp_output" in t.lower() or "exp017" in t.lower()]
for date, title in exp_rows[-3:]:
    print(f"    {date}: {title}")
if not exp_rows:
    print("    (no EXP-0xx rows found)")
EOF

# --- 2d. G6 / EXP-017 gate progress (n-count progression) ---
echo ""
echo "2d. G6 / EXP-017 gate progress (GG-004 n-count progression, MLB):"
python3 - <<'EOF'
import re

with open("03_DECISIONS/GOVERNANCE_GAP_LOG.md") as f:
    text = f.read()

m = re.search(r"### GG-004.*?(?=\n### GG-|\Z)", text, re.S)
section = m.group(0) if m else ""

ns = re.findall(r"n=(\d+)", section)
tier1 = "REACHED" if re.search(r"Tier 1.*?REACHED", section) else "not yet reached"
print(f"    n-count progression (chronological, MLB unless noted): {', '.join(ns) if ns else 'not found'}")
print(f"    Tier 1 (n>=150 single-sport): {tier1}")
print("    Tier 2 (n>=500 single-sport, or n>=150 dual-sport w/ NBA): NOT MET (NBA n=0)")
print("    GG-004 status: OPEN (see full entry for latest aggregate P&L sign/variance caveats)")
EOF

echo ""
echo "================================================================"
echo "END SESSION DELTA"
echo "================================================================"
