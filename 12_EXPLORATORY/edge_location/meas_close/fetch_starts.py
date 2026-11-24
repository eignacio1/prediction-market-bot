"""W124.2: game start times from Kalshi public milestones (unauthenticated GET /milestones).
usage: fetch_starts.py <out_json inside 12_EXPLORATORY>  -> {event_ticker: start_date_iso} for basketball/football/hockey/baseball games."""
import json, os, sys, time, urllib.error, urllib.request
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from _fence import safe_out  # noqa: E402
B = "https://api.elections.kalshi.com/trade-api/v2"
TYPES = {"basketball_game", "football_game", "hockey_game", "hockey_match", "baseball_game"}


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


def main(out):
    starts, cur, pages = {}, "", 0
    while True:
        d = get("/milestones?minimum_start_date=2026-07-31T00:00:00Z&maximum_start_date=2026-12-10T00:00:00Z&limit=500"
                + (f"&cursor={cur}" if cur else ""))
        time.sleep(0.4)
        if not d:
            break
        for m in d.get("milestones", []):
            if m.get("type") in TYPES:
                for e in set((m.get("related_event_tickers") or []) + (m.get("primary_event_tickers") or [])):
                    starts[e] = m["start_date"]
        pages += 1
        cur = d.get("cursor") or ""
        print(pages, len(starts), flush=True)
        if not cur or not d.get("milestones"):
            break
    json.dump(starts, open(safe_out(out), "w"))


if __name__ == "__main__":
    main(sys.argv[1])
