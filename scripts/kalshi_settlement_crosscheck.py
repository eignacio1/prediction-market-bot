#!/usr/bin/env python3
"""W59.2 Part D (GG-487): READ-ONLY cross-check of settled shadow rows against Kalshi's own market settlement.

For every distinct market_ticker in the given settled dir (NFL/MLB `y`), GET the public Kalshi market and compare
the assigned outcome with Kalshi's `result`. Never writes to any ledger. Prints agreements / disagreements / voids / unresolved.
"""
import argparse, glob, json, os, sys, time, urllib.request, urllib.error
from collections import Counter
BASE = "https://api.elections.kalshi.com/trade-api/v2/markets/"


def tickers(d):
    out = {}
    for f in sorted(glob.glob(os.path.join(d, "*.jsonl"))):
        sp = os.path.basename(f).split("_")[0]
        for l in open(f):
            try: r = json.loads(l)
            except ValueError: continue
            y = r.get("y", r.get("outcome"))
            if y is None or sp not in ("NFL", "MLB"): continue
            out.setdefault(r["market_ticker"], (sp, os.path.basename(f), float(y)))
    return out


def fetch(t):
    for i in range(4):
        try:
            with urllib.request.urlopen(BASE + t, timeout=20) as r:
                return json.load(r).get("market", {})
        except urllib.error.HTTPError as e:
            if e.code == 404: return {"_missing": True}
            time.sleep(2 * (i + 1))
        except Exception:
            time.sleep(2 * (i + 1))
    return {"_error": True}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("settled_dir"); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ts = tickers(a.settled_dir); rows = []
    for i, (t, (sp, f, y)) in enumerate(ts.items()):
        m = fetch(t); res = m.get("result"); st = m.get("status")
        if m.get("_missing"): cls = "MISSING"
        elif m.get("_error"): cls = "FETCH_ERROR"
        elif res in ("yes", "no"): cls = "AGREE" if (res == "yes") == (y == 1.0) and y in (0.0, 1.0) else "DISAGREE"
        elif res in ("", None): cls = "UNRESOLVED_AT_KALSHI"
        else: cls = "VOID_OR_OTHER"
        rows.append(dict(sport=sp, file=f, ticker=t, assigned_y=y, kalshi_result=res, kalshi_status=st, cls=cls))
        time.sleep(0.12)
    json.dump(rows, open(a.out, "w"), indent=1)
    print(Counter((r["sport"], r["cls"]) for r in rows))
    for r in rows:
        if r["cls"] not in ("AGREE",): print(r)


if __name__ == "__main__":
    sys.exit(main())
