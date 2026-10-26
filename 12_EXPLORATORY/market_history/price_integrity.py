"""W87.3 Part B: price-integrity shares for one shadow cell's rows. Reads price fields ONLY (bid, ask, mid, strike);
never reads p_yes, brier_* or outcome, and computes no score. Read-only on the ledger.
Applies when a cell's rows carry a quote snapshot; a check whose field is absent is reported NOT MEASURABLE, not 0."""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict

WIDE = 0.10            # full bid-ask width above this (10 points on a 0-1 contract) = wide
FAR_STRIKE = 1.5       # strike more than this many goals from the event's own line (strike nearest mid 0.5)


def strike_of(ticker: str):
    m = re.search(r"-(\d+)$", ticker or "")
    return int(m.group(1)) if m else None


def shares(rows: list[dict]) -> dict:
    n = len(rows)
    wide = one_sided = bad = far = 0
    by_event = defaultdict(list)
    for r in rows:
        bid, ask = r.get("yes_bid"), r.get("yes_ask")
        if bid is None or ask is None:
            bad += 1
            continue
        if bid <= 0.0 or ask >= 1.0:
            one_sided += 1
        if ask - bid > WIDE:
            wide += 1
        by_event[r.get("event_ticker")].append(r)
    for ev, rs in by_event.items():
        sk = [(abs(r["mid"] - 0.5), strike_of(r["market_ticker"])) for r in rs if r.get("mid") is not None]
        sk = [s for s in sk if s[1] is not None]
        if not sk:
            continue
        line = min(sk)[1]
        far += sum(1 for r in rs if (s := strike_of(r["market_ticker"])) is not None and abs(s - line) > FAR_STRIKE)
    has_age = sum(1 for r in rows if any(k in r for k in ("last_trade_ts", "quote_ts", "last_price_ts")))
    d = lambda k: {"n": k, "share": round(k / n, 4) if n else None}
    return {"rows": n, "events": len(by_event), "missing_bid_or_ask": d(bad), "wide_gt_10pts": d(wide),
            "one_sided_book": d(one_sided), "strike_far_from_event_line": d(far),
            "stale_quote_age": "NOT MEASURABLE from rows" if not has_age else d(0)}


if __name__ == "__main__":
    rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
    print(json.dumps(shares(rows), indent=1))
