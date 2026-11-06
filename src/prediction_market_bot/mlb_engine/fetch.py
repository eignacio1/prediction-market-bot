"""Resumable day-by-day Baseball Savant (Statcast) pitch fetch. $0, off-box only.

Savant's search CSV is capped at 25,000 rows per query; one regular-season day is ~2.5-4.5k pitches,
so one request per game date is safe. Each day is cached as raw/<year>/<date>.csv.gz (an empty day is
cached as a zero-row marker so a rerun does not refetch it).
"""
from __future__ import annotations

import gzip
import time
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from typing import Iterator

SAVANT_URL = (
    "https://baseballsavant.mlb.com/statcast_search/csv?all=true&hfGT=R%7C&hfSea={year}%7C"
    "&player_type=pitcher&game_date_gt={d}&game_date_lt={d}&type=details&min_pitches=0&min_results=0"
    "&group_by=name&sort_col=pitches&player_event_sort=h_launch_speed&sort_order=desc&min_abs=0"
)
ROW_CAP = 25_000
_UA = "Mozilla/5.0 (research; pm-bot mlb_engine)"


def daterange(start: date, end: date) -> Iterator[date]:
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def raw_path(store: Path, d: date) -> Path:
    return Path(store) / "raw" / str(d.year) / f"{d.isoformat()}.csv.gz"


def fetch_day(d: date, timeout: int = 90) -> bytes:
    url = SAVANT_URL.format(year=d.year, d=d.isoformat())
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def row_count(csv_bytes: bytes) -> int:
    return max(0, csv_bytes.count(b"\n") - 1) if csv_bytes.strip() else 0


def fetch_range(store: Path, start: date, end: date, pause: float = 1.0, retries: int = 4) -> dict:
    """Fetch every missing day in [start, end]. Returns {fetched, cached, empty, capped}."""
    out = {"fetched": 0, "cached": 0, "empty": 0, "capped": []}
    for d in daterange(start, end):
        p = raw_path(store, d)
        if p.exists():
            out["cached"] += 1
            continue
        body = b""
        for k in range(retries):
            try:
                body = fetch_day(d)
                break
            except Exception:  # network / 5xx: back off and retry
                if k == retries - 1:
                    raise
                time.sleep(5 * (k + 1))
        n = row_count(body)
        if n >= ROW_CAP:
            out["capped"].append(d.isoformat())  # would be truncated: must be split by caller
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        with gzip.open(tmp, "wb") as fh:
            fh.write(body)
        tmp.replace(p)
        out["fetched"] += 1
        out["empty"] += int(n == 0)
        time.sleep(pause)
    return out


if __name__ == "__main__":  # python -m prediction_market_bot.mlb_engine.fetch STORE START END
    import sys

    s, a, b = sys.argv[1:4]
    print(fetch_range(Path(s), date.fromisoformat(a), date.fromisoformat(b)))
