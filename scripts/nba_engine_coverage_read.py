#!/usr/bin/env python3
"""READ-ONLY (W101.1 / B-030): per NBA engine arm, per night (ET game date), games scheduled, logged before tip, missed past tip, reasons.

Sources: <arm>/rows.jsonl (logged), <arm>/coverage.jsonl (explicit misses, written by the runner), logs/t3_skips.jsonl (lock skips),
OOM kills are in box_memory_read. A game is "scheduled" if ANY arm saw it (rows or coverage). A miss with no coverage row (a night before
the arm wrote coverage, e.g. v3 before W101.1) is RECONSTRUCTED from the other arms' universe and marked source=reconstructed.
Output is one compact table + counts; nothing is written.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARMS = {"v1": "NBA_ENGINE_LIVE", "v2": "NBA_ENGINE_LIVE_V2", "v3": "NBA_ENGINE_LIVE_V3"}
EV_DATE = re.compile(r"-(\d{2})([A-Z]{3})(\d{2})")
MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}


def read_jsonl(p: Path) -> list:
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def event_date(ev: str, fallback: str | None = None) -> str:
    m = EV_DATE.search(ev)
    return "20%s-%02d-%s" % (m.group(1), MON[m.group(2)], m.group(3)) if m and m.group(2) in MON else (fallback or "unknown")


def per_arm(root: Path, out_root: Path | None = None) -> dict:
    """arm -> dict(event -> dict(logged_before_tip, logged_at, tip, game_date)), and arm -> coverage reasons."""
    out_root = out_root or root / "exp_output"
    res = {}
    for arm, d in ARMS.items():
        rows = read_jsonl(out_root / d / "rows.jsonl")
        cov = read_jsonl(out_root / d / "coverage.jsonl")
        ev = {}
        for r in rows:
            e = r["event_ticker"]
            if e in ev:
                continue
            tip, at = r.get("tip_utc"), r.get("logged_at")
            before = None
            if tip and at:
                before = datetime.fromisoformat(at) < datetime.fromisoformat(tip)
            ev[e] = dict(game_date=r.get("game_date") or event_date(e), before_tip=before, logged_at=at)
        res[arm] = dict(logged=ev, coverage={c["event_ticker"]: c for c in cov})
    return res


def build(arms: dict, nights: list | None = None) -> dict:
    universe = {}
    for a in arms.values():
        for e, v in a["logged"].items():
            universe[e] = v["game_date"]
        for e in a["coverage"]:
            universe.setdefault(e, event_date(e))
    out = defaultdict(dict)
    for night in sorted(set(universe.values())):
        if nights and night not in nights:
            continue
        evs = sorted(e for e, d in universe.items() if d == night)
        for arm, a in arms.items():
            logged = [e for e in evs if e in a["logged"]]
            ok = [e for e in logged if a["logged"][e]["before_tip"] is not False]
            late = [e for e in logged if a["logged"][e]["before_tip"] is False]
            miss = []
            for e in evs:
                if e in a["logged"]:
                    continue
                if e in a["coverage"]:
                    miss.append(dict(event=e, reason=a["coverage"][e]["reason"], source="coverage.jsonl"))
                else:
                    miss.append(dict(event=e, reason="not_in_rows_and_no_coverage_row", source="reconstructed"))
            out[night][arm] = dict(scheduled=len(evs), logged_before_tip=len(ok), logged_after_tip=len(late), missed=len(miss),
                                   reasons={"%s|%s" % k: v for k, v in Counter((m["reason"], m["source"]) for m in miss).items()},
                                   missed_events=miss)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nights", default="", help="comma list of YYYY-MM-DD game dates (default: all)")
    ap.add_argument("--root", default=str(ROOT))
    a = ap.parse_args(argv)
    root = Path(a.root)
    nights = [n for n in a.nights.split(",") if n] or None
    res = build(per_arm(root), nights)
    print("== NBA engine coverage per arm per night (game date from ticker) ==")
    for night, arms in res.items():
        print(night)
        for arm, s in arms.items():
            print("  %s scheduled=%d logged_before_tip=%d logged_after_tip=%d missed=%d %s" % (
                arm, s["scheduled"], s["logged_before_tip"], s["logged_after_tip"], s["missed"], json.dumps(s["reasons"])))
    print("\n== missed events ==")
    for night, arms in res.items():
        for arm, s in arms.items():
            for m in s["missed_events"]:
                print("  %s %s %s %s [%s]" % (night, arm, m["event"], m["reason"], m["source"]))
    sk = read_jsonl(root / "logs" / "t3_skips.jsonl")
    print("\n== lock skips (UTC date, runner): %s ==" % json.dumps(dict(Counter("%s %s" % (r["ts"][:10], r.get("runner")) for r in sk))))
    st = root / "exp_output" / "NBA_EVENTS" / "current" / "status.json"
    print("== store status: %s ==" % (st.read_text()[:400].replace("\n", " ") if st.exists() else "missing"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
