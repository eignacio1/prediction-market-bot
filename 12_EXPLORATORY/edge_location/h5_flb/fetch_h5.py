"""W125.3: read-only public GETs for H-EDGE-5 (no auth, $0). Fetches 2025-26 milestone starts, then the last
hours of hourly candles before each in-population market's start. Writes only under h5_flb/data/ (untracked).
usage: fetch_h5.py starts | candles <market_dir_nba_nfl>"""
import json, os, sys, time, urllib.error, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from _fence import safe_out  # noqa: E402
B = "https://api.elections.kalshi.com/trade-api/v2"
TYPES = {"basketball_game", "football_game", "hockey_game", "hockey_match", "hockey_tournament"}
DATA = os.path.join(HERE, "data")


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


def starts():
    out, cur = {}, ""
    while True:
        d = get("/milestones?minimum_start_date=2025-09-01T00:00:00Z&maximum_start_date=2026-05-01T00:00:00Z&limit=500"
                + (f"&cursor={cur}" if cur else ""))
        time.sleep(0.4)
        if not d:
            break
        for m in d.get("milestones", []):
            if m.get("type") in TYPES:
                for e in set((m.get("related_event_tickers") or []) + (m.get("primary_event_tickers") or [])):
                    out[e] = m["start_date"]
        cur = d.get("cursor") or ""
        print(len(out), flush=True)
        if not cur or not d.get("milestones"):
            break
    json.dump(out, open(safe_out(os.path.join(DATA, "starts_2025_26.json")), "w"))


def candles(series, market_file, nba_nfl_start_json):
    from datetime import datetime
    st = json.load(open(nba_nfl_start_json))
    rows = [json.loads(l) for l in open(market_file)]
    outp = safe_out(os.path.join(DATA, f"candles_{series}.jsonl"))
    done = set()
    if os.path.exists(outp):
        done = {json.loads(l)["ticker"] for l in open(outp)}
    n = 0
    with open(outp, "a") as f:
        for r in rows:
            e, t = r["event_ticker"], r["ticker"]
            if e not in st or t in done:
                continue
            s = int(datetime.fromisoformat(st[e].replace("Z", "+00:00")).timestamp())
            d = get(f"/historical/markets/{t}/candlesticks?start_ts={s - 8 * 3600}&end_ts={s + 3600}&period_interval=60")
            time.sleep(0.25)
            f.write(json.dumps({"ticker": t, "event": e, "start": st[e], "candlesticks": (d or {}).get("candlesticks", []), "ok": d is not None}) + "\n")
            n += 1
            if n % 200 == 0:
                f.flush(); print(series, n, flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "starts":
        starts()
    else:
        candles(sys.argv[2], sys.argv[3], sys.argv[4])
