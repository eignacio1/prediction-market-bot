"""EXP-034 D1(b)-2: read-only live yes_bid/yes_ask sampler. Same ticker rule, rounds and reads as the frozen D1(b)
sampler (D1B2_AMENDMENT_PREREG.md). Public endpoint, no auth, no orders. One request in flight, spaced apart."""
import json
import sys
import time
import datetime as dt
import urllib.request
import urllib.error

B = "https://api.elections.kalshi.com/trade-api/v2"
SERIES = ["KXHIGHNY", "KXHIGHCHI", "KXHIGHMIA", "KXCPI", "KXPAYROLLS", "KXGDP"]
ROUNDS, GAP_S = 7, 21 * 60
_spacing = [1.3]


def get(path):
    for _ in range(5):
        time.sleep(_spacing[0])
        try:
            req = urllib.request.Request(B + path, headers={"User-Agent": "exp034-d1b2"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            _spacing[0] *= 2
    raise RuntimeError("429 persisted")


def main(out):
    tickers = []
    for s in SERIES:
        tickers += [m["ticker"] for m in get(f"/markets?series_ticker={s}&status=open&limit=100")["markets"][:2]]
    with open(out + ".tickers.json", "w") as f:
        json.dump(tickers, f)
    for rnd in range(ROUNDS):
        for t in tickers:
            m = get(f"/markets/{t}")["market"]
            row = {"round": rnd, "ticker": t, "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
                   "yes_bid": m.get("yes_bid_dollars"), "yes_ask": m.get("yes_ask_dollars"),
                   "status": m.get("status"), "open_time": m.get("open_time")}
            with open(out, "a") as f:
                f.write(json.dumps(row) + "\n")
        if rnd < ROUNDS - 1:
            time.sleep(GAP_S)


if __name__ == "__main__":
    main(sys.argv[1])
