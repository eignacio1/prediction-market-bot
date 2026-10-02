"""EXP-034 D1(b): read-only live yes_bid/yes_ask sampler (public endpoint, no auth, no orders)."""
import json, sys, time, datetime as dt, urllib.request

B = "https://api.elections.kalshi.com/trade-api/v2"
SERIES = ["KXHIGHNY", "KXHIGHCHI", "KXHIGHMIA", "KXCPI", "KXPAYROLLS", "KXGDP"]
ROUNDS, GAP_S = 7, 21 * 60


def get(path):
    with urllib.request.urlopen(urllib.request.Request(B + path, headers={"User-Agent": "exp034-d1b"}), timeout=30) as r:
        return json.load(r)


def main(out):
    tickers = []
    for s in SERIES:
        tickers += [m["ticker"] for m in get(f"/markets?series_ticker={s}&status=open&limit=100")["markets"][:2]]
        time.sleep(1)
    for rnd in range(ROUNDS):
        for t in tickers:
            m = get(f"/markets/{t}")["market"]
            row = {"round": rnd, "ticker": t, "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
                   "yes_bid": m.get("yes_bid_dollars"), "yes_ask": m.get("yes_ask_dollars"), "status": m.get("status")}
            with open(out, "a") as f:
                f.write(json.dumps(row) + "\n")
            time.sleep(1)
        if rnd < ROUNDS - 1:
            time.sleep(GAP_S)


if __name__ == "__main__":
    main(sys.argv[1])
