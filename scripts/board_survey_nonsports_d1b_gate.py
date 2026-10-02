"""EXP-034 D1(b) gate runner. Frozen rules: D1B_TOLERANCE_PREREG.md (38b8490). Read-only public GETs, ~1 req/s."""
import json, os, sys, time, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board_survey_nonsports_candles as bc

B = "https://api.elections.kalshi.com/trade-api/v2"
D = "exp_output/EXP-034-NONSPORTS-CONTROL"


def get(path):
    for wait in (0, 2, 4, 8):
        time.sleep(wait)
        try:
            with urllib.request.urlopen(urllib.request.Request(B + path, headers={"User-Agent": "exp034-d1b"}), timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
    raise RuntimeError("429 persisted")


def main():
    rows = [json.loads(l) for l in open(f"{D}/d1b_live_quotes.jsonl")]
    last = max(bc.to_epoch(r["ts"]) for r in rows)
    assert time.time() >= last + 600, "settle window (last round + 10 min) not elapsed"
    first = min(bc.to_epoch(r["ts"]) for r in rows)
    raw, results = {}, []
    for t in sorted({r["ticker"] for r in rows}):
        ser = t.split("-")[0]
        d = get(f"/series/{ser}/markets/{t}/candlesticks?start_ts={int(first)-3600}&end_ts={int(last)+900}&period_interval=1")
        raw[t] = d
        time.sleep(1)
    json.dump(raw, open(f"{D}/d1b_candles_raw.json", "w"))
    for r in rows:
        cs = [bc.parse_candle(c) for c in raw[r["ticker"]].get("candlesticks", [])]
        results.append(bc.compare(r, cs))
    g = bc.gate(results)
    json.dump({"gate": g, "pairs": results}, open(f"{D}/d1b_gate_result.json", "w"), indent=1)
    print(json.dumps(g))
    for x in results:
        print(x["round"], x["ticker"], x["kind"], x["bid_read"], x["bid_miss"], x["ask_read"], x["ask_miss"], "PASS" if x["pass"] else "FAIL")


if __name__ == "__main__":
    main()
