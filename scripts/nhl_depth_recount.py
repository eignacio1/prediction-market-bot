#!/usr/bin/env python3
"""READ-ONLY (W129.1): re-count the NHL game join (both_expected / any_backup / prior_only / unknown / no_game) over the box's NHL shadow
rows from 2026-11-10, per distinct game (event ticker), at the LAST row before first pitch is not needed: one row per event, the latest.

Two passes over the same rows: ``muse_only`` (no event store: the W128.1 starter definition, Muse-confirmed history alone) and
``store+muse`` (W129.1). Also the unknown-starter share, and the first date the frozen PREREG's judged n (~370 games) is reached at
the observed games/day. Writes nothing: stdout only."""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))
import candidate_arms_read as car  # noqa: E402
from prediction_market_bot.decision_trees.filters import nhl_depth as nd  # noqa: E402

SINCE = datetime(2026, 11, 10, tzinfo=timezone.utc)
JUDGED_N = 370


def games(since: datetime = SINCE) -> dict:
    out: dict = {}
    for r in car.rows(since):
        if str(r.get("sport") or "").upper() != "NHL" or not r.get("event_ticker"):
            continue
        k = r["event_ticker"]
        if k not in out or r["ts_utc"] > out[k]["ts_utc"]:
            out[k] = {"event_ticker": k, "ts_utc": r["ts_utc"]}
    return out


def tally(rows, store) -> Counter:
    c: Counter = Counter()
    for r in rows:
        d = nd.depth_for_row(r, None, store)
        c["no_game" if d is None else d[0]["goalie@game"]] += 1
    return c


def main() -> int:
    g = list(games().values())
    muse = os.environ.get("NHL_MUSE_DIR")
    days = sorted({nd._parse_event(r["event_ticker"])[0] for r in g if nd._parse_event(r["event_ticker"])})
    before = tally(g, False)
    after = tally(g, nd.default_store())
    n = len(g)
    print(json.dumps({"muse_dir": muse, "games": n, "days": [days[0], days[-1]] if days else None, "muse_only": dict(before), "store_plus_muse": dict(after),
                      "unknown_share_before": round(before["unknown"] / n, 3) if n else None,
                      "unknown_share_after": round(after["unknown"] / n, 3) if n else None}, sort_keys=True))
    if days:
        span = (date.fromisoformat(days[-1]) - date.fromisoformat(days[0])).days + 1
        per_day = n / span
        need = max(0, JUDGED_N - n)
        eta = date.fromisoformat(days[-1]).toordinal() + (int(need / per_day) + 1 if per_day else 0)
        print(f"JUDGED_N {JUDGED_N}: {n} games over {span} days = {per_day:.2f}/day; reached about {date.fromordinal(eta)} at the current schedule "
              f"(NHL regular season runs to mid-April 2027; the date is only an extrapolation of the observed rate)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
