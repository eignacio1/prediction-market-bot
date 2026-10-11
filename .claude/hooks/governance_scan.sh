#!/bin/bash
# Governance scan — runs before every model response in this project.
# Output is injected into model context. Model cannot skip what it sees.

# GG-426 (W60.3): resolve the repo root from this script's own location, not a hardcoded
# path. The hardcoded main-checkout path made every worktree session read the (often stale)
# main tree's gap log -- 176 OPEN printed vs 134 from the anchored grep on the live log.
# Hardcoded path kept only as a fallback if the script is run from outside a checkout.
PROJECT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." 2>/dev/null && pwd)"
[ -f "$PROJECT/03_DECISIONS/GOVERNANCE_GAP_LOG.md" ] || PROJECT="/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
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
# GG-144 / 2026-08-05 restructure (T-420): the old table-cell format (`| Status | OPEN...`)
# let bold-vs-plain formatting hide entries from an unanchored scan (fixed here 2026-07-16
# GG-122, but CLAUDE.md's Step 3 kept the unanchored form 13 more days). The restructure
# replaced that format entirely -- RESOLVED/CLOSED-AS-ARTIFACT entries moved verbatim to
# GOVERNANCE_GAP_LOG_ARCHIVE.md (never OPEN by construction) and every remaining entry in
# GOVERNANCE_GAP_LOG.md carries one machine-uniform line, `**Status:** TOKEN · **Severity:**
# LEVEL`, immediately under its header. There is no bold/plain variant left to reconcile --
# the structural assertion below (one Status line per header) replaces the old
# plain+bold==raw check.
OPEN=$(grep -E "^\*\*Status:\*\* OPEN\b" "03_DECISIONS/GOVERNANCE_GAP_LOG.md" 2>/dev/null)
OPEN_N=0
if [ -n "$OPEN" ]; then
    OPEN_N=$(echo "$OPEN" | wc -l | tr -d ' ')
fi
# TOTAL_N feeds governance_gap_burndown.py's resolved_n = total_n - open_n, so it must be
# ALL gaps ever logged, not just the entries currently living in the live file -- the split
# moved every RESOLVED/CLOSED-AS-ARTIFACT entry out to the archive, so it has to be summed
# back in here or burn-down would silently read ~100% open the moment the archive existed.
# [0-9] anchor excludes the "### GG-NNN — [Short title]" line inside the Gap Registration
# Template's example fence at the bottom of GOVERNANCE_GAP_LOG.md -- a real header pattern
# match but not a real gap; pre-existing in the old TOTAL_N grep too, just newly visible now
# that this count is asserted against STATUS_LINE_N below instead of only ever added to OPEN_N.
# Note: deliberately NOT "grep -c ... || echo 0" -- grep -c prints "0" to stdout
# AND exits nonzero when a file exists but has zero matches, so that idiom double-
# prints ("0\n0") on a legitimate zero-match file and breaks the -ne test below.
# ${VAR:-0} only fires when grep produced no stdout at all (file missing).
LIVE_N=$(grep -cE "^### GG-[0-9]" "03_DECISIONS/GOVERNANCE_GAP_LOG.md" 2>/dev/null)
LIVE_N=${LIVE_N:-0}
ARCHIVE_N=$(grep -cE "^### GG-[0-9]" "03_DECISIONS/GOVERNANCE_GAP_LOG_ARCHIVE.md" 2>/dev/null)
ARCHIVE_N=${ARCHIVE_N:-0}
TOTAL_N=$((LIVE_N + ARCHIVE_N))
STATUS_LINE_N=$(grep -cE "^\*\*Status:\*\*" "03_DECISIONS/GOVERNANCE_GAP_LOG.md" 2>/dev/null)
STATUS_LINE_N=${STATUS_LINE_N:-0}
if [ "$STATUS_LINE_N" -ne "$LIVE_N" ]; then
    echo "  *** STRUCTURE FAILURE: $LIVE_N gap headers but $STATUS_LINE_N structured Status lines in GOVERNANCE_GAP_LOG.md ***"
    echo "  *** Every entry in this file must carry exactly one '**Status:**' line -- do not trust OPEN_N below until fixed. ***"
fi

# GG-199 (T-476): the header==status-line parity check above CANNOT see a
# DUPLICATE id -- both counters increment together per duplicate row. Three
# real concurrent-claim collisions have hit exactly this (GG-187 x2, GG-197
# x1, 2026-08-18/2026-08-21) with none caught by the check above. Checks the
# live log AND the archive combined (a number could be reused against an
# already-resolved/archived id too).
python3 "scripts/lib/gg_id_uniqueness_check.py" \
    "03_DECISIONS/GOVERNANCE_GAP_LOG.md" "03_DECISIONS/GOVERNANCE_GAP_LOG_ARCHIVE.md"

python3 "scripts/lib/governance_gap_burndown.py" "$OPEN_N" "$TOTAL_N" "logs/.governance_gap_history.jsonl"

# --- Retirement debt: zero-resolved-class-in-live-log assertion (T-570, 2026-09-23) ---
# WARN-ONLY. Creation (session claims, gap registration) is mechanical and enforced;
# retirement (archiving a gap once its own Status line already reads resolved-class)
# has been manual and forgotten -- this surfaces the debt every session without
# gating on it. Runs scripts/retire_resolved_gaps.py in its default dry-run mode
# (read-only against both files; it never writes without --apply, which this call
# never passes) and prints its resolved-class count as a loud, non-fatal warning.
# Never `|| true`-suppressed on purpose -- the script itself always exits 0 in
# dry-run, so there is nothing to suppress; this comment records that invariant
# rather than relying on a shell idiom to enforce it.
#
# PROMOTION CRITERION for turning this into a hard-fail later: only once (a) an
# operator-approved --apply run has actually landed against the real live log at
# least once (this session explicitly defers that first real run), and (b) the
# archive-move has been running warn-only for long enough that a nonzero count here
# reliably means "nobody has retired this gap yet," not "the tool is still new and
# nobody's looked." Until both hold, a hard-fail would gate every session on a debt
# nobody has a mechanism to clear yet -- do not flip this without an ADR recording
# that both conditions were checked.
RETIREMENT_DEBT_OUT=$(python3 "scripts/retire_resolved_gaps.py" \
    --src "03_DECISIONS/GOVERNANCE_GAP_LOG.md" \
    --archive "03_DECISIONS/GOVERNANCE_GAP_LOG_ARCHIVE.md" 2>&1)
RETIREMENT_DEBT_N=$(echo "$RETIREMENT_DEBT_OUT" | grep -oE "^resolved-class entries that WOULD move: [0-9]+" | grep -oE "[0-9]+$")
RETIREMENT_DEBT_N=${RETIREMENT_DEBT_N:-0}
if [ "$RETIREMENT_DEBT_N" -gt 0 ]; then
    echo "  *** RETIREMENT DEBT (warn-only): $RETIREMENT_DEBT_N resolved-class gap(s) still in the live log, not yet archived. ***"
    echo "  *** Run: python3 scripts/retire_resolved_gaps.py  (dry-run) to see which; --apply requires operator sign-off. ***"
else
    echo "  Retirement debt: 0 resolved-class gaps sitting unarchived in the live log."
fi

# --- Operator console (T-420, 2026-08-05 restructure) ---
# Regenerate on every scan from GOVERNANCE_GAP_LOG.md's live entries -- read-only
# against the log, three sections ranked by "blocks operator" not severity.
# Generated file; never hand-patch 03_DECISIONS/OPERATOR_CONSOLE.md directly.
echo ""
echo "OPERATOR CONSOLE:"
python3 "scripts/generate_operator_console.py" 2>&1 | sed 's/^/  /'

if [ -z "$OPEN" ]; then
    echo "  CLEAN — no open gaps"
else
    echo "$OPEN" | while read -r line; do echo "  $line"; done
fi

# --- Claim lifecycle: claims with no CLOSED row (GG-199/T-476, GG-188 class) ---
# GG-188 found this blind spot twice (T-463, T-465: claimed, work landed, but
# no CLOSED row ever written under their own T-number) and named the fix
# "Block I" -- this is that assertion. Matches by extracted T-NNN token and
# row order, never by timestamp equality (GG-177: branch-creation time and
# claim-command time differ by seconds-to-minutes, which guarantees false
# negatives on an exact-match join). Scoped to claims on/after 2026-08-07,
# when the "CLOSED — ..." body convention was first adopted (T-430) -- a
# dry run against the full unscoped file history flagged 108/149 T-numbers,
# almost all of them legacy rows that predate the convention and are not a
# live problem.
echo ""
echo "CLAIM LIFECYCLE (claims without a CLOSED row):"
python3 "scripts/lib/claim_closure_check.py" "04_EXECUTION/SESSION_CLAIMS.md" | sed 's/^/  /'

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
from run_band_monitor import load_t4_ledger, load_t4_ledger_execution, filter_clean

def _load(cache, local):
    path = cache if os.path.exists(cache) else local
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None

from prediction_market_bot import t4_fill_status as _tfs
_t1_fills = _tfs.load_fill_status(Path("logs/t1_mlb_fill_status.jsonl"))

def _band_counts(portfolio, band):
    closed = portfolio.get('closed_positions', []) if portfolio else []
    rows = [p for p in closed if p.get('band') == band]
    if band == 'T1':
        # GG-536: T1 execution evidence = CONFIRMED_FILLED only (sidecar); no ledger row rewritten.
        rows = _tfs.filter_confirmed_filled(rows, _t1_fills)
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
            parts.append(f'MLB {band}: raw_n={raw_n} clean_n={clean_n}' + (' (CONFIRMED_FILLED only, GG-536)' if band == 'T1' else ''))
    else:
        parts.append('MLB T1/T2: portfolio unavailable')
    # GG-527: T4M-PROJ G6 counting = CONFIRMED_FILLED rows only; all-rows is calibration.
    t4_all = load_t4_ledger(Path(t4_ledger_path))
    t4_recs = load_t4_ledger_execution(Path(t4_ledger_path))
    t4_raw_n = len(t4_recs)
    t4_clean_n = len(filter_clean(t4_recs))
    parts.append(f'MLB T4M-PROJ (fills only): raw_n={t4_raw_n} clean_n={t4_clean_n}; all-rows n={len(t4_all)} [calibration only - not execution evidence]')
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

# --- GG-280: capture-coverage gap detector (generalized from GG-276) ---
# GG-276 found 2026-09-12 (a Saturday) had zero KXNFL rows because
# deploy/cron.conf's NFL-capture block had day-of-week entries for 0-5
# (Sun-Fri) only, no 6 (Saturday) -- since fixed. GG-280 generalizes the
# detector from that one NFL/Saturday instance to the failure *shape*: it
# parses deploy/cron.conf's own archiver lines to derive, per sport, which
# cron day-of-week values are actually scheduled, then alarms if any in-season
# day that a sport is scheduled for produces zero rows of that sport in the
# archive file -- catching a repeat of GG-261 (Wednesday/NFL) or GG-276
# (Saturday/NFL), a symmetric gap in MLB's schedule, or a future sport, without
# needing a new detector each time. Reads the local synced copy of
# exp_output/PRICE_ARCHIVE/ (the sync block immediately above). Alarm-only,
# same as the GG-163 probe below. Verified 2026-09-15 (T-549): fires on
# 2026-09-12 (zero NFL rows), stays quiet on 09-11 and 09-13, and MLB (whose
# cron lines are unrestricted day-of-week, `* * *`) shows OK on all three days
# with no false alarms -- superseding (and removing) the NFL-only
# scripts/lib/nfl_capture_gap_check.py this script replaces.
echo ""
echo "CAPTURE COVERAGE GAP (GG-280 — zero rows for a sport due that day, per cron.conf's own schedule):"
python3 "$PROJECT/scripts/lib/capture_coverage_gap_check.py" 2>&1 | sed 's/^/  /'

# --- GG-163: T4 MLB cycle-log write-recency probe ---
# Every VPS-facing check above this point reads systemd state or a portfolio
# JSON snapshot -- none of them ever checked whether t4_mlb_cycle_log.jsonl
# itself is still being written. GG-163 (2026-08-04 23:41 UTC, found 2026-08-05,
# fixed T-429 2026-08-07) was a 43.5h+ ESPN-403 discovery outage that ran the
# entire time with `systemctl is-active t4-mlb` reporting "active" -- the
# process never crashed, it just looped a failing discovery request before
# ever reaching the code path that writes a cycle-log row. This makes that
# specific blind spot a structural, every-scan check instead of something a
# session has to notice by hand. Age-gated cache, same pattern/TTL as the
# portfolio caches above -- fails silently (prints UNREACHABLE) if the VPS
# is unreachable rather than blocking the scan.
echo ""
echo "T4 MLB CYCLE-LOG WRITE-RECENCY (GG-163/T-429):"
CACHE_T4CYCLE="logs/.vps_t4_cycle_log_last_row.txt"
CACHE_MAX_AGE=600
fetch_needed=1
if [ -f "$CACHE_T4CYCLE" ]; then
    age=$(( $(date +%s) - $(stat -f %m "$CACHE_T4CYCLE" 2>/dev/null || echo 0) ))
    [ "$age" -lt "$CACHE_MAX_AGE" ] && fetch_needed=0
fi
if [ "$fetch_needed" -eq 1 ]; then
    if ssh -o ConnectTimeout=3 -o BatchMode=yes prediction-market-vps \
         "tail -1 /opt/prediction-market-bot/logs/t4_mlb_cycle_log.jsonl" > "$CACHE_T4CYCLE.tmp" 2>/dev/null; then
        mv "$CACHE_T4CYCLE.tmp" "$CACHE_T4CYCLE"
    else
        rm -f "$CACHE_T4CYCLE.tmp"
    fi
fi
if [ -s "$CACHE_T4CYCLE" ]; then
    python3 - "$CACHE_T4CYCLE" <<'EOF'
import json, sys
from datetime import datetime, timezone

path = sys.argv[1]
try:
    with open(path) as f:
        row = json.loads(f.read().strip())
    ts = row.get("ts", "")
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    age_h = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
    in_season = datetime.now(timezone.utc).month in range(3, 11)
    print(f"  last_row={ts} age_hours={age_h:.1f}")
    if in_season and age_h > 8:
        print(f"  *** GG-163-CLASS ALERT: T4 MLB cycle log is {age_h:.1f}h stale during MLB season.")
        print("      systemctl is-active can show 'active' throughout a discovery-level outage")
        print("      like GG-163 -- do not treat that alone as evidence T4 is healthy. Cross-check")
        print("      T1's same-day player-match count (CLAUDE.md Step 4) before ruling this out. ***")
    elif not in_season:
        print("  (off-season by month -- staleness alone is not a signal here)")
except Exception as e:
    print(f"  Could not parse cached last row: {e}")
EOF
else
    echo "  UNREACHABLE or no rows -- VPS unreachable, or t4_mlb_cycle_log.jsonl missing/empty"
fi

# --- VPS deploy drift (GG-185/T-465) ---
# GG-185 root cause: the GG-166 guard (commit 58b2eb6, pushed 2026-08-07T05:37:38Z)
# sat on origin/main for 8.5 days -- 2026-08-07T05:26:27Z to 2026-08-15T19:44:27Z --
# before anyone `git pull`ed it onto the VPS (confirmed via VPS `git reflog`: a gap
# between consecutive pulls spanning that exact window). During the gap, BOTH the
# persistent t4-mlb live-eval service and every fresh run_resolve_mlb.py cron
# invocation executed the pre-fix checkout on disk -- the write-side ticker-date
# fix and the read-side game_date_ticker_mismatch guard were both structurally
# ABSENT from the deployed source (confirmed: 0 occurrences of either string in
# VPS commit 687bf9e), not merely unreached by a live logic bug. This is why an
# "unconditional, deployed" guard produced zero warnings for the 532 GG-185 rows:
# it did not yet exist in the code actually running. No amount of auditing the
# guard's own logic would have caught this -- only checking deploy currency does.
# This probe makes that currency check structural instead of incidental.
echo ""
echo "VPS DEPLOY DRIFT (GG-185/T-465):"
VPS_HEAD=$(ssh -o ConnectTimeout=3 -o BatchMode=yes prediction-market-vps \
    "cd /opt/prediction-market-bot && git rev-parse HEAD" 2>/dev/null)
if [ -z "$VPS_HEAD" ]; then
    echo "  UNREACHABLE -- could not read VPS deployed HEAD"
else
    LOCAL_MAIN=$(git rev-parse origin/main 2>/dev/null)
    if [ "$VPS_HEAD" = "$LOCAL_MAIN" ]; then
        echo "  deployed HEAD matches origin/main ($VPS_HEAD) -- up to date"
    else
        OLDEST_LINE=$(git log --format='%H %cI' "${VPS_HEAD}..origin/main" 2>/dev/null | tail -1)
        if [ -z "$OLDEST_LINE" ]; then
            echo "  deployed HEAD ($VPS_HEAD) not found in local origin/main history --"
            echo "  diverged, or this worktree's origin/main ref is stale (try a fetch)"
        else
            OLDEST_TS=$(echo "$OLDEST_LINE" | awk '{print $2}')
            N_BEHIND=$(git rev-list --count "${VPS_HEAD}..origin/main" 2>/dev/null)
            AGE_H=$(python3 -c "
from datetime import datetime, timezone
dt = datetime.fromisoformat('$OLDEST_TS')
print(f'{(datetime.now(timezone.utc) - dt).total_seconds()/3600:.1f}')" 2>/dev/null)
            echo "  deployed HEAD=$VPS_HEAD is $N_BEHIND commit(s) behind origin/main;"
            echo "  oldest undeployed commit is ${AGE_H}h old (committed $OLDEST_TS)"
            if [ -n "$AGE_H" ] && python3 -c "import sys; sys.exit(0 if float('$AGE_H') > 24 else 1)" 2>/dev/null; then
                echo "  *** GG-185-CLASS ALERT: VPS has not deployed a commit that is >24h old."
                echo "      Any guard/fix merged to main since then is NOT running in production --"
                echo "      resolve/live cron are silently executing pre-fix code. Deploy now. ***"
            fi
        fi
    fi
fi

# --- GitHub Actions status (W68.1 / GG-582) ---
# 2026-10-11 17:48Z GitHub stopped starting jobs ($0 budget on a private repo). MLB Games Cache Sync and MLB Features
# Sync are the only route around statsapi's 406 to the VPS, and the shadow runner refuses a games-cache stamp older
# than 26h -- so a silent Actions stall becomes a dark MLB data feed ~26h later with no other alarm. This prints
# visibility, last run per workflow, and flags any run that never started a step (the billing-refusal signature).
echo ""
echo "GITHUB ACTIONS STATUS (W68.1 — feed for MLB games cache / features):"
python3 - <<'PYEOF' 2>/dev/null || echo "  UNAVAILABLE -- gh missing, unauthenticated, or offline"
import json, subprocess, sys
from datetime import datetime, timezone
R = "eignacio1/prediction-market-bot"
def gh(*a):
    return json.loads(subprocess.check_output(["gh", "api", *a], text=True, timeout=20))
repo = gh(f"repos/{R}")
vis = repo.get("visibility", "?")
print(f"  visibility={vis}" + ("" if vis == "public" else "  *** PRIVATE: hosted minutes are capped; scheduled feeds may be refused ***"))
wfs = gh(f"repos/{R}/actions/workflows?per_page=50")["workflows"]
now = datetime.now(timezone.utc)
for w in sorted(wfs, key=lambda x: x["name"]):
    if w["path"].startswith("dynamic/") or w["state"] != "active":
        continue
    runs = gh(f"repos/{R}/actions/workflows/{w['id']}/runs?per_page=5&exclude_pull_requests=true")["workflow_runs"]
    if not runs:
        print(f"  {w['name']}: no runs")
        continue
    last = runs[0]
    age_h = (now - datetime.fromisoformat(last["created_at"].replace("Z", "+00:00"))).total_seconds() / 3600
    flag = ""
    if last["conclusion"] == "failure":
        jobs = gh(f"repos/{R}/actions/runs/{last['id']}/jobs")["jobs"]
        if not jobs or any(not j.get("steps") for j in jobs):
            flag = "  *** REFUSED/never started a step (billing or runner-capacity) ***"
        else:
            flag = "  (ran and failed)"
    print(f"  {w['name']}: last={last['conclusion'] or last['status']} ({last['event']}, {age_h:.1f}h ago){flag}")
PYEOF

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
            # GG-197: a MET verdict is only trustworthy if the clean cohort
            # it was computed from is itself trustworthy. mismatch_n is
            # live-computed (run_power_calc.analyze_band_power ->
            # _ticker_date_mismatch_n) over whatever the CURRENT clean
            # cohort is -- never hardcoded to 532/epoch-12 -- so this check
            # self-clears once the underlying corruption (GG-166/GG-170/
            # GG-185) is actually repaired and self-fires again if the same
            # defect recurs in a future epoch or cell. The "5,580" figure
            # below is ADR-0055 Addendum A's own dry-run citation, not a
            # live recomputation -- the repair is unauthorized (ADR-0055 is
            # PROPOSED, D1 unsigned) so this hook must not compute or act on
            # repaired figures itself.
            mismatch_n = r.get("ticker_date_mismatch_n", 0)
            if mismatch_n > 0:
                mismatch_pct = r.get("ticker_date_mismatch_pct", 0.0)
                print(f"      - APR-0024 n* (clean_n>=n*): clean_n={r['clean_n']} / n*={r['n_star']} -- "
                      f"VERDICT WITHHELD: {mismatch_n}/{r['clean_n']} rows ({mismatch_pct:.1f}%) carry a "
                      f"ticker-vs-game_date mismatch (GG-170/GG-185). n* recomputed on ADR-0055's repaired "
                      f"figures = 5,580 (NOT met). See ADR-0055.")
            else:
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

# --- Ledger field-integrity invariants (T-432/BLOCK B, GG-166 follow-on) ---
# GG-166 corrupted ~44% of the epoch-12 clean cohort's outcomes/P&L and was
# baked into four analysis sessions before an independent decoupled data
# path happened to disagree with the ledger. Nothing above this line checks
# a VALUE in the ledger is correct -- only that a step ran. This is
# ALARM-ONLY by design (operator directive): it runs without --strict, so
# its own exit code is always 0, and that exit code is discarded here
# (`|| true`) on top of that -- a defect in the checker itself must never
# gate this hook. Full assertion definitions, baselines, and the
# (currently unwired) --strict promotion path live in
# scripts/assert_ledger_invariants.py's docstring.
echo ""
echo "LEDGER FIELD INTEGRITY (T-432 -- alarm-only, does not affect this hook's exit code):"
python3 "$PROJECT/scripts/assert_ledger_invariants.py" 2>&1 | tail -20 || true

# --- Order-write parity check (GG-203/T-547 D5) ---
# GG-203 sat undetected for 10 days (2026-08-15 through 2026-08-24): every
# risk_eval_approved event was followed by a kalshi_order_failed event, a
# 100% execution-layer failure rate, while every other liveness probe
# above (systemctl is-active, cycle-log recency, T1 player-match counts)
# reported healthy throughout. This compares approvals against execution
# outcomes directly instead of relying on a session to notice by hand.
# ALARM-ONLY (operator directive): the detector always exits 0; its output
# is read, its exit code is not gating.
echo ""
echo "ORDER-WRITE PARITY (GG-203/T-547 D5 -- alarm-only, does not affect this hook's exit code):"
python3 "$PROJECT/scripts/gg203_order_write_detector.py" 2>&1 | tail -20 || true

# --- Silent-arm alarm (W62.1 Part B / GG-532 follow-on) ---
# For each shadow/paper arm: was a game scheduled to start in the arm's window (N hours, per its own schedule
# source) with zero rows written? Off-days and off-season are not alarms. READ-ONLY; alarm-only. Reads the
# ledgers in THIS checkout's exp_output/ (the VPS checkout is where the real ones live; locally the sources are
# usually absent, which prints "cannot check", not an alarm).
echo ""
echo "SILENT ARMS (W62.1 -- games in window with zero rows written; alarm-only):"
PYTHONPATH="$PROJECT/src" python3 -m prediction_market_bot.pregame_shadow.silent_arms 2>&1 | tail -12 || true

# --- Distance to optimum, computed (W63.3 / Hard Rule 12) ---
# Every measure (B1-B4, D1-D3, E1-E3, P1-P3) derived from its source of truth, with source path + as-of. Missing inputs print
# UNAVAILABLE with the reason (fill sidecars and the calibration engine output live on the VPS). A D1 manifest mismatch prints
# ERROR. READ-ONLY; alarm-only (exit code discarded).
echo ""
echo "DISTANCE TO OPTIMUM (W63.3 -- computed, not typed; alarm-only):"
python3 "$PROJECT/scripts/distance_to_optimum.py" 2>&1 | tail -45 || true

echo "============================================================"
echo "MANDATORY BEFORE ANY IMPLEMENTATION WORK:"
echo "  Complete ARE WE COMPROMISED? (CLAUDE.md Q1-Q7)"
echo "  Q6 is non-negotiable: what are you actually worried about?"
echo "  Q7: field integrity -- does the data mean what the label says?"
echo "============================================================"
