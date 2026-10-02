#!/usr/bin/env python3
"""Backfill NHL schedules + boxscores into data/raw/nhl (T-607). Read-only, <=1 req/s, resumable.

usage: nhl_backfill.py [--seasons 2021 2022 ...] [--root data/raw/nhl]
Finished (FINAL/OFF) regular-season games only get boxscores; existing files are skipped.
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from prediction_market_bot.c1_signal_ingestion import nhl_ingest as N


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", nargs="*", type=int, default=[2021, 2022, 2023, 2024, 2025, 2026])
    ap.add_argument("--root", default=str(N.RAW_DIR))
    ap.add_argument("--refresh-schedule", action="store_true")
    a = ap.parse_args()
    root, th = Path(a.root), N.Throttle()
    for s in a.seasons:
        have = N.load_schedule(s, root)
        if not have or a.refresh_schedule:
            games = N.fetch_season_schedule(s, th)
            N.save_schedule(s, games, root)
            have = list(games.values())
        fin = [g for g in have if g["state"] in ("FINAL", "OFF")]
        print(f"season {s}: {len(have)} reg-season games, {len(fin)} final", flush=True)
        for i, g in enumerate(sorted(fin, key=lambda g: g["start_time_utc"])):
            if N.box_path(g["game_id"], root).exists():
                continue
            N.fetch_boxscore(g["game_id"], th, root)
            if i % 100 == 0:
                print(f"  {s} {i}/{len(fin)} interval={th.interval_s:.2f}", flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(main())
