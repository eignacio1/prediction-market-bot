"""W108.4 B-065 fetcher: Kalshi settled daily-high markets + price near a fixed snapshot + Open-Meteo previous-day-1 forecast.
Public unauthenticated GETs only. Read-only. Resumable (cache json). Python 3.9.
Snapshot = 23:00Z on D-1 (day before the target local date D). Forecast = Open-Meteo previous_day1 hourly (the value issued
24h before each hour); only hours valid by D 23:00Z enter the daily max, so every forecast value was issued by the snapshot."""
import json, sys, os, time, urllib.request, urllib.error, datetime as dt, os
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _fence import safe_out

B = "https://api.elections.kalshi.com/trade-api/v2"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CITIES = {  # series: (lat, lon, tz)  station coordinates of the CLI airport / park
    "KXHIGHNY": (40.779, -73.969, "America/New_York"),
    "KXHIGHCHI": (41.786, -87.752, "America/Chicago"),
    "KXHIGHMIA": (25.791, -80.316, "America/New_York"),
    "KXHIGHAUS": (30.183, -97.680, "America/Chicago"),
    "KXHIGHDEN": (39.847, -104.656, "America/Denver"),
    "KXHIGHLAX": (33.938, -118.389, "America/Los_Angeles"),
}
START = "2025-11-01"
HIST_CUTOFF = "2026-09-11T00:00:00Z"


def get(url, tries=4):
    for i in range(tries):
        try:
            return json.load(urllib.request.urlopen(url, timeout=60))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {"err": 404}
            time.sleep(1 + i)
        except Exception:
            time.sleep(1 + i)
    return {"err": "fail"}


def events(series):
    out, cur = [], None
    while True:
        d = get(f"{B}/events?series_ticker={series}&status=settled&limit=200" + (f"&cursor={cur}" if cur else ""))
        out += d.get("events", [])
        cur = d.get("cursor")
        if not cur:
            return out


def markets(ev):
    d = get(f"{B}/markets?event_ticker={ev}&limit=50")
    if d.get("markets"):
        return d["markets"]
    return get(f"{B}/historical/markets?event_ticker={ev}&limit=50").get("markets", [])


def snap_ts(date_str):
    d = dt.datetime.strptime(date_str, "%Y-%m-%d") - dt.timedelta(days=1)
    return int(dt.datetime(d.year, d.month, d.day, 23, tzinfo=dt.timezone.utc).timestamp())


def trades_before(ticker, ts):
    """All trades in [ts-2h, ts] (up to 1000), live endpoint then historical."""
    for ep in ("markets/trades", "historical/trades"):
        d = get(f"{B}/{ep}?ticker={ticker}&min_ts={ts-7200}&max_ts={ts}&limit=1000")
        if d.get("trades"):
            return d["trades"]
    # fall back to latest trade at all before ts (older than 2h)
    for ep in ("markets/trades", "historical/trades"):
        d = get(f"{B}/{ep}?ticker={ticker}&max_ts={ts}&limit=1")
        if d.get("trades"):
            return d["trades"]
    return []


def forecast_max(lat, lon, tz, date_str):
    d0 = dt.datetime.strptime(date_str, "%Y-%m-%d")
    s, e = (d0 - dt.timedelta(days=1)).strftime("%Y-%m-%d"), (d0 + dt.timedelta(days=1)).strftime("%Y-%m-%d")
    u = (f"https://previous-runs-api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&start_date={s}"
         f"&end_date={e}&hourly=temperature_2m_previous_day1&temperature_unit=fahrenheit&timezone=UTC&models=gfs_seamless")
    d = get(u)
    h = d.get("hourly")
    if not h:
        return None
    from zoneinfo import ZoneInfo
    z = ZoneInfo(tz)
    cut = dt.datetime(d0.year, d0.month, d0.day, 23, tzinfo=dt.timezone.utc)
    vals = []
    for t, v in zip(h["time"], h["temperature_2m_previous_day1"]):
        if v is None:
            continue
        u_ = dt.datetime.strptime(t + "+0000", "%Y-%m-%dT%H:%M%z")
        if u_.astimezone(z).strftime("%Y-%m-%d") == date_str and u_ <= cut:
            vals.append(v)
    return max(vals) if len(vals) >= 12 else None


def day(series, ev):
    lat, lon, tz = CITIES[series]
    ds = ev["event_ticker"].split("-")[-1]
    date_str = dt.datetime.strptime(ds, "%y%b%d").strftime("%Y-%m-%d")
    ms = markets(ev["event_ticker"])
    ts = snap_ts(date_str)
    rows = []
    for m in ms:
        if m.get("result") not in ("yes", "no"):
            continue
        tr = trades_before(m["ticker"], ts)
        rows.append({"ticker": m["ticker"], "floor": m.get("floor_strike"), "cap": m.get("cap_strike"), "result": m["result"],
                     "exp_value": m.get("expiration_value"), "vol": m.get("volume_fp"),
                     "trades": [(t["created_time"], t["yes_price_dollars"], t["taker_side"], t["count_fp"]) for t in tr[:200]]})
    return {"series": series, "date": date_str, "fc_max": forecast_max(lat, lon, tz, date_str), "snap_ts": ts, "markets": rows}


def main(series_list):
    for s in series_list:
        path = os.path.join(OUT, f"{s}.json")
        done = {}
        if os.path.exists(path):
            done = {r["date"]: r for r in json.load(open(path))}
        evs = [e for e in events(s) if e["event_ticker"].startswith("KX")]
        todo = []
        for e in evs:
            ds = e["event_ticker"].split("-")[-1]
            try:
                d = dt.datetime.strptime(ds, "%y%b%d").strftime("%Y-%m-%d")
            except ValueError:
                continue
            if START <= d <= "2026-11-06" and d not in done:
                todo.append(e)
        print(s, "events", len(evs), "todo", len(todo), flush=True)
        with ThreadPoolExecutor(8) as ex:
            for r in ex.map(lambda e: day(s, e), todo):
                done[r["date"]] = r
        json.dump(sorted(done.values(), key=lambda r: r["date"]), open(safe_out(path), "w"))
        print(s, "saved", len(done), flush=True)


if __name__ == "__main__":
    main(sys.argv[1:] or list(CITIES))
