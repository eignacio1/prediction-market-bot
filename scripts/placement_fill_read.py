#!/usr/bin/env python3
"""READ-ONLY (W125.1 Part A + C, B-095 / B-113): the placement fill model and the skip-reason counts, compact enough for the box's
60 KB output cap. Writes nothing: stdout only.

Part A: per epoch (pre-epoch YES-only and post-epoch all sides, never pooled) the table placement.fill_model builds from the
per-order join: arm x family x hours-to-start -> fill rate, adverse selection, net per FILLED contract (90% game-clustered),
markouts at +5 / +30 min, partial pooling within an arm. DESCRIPTIVE where it overlaps H-EXEC-4's frozen forward population.

Part C: every skip reason since --since (default 2026-11-12, the first arm-order day) as a reported number, per reason and per
arm, and the orders placed per day against the demo book's day cap, so a cap that starves the test shows as a count.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import arm_orders_read as aor  # noqa: E402
from prediction_market_bot.timeparse import parse_ts  # noqa: E402

SINCE = "2026-11-12"


def skip_counts(rows: List[dict], since: str = SINCE) -> dict:
    """How many arm decisions each skip reason removed since ``since`` (UTC date). A reason of the form ``a:b`` also counts under ``a``."""
    by_reason: Counter = Counter()
    by_arm: dict = {}
    placed: Counter = Counter()
    day_stake: Counter = Counter()
    decisions = 0
    for r in rows:
        ev = r.get("event")
        if ev not in ("arm_skip", "arm_order", "arm_would_order"):
            continue
        ts = parse_ts(r.get("ts"))
        if ts is None or ts.strftime("%Y-%m-%d") < since:
            continue
        decisions += 1
        d = ts.strftime("%Y-%m-%d")
        if ev == "arm_order" and r.get("ok"):
            placed[d] += 1
            day_stake[d] += float(r.get("stake_usd") or 0)
        elif ev == "arm_skip":
            why = str(r.get("reason"))
            by_reason[why] += 1
            by_arm.setdefault(str(r.get("arm")), Counter())[why] += 1
    return {"since": since, "decisions": decisions, "skips": sum(by_reason.values()),
            "by_reason": dict(by_reason.most_common()),
            "by_arm_reason": {a: dict(c.most_common(8)) for a, c in sorted(by_arm.items())},
            "placed_per_day": dict(sorted(placed.items())), "stake_usd_per_day": {d: round(v, 2) for d, v in sorted(day_stake.items())}}


def model_read(rows: List[dict], client, now: datetime) -> dict:
    from prediction_market_bot.c5_execution.placement import archive_book as ab, join as pj, fill_model as fm
    fills, market_of, candles_of, note = aor.make_join_inputs(rows, client, now)
    book_of = ab.book_of_for(rows, REPO / "exp_output" / "PRICE_ARCHIVE")
    recs = pj.records(rows, fills, market_of, candles_of, now, book_of=book_of)
    out = {"join_note": note, "join_health": pj.join_health(recs)}
    for ep in (aor.PRE, aor.POST):
        out[ep] = fm.fill_model(pj.model_records([r for r in recs if r["epoch"] == ep]))
    return out


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=str(aor.LOG))
    ap.add_argument("--since", default=SINCE)
    a = ap.parse_args(argv)
    rows = aor.load_rows(Path(a.log))
    now = datetime.now(timezone.utc)
    rep = {"read_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "rows": len(rows), "skips": skip_counts(rows, a.since)}
    client, why = aor.demo_client()
    try:
        rep["fill_model"] = model_read(rows, client, now) if client is not None else {"join_note": why}
    except Exception as e:  # noqa: BLE001 - the skip counts must still print
        rep["fill_model"] = {"join_note": "join failed: " + type(e).__name__ + ": " + str(e)[:200]}
    print(json.dumps(rep, separators=(",", ":"), sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
