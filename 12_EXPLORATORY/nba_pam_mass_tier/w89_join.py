"""W89.5 Part A - EXPLORATORY. Join settled KXNBAPTS strikes (public Kalshi market data) to actual points (ESPN box scores).

Reads only public unauthenticated GETs (Kalshi market data, ESPN scoreboard/summary). Does NOT read any shadow ledger (CHARTER rule 2):
the strike, the market's quotes and the result are all public Kalshi data. Writes only under 12_EXPLORATORY via safe_out.

    python3 w89_join.py --out results/w89 [--dates 2026-10-20 ... ] [--cache <dir>]
"""
import argparse
import datetime as dt
import json
import re
import time
import unicodedata
import urllib.request

from _fence import safe_out

KALSHI = "https://api.elections.kalshi.com/trade-api/v2"
ESPN = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
CANDLE_ERRORS = []
ALIAS = {"UTAH": "UTA", "NY": "NYK", "SA": "SAS", "GS": "GSW", "NO": "NOP", "WSH": "WAS"}
MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}


def get(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            return json.load(urllib.request.urlopen(req, timeout=30))
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(1.5 * (i + 1))


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\b(jr|sr|ii|iii|iv)\b\.?", "", s)
    return re.sub(r"[^a-z]", "", s)


def parse_event(et):
    """KXNBAPTS-26OCT26MEMUTA -> (date, away, home); Kalshi codes are 3 letters each."""
    m = re.match(r"KXNBAPTS-(\d\d)([A-Z]{3})(\d\d)([A-Z]{3})([A-Z]{3})$", et)
    if not m:
        return None
    return dt.date(2000 + int(m[1]), MON[m[2]], int(m[3])), m[4], m[5]


def kalshi_markets():
    out, cur = [], None
    while True:
        d = get(f"{KALSHI}/markets?series_ticker=KXNBAPTS&limit=1000" + (f"&cursor={cur}" if cur else ""))
        out += d["markets"]
        cur = d.get("cursor")
        if not cur:
            return out


def espn_games(date):
    d = get(f"{ESPN}/scoreboard?dates={date:%Y%m%d}")
    return [e for e in d["events"] if e["status"]["type"]["name"] == "STATUS_FINAL"]


def espn_box(eid):
    b = get(f"{ESPN}/summary?event={eid}")
    rows = []
    for t in b["boxscore"]["players"]:
        ab = ALIAS.get(t["team"]["abbreviation"], t["team"]["abbreviation"])
        st = t["statistics"][0]
        lab = st["labels"]
        for a in st["athletes"]:
            s = a["stats"]
            pts = int(s[lab.index("PTS")]) if s and s[lab.index("PTS")] not in ("", "--") else None
            mn = s[lab.index("MIN")] if s else None
            rows.append({"team": ab, "name": a["athlete"]["displayName"], "key": norm(a["athlete"]["displayName"]),
                         "pts": pts, "min": mn, "did_not_play": bool(a.get("didNotPlay")) or not s})
    return rows


def candles(ticker, open_t, close_t):
    # tolerant of 5-digit fractional seconds (Kalshi; the box's Python 3.9 rejects them, W80.2)
    f = lambda s: int(dt.datetime.fromisoformat(re.sub(r"Z$", "+00:00", re.sub(r"\.(\d+)", lambda m: "." + m[1][:6].ljust(6, "0"), s))).timestamp())
    # window capped at 6h from open: the anchor is the first usable quote after open, and a wider span 400s (candle-count limit)
    t0 = f(open_t)
    t1 = min(f(close_t), t0 + 6 * 3600)
    try:
        d = get(f"{KALSHI}/series/KXNBAPTS/markets/{ticker}/candlesticks?start_ts={t0}&end_ts={t1}&period_interval=1")
    except Exception as e:  # recorded, not hidden: counted in join_summary candle_errors
        CANDLE_ERRORS.append({"ticker": ticker, "err": str(e)[:80]})
        return []
    out = []
    for c in d.get("candlesticks", []):
        num = lambda x: None if x in (None, "") else float(x)
        out.append([c["end_period_ts"], num(c["yes_bid"]["close_dollars"]), num(c["yes_ask"]["close_dollars"]),
                    num(c["price"].get("close_dollars")), num(c.get("volume_fp"))])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/w89")
    a = ap.parse_args()
    mk = [m for m in kalshi_markets() if m["result"] in ("yes", "no")]
    evs = {}
    for m in mk:
        p = parse_event(m["event_ticker"])
        if p:
            evs.setdefault(m["event_ticker"], p)
    dates = sorted({p[0] for p in evs.values()})
    # ESPN lists a game under its US date; Kalshi event dates are the same calendar date
    games, unmatched_events = {}, []
    sb = {d: espn_games(d) for d in dates if d >= dt.date(2026, 10, 20)}
    for et, (d, away, home) in evs.items():
        hit = None
        for e in sb.get(d, []):
            c = e["competitions"][0]["competitors"]
            ab = {x["homeAway"]: ALIAS.get(x["team"]["abbreviation"], x["team"]["abbreviation"]) for x in c}
            if ab.get("away") == away and ab.get("home") == home:
                hit = e
        if hit:
            games[et] = {"espn_id": hit["id"], "tip_utc": hit["date"], "away": away, "home": home, "date": str(d)}
        else:
            unmatched_events.append(et)
    boxes = {}
    for et, g in games.items():
        if g["espn_id"] not in boxes:
            boxes[g["espn_id"]] = espn_box(g["espn_id"])
            time.sleep(0.15)
    rows, unmatched_players, bad_result = [], [], []
    for m in mk:
        g = games.get(m["event_ticker"])
        if not g:
            continue
        name = m["yes_sub_title"].split(":")[0]
        k = norm(name)
        pl = [r for r in boxes[g["espn_id"]] if r["key"] == k]
        if len(pl) != 1:
            unmatched_players.append({"ticker": m["ticker"], "name": name, "n_found": len(pl), "result": m["result"]})
            continue
        pl = pl[0]
        strike = m["floor_strike"]
        if pl["pts"] is None:  # listed on the roster, no stat line
            outcome_box = None
        else:
            outcome_box = int(pl["pts"] > strike)
        res = int(m["result"] == "yes")
        if outcome_box is not None and outcome_box != res:
            bad_result.append({"ticker": m["ticker"], "pts": pl["pts"], "strike": strike, "result": m["result"]})
        rows.append({"ticker": m["ticker"], "event": m["event_ticker"], "espn_id": g["espn_id"], "date": g["date"], "tip_utc": g["tip_utc"],
                     "team": pl["team"], "player": pl["name"], "key": pl["key"], "strike": strike, "result_yes": res,
                     "pts": pl["pts"], "dnp": pl["did_not_play"], "open_time": m["open_time"], "close_time": m["close_time"]})
    for r in rows:
        r["candles"] = candles(r["ticker"], r["open_time"], r["close_time"])
        time.sleep(0.05)
    json.dump(rows, open(safe_out(f"{a.out}/join_rows.json"), "w"))
    summ = {"settled_binary_markets": len(mk), "events": len(evs), "events_matched_to_espn": len(games),
            "unmatched_events": unmatched_events, "markets_joined": len(rows),
            "unmatched_players": unmatched_players, "result_vs_box_disagreements": bad_result,
            "dnp_rows": sum(r["dnp"] for r in rows), "candle_errors": CANDLE_ERRORS,
            "rows_without_candles": sum(1 for r in rows if not r["candles"])}
    json.dump(summ, open(safe_out(f"{a.out}/join_summary.json"), "w"), indent=1)
    print(json.dumps({k: (v if not isinstance(v, list) else len(v)) for k, v in summ.items()}))


if __name__ == "__main__":
    main()
