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

# --- Open governance gaps + burn-down trend (T-368) ---
# Root cause: prior sessions had no visibility into whether the OPEN backlog
# was growing or shrinking — it was discovered ad hoc (efficiency review,
# 2026-07-15) that it was growing faster than it closes. GOVERNANCE_GAP_LOG.md
# entries carry no structured open/resolved *date* field (dates are free-text
# prose inside "Status" cells, not parseable reliably) so burn-down is tracked
# via a self-maintained snapshot history instead of mining the log's prose.
# This section is READ-ONLY against GOVERNANCE_GAP_LOG.md itself (grep only) —
# it never writes to that file. History snapshots live in logs/.governance_gap_history.jsonl
# (gitignored, same pattern as the portfolio caches above).
echo ""
echo "OPEN GOVERNANCE GAPS:"
# GG-144: pattern standardized to match CLAUDE.md's Step 3 (^\| Status \| \*{0,2}OPEN) so the
# two copies cannot drift apart again the way this exact bug did once already (GG-122, 2026-07-16
# fixed it here but CLAUDE.md's Step 3 kept the old unanchored "| OPEN" substring match for 13
# more days). Reconciliation assertion below catches a future re-drift instead of silently
# under-reporting again.
OPEN=$(grep -E "^\| Status \| \*{0,2}OPEN" "03_DECISIONS/GOVERNANCE_GAP_LOG.md" 2>/dev/null | grep -v "OPEN / IN PROGRESS" | grep -v "template")
OPEN_N=0
if [ -n "$OPEN" ]; then
    OPEN_N=$(echo "$OPEN" | wc -l | tr -d ' ')
fi
TOTAL_N=$(grep -c "^### GG-" "03_DECISIONS/GOVERNANCE_GAP_LOG.md" 2>/dev/null || echo 0)
PLAIN_N=$(grep -cE "^\| Status \| OPEN" "03_DECISIONS/GOVERNANCE_GAP_LOG.md" 2>/dev/null || echo 0)
BOLD_N=$(grep -cE "^\| Status \| \*{1,2}OPEN" "03_DECISIONS/GOVERNANCE_GAP_LOG.md" 2>/dev/null || echo 0)
RAW_N=$(grep -cE "^\| Status \| \*{0,2}OPEN" "03_DECISIONS/GOVERNANCE_GAP_LOG.md" 2>/dev/null || echo 0)
if [ "$((PLAIN_N + BOLD_N))" -ne "$RAW_N" ]; then
    echo "  *** GG-144 RECONCILIATION FAILURE: plain($PLAIN_N) + bold($BOLD_N) != raw-anchored($RAW_N) ***"
    echo "  *** The OPEN-gap regex has drifted again — do not trust OPEN_N below until fixed. ***"
fi

python3 "scripts/lib/governance_gap_burndown.py" "$OPEN_N" "$TOTAL_N" "logs/.governance_gap_history.jsonl"

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
mkdir -p logs  # GG-138: logs/ is gitignored, absent on a fresh worktree; cache writes below need it to exist
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
#
# GG-112/T-344: this section previously computed T4M-PROJ's raw_n/clean_n with
# a standalone `_band_counts()` filter requiring `p.get('band') == 'T4M-PROJ'`
# on the raw portfolio. 356 legacy closed_positions rows in
# paper_portfolio_mlb_t4.json predate the `band` field being written and were
# silently excluded (undercounted clean_n by 112 vs SAMPLE ADEQUACY below,
# 300 vs 412 observed 2026-07-12). The canonical build_t4_resolved_ledger.py ->
# run_band_monitor.py pipeline correctly treats every row in this
# T4M-dedicated file as T4M-PROJ regardless of an unpopulated band field.
# Both sections now share one ledger build and one counting function
# (run_band_monitor.load_t4_ledger + filter_clean) so they cannot diverge
# again for T4M-PROJ. T1/T2 are unaffected (load_pool_by_band already used
# the same band-field filter as _band_counts()) and keep their existing path.
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
python3 scripts/build_t4_resolved_ledger.py --portfolio "$CACHE_T4M" \
    --out logs/t4_mlb_resolved_ledger.jsonl >/dev/null 2>&1
python3 - "logs/.vps_portfolio_cache_mlb.json" "logs/paper_portfolio_mlb.json" "logs/t4_mlb_resolved_ledger.jsonl" <<'EOF'
import json, os, sys
from pathlib import Path

mlb_cache, mlb_local, t4_ledger_path = sys.argv[1:4]

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")
try:
    from prediction_market_bot.logic_epoch import CURRENT_LOGIC_EPOCH
except Exception:
    CURRENT_LOGIC_EPOCH = None
from run_band_monitor import load_t4_ledger, filter_clean

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
    parts = []
    if mlb is not None:
        for band in ('T1', 'T2'):
            raw_n, clean_n = _band_counts(mlb, band)
            parts.append(f'MLB {band}: raw_n={raw_n} clean_n={clean_n}')
    else:
        parts.append('MLB T1/T2: portfolio unavailable')
    t4_recs = load_t4_ledger(Path(t4_ledger_path))
    t4_raw_n = len(t4_recs)
    t4_clean_n = len(filter_clean(t4_recs))
    parts.append(f'MLB T4M-PROJ: raw_n={t4_raw_n} clean_n={t4_clean_n}')
    print('  ' + ', '.join(parts) + '.')
    print('  (clean_n = resolved under CURRENT_LOGIC_EPOCH; G6 progress language should cite clean_n, not raw_n.)')
    print('  (T4M-PROJ counted via the canonical build_t4_resolved_ledger.py/run_band_monitor.py path — GG-112/T-344.)')
EOF

# --- GG-158: price archive local backup (rsync pull-back, age-gated like the
# portfolio caches above). exp_output/PRICE_ARCHIVE/ on the VPS is the only
# copy of unbackfillable season price/depth data -- three prior sessions
# reported the archiver "verified"/"deployed" without ever confirming a
# second copy existed anywhere off that one disk. This does not commit the
# files to git (see .gitignore) -- it is a local-disk backup only, same
# treatment as logs/.vps_portfolio_cache_*.json.
echo ""
echo "PRICE ARCHIVE SYNC (GG-158 — local backup of VPS exp_output/PRICE_ARCHIVE/):"
mkdir -p exp_output/PRICE_ARCHIVE
PA_STAMP="exp_output/PRICE_ARCHIVE/.last_sync"
PA_MAX_AGE=900
pa_fetch_needed=1
if [ -f "$PA_STAMP" ]; then
    pa_age=$(( $(date +%s) - $(stat -f %m "$PA_STAMP" 2>/dev/null || echo 0) ))
    [ "$pa_age" -lt "$PA_MAX_AGE" ] && pa_fetch_needed=0
fi
if [ "$pa_fetch_needed" -eq 1 ]; then
    if rsync -az -e "ssh -o ConnectTimeout=5 -o BatchMode=yes" \
         prediction-market-vps:/opt/prediction-market-bot/exp_output/PRICE_ARCHIVE/ \
         exp_output/PRICE_ARCHIVE/ 2>/dev/null; then
        touch "$PA_STAMP"
        echo "  synced ($(ls exp_output/PRICE_ARCHIVE/*.jsonl 2>/dev/null | wc -l | tr -d ' ') files, $(du -sh exp_output/PRICE_ARCHIVE 2>/dev/null | cut -f1) local)"
    else
        echo "  SYNC FAILED — rsync/ssh unreachable; local backup may be stale (see $PA_STAMP mtime)"
    fi
else
    echo "  skipped (last sync $(( pa_age / 60 ))min ago, under ${PA_MAX_AGE}s TTL)"
fi

# --- Sample adequacy: clean_n vs n* per band (T-323/T-338, GG-004) ---
# n* is the variance-derived sample needed for 95% power to distinguish
# edge>0 from edge=0 (one-sided, alpha=0.05) — not the flat 30/150/500
# heuristic. See 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T338_CLEAN_N_VS_N_STAR_MEMO.md.
# Ledger already built above (shared with CLEAN-LOGIC PROVENANCE, GG-112/T-344).
echo ""
echo "SAMPLE ADEQUACY (T-338 — clean_n vs n* per band):"
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
        if r["status"] == "INSUFFICIENT_DATA":
            parts.append(f"[{band}] clean_n={r['clean_n']} {r['status'].lower()}")
            continue
        if r["status"] == "NO_POSITIVE_EFFECT":
            grade = "GOV-GRADE" if r.get("neg_sign_governance_grade") else "pre-confirm"
            parts.append(f"[{band}] clean_n={r['clean_n']} no_positive_effect ({grade})")
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

# --- GG-046: T4 commercial-gate threshold-crossing auto-flag (T-375, T-391) ---
# Three independent thresholds bear on T4M-PROJ's commercial-gate status:
#   (a) legacy ADR-0024 Tier 2 flat floor, n>=500 (raw_n, single-sport) — the
#       pre-APR-0024 heuristic; not the current governing standard but still
#       a milestone worth surfacing since GG-004's own history is written in
#       these terms.
#   (b) APR-0024 n* (variance-derived, clean_n-based) — the current governing
#       standard; computed above and available as results["T4M-PROJ"].
#   (c) T-391: the negative-sign re-check floor (run_power_calc.py's
#       NEG_SIGN_CONFIRM_N=150 clean_n and MATURE_CADENCE_SPAN_DAYS=14) — when
#       the observed mean flips to NO_POSITIVE_EFFECT (as it did 2026-07-20,
#       clean_n=30, cadence_immature=True), (a) and (b) can't fire (mu<=0
#       has no finite n*), so without this the negative sign would sit as an
#       open-ended "flagged, no action" with nothing re-evaluating it. This
#       closes that gap the same way (a)/(b) already close it for the
#       positive-sign case.
# Prior to this check, crossing either threshold depended on a human
# remembering to re-pull clean_n by hand (GG-046, last done 2026-07-11,
# already stale by the time GG-046 was re-examined 2026-07-16). This makes
# all three checks automatic and part of every session's mandatory scan output.
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
    r = results.get("T4M-PROJ")
except Exception as e:
    r = None
    print(f"  GG-046 threshold check: could not compute — {e}")
if r:
    raw_n = r["raw_n"]
    tier2_crossed = raw_n >= 500
    nstar_crossed = r["status"] == "COMPUTED" and r.get("met")
    neg_sign_crossed = r["status"] == "NO_POSITIVE_EFFECT" and r.get("neg_sign_governance_grade")
    if tier2_crossed or nstar_crossed:
        print("")
        print("  *** GG-046 ALERT: T4M-PROJ has crossed a commercial-validation")
        print("      sample threshold. DO NOT silently re-run EXP-T4-01 -- register")
        print("      the decision first (see GOVERNANCE_GAP_LOG.md GG-046). ***")
        if tier2_crossed:
            print(f"      - legacy ADR-0024 Tier 2 floor (raw_n>=500): raw_n={raw_n} -- CROSSED")
        if nstar_crossed:
            print(f"      - APR-0024 n* (clean_n>=n*): clean_n={r['clean_n']} n*={r['n_star']} -- MET")
    elif neg_sign_crossed:
        print("")
        print("  *** GG-046 NEGATIVE-SIGN ALERT: T4M-PROJ's NO_POSITIVE_EFFECT finding")
        print("      has cleared its re-check thresholds (T-391) and should now be")
        print("      treated as governance-grade, not a first-look artifact. Register")
        print("      Earl's decision before taking any band action (GOVERNANCE_GAP_LOG.md GG-046). ***")
        print(f"      - clean_n={r['clean_n']} >= NEG_SIGN_CONFIRM_N=150 -- CROSSED")
        print(f"      - cadence_span_days={r['cadence_span_days']:.1f} >= MATURE_CADENCE_SPAN_DAYS=14 -- CROSSED")
        print(f"      - mean_pnl_per_bet=${r['mean_pnl_per_bet']:+.4f}")
    else:
        nstar_txt = (f"n*={r['n_star']} (clean_n={r['clean_n']}, needs {r['gap_to_n_star']} more)"
                     if r["status"] == "COMPUTED" else f"n* not computable ({r['status']})")
        print(f"  GG-046: T4M-PROJ still short on both thresholds -- raw_n={raw_n}/500 (legacy Tier 2), {nstar_txt}.")
        if r["status"] == "NO_POSITIVE_EFFECT":
            print(f"  GG-046: negative-sign re-check thresholds not yet cleared -- {r['reason']}")
EOF

echo ""
echo "REGISTER PARITY (GG-126 — APR/ADR doc Status vs APPROVALS_REGISTER.md):"
python3 "$PROJECT/scripts/check_register_parity.py" || true

echo ""

# --- Nav-hub staleness check (GG-127, T-389 provisional) ---
# 00_ADMIN/README.md is this project's designated nav hub (ADR-0001) but went
# ~7 weeks (2026-05-21 to 2026-07-19) without a single edit while the project
# moved through multiple phase transitions -- nothing in the prior session-start
# protocol checked THIS file's own freshness, only code/gaps/pipeline health.
# This mirrors the register-parity check above: read-only against the target
# file, prints an ALERT rather than silently passing when stale. Threshold is
# 14 days -- double the nominal weekly Directory Integrity Review cadence
# (00_ADMIN/README.md's own Update Cadence table), so routine day-to-day
# variance doesn't fire false alarms but two missed weekly cycles will.
echo ""
echo "NAV-HUB STALENESS (GG-127 -- 00_ADMIN/README.md Last Reviewed date):"
python3 - <<'INNEREOF'
import re
from datetime import date

path = "00_ADMIN/README.md"
THRESHOLD_DAYS = 14
try:
    with open(path) as f:
        text = f.read()
    m = re.search(r"\*\*Last reviewed:\*\*\s*(\d{4}-\d{2}-\d{2})", text)
    if not m:
        print(f"  Could not find a '**Last reviewed:**' date in {path}")
    else:
        last = date.fromisoformat(m.group(1))
        age = (date.today() - last).days
        if age > THRESHOLD_DAYS:
            print(f"  *** GG-127 ALERT: {path} Last Reviewed {last} is {age} days old")
            print(f"      (threshold {THRESHOLD_DAYS}d, ~2x the weekly DIR cadence it documents).")
            print("      Nav hub may be describing a stale phase/gate/band state. ***")
        else:
            print(f"  OK -- {path} Last Reviewed {last} ({age}d ago, within {THRESHOLD_DAYS}d threshold)")
except FileNotFoundError:
    print(f"  {path} not found -- cannot check staleness")
except Exception as e:
    print(f"  Could not check nav-hub staleness: {e}")
INNEREOF

echo "============================================================"
echo "MANDATORY BEFORE ANY IMPLEMENTATION WORK:"
echo "  Complete ARE WE COMPROMISED? (CLAUDE.md Q1-Q6)"
echo "  Q6 is non-negotiable: what are you actually worried about?"
echo "============================================================"
