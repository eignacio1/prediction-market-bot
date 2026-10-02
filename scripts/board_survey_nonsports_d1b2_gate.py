"""EXP-034 D1(b)-2 gate runner. Rules: D1B_TOLERANCE_PREREG.md (frozen) + D1B2_AMENDMENT_PREREG.md (lookback = market
open). Comparator reused unmodified from board_survey_nonsports_candles. Read-only public GETs, <= 0.77 req/s."""
import calendar
import datetime as dt
import json
import os
import sys
import time
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board_survey_nonsports_candles as bc  # noqa: E402

B = "https://api.elections.kalshi.com/trade-api/v2"
D = "exp_output/EXP-034-NONSPORTS-CONTROL"
CHUNK_S = 2 * 86400
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


def pull_back_to_open(fetch, first_read, last_read, open_ts):
    """Pull candle dicts backward in CHUNK_S windows from last_read+900. Stop once a candle with end_period_ts <
    first_read is held (no earlier pull can change any match) or the window start reaches open_ts."""
    end, out = int(last_read) + 900, []
    floor_ts = int(open_ts) if open_ts else int(first_read) - 3600
    while True:
        start = max(end - CHUNK_S, floor_ts)
        out += fetch(start, end)
        if any(int(c["end_period_ts"]) < first_read for c in out) or start <= floor_ts:
            return out
        end = start


def main():
    rows = [json.loads(line) for line in open(f"{D}/d1b2_live_quotes.jsonl")]
    last = max(bc.to_epoch(r["ts"]) for r in rows)
    assert time.time() >= last + 600, "settle window (last round + 10 min) not elapsed"
    raw, results, calls = {}, [], []
    for t in sorted({r["ticker"] for r in rows}):
        tr = [r for r in rows if r["ticker"] == t]
        first = min(bc.to_epoch(r["ts"]) for r in tr)
        ot = tr[0].get("open_time")
        open_ts = calendar.timegm(dt.datetime.fromisoformat(ot.replace("Z", "+00:00")).utctimetuple()) if ot else None
        ser = t.split("-")[0]

        def fetch(s, e, t=t, ser=ser):
            calls.append((t, s, e))
            path = f"/series/{ser}/markets/{t}/candlesticks?start_ts={s}&end_ts={e}&period_interval=1"
            return get(path).get("candlesticks", [])
        raw[t] = {"open_ts": open_ts, "candlesticks": pull_back_to_open(fetch, first, last, open_ts)}
    with open(f"{D}/d1b2_candles_raw.json", "w") as f:
        json.dump(raw, f)
    for r in rows:
        cs = [bc.parse_candle(c) for c in raw[r["ticker"]]["candlesticks"]]
        results.append(bc.compare(r, cs))
    g = bc.gate(results)
    with open(f"{D}/d1b2_gate_result.json", "w") as f:
        json.dump({"gate": g, "pairs": results, "candle_requests": len(calls)}, f, indent=1)
    print(json.dumps(g), "requests", len(calls))


if __name__ == "__main__":
    main()
