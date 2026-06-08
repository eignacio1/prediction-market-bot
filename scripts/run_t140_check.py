#!/usr/bin/env python3
"""
T-140 — TSS cache pre-flight check.

Runs at 21:25 UTC (30 min before PIPE-02 at 21:55 UTC).
Checks team_stats_cache_{TODAY}.json in the logs directory.
If the file is missing or < 1000 bytes, rebuilds it using build_tss_cache.py.

Exit codes: 0 = cache OK, 1 = rebuilt successfully, 2 = rebuild failed.
"""
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJ = Path(__file__).parent.parent
LOG_DIR = PROJ / "logs"
BUILD_SCRIPT = PROJ / "scripts" / "build_tss_cache.py"
MIN_CACHE_BYTES = 1000
PYTHON = sys.executable


def _cache_path(game_date: str) -> Path:
    return LOG_DIR / f"team_stats_cache_{game_date}.json"


def main() -> int:
    game_date = datetime.now(tz=timezone.utc).strftime("%Y%m%d")
    cache = _cache_path(game_date)
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    size = cache.stat().st_size if cache.exists() else 0

    if size >= MIN_CACHE_BYTES:
        print(f"[T-140 {ts}] TSS cache OK — {size} bytes ({cache.name})")
        return 0

    print(
        f"[T-140 {ts}] TSS cache STALE — {size} bytes. "
        f"Rebuilding via build_tss_cache.py ..."
    )

    # Run build_tss_cache.py with CWD=logs/ so it writes team_stats_cache_{DATE}.json there.
    result = subprocess.run(
        [PYTHON, str(BUILD_SCRIPT)],
        cwd=str(LOG_DIR),
        capture_output=True,
        text=True,
        timeout=120,
    )

    new_size = cache.stat().st_size if cache.exists() else 0
    ts2 = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if result.returncode != 0 or new_size < MIN_CACHE_BYTES:
        print(
            f"[T-140 {ts2}] REBUILD FAILED — returncode={result.returncode}  "
            f"new_size={new_size} bytes"
        )
        if result.stderr:
            print(result.stderr[:500])
        print(
            "[T-140] WARNING: PIPE-02 will run without adj_lambda "
            "(opp_adj_lambda == pts_l10_mean). Bets will still be placed."
        )
        return 2

    print(
        f"[T-140 {ts2}] REBUILD OK — {new_size} bytes written to {cache.name}"
    )
    if result.stdout:
        print(result.stdout[:200])
    return 1


if __name__ == "__main__":
    sys.exit(main())
