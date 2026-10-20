"""Per-family quoted depth from the forward capture (W80.1 Part A). Read-only; runs where the store lives (the box).

Usage: python3 12_EXPLORATORY/thin_markets/depth_stats.py [--store exp_output/KALSHI_HISTORY/thin_capture]
Per series and time-to-kickoff bucket: spread (cents), contracts quoted within 1/2/5 cents of mid (both sides summed),
share of snapshots where the cheapest side could fill 5/10/25 contracts within 2 cents, with n snapshots and n tickers.
Rows that repeat a book (`unchanged_of`) carry the last seen book forward, so they count as observations.
post-game = more than 3.5h after kickoff (book is of a finished/settling market).
Rows written before W80.1 have no event_time: kickoff is estimated as close_time - 45h - 3h and flagged `est`.
"""
import argparse, glob, json, os
from collections import defaultdict
from datetime import datetime, timezone

BUCKETS = [("post-game", -10**9, -12600), ("in-game", -12600, 0), ("0-30m", 0, 1800), ("30m-2h", 1800, 7200), ("2-6h", 7200, 21600), (">6h", 21600, 10**9)]
LEAD_EST_S = (45 + 3) * 3600


def _ts(s):
    return datetime.fromisoformat(s[:-1] + "+00:00" if s.endswith("Z") else s).timestamp()


def levels(side):
    """-> [(price_cents, size)] from either schema (cents ints, or dollar strings)."""
    out = []
    for p, q in side or []:
        p, q = float(p), float(q)
        out.append((round(p * 100, 4) if p < 1.0 else p, q))
    return out


def parse(book):
    ob = book.get("orderbook_fp") or book.get("orderbook") or book
    yes = levels(ob.get("yes_dollars") or ob.get("yes"))
    no = levels(ob.get("no_dollars") or ob.get("no"))
    return yes, no


def metrics(yes, no):
    if not yes or not no:
        return None
    by, bn = max(p for p, _ in yes), max(p for p, _ in no)
    ask_y = 100 - bn
    spread, mid = ask_y - by, (by + ask_y) / 2
    d = lambda k: sum(q for p, q in yes if p >= mid - k) + sum(q for p, q in no if p >= (100 - mid) - k)
    side2 = min(sum(q for p, q in yes if p >= mid - 2), sum(q for p, q in no if p >= (100 - mid) - 2))
    return {"spread": spread, "d1": d(1), "d2": d(2), "d5": d(5), "side2": side2}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="exp_output/KALSHI_HISTORY/thin_capture")
    a = ap.parse_args(argv)
    last, acc, tick, est = {}, defaultdict(list), defaultdict(set), defaultdict(int)
    rows = []
    for f in sorted(glob.glob(os.path.join(a.store, "books_*.jsonl"))):
        for line in open(f):
            try:
                rows.append(json.loads(line))
            except ValueError:
                pass
    rows.sort(key=lambda r: r.get("retrieved_utc", ""))
    for r in rows:
        t = r["ticker"]
        if "book" in r:
            last[t] = parse(r["book"])
        elif t not in last:
            continue
        m = metrics(*last[t])
        if m is None:
            continue
        if "secs_to_kickoff_est" in r:
            s, e = r["secs_to_kickoff_est"], False
        else:
            s, e = _ts(r["close_time"]) - LEAD_EST_S - _ts(r["retrieved_utc"]), True
        b = next(n for n, lo, hi in BUCKETS if lo <= s < hi)
        acc[(r["series"], b)].append(m)
        tick[(r["series"], b)].add(t)
        est[(r["series"], b)] += e
    print("| series | bucket | n snaps | n tickers | est-time share | median spread c | median d1 | median d2 | median d5 | P(side>=5 @2c) | P(>=10) | P(>=25) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    med = lambda xs: sorted(xs)[len(xs) // 2]
    for (s, b), ms in sorted(acc.items(), key=lambda kv: (kv[0][0], [n for n, *_ in BUCKETS].index(kv[0][1]))):
        n = len(ms)
        fr = lambda k: sum(m["side2"] >= k for m in ms) / n
        print(f"| {s} | {b} | {n} | {len(tick[(s, b)])} | {est[(s, b)] / n:.0%} | {med([m['spread'] for m in ms]):.0f} | "
              f"{med([m['d1'] for m in ms]):.0f} | {med([m['d2'] for m in ms]):.0f} | {med([m['d5'] for m in ms]):.0f} | "
              f"{fr(5):.0%} | {fr(10):.0%} | {fr(25):.0%} |")


if __name__ == "__main__":
    main()
