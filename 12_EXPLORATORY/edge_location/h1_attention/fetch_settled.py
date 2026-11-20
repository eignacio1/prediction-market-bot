"""W123.1 Part A: settled results for every series in PRICE_ARCHIVE since 2026-07-31 (public unauthenticated GET /markets).
usage: fetch_settled.py <out_dir inside 12_EXPLORATORY> <archive_dir> ; writes <out_dir>/<SERIES>.json = [{ticker,event_ticker,result,close_time,floor_strike,strike_type}]"""
import json, os, sys, time, urllib.error, urllib.request
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src"))
from _fence import safe_out  # noqa: E402
from prediction_market_bot import io_jsonl  # noqa: E402
B = "https://api.elections.kalshi.com/trade-api/v2"
MIN_TS = 1785456000  # 2026-07-31T00:00:00Z


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


def main(out, archive):
    seen = set()
    for f in io_jsonl.glob_files(f"{archive}/prices_*.jsonl"):
        for l in io_jsonl.open_jsonl(f):
            seen.add(json.loads(l)["series_ticker"]) if '"series_ticker"' in l else None
    for s in sorted(seen):
        dst = f"{out}/{s}.json"
        if os.path.exists(dst):
            continue
        rows, cur = [], ""
        while True:
            d = get(f"/markets?series_ticker={s}&status=settled&min_close_ts={MIN_TS}&limit=1000" + (f"&cursor={cur}" if cur else ""))
            time.sleep(0.4)
            if not d:
                break
            ms = d.get("markets", [])
            rows += [{k: m.get(k) for k in ("ticker", "event_ticker", "result", "close_time", "floor_strike", "strike_type", "title")} for m in ms]
            cur = d.get("cursor") or ""
            if not cur or not ms:
                break
        json.dump(rows, open(safe_out(dst), "w"))
        print(s, len(rows), flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
