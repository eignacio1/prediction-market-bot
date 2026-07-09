#!/usr/bin/env python3
"""T-300 (A4) — cron_log_aggregator.py: Tier 2 cron/audit executive summary.

ADR-0041 | Window A: context/token optimization infra

Computes per-day T1/T4 MLB throughput and anomaly figures (rows/game-day,
fire rate, contamination halts, SemanticFloorViolation count) DIRECTLY ON
THE VPS via a remote python invocation over ssh. Only the small text summary
crosses the wire and lands in a session's context — the raw logs
(t4_mlb_cycle_log.jsonl, audit_mlb_t4.jsonl, audit_mlb_t4_edge_decisions.jsonl,
paper_mlb_cron.log — tens of MB combined) are never pulled to local disk and
never loaded into a session's conversation. This is the ADR-0041 Tier 2
pattern: raw trace stays on disk untouched; a session reads the compressed,
source-traceable summary instead.

Usage:
    scripts/cron_log_aggregator.py [--days N] [--host SSH_ALIAS]

Output is printed to stdout and also written to
logs/cron_summary_<UTC-timestamp>.md (gitignored, regenerable Tier 2
artifact — safe to delete, safe to regenerate on demand).
"""
import argparse
import datetime
import pathlib
import subprocess
import sys

REMOTE_SCRIPT = r'''
import json, sys, collections
from datetime import datetime, timezone, timedelta

days_limit = int(sys.argv[1]) if len(sys.argv) > 1 else 3
today = datetime.now(timezone.utc).date()
keep_dates = {str(today - timedelta(days=i)) for i in range(days_limit)}

# argv[2] lets tests point this at a temp fixture dir instead of the VPS path;
# production invocation (main(), over ssh) never passes it, so the real path applies.
LOG_DIR = sys.argv[2] if len(sys.argv) > 2 else "/opt/prediction-market-bot/logs"

# --- 1. T4 cycle rows/games per day (t4_mlb_cycle_log.jsonl) ---
cycle_rows = collections.Counter()
cycle_games = collections.defaultdict(set)
lines_read = 0
with open(f"{LOG_DIR}/t4_mlb_cycle_log.jsonl") as f:
    for line in f:
        lines_read += 1
        try:
            d = json.loads(line)
        except Exception:
            continue
        gd = d.get("game_date")
        if gd not in keep_dates:
            continue
        cycle_rows[gd] += 1
        ticker = d.get("ticker", "")
        parts = ticker.split("-")
        game_id = parts[1] if len(parts) > 1 else ticker
        cycle_games[gd].add(game_id)

# --- 2. T4 edge decisions / fires per day (audit_mlb_t4_edge_decisions.jsonl) ---
fire_counts = collections.Counter()
total_decisions = collections.Counter()
with open(f"{LOG_DIR}/audit_mlb_t4_edge_decisions.jsonl") as f:
    for line in f:
        try:
            d = json.loads(line)
        except Exception:
            continue
        day = d.get("timestamp", "")[:10]
        if day not in keep_dates:
            continue
        total_decisions[day] += 1
        if d.get("payload", {}).get("decision") == "APPROVED":
            fire_counts[day] += 1

# --- 3. Contamination halts per day + recency-windowed staleness (audit_mlb_t4.jsonl) ---
# Recency check mirrors CLAUDE.md Step 4 / GG-085: a cumulative staleness_halts
# counter never resets mid-session, so only a recency-windowed count is a live signal.
halt_counts = collections.Counter()
recency_tail = collections.deque(maxlen=500)
with open(f"{LOG_DIR}/audit_mlb_t4.jsonl") as f:
    for line in f:
        recency_tail.append(line)
        try:
            d = json.loads(line)
        except Exception:
            continue
        if d.get("event_type") == "CONTAMINATION_HALT":
            day = d.get("timestamp", "")[:10]
            if day in keep_dates:
                halt_counts[day] += 1

recency_fresh_fail = sum(1 for line in recency_tail if '"failed_checks": ["game_state_fresh"]' in line)

# --- 4. T1 paper_mlb_cron.log: run blocks + SemanticFloorViolation ---
t1_runs = []
cur_date = None
semantic_floor_total = 0
abort_counts = collections.Counter()
with open(f"{LOG_DIR}/paper_mlb_cron.log") as f:
    for line in f:
        if "[PIPE-05] MLB Paper trading" in line:
            tok = line.strip().split()[-1]
            cur_date = f"{tok[0:4]}-{tok[4:6]}-{tok[6:8]}" if len(tok) == 8 and tok.isdigit() else None
        if "aborting bet placement" in line and cur_date:
            abort_counts[cur_date] += 1
        if "players in live MLB markets" in line:
            try:
                players = int(line.strip().split()[0])
            except Exception:
                players = None
            t1_runs.append({"date": cur_date, "players": players, "bets": None})
        if "Bets placed today" in line and t1_runs:
            try:
                t1_runs[-1]["bets"] = int(line.strip().split(":")[-1].strip())
            except Exception:
                pass
        if "SemanticFloorViolation" in line:
            semantic_floor_total += 1

t1_by_date = collections.defaultdict(lambda: {"runs": 0, "players_sum": 0, "bets_sum": 0})
for r in t1_runs:
    if r["date"] in keep_dates:
        agg = t1_by_date[r["date"]]
        agg["runs"] += 1
        agg["players_sum"] += r["players"] or 0
        agg["bets_sum"] += r["bets"] or 0

print(f"=== T4 MLB (t4_mlb_cycle_log.jsonl + audit_mlb_t4_edge_decisions.jsonl + audit_mlb_t4.jsonl), last {days_limit}d ===")
for day in sorted(keep_dates):
    rows = cycle_rows.get(day, 0)
    games = len(cycle_games.get(day, set()))
    fires = fire_counts.get(day, 0)
    decisions = total_decisions.get(day, 0)
    halts = halt_counts.get(day, 0)
    rpg = f"{rows/games:.0f}" if games else "n/a"
    fire_rate = f"{100*fires/decisions:.2f}%" if decisions else "n/a"
    bpg = f"{fires/games:.2f}" if games else "n/a"
    print(f"  {day}: rows={rows} games={games} rows/game={rpg} fires={fires} decisions={decisions} fire_rate={fire_rate} bets/game={bpg} contamination_halts={halts}")
print(f"  Recency check (last 500 audit_mlb_t4.jsonl records): game_state_fresh failures = {recency_fresh_fail} ({'ALARM - investigate now' if recency_fresh_fail else 'healthy'})")

print("")
print(f"=== T1 MLB (paper_mlb_cron.log), last {days_limit}d ===")
for day in sorted(keep_dates):
    agg = t1_by_date.get(day)
    aborts = abort_counts.get(day, 0)
    if agg:
        print(f"  {day}: runs={agg['runs']} total_players_matched={agg['players_sum']} total_bets={agg['bets_sum']} contamination_guard_aborts={aborts}")
    else:
        print(f"  {day}: no completed run found in current log window (contamination_guard_aborts={aborts})")
print(f"  SemanticFloorViolation count (whole file, not date-filtered): {semantic_floor_total} ({'ALARM - T1 pipeline silence' if semantic_floor_total else 'healthy'})")

print("")
print("  Game-count methodology note: \"games\" above = distinct ticker date/matchup")
print("  segments seen in t4_mlb_cycle_log.jsonl that day, NOT an ESPN box-score count.")
print("  This is a different, live-computable proxy from GG-080's manual box-score")
print("  count (2026-07-02/03, 924/464 rows-per-game-day) — treat as a complementary")
print("  ongoing signal, not a recomputation or correction of that historical figure.")
print("")
print("=== Source trace (ADR-0041 Tier 2 traceability requirement) ===")
print(f"  t4_mlb_cycle_log.jsonl: {lines_read} lines scanned on VPS, filtered to game_date in {sorted(keep_dates)}")
print("  audit_mlb_t4_edge_decisions.jsonl, audit_mlb_t4.jsonl: streamed full file on VPS, filtered by timestamp date prefix")
print("  paper_mlb_cron.log: streamed full file on VPS, [PIPE-05]-delimited run blocks")
print("  All four files: /opt/prediction-market-bot/logs/ — untouched, unmodified, not copied off-host by this script")
'''


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--days", type=int, default=3, help="Trailing UTC calendar days to summarize (default 3)")
    ap.add_argument("--host", default="prediction-market-vps", help="SSH alias for the VPS (default prediction-market-vps)")
    args = ap.parse_args()

    cmd = ["ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes", args.host, f"python3 - {args.days}"]
    try:
        result = subprocess.run(cmd, input=REMOTE_SCRIPT, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        print("ERROR: remote aggregation timed out after 120s", file=sys.stderr)
        return 1

    if result.returncode != 0:
        print("ERROR: remote aggregation failed", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return 1

    now = datetime.datetime.now(datetime.timezone.utc)
    header = (
        "================================================================\n"
        f"CRON LOG EXECUTIVE SUMMARY — generated {now.strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
        "T-300 (A4) | ADR-0041 Tier 2 — computed remotely on the VPS; raw logs\n"
        "never pulled to local disk or loaded into a session's context.\n"
        "================================================================\n\n"
    )
    body = header + result.stdout

    out_dir = pathlib.Path("logs")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"cron_summary_{now.strftime('%Y%m%dT%H%M%SZ')}.md"
    out_path.write_text(body)

    print(body)
    print(f"(written to {out_path})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
