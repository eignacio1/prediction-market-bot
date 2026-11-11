"""W109.3 Part B step 1: settled NBA prop markets since 2026-10-20 + hourly candles (public GETs only). Cached JSONL."""
import calendar, json, sys, time, urllib.request, urllib.error, datetime
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
from _fence import safe_out  # noqa: E402
B = "https://api.elections.kalshi.com/trade-api/v2"
SERIES = ["KXNBAPTS", "KXNBAREB", "KXNBAAST", "KXNBA3PT"]
FROM = "2026-10-20T00:00:00Z"


def ts(s):
    return int(calendar.timegm(time.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")))


def get(p):
    for a in range(6):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(B + p, headers={"User-Agent": "research-client"}), timeout=60))
        except urllib.error.HTTPError as e:
            time.sleep(2 + 3 * a)
            if e.code != 429 and e.code < 500:
                return None
        except Exception:
            time.sleep(2)
    return None


def main(out_m, out_c):
    mk = []
    for s in SERIES:
        cur = ""
        while True:
            d = get("/markets?series_ticker=%s&status=settled&limit=1000%s" % (s, "&cursor=" + cur if cur else ""))
            time.sleep(0.5)
            if not d:
                break
            rows = d.get("markets", [])
            mk += [dict(m, s=s) for m in rows if (m.get("close_time") or "") >= FROM and m.get("result") in ("yes", "no")]
            cur = d.get("cursor") or ""
            if not cur or not rows or min(m.get("close_time") or "9" for m in rows) < FROM:
                break
        print(s, len([m for m in mk if m["s"] == s]), flush=True)
    with open(safe_out(out_m), "w") as f:
        for m in mk:
            f.write(json.dumps({k: m.get(k) for k in ("ticker", "s", "event_ticker", "floor_strike", "result", "close_time", "title", "volume_fp", "open_time")}) + "\n")
    mk = [m for m in mk if float(m.get("volume_fp") or 0) > 0]
    print("with volume", len(mk), flush=True)
    with open(safe_out(out_c), "w") as f:
        for i in range(0, len(mk), 100):
            ch = mk[i:i + 100]
            mx = max(ts(m["close_time"]) for m in ch)
            d = get("/markets/candlesticks?market_tickers=%s&start_ts=%d&end_ts=%d&period_interval=60" % (",".join(m["ticker"] for m in ch), mx - 3 * 86400, mx + 3600))
            time.sleep(0.7)
            for x in (d or {}).get("markets", []):
                f.write(json.dumps(x) + "\n")
            f.flush()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
