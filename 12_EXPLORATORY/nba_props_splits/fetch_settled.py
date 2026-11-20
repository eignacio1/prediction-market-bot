"""W121.2: settled NBA prop markets since 2026-11-10 (public GET). Writes ticker, series, floor_strike, result, close_time, title."""
import json, sys, time, urllib.request, urllib.error
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parent.parent))
from _fence import safe_out  # noqa: E402
B = "https://api.elections.kalshi.com/trade-api/v2"


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


out = []
for s in ["KXNBAPTS", "KXNBAREB", "KXNBAAST", "KXNBA3PT"]:
    cur = ""
    while True:
        d = get(f"/markets?series_ticker={s}&status=settled&limit=1000" + (f"&cursor={cur}" if cur else ""))
        time.sleep(0.5)
        if not d:
            break
        rows = d.get("markets", [])
        out += [{k: m.get(k) for k in ("ticker", "event_ticker", "floor_strike", "result", "close_time", "title")} | {"s": s}
                for m in rows if (m.get("close_time") or "") >= "2026-11-10" and m.get("result") in ("yes", "no")]
        cur = d.get("cursor") or ""
        if not cur or not rows or min(m.get("close_time") or "9" for m in rows) < "2026-11-10":
            break
    print(s, sum(1 for m in out if m["s"] == s), flush=True)
json.dump(out, open(safe_out(sys.argv[1]), "w"))
