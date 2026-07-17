#!/usr/bin/env python3
"""
T-375 — GG-060 Phase 2: 7-day edge-rate trend

WHY THIS EXISTS
----------------
`risk.summarize_edge_run()` (T-213) answers "is this ONE run/session healthy?"
It reads a single edge-decision JSONL sink cumulatively and classifies it as
PIPELINE_BROKEN / NO_EDGE / RISK_REJECTED / ACTIVE, with a `silent_success_flag`
for total_evaluations>=50 and edge_signals_found==0. That is a point-in-time
check — it does not answer "has this band's edge-signal rate been silently
decaying over the last week?" A band can look ACTIVE on any single day (a few
edge signals found) while the day-over-day rate trends toward zero — exactly
the kind of slow-fade silent failure that a single-run summary cannot see,
because each individual day still clears the >=50-eval / >0-signal bar.

This script re-buckets the SAME edge-decision sinks used by summarize_edge_run
(T1: audit_mlb_edge_decisions.jsonl, T4M-PROJ: audit_mlb_t4_edge_decisions.jsonl,
T2: audit_mlb_t2_edge_decisions.jsonl — GG-060 Phase 1 wiring, T-375) by UTC
calendar day over a trailing window (default 7 days) and reports, per band per
day: total_evaluations, edge_signals_found, edge_rate, bets_approved, run_state.
It flags two distinct conditions, deliberately kept separate because they mean
different things operationally:

  SUSTAINED_ZERO_EDGE — >=3 consecutive days-with-data (total_evaluations>0)
                        where edge_signals_found==0. The pipeline is running
                        and evaluating, but has stopped finding edge — this is
                        the drift condition GG-060 Phase 2 was scoped to catch.
  MISSING_DAYS        — one or more days in the trailing window with ZERO
                         edge_decision records at all. This is reported, not
                         auto-classified as broken, because it is
                         indistinguishable from "no games that day" without an
                         external schedule signal (this script does not have
                         one) — see CLAUDE.md Step 4's own T1-vs-NBA-off-season
                         precedent for why that ambiguity is called out rather
                         than resolved here.

Composition: reuses `risk.summarize_edge_run`'s exact vocabulary
(run_state, silent_success_flag, edge_signal) and its STATUS_APPROVED /
MIN_EDGE_TO_APPROVE constants indirectly (via the same payload fields each
edge_decision record already carries) so this script cannot drift from what
Phase 1 already defines as "an edge signal."

Run:
  python3 scripts/edge_rate_trend.py
  python3 scripts/edge_rate_trend.py --days 14
  python3 scripts/edge_rate_trend.py --json
  python3 scripts/edge_rate_trend.py --t1 logs/.vps_audit_mlb_edge_decisions.jsonl \\
      --t4 logs/.vps_audit_mlb_t4_edge_decisions.jsonl --t2 logs/.vps_audit_mlb_t2_edge_decisions.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_SRC_ROOT = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(_SRC_ROOT))
from prediction_market_bot.c4_risk_engine.risk import STATUS_APPROVED  # noqa: E402

DEFAULT_SINKS = {
    "T1": Path("logs/audit_mlb_edge_decisions.jsonl"),
    "T4M-PROJ": Path("logs/audit_mlb_t4_edge_decisions.jsonl"),
    "T2": Path("logs/audit_mlb_t2_edge_decisions.jsonl"),
}

SUSTAINED_ZERO_EDGE_MIN_DAYS = 3


def _load_entries(path: Path) -> list[dict[str, Any]]:
    """Read a JSONL edge-decision sink, skipping any malformed lines rather
    than crashing — this is monitoring tooling reading a live-appended file,
    a torn last line (mid-write) is expected, not exceptional."""
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def _day_key(entry: dict[str, Any]) -> str | None:
    ts = entry.get("timestamp")
    if not ts or not isinstance(ts, str) or len(ts) < 10:
        return None
    return ts[:10]


def _classify_day(total: int, edge_signals: int, approved: int) -> str:
    """Same state machine as risk.summarize_edge_run(), applied to one day's
    slice instead of a whole-file/session cumulative read."""
    if total == 0:
        return "PIPELINE_BROKEN"
    if edge_signals == 0:
        return "NO_EDGE"
    if approved == 0:
        return "RISK_REJECTED"
    return "ACTIVE"


def daily_edge_stats(
    entries: list[dict[str, Any]],
    days: int,
    reference_date: str | None = None,
) -> dict[str, dict[str, Any]]:
    """
    Bucket edge_decision entries by UTC calendar day over the trailing
    `days`-day window ending at `reference_date` (default: today UTC,
    inclusive). Returns {date_str: {total_evaluations, edge_signals_found,
    bets_approved, edge_rate, run_state}}, one key per day in the window
    REGARDLESS of whether that day has any data (missing days get
    total_evaluations=0 / run_state=PIPELINE_BROKEN so gaps are visible,
    not silently skipped).
    """
    if reference_date is None:
        ref = datetime.now(tz=timezone.utc).date()
    else:
        ref = datetime.strptime(reference_date, "%Y-%m-%d").date()

    window_days = [(ref - timedelta(days=i)).isoformat() for i in range(days - 1, -1, -1)]

    buckets: dict[str, list[dict[str, Any]]] = {d: [] for d in window_days}
    for entry in entries:
        d = _day_key(entry)
        if d in buckets:
            buckets[d].append(entry)

    out: dict[str, dict[str, Any]] = {}
    for d in window_days:
        day_entries = buckets[d]
        total = len(day_entries)
        edge_signals = sum(1 for e in day_entries if (e.get("payload") or {}).get("edge_signal"))
        approved = sum(
            1 for e in day_entries
            if (e.get("payload") or {}).get("approval_status") == STATUS_APPROVED
        )
        edge_rate = (edge_signals / total) if total > 0 else None
        out[d] = {
            "total_evaluations": total,
            "edge_signals_found": edge_signals,
            "bets_approved": approved,
            "edge_rate": edge_rate,
            "run_state": _classify_day(total, edge_signals, approved),
        }
    return out


def detect_sustained_zero_edge(daily: dict[str, dict[str, Any]]) -> list[str]:
    """
    Return the list of consecutive-day runs (as 'YYYY-MM-DD..YYYY-MM-DD'
    strings) where total_evaluations>0 (pipeline is running) but
    edge_signals_found==0 (NO_EDGE) for >=SUSTAINED_ZERO_EDGE_MIN_DAYS days
    in a row. Days with total_evaluations==0 (no data) BREAK a streak rather
    than counting toward it — a missing day is a different condition
    (MISSING_DAYS) and must not be conflated with "ran and found nothing."
    """
    days_sorted = sorted(daily.keys())
    flags: list[str] = []
    streak: list[str] = []

    def _flush() -> None:
        if len(streak) >= SUSTAINED_ZERO_EDGE_MIN_DAYS:
            flags.append(f"{streak[0]}..{streak[-1]} ({len(streak)} days)")
        streak.clear()

    for d in days_sorted:
        stats = daily[d]
        if stats["total_evaluations"] > 0 and stats["edge_signals_found"] == 0:
            streak.append(d)
        else:
            _flush()
    _flush()
    return flags


def detect_missing_days(daily: dict[str, dict[str, Any]]) -> list[str]:
    return sorted(d for d, stats in daily.items() if stats["total_evaluations"] == 0)


def build_report(
    sinks: dict[str, Path],
    days: int,
    reference_date: str | None = None,
) -> dict[str, Any]:
    report: dict[str, Any] = {}
    for band, path in sinks.items():
        entries = _load_entries(path)
        daily = daily_edge_stats(entries, days, reference_date)
        report[band] = {
            "sink_path": str(path),
            "sink_exists": path.exists(),
            "daily": daily,
            "sustained_zero_edge_streaks": detect_sustained_zero_edge(daily),
            "missing_days": detect_missing_days(daily),
        }
    return report


def _fmt_rate(rate: float | None) -> str:
    return "  n/a" if rate is None else f"{rate * 100:5.1f}%"


def print_report(report: dict[str, Any], days: int) -> None:
    print(f"=== GG-060 Phase 2 — {days}-day edge-rate trend (UTC calendar days) ===\n")
    for band, band_report in report.items():
        print(f"--- {band}  (sink: {band_report['sink_path']}) ---")
        if not band_report["sink_exists"]:
            print("  sink file does not exist — nothing to report.\n")
            continue
        for d in sorted(band_report["daily"].keys()):
            s = band_report["daily"][d]
            print(
                f"  {d}  evals={s['total_evaluations']:>5}  "
                f"edge_signals={s['edge_signals_found']:>5}  "
                f"rate={_fmt_rate(s['edge_rate'])}  "
                f"approved={s['bets_approved']:>4}  "
                f"state={s['run_state']}"
            )
        if band_report["missing_days"]:
            print(f"  MISSING_DAYS (0 records, unknown if off-day or broken): {', '.join(band_report['missing_days'])}")
        if band_report["sustained_zero_edge_streaks"]:
            print(f"  *** SUSTAINED_ZERO_EDGE: {'; '.join(band_report['sustained_zero_edge_streaks'])} ***")
        print()


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--days", type=int, default=7, help="Trailing window size in UTC calendar days (default: 7).")
    p.add_argument("--reference-date", default=None, help="YYYY-MM-DD; window ends on this date inclusive (default: today UTC).")
    p.add_argument("--t1", type=Path, default=DEFAULT_SINKS["T1"], help="Path to T1's edge-decision JSONL sink.")
    p.add_argument("--t4", type=Path, default=DEFAULT_SINKS["T4M-PROJ"], help="Path to T4M-PROJ's edge-decision JSONL sink.")
    p.add_argument("--t2", type=Path, default=DEFAULT_SINKS["T2"], help="Path to T2's edge-decision JSONL sink.")
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of the printed report.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    sinks = {"T1": args.t1, "T4M-PROJ": args.t4, "T2": args.t2}
    report = build_report(sinks, args.days, args.reference_date)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report, args.days)

    any_flag = any(
        band_report["sustained_zero_edge_streaks"] for band_report in report.values()
    )
    return 1 if any_flag else 0


if __name__ == "__main__":
    raise SystemExit(main())
