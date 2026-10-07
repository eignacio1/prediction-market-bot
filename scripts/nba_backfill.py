#!/usr/bin/env python3
"""Backfill NBA schedules + scores into data/raw/nba (W58.2 / EXP-038). Read-only, <=2 req/s, resumable.

usage: nba_backfill.py [--seasons 2016 2017 ...] [--root data/raw/nba]
Season = ending year (2024 == 2023-24). Past dates already fetched are skipped; the trailing 3 days refresh.
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from prediction_market_bot.c1_signal_ingestion import nba_ingest as N


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", nargs="*", type=int, default=[2026, 2027])
    ap.add_argument("--root", default=str(N.RAW_DIR))
    ap.add_argument("--lookahead", type=int, default=21, help="also fetch/refresh the next N days of schedule")
    a = ap.parse_args()
    th = N.Throttle()
    for s in a.seasons:
        n = N.backfill_season(s, th, Path(a.root), lookahead_days=a.lookahead)
        st = N.load_season(s, Path(a.root))
        print(f"season {s}: fetched {n} dates; {len(N.completed_regular(st))} completed regular-season games", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
