#!/usr/bin/env python3
"""W116.3 / B-092 (GG-1953): refresh the box's NHL event store -- the source of NHL layer-3 filters (filter_supply.nhl_adapter).

Fetches the two seasons the box keeps (nhl_event_store.store_seasons: the one in progress and the one before it; resumable, only
games not yet cached are fetched, public NHL API GETs at <= 2 req/s), then compiles exactly those two seasons with the streamed
compile (parsed rows flushed every COMPILE_CHUNK_GAMES games; measured 270 MB peak locally vs 2,049 MB before). Each table is
written aside and renamed, so a runner reading the store mid-refresh sees the old table or the new one, never half of one.

Writes only exp_output/NHL_EVENTS/ (raw cache, schedule_games.json, <table>_<season>.parquet, recon.json). No order, stake or kelly.
Runs from deploy/cron.nhl_event_store, PAUSED until the operator approves the named install task `nhl_event_store_install`.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from prediction_market_bot.c1_signal_ingestion import nhl_event_store as es  # noqa: E402

RPS = 2.0
THREADS = 2


def main(root: Path = ROOT / es.DEFAULT_ROOT, fetch=es.build_fetch, compile_=es.compile_store) -> int:
    seasons = es.store_seasons()
    t0 = time.time()
    f = fetch(root, seasons, RPS, THREADS, None)
    t1 = time.time()
    c = compile_(root, seasons)
    print(json.dumps({"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "runner": "nhl_event_store_refresh",
                      "seasons": seasons, "fetch": f, "fetch_s": round(t1 - t0, 1),
                      "compiled": {k: v for k, v in c.items()}, "compile_s": round(time.time() - t1, 1)}, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
