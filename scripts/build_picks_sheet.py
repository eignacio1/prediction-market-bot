#!/usr/bin/env python3
"""Nightly picks-sheet builder (W97.3, B-026). Read-only over ledgers; writes exp_output/PICKS_SHEET/picks_<date>.json
and picks_latest.json. No order path, no network. Memory bounded: ledgers are tailed, never loaded whole."""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from prediction_market_bot.pregame_shadow import picks_sheet as ps  # noqa: E402

LEDGER_GLOBS = [
    "exp_output/PREGAME_SHADOW/*_T[123].jsonl",
    "exp_output/PREGAME_SHADOW_NFLQB/*.jsonl",
    "exp_output/PREGAME_SHADOW_EXP040/*.jsonl",
    "data/shadow/nhl/NHL_*_T[123].jsonl",
]
ENGINE_FILES = {"nba_engine_v1": "exp_output/NBA_ENGINE_LIVE/rows.jsonl", "nba_engine_v2": "exp_output/NBA_ENGINE_LIVE_V2/rows.jsonl"}


def _arm_name(path: str) -> str:
    return os.path.basename(path)[:-len(".jsonl")]


def collect(root: str, since: dt.datetime, tail_bytes: int) -> tuple:
    picks, notes = [], []
    for pat in LEDGER_GLOBS:
        for path in sorted(glob.glob(os.path.join(root, pat))):
            picks += list(ps.latest_picks(ps.tail_rows(path, tail_bytes), _arm_name(path), since).values())
    for arm, rel in ENGINE_FILES.items():
        path = os.path.join(root, rel)
        if not os.path.exists(path):
            notes.append(f"{arm}: no rows file yet")
            continue
        got = ps.latest_picks(ps.tail_rows(path, tail_bytes), arm, since)
        picks += list(got.values())
        if not got:
            notes.append(f"{arm}: no pick in window")
    orders = ps.orders_by_ticker(ps.tail_rows(os.path.join(root, "logs/demo_fill_policy.jsonl"), 15_000_000), since)
    ps.attach_orders(picks, orders)
    settled = []
    for path in glob.glob(os.path.join(root, "exp_output/PREGAME_SHADOW/settled/*.jsonl")):
        settled += list(ps.tail_rows(path, 2_000_000))
    ps.attach_results(picks, settled)
    return picks, notes


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--date", default=None, help="sheet date UTC (default today); window is the 30h ending at end of that day")
    ap.add_argument("--tail-bytes", type=int, default=6_000_000)
    a = ap.parse_args(argv)
    day = dt.date.fromisoformat(a.date) if a.date else dt.datetime.now(dt.timezone.utc).date()
    end = dt.datetime.combine(day + dt.timedelta(days=1), dt.time(), tzinfo=dt.timezone.utc)
    picks, notes = collect(a.root, end - dt.timedelta(hours=30), a.tail_bytes)
    sheet = ps.build(day.isoformat(), picks, notes)
    out = os.path.join(a.root, "exp_output", "PICKS_SHEET")
    os.makedirs(out, exist_ok=True)
    for name in (f"picks_{day.isoformat()}.json", "picks_latest.json"):
        tmp = os.path.join(out, name + ".tmp")
        with open(tmp, "w") as fh:
            json.dump(sheet, fh, indent=1)
        os.replace(tmp, os.path.join(out, name))
    print(f"picks sheet {day}: {sheet['n_picks']} picks in {len(sheet['games'])} games")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
