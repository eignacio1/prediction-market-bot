"""W121.2: ESPN public box scores (NBA, 2026-27) for dates in [start, end], merged into the cached box file format
(gid -> {date, hdr:["ABBR:home|away:score"], box: summary.boxscore}). Public GETs only. Usage: fetch_box.py base.json start end out.json"""
import datetime as dt, json, sys, time, urllib.request
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parent.parent))
from _fence import safe_out  # noqa: E402
B = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"


def get(u):
    for a in range(4):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "research-client"}), timeout=60))
        except Exception:
            time.sleep(2 + 2 * a)
    return None


def main(base, s, e, out):
    d = json.load(open(base)) if base != "-" else {}
    a, b = dt.date.fromisoformat(s), dt.date.fromisoformat(e)
    while a <= b:
        sb = get(f"{B}/scoreboard?dates={a:%Y%m%d}")
        for ev in (sb or {}).get("events", []):
            if ev["id"] in d or not ev["status"]["type"].get("completed"):
                continue
            sm = get(f"{B}/summary?event={ev['id']}")
            if not sm:
                continue
            hdr = [f"{c['team']['abbreviation']}:{c['homeAway']}:{c.get('score', 0)}" for c in ev["competitions"][0]["competitors"]]
            d[ev["id"]] = {"date": a.isoformat(), "hdr": hdr, "box": sm["boxscore"]}
            time.sleep(0.3)
        print(a, len(d), flush=True)
        a += dt.timedelta(days=1)
    json.dump(d, open(safe_out(out), "w"))


if __name__ == "__main__":
    main(*sys.argv[1:5])
