"""W89.7 Part A: settled Kalshi history for NBA / NHL / NFL with TRUE scheduled start times.

Public unauthenticated GETs only (Kalshi market data; ESPN public scoreboard for the schedule). Raw Kalshi pages and candles are kept
verbatim by board_survey_sports_store.Store under --out/<sport>/raw. Phases (each idempotent, resumable):

  list      settled markets per series -> markets/<SERIES>.jsonl (slim rows)
  schedule  ESPN scoreboard over the window -> schedule.jsonl (start_utc per game)
  join      Kalshi event -> ESPN game by ET date + team pair -> events.jsonl (start_utc, matched or not)
  candles   hourly candles [start-30h, start] for a deterministic, outcome-independent market sample -> candles/<SERIES>.jsonl
  manifest  coverage per family x season -> manifests/w89_7/<sport>/MANIFEST.json (the part that is tracked in git)

Why a schedule: Kalshi's `occurrence_datetime` is NOT the start (measured in this block: it runs ~3-4 h after tip/kickoff/puck
for the three sports), and NFL event tickers carry the date only (GG-1252).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import board_survey_sports_store as bs  # noqa: E402
sys.path.insert(0, str(ROOT / "12_EXPLORATORY"))
from _fence import safe_out  # noqa: E402

# The tracked manifests live inside the fence (CHARTER rule 3); the bulk Kalshi pages stay in the untracked exp_output cache.
MANIFEST_DIR = ROOT / "12_EXPLORATORY" / "market_history" / "manifests" / "w89_7"

try:
    from zoneinfo import ZoneInfo
    ET = ZoneInfo("America/New_York")
except Exception:  # py3.8 safety; the box is 3.9 so this should not trigger
    ET = timezone(timedelta(hours=-5))

TEAM_FAMILIES = ("GAME", "SPREAD", "TOTAL", "TEAMTOTAL")
SPORTS = {
    "nba": {"espn": "basketball/nba", "team": ["KXNBAGAME", "KXNBASPREAD", "KXNBATOTAL", "KXNBATEAMTOTAL"],
            "prop": ["KXNBAPTS", "KXNBAREB", "KXNBAAST", "KXNBA3PT"]},
    "nhl": {"espn": "hockey/nhl", "team": ["KXNHLGAME", "KXNHLSPREAD", "KXNHLTOTAL", "KXNHLTEAMTOTAL"],
            "prop": ["KXNHLGOAL", "KXNHLPTS", "KXNHLAST", "KXNHLSAVES"]},
    "nfl": {"espn": "football/nfl", "team": ["KXNFLGAME", "KXNFLSPREAD", "KXNFLTOTAL", "KXNFLTEAMTOTAL"],
            "prop": ["KXNFLANYTD", "KXNFLPASSYDS", "KXNFLRECYDS", "KXNFLREC"]},
}
# Kalshi ticker code <-> ESPN abbreviation differences; the join tries every alias of each side.
ALIAS = {
    "GS": ["GSW"], "NY": ["NYK"], "NO": ["NOP"], "SA": ["SAS"], "UTAH": ["UTA"], "WSH": ["WAS"],
    "NJ": ["NJD"], "SJ": ["SJS"], "TB": ["TBL"], "LA": ["LAK"], "LAR": ["LA", "LAR"], "VGK": ["VGK", "LVG"], "MTL": ["MTL", "MON"],
    "CBJ": ["CBJ", "CLB"], "NSH": ["NSH", "NAS"], "WPG": ["WPG", "WIN"], "UTA": ["UTA", "UTAH"], "JAX": ["JAC", "JAX"],
    "LV": ["LVR", "LV"], "NE": ["NEP", "NE"], "NYG": ["NYG"], "NYJ": ["NYJ"], "KC": ["KCC", "KC"], "GB": ["GBP", "GB"],
    "TB_": ["TBB"], "SF": ["SFO", "SF"], "LAC": ["LAC"], "WAS": ["WAS", "WSH"],
}
SAMPLE_STRIKES = 4        # team-total-type families: evenly spaced strikes per event, by strike value (outcome-independent)
SAMPLE_PROPS = 6          # prop families: top-N markets per event by volume
LOOKBACK_H = 30           # hourly candles from start-30h to start: covers the T>24h, T6-24h, T2-6h and T0-2h tiers


# ---------------------------------------------------------------------------------------------- pure helpers
def parse_event(event_ticker: str):
    """'KXNBAGAME-26OCT26GSWDEN' -> (date(2026,10,26), 'GSWDEN'); None when it does not parse."""
    m = re.search(r"-(\d{2})([A-Z]{3})(\d{2})([A-Z]{4,8})(?:$|-)", event_ticker)
    if not m:
        return None
    try:
        d = datetime.strptime(f"{m.group(1)}{m.group(2)}{m.group(3)}", "%y%b%d").date()
    except ValueError:
        return None
    return d, m.group(4)


def code_options(abbr: str) -> list[str]:
    return list(dict.fromkeys([abbr] + ALIAS.get(abbr, [])))


def team_pair_matches(code: str, away: str, home: str) -> bool:
    """Ticker team code (away+home concatenated) equals some alias combination of the ESPN abbreviations."""
    for a in code_options(away):
        for h in code_options(home):
            if code == a + h:
                return True
    return False


def et_date(start_utc: str):
    return datetime.strptime(start_utc + "+0000", "%Y-%m-%dT%H:%MZ%z").astimezone(ET).date()


def match_event(code: str, tdate, games: list[dict]):
    """Games within +-1 ET day of the ticker's date whose team pair matches; exactly one -> that game, else None."""
    hits = [g for g in games if abs((et_date(g["start_utc"]) - tdate).days) <= 1 and team_pair_matches(code, g["away"], g["home"])]
    if len(hits) == 1:
        return hits[0], "matched"
    if not hits:
        return None, "no_team_pair"
    exact = [g for g in hits if et_date(g["start_utc"]) == tdate]       # doubleheader / repeat meeting: prefer same ET day
    return (exact[0], "matched_same_day") if len(exact) == 1 else (None, "ambiguous")


def pick_sample(markets: list[dict], family_kind: str) -> list[dict]:
    """Deterministic and outcome-independent: never looks at `result` or prices."""
    ms = sorted(markets, key=lambda m: m["ticker"])
    if family_kind == "game":
        return ms[:1]
    if family_kind == "prop":
        return sorted(ms, key=lambda m: (-float(m.get("volume_fp") or 0), m["ticker"]))[:SAMPLE_PROPS]
    ms = sorted(ms, key=lambda m: (m.get("floor_strike") is None, m.get("floor_strike") or 0.0, m["ticker"]))
    if len(ms) <= SAMPLE_STRIKES:
        return ms
    idx = sorted({round(i * (len(ms) - 1) / (SAMPLE_STRIKES - 1)) for i in range(SAMPLE_STRIKES)})
    return [ms[i] for i in idx]


def family_kind(series: str) -> str:
    return "game" if series.endswith("GAME") else ("team" if series.endswith(("SPREAD", "TOTAL", "TEAMTOTAL")) else "prop")


def season_label(sport: str, iso: str) -> str:
    y, m = int(iso[:4]), int(iso[5:7])
    if sport == "nfl":
        return str(y if m >= 7 else y - 1)
    return f"{y}-{str(y + 1)[2:]}" if m >= 7 else f"{y - 1}-{str(y)[2:]}"


SLIM = ("ticker", "event_ticker", "series_ticker", "title", "yes_sub_title", "floor_strike", "strike_type", "result", "open_time",
        "close_time", "occurrence_datetime", "settlement_ts", "volume_fp", "last_price_dollars")


# ---------------------------------------------------------------------------------------------- phases
def _jl(path: Path):
    return [json.loads(l) for l in path.open()] if path.exists() else []


def phase_list(a, sport, out):
    client = bs.Client(pause=1.0 / a.rate); store = bs.Store(out / "raw")
    cj, _ = client.get("/historical/cutoff"); cutoff = cj["market_settled_ts"]
    lo = bs.iso_ts(a.from_iso)
    (out / "markets").mkdir(exist_ok=True)
    for series in SPORTS[sport]["team"] + SPORTS[sport]["prop"]:
        try:
            ms = [m for m in bs.list_markets(client, store, series, cutoff) if m.get("result") in ("yes", "no")]
        except bs.FetchFailed as e:
            print("LIST FAILED", series, e, flush=True); continue
        ms = [m for m in ms if bs.iso_ts(m.get("occurrence_datetime") or m["close_time"]) >= lo]
        with (out / "markets" / f"{series}.jsonl").open("w") as fh:
            for m in sorted(ms, key=lambda x: x["ticker"]):
                fh.write(json.dumps({k: m.get(k) for k in SLIM}, sort_keys=True) + "\n")
        print(series, len(ms), "settled markets", client.stats(), flush=True)


def phase_schedule(a, sport, out):
    from concurrent.futures import ThreadPoolExecutor
    start = datetime.strptime(a.from_iso[:10], "%Y-%m-%d").date()
    end = datetime.now(timezone.utc).date() + timedelta(days=1)
    days = [start + timedelta(days=i) for i in range((end - start).days + 1)]

    def one(d):  # ESPN now rejects multi-day ranges (HTTP 400, measured 2026-10-26); one date per request works
        url = f"https://site.api.espn.com/apis/site/v2/sports/{SPORTS[sport]['espn']}/scoreboard?dates={d:%Y%m%d}"
        for attempt in range(4):
            try:
                return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "pm-w89-7/1"}), timeout=30)).get("events", [])
            except Exception:
                time.sleep(2 ** attempt)
        print("SCHEDULE FAILED", url, flush=True)
        return []

    rows = {}
    with ThreadPoolExecutor(6) as ex:
        for evs in ex.map(one, days):
            for ev in evs:
                comp = ev["competitions"][0]
                cs = {c["homeAway"]: c["team"].get("abbreviation") for c in comp["competitors"]}
                if cs.get("away") and cs.get("home") and "home" in cs:
                    rows[ev["id"]] = {"espn_id": ev["id"], "start_utc": ev["date"], "away": cs["away"], "home": cs["home"],
                                      "status": comp.get("status", {}).get("type", {}).get("name")}
    with (out / "schedule.jsonl").open("w") as fh:
        for r in sorted(rows.values(), key=lambda r: (r["start_utc"], r["espn_id"])):
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    print("schedule games", len(rows), flush=True)


def phase_join(a, sport, out):
    games = _jl(out / "schedule.jsonl")
    events: dict[str, dict] = {}
    for series in SPORTS[sport]["team"] + SPORTS[sport]["prop"]:
        for m in _jl(out / "markets" / f"{series}.jsonl"):
            ev = m["event_ticker"]
            if ev in events:
                continue
            p = parse_event(ev)
            rec = {"event_ticker": ev, "series": series, "kalshi_occurrence": m["occurrence_datetime"]}
            if p is None:
                rec["join"] = "unparsed"
            else:
                g, why = match_event(p[1], p[0], games)
                rec["join"] = why
                if g:
                    rec.update(start_utc=g["start_utc"], espn_id=g["espn_id"], away=g["away"], home=g["home"])
            events[ev] = rec
    with (out / "events.jsonl").open("w") as fh:
        for r in sorted(events.values(), key=lambda r: r["event_ticker"]):
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    c = Counter(r["join"] for r in events.values())
    print("events", len(events), dict(c), flush=True)
    miss = Counter(parse_event(r["event_ticker"])[1] for r in events.values() if r["join"] in ("no_team_pair",) and parse_event(r["event_ticker"]))
    print("most common unmatched team codes:", miss.most_common(12), flush=True)


def phase_candles(a, sport, out):
    client = bs.Client(pause=1.0 / a.rate); store = bs.Store(out / "raw")
    cj, _ = client.get("/historical/cutoff"); cutoff = bs.iso_ts(cj["market_settled_ts"])
    starts = {r["event_ticker"]: r for r in _jl(out / "events.jsonl") if r.get("start_utc")}
    (out / "candles").mkdir(exist_ok=True)
    deadline = time.time() + a.minutes * 60
    series_list = [s for s in (SPORTS[sport]["team"] + SPORTS[sport]["prop"]) if not a.series or s in a.series]
    # newest events first: the in-season 2026-27 data is the scarcest and the most useful to Wave 90
    for series in series_list:
        path = out / "candles" / f"{series}.jsonl"
        done = {r["ticker"] for r in _jl(path)}
        by_ev = defaultdict(list)
        for m in _jl(out / "markets" / f"{series}.jsonl"):
            if m["event_ticker"] in starts:
                by_ev[m["event_ticker"]].append(m)
        todo = []
        for ev in sorted(by_ev, key=lambda e: starts[e]["start_utc"], reverse=True):
            todo += [m for m in pick_sample(by_ev[ev], family_kind(series)) if m["ticker"] not in done]
        print(series, "to fetch", len(todo), flush=True)
        with path.open("a") as fh:
            for i, m in enumerate(todo):
                if time.time() > deadline:
                    print("DEADLINE reached at", series, i, client.stats(), flush=True); return
                s = bs.iso_ts(starts[m["event_ticker"]]["start_utc"])
                try:
                    cs = bs.candles(client, store, series, m, s - LOOKBACK_H * 3600, s + 60, 60, cutoff)
                except bs.FetchFailed as e:
                    print("FAILED", m["ticker"], e, flush=True); continue
                fh.write(json.dumps({"ticker": m["ticker"], "event_ticker": m["event_ticker"], "series": series, "start_ts": s,
                                     "result": m["result"], "n_candles": len(cs), "candles": cs}, sort_keys=True) + "\n"); fh.flush()
                if i % 200 == 0:
                    print(series, i, "/", len(todo), client.stats(), flush=True)
    print("done", client.stats(), flush=True)


def phase_manifest(a, sport, out):
    starts = {r["event_ticker"]: r for r in _jl(out / "events.jsonl")}
    rows = []
    for series in SPORTS[sport]["team"] + SPORTS[sport]["prop"]:
        ms = _jl(out / "markets" / f"{series}.jsonl")
        cs = {r["ticker"]: r for r in _jl(out / "candles" / f"{series}.jsonl")}
        per = defaultdict(lambda: Counter())
        for m in ms:
            s = season_label(sport, m["occurrence_datetime"] or m["close_time"])
            c = per[s]
            c["markets"] += 1
            c["events_joined"] += 0
            if starts.get(m["event_ticker"], {}).get("start_utc"):
                c["markets_with_true_start"] += 1
            if m["ticker"] in cs:
                c["candle_markets"] += 1
                c["candle_markets_nonempty"] += 1 if cs[m["ticker"]]["n_candles"] else 0
        for s, c in sorted(per.items()):
            ev_all = {m["event_ticker"] for m in ms if season_label(sport, m["occurrence_datetime"] or m["close_time"]) == s}
            rows.append({"sport": sport, "series": series, "season": s, "events": len(ev_all),
                         "events_with_true_start": sum(1 for e in ev_all if starts.get(e, {}).get("start_utc")),
                         **{k: c[k] for k in ("markets", "markets_with_true_start", "candle_markets", "candle_markets_nonempty")}})
    # Kalshi occurrence_datetime vs the schedule: the measured offset
    offs = []
    for r in starts.values():
        if r.get("start_utc") and r.get("kalshi_occurrence"):
            offs.append((bs.iso_ts(r["kalshi_occurrence"]) - bs.iso_ts(r["start_utc"])) / 3600.0)
    offs.sort()
    summary = {"sport": sport, "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "rows": rows,
               "join": dict(Counter(r["join"] for r in starts.values())),
               "occurrence_minus_start_hours": {"n": len(offs), "p10": offs[len(offs) // 10] if offs else None,
                                                "median": offs[len(offs) // 2] if offs else None,
                                                "p90": offs[(9 * len(offs)) // 10] if offs else None}}
    safe_out(MANIFEST_DIR / sport / "MANIFEST.json").write_text(json.dumps(summary, indent=1, sort_keys=True))
    print(json.dumps(summary, indent=1))


PHASES = {"list": phase_list, "schedule": phase_schedule, "join": phase_join, "candles": phase_candles, "manifest": phase_manifest}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=PHASES)
    ap.add_argument("--sport", required=True, choices=SPORTS)
    ap.add_argument("--out", default=str(ROOT / "exp_output" / "KALSHI_HISTORY" / "w89_7"))
    ap.add_argument("--from-iso", default="2025-08-01T00:00:00Z")
    ap.add_argument("--rate", type=float, default=1.5)
    ap.add_argument("--minutes", type=float, default=40.0, help="candles phase: wall-clock budget")
    ap.add_argument("--series", nargs="*", help="candles phase: restrict to these series")
    a = ap.parse_args(argv)
    out = Path(a.out) / a.sport; out.mkdir(parents=True, exist_ok=True)
    PHASES[a.phase](a, a.sport, out)


if __name__ == "__main__":
    main()
