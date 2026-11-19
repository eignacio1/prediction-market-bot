"""W117.1 / B-095 Part A2: the book at submit for orders that did not log it, read from the price archive.

READ-ONLY. The arm-order log is append-only and is never edited: a backfill is computed at read time. For an order with no
``book_at_submit`` the book is the LATEST archive tick for that ticker at or before the order's submit time and no older than
``MAX_AGE`` (the archiver samples about every 20 minutes, so a tick up to one cycle old is the nearest the archive has). The tick must be
two-sided (the placement rule refuses a one-sided book, so every placed order saw one). The source and the tick's age are carried on
every record (``spread_src`` = "logged" | "archive", ``spread_age_s``) so the age can be read, never assumed.

WHAT IT CANNOT SUPPORT: the archive tick is NOT the book at the instant of submit (up to MAX_AGE earlier). A spread filled from it is an
estimate, labelled "archive"; depth at the touch is not in the plain price rows and is not backfilled. A ticker the archive does
not cover (series not archived, or the cron not installed at that time) stays None - never filled with a default.
"""
from __future__ import annotations

import bisect
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from prediction_market_bot.io_jsonl import open_jsonl  # W119.4: reads .jsonl or .jsonl.gz
from prediction_market_bot.timeparse import parse_ts

MAX_AGE = timedelta(minutes=30)
Tick = Tuple[float, float, float]  # (epoch seconds, yes_bid, yes_ask)


def _f(x: Any) -> Optional[float]:
    try:
        return None if x is None or x == "" else float(x)
    except (TypeError, ValueError):
        return None


def load_ticks(archive_dir: Path, tickers: Iterable[str], days: Iterable[str]) -> Dict[str, List[Tick]]:
    """ticker -> ticks sorted by time, two-sided only, from prices_<day>.jsonl for the given UTC days (missing files skipped)."""
    want = set(tickers)
    out: Dict[str, List[Tick]] = {}
    for day in sorted(set(days)):
        f = Path(archive_dir) / f"prices_{day}.jsonl"
        try:
            fh = open_jsonl(f)
        except OSError:  # FileNotFoundError is an OSError: a missing day is skipped
            continue
        with fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                tk = r.get("ticker")
                if tk not in want:
                    continue
                t, yb, ya = parse_ts(r.get("run_ts")), _f(r.get("yes_bid")), _f(r.get("yes_ask"))
                if t is None or yb is None or ya is None or yb <= 0 or ya <= 0 or ya < yb:
                    continue
                out.setdefault(tk, []).append((t.timestamp(), yb, ya))
    for v in out.values():
        v.sort()
    return out


def book_from_ticks(ticks: Dict[str, List[Tick]], ticker: str, at: datetime, max_age: timedelta = MAX_AGE) -> Optional[dict]:
    """Latest two-sided tick at or before ``at`` and not older than ``max_age``; None when the archive has none."""
    v = ticks.get(ticker)
    if not v:
        return None
    t = at.timestamp()
    i = bisect.bisect_right([x[0] for x in v], t) - 1
    if i < 0 or t - v[i][0] > max_age.total_seconds():
        return None
    ts, yb, ya = v[i]
    return {"yes_bid": yb, "yes_ask": ya, "spread": round(ya - yb, 4), "age_s": int(t - ts), "src": "archive"}


def book_of_for(rows: Iterable[dict], archive_dir: Path) -> Callable[[str, datetime], Optional[dict]]:
    """A ``book_of(ticker, submit_ts)`` closure for the arm orders in ``rows`` that carry no spread (their ticker and the UTC day
    of submit, plus the day before, because an order just after 00:00Z sits on the previous day's last ticks)."""
    tickers, days = set(), set()
    for r in rows:
        if r.get("event") != "arm_order" or not r.get("ok"):
            continue
        b = r.get("book_at_submit") or {}
        if _f(b.get("yes_bid")) is not None and _f(b.get("yes_ask")) is not None:
            continue
        ts = parse_ts(r.get("ts"))
        if ts is None or not r.get("ticker"):
            continue
        tickers.add(str(r["ticker"]))
        days.update({ts.strftime("%Y-%m-%d"), (ts - timedelta(days=1)).strftime("%Y-%m-%d")})
    ticks = load_ticks(archive_dir, tickers, days)
    return lambda ticker, at: book_from_ticks(ticks, ticker, at)
