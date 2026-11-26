#!/usr/bin/env python3
"""READ-ONLY (W130.2, EXP-NBAPROPS-002): summarise logs/props_arm_orders/orders.jsonl.

Prints: every skip reason as a counted number; orders / would-orders / rejects; and, from the per-order fills + settlement join
(placement/join.py, same as arm_orders_read.py), E1 fill rate, E2 per filled contract after exact fees, E3 win rate on fills vs the
counterfactual win rate of non-fills, pooled and per leaf. Pre-epoch YES-only and post-epoch all-sides are reported separately
(GG-1771 epoch 2026-11-06T01:03:42Z). Markets that finalize with no yes/no result (the player sat: void / refund) leave E2 and E3
and are counted under join_health.void. Judged n and the verdict rule are in PREREG s6/s7: nothing here is a verdict below n*.
Writes nothing.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import arm_orders_read as aor  # noqa: E402

LOG = REPO / "logs" / "props_arm_orders" / "orders.jsonl"


def skip_counts(rows: list) -> dict:
    c = Counter(r.get("reason") for r in rows if r.get("event") == "arm_skip")
    return {"total": sum(c.values()), "by_reason": dict(c.most_common())}


def summarise(rows: list, recs: list) -> dict:
    from prediction_market_bot.c5_execution.placement import join as pj
    ev = Counter(r.get("event") for r in rows)
    rej = sum(1 for r in rows if r.get("event") == "arm_order" and not r.get("ok"))
    out = {"events": dict(ev), "orders_rejected": rej, "skips": skip_counts(rows),
           "join_health": pj.join_health(recs), "pooled": pj.per_arm(recs)}
    per_leaf = []
    for r in recs:
        q = dict(r)
        q["arm"] = "%s|%s" % (r.get("leaf") or r.get("leaf_id") or "?", r["arm"])
        per_leaf.append(q)
    out["per_leaf"] = pj.per_arm(per_leaf)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=str(LOG))
    ap.add_argument("--no-fills", action="store_true")
    a = ap.parse_args(argv)
    rows = aor.load_rows(Path(a.log))
    now = datetime.now(timezone.utc)
    rep = {"source": a.log, "read_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "rows": len(rows), "prereg": "EXP-NBAPROPS-002"}
    if a.no_fills:
        rep.update(events=dict(Counter(r.get("event") for r in rows)), skips=skip_counts(rows), note="fills skipped: --no-fills")
    else:
        client, why = aor.demo_client()
        if client is None:
            rep.update(events=dict(Counter(r.get("event") for r in rows)), skips=skip_counts(rows), note=why)
        else:
            from prediction_market_bot.c5_execution.placement import join as pj
            fills, market_of, candles_of, note = aor.make_join_inputs(rows, client, now)
            recs = pj.records(rows, fills, market_of, candles_of, now)
            rep.update(summarise(rows, recs), join_note=note)
    print(json.dumps(rep, indent=1, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
