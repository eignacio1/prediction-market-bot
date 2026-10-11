#!/usr/bin/env python3
"""Backfill NBA player box scores into data/raw/nba/players_<season>.json (W65.1 / EXP-039). Read-only, <=2 req/s, resumable.

usage: nba_player_box_backfill.py --seasons 2023 2024 2025 2026 [--root data/raw/nba] [--with-scoreboard]
Season = ending year. --with-scoreboard first runs the scoreboard backfill (needed to know the game ids).
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from prediction_market_bot.c1_signal_ingestion import nba_ingest as N
from prediction_market_bot.c1_signal_ingestion import nba_player_ingest as P


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", nargs="*", type=int, default=[2027])
    ap.add_argument("--root", default=str(N.RAW_DIR))
    ap.add_argument("--with-scoreboard", action="store_true")
    a = ap.parse_args()
    root, th = Path(a.root), N.Throttle()
    for s in a.seasons:
        if a.with_scoreboard:
            n = N.backfill_season(s, th, root)
            print(f"season {s}: scoreboard dates fetched {n}", flush=True)
        g = P.backfill_players(s, th, root)
        print(f"season {s}: box scores fetched {g}; stored {len(P.load_players(s, root)['games'])}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
