#!/usr/bin/env python3
"""W118.3 Part B: goalie-confirmation price timing (PREREG.md, frozen first). Reads data/goalies-*.jsonl and PRICE_ARCHIVE; stdout JSON."""
from __future__ import annotations

import argparse, glob, json, os, random, re, sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ALIAS = {"LA": "LAK", "NJ": "NJD", "TB": "TBL", "SJ": "SJS", "LAK": "LAK", "NJD": "NJD", "TBL": "TBL", "SJS": "SJS"}
MON = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()
LAGS = (20, 40, 60, 120)


def ts(s):
    s = s.split(".")[0].rstrip("Z")
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)


CODE = {"Anaheim Ducks": "ANA", "Boston Bruins": "BOS", "Buffalo Sabres": "BUF", "Calgary Flames": "CGY", "Carolina Hurricanes": "CAR",
        "Chicago Blackhawks": "CHI", "Colorado Avalanche": "COL", "Columbus Blue Jackets": "CBJ", "Dallas Stars": "DAL", "Detroit Red Wings": "DET",
        "Edmonton Oilers": "EDM", "Florida Panthers": "FLA", "Los Angeles Kings": "LA", "Minnesota Wild": "MIN", "Montreal Canadiens": "MTL",
        "Nashville Predators": "NSH", "New Jersey Devils": "NJ", "New York Islanders": "NYI", "New York Rangers": "NYR", "Ottawa Senators": "OTT",
        "Philadelphia Flyers": "PHI", "Pittsburgh Penguins": "PIT", "San Jose Sharks": "SJ", "Seattle Kraken": "SEA", "St Louis Blues": "STL",
        "St. Louis Blues": "STL", "Tampa Bay Lightning": "TB", "Toronto Maple Leafs": "TOR", "Utah Mammoth": "UTA", "Vancouver Canucks": "VAN",
        "Vegas Golden Knights": "VGK", "Washington Capitals": "WSH", "Winnipeg Jets": "WPG"}


def load_snaps(d):
    """Game key AWAY-HOME-DATE in Kalshi codes (the snapshot game_id format varies; the full names and source_url date do not)."""
    rows = []
    for f in sorted(glob.glob(os.path.join(d, "goalies-*.jsonl"))):
        rows += [json.loads(l) for l in open(f) if '"home_team"' in l]
    g = defaultdict(list)
    for r in rows:
        date = r["source_url"].rstrip("/").rsplit("/", 1)[1]
        g[f"{CODE[r['away_team']]}-{CODE[r['home_team']]}-{date}"].append(r)
    for v in g.values():
        v.sort(key=lambda r: r["snapshot_at_utc"])
    return g


def load_prices(arch, dates):
    """(date, frozenset(teams)) -> {'home': team, 'series': [(ts, mid, halfspread)]} for the HOME-side market is resolved later."""
    out = defaultdict(lambda: defaultdict(list))  # event_ticker -> team -> [(ts, mid, hs)]
    for d in dates:
        p = os.path.join(arch, f"prices_{d}.jsonl")
        if not os.path.exists(p):
            continue
        with open(p) as f:
            for line in f:
                if "KXNHLGAME" not in line[:80] and '"KXNHLGAME"' not in line[:120]:
                    continue
                r = json.loads(line)
                if r.get("series_ticker") != "KXNHLGAME" or r.get("yes_mid") is None:
                    continue
                out[r["event_ticker"]][r["ticker"].rsplit("-", 1)[1]].append((ts(r["run_ts"]), float(r["yes_mid"]), float(r["half_spread"])))
    return out


def event_for(game_id, prices):
    a, h, y, m, d = game_id.split("-")
    tag = f"{y[2:]}{MON[int(m) - 1]}{d}"
    want = {a, h}
    for ev, teams in prices.items():
        mm = re.match(r"KXNHLGAME-(\d\d[A-Z]{3}\d\d)(\w+)$", ev)
        if mm and mm.group(1) == tag and set(teams) == want:
            return ev
    return None


def home_series(prices_ev, home):
    for t, s in prices_ev.items():
        if t == home:
            return sorted(s)
    return None


def near(series, when, tol_min, before=False):
    best = None
    for t, mid, hs in series:
        dt = (t - when).total_seconds() / 60
        if before:
            if -tol_min <= dt <= 0 and (best is None or t > best[0]):
                best = (t, mid, hs)
        elif abs(dt) <= tol_min and (best is None or abs(dt) < abs((best[0] - when).total_seconds() / 60)):
            best = (t, mid, hs)
    return best


def build(g, prices, rng):
    events, placebos = [], defaultdict(list)
    for gid, snaps in g.items():
        ev = event_for(gid, prices)
        if not ev:
            continue
        home = gid.split("-")[1]
        ser = home_series(prices[ev], home)
        if not ser:
            continue
        y, m, d = gid.split("-")[2:]
        cutoff = datetime(int(y), int(m), int(d), 22, tzinfo=timezone.utc)
        confs = []
        for side in ("home", "away"):
            seen = None
            prev_name = None
            for s in snaps:
                if prev_name is None:
                    prev_name = s[side + "_goalie"]
                    first = s
                    continue
            names = [s[side + "_goalie"] for s in snaps]
            c = min((s[side + "_confirmed_at_utc"] for s in snaps if s.get(side + "_confirmed_at_utc")), default=None)
            if c:
                confs.append((ts(c), side, len(set(names)) > 1))
        busy = [c for c, _, _ in confs] + [ts(s[k]) for s in snaps for k in ("home_status_at_utc", "away_status_at_utc") if s.get(k)]
        for c, side, informative in confs:
            pre = near(ser, c, 25, before=True)
            if not pre:
                continue
            row = {"game": gid, "side": side, "informative": informative, "c": c.isoformat(), "half_spread": pre[2]}
            ok = True
            for L in LAGS:
                post = near(ser, c + timedelta(minutes=L), 10)
                if not post or post[0] >= cutoff:
                    ok = False
                    break
                row[f"p{L}"] = post[1]
            if not ok:
                continue
            row["p0"] = pre[1]
            events.append(row)
        # placebo windows: same game, windows [t, t+L] with no confirmation / status change within +-2h of the window, before cutoff
        for t0, mid0, hs in ser:
            if t0 >= cutoff or any(abs((t0 - b).total_seconds()) < 7200 for b in busy):
                continue
            rec = {}
            for L in LAGS:
                post = near(ser, t0 + timedelta(minutes=L), 10)
                if not post or post[0] >= cutoff or any(abs((post[0] - b).total_seconds()) < 7200 for b in busy):
                    rec = None
                    break
                rec[L] = post[1]
            if rec is not None:
                placebos[gid].append((mid0, rec))
    return events, placebos


def med(x):
    x = sorted(x)
    return x[len(x) // 2] if x else float("nan")


def stats(events, placebos, rng, B=2000):
    by_game = defaultdict(list)
    for e in events:
        by_game[e["game"]].append(e)
    games = [g for g in by_game if placebos.get(g)]

    def per_game(g):
        pl = placebos[g]
        pm60 = med([abs(r[60] - m0) for m0, r in pl])
        pm_lag = med([abs(r[120] - r[40]) for m0, r in pl])
        pm = {L: med([abs(r[L] - m0) for m0, r in pl]) for L in LAGS}
        out = []
        for e in by_game[g]:
            out.append(({L: abs(e[f"p{L}"] - e["p0"]) - pm[L] for L in LAGS}, abs(e["p120"] - e["p40"]) - pm_lag, e["informative"], e["half_spread"]))
        return out

    pg = {g: per_game(g) for g in games}

    def agg(gs, key):
        v = [k for g in gs for k in key(pg[g])]
        return sum(v) / len(v) if v else float("nan")

    def one(gs):
        r = {}
        for L in LAGS:
            r[f"D{L}"] = agg(gs, lambda xs, L=L: [x[0][L] for x in xs])
        r["D_lag"] = agg(gs, lambda xs: [x[1] for x in xs])
        r["D60_informative"] = agg(gs, lambda xs: [x[0][60] for x in xs if x[2]])
        r["D60_routine"] = agg(gs, lambda xs: [x[0][60] for x in xs if not x[2]])
        return r

    pt = one(games)
    boots = [one([rng.choice(games) for _ in games]) for _ in range(B)]
    ci = {}
    for k in pt:
        v = sorted(b[k] for b in boots if b[k] == b[k])
        ci[k] = [round(v[int(0.05 * len(v))], 4), round(v[int(0.95 * len(v)) - 1], 4)] if len(v) > 20 else None
    return {"n_events": sum(len(pg[g]) for g in games), "n_games": len(games), "point": {k: round(v, 4) for k, v in pt.items()}, "ci90": ci}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default=os.path.join(HERE, "..", "..", "exp_output", "PRICE_ARCHIVE"))
    a = ap.parse_args()
    g = load_snaps(os.path.join(HERE, "data"))
    dates = sorted({k.split("-", 2)[2] for k in g} | {(datetime.strptime(k.split("-", 2)[2], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d") for k in g})
    prices = load_prices(a.archive, dates)
    events, placebos = build(g, prices, random.Random(7))
    res = {"snapshot_games": len(g), "games_with_kalshi_event": sum(1 for k in g if event_for(k, prices)), "events_eligible": len(events),
           "placebo_windows": sum(len(v) for v in placebos.values()), **stats(events, placebos, random.Random(11)),
           "events_informative": sum(e["informative"] for e in events), "mean_half_spread": round(sum(e["half_spread"] for e in events) / max(1, len(events)), 4)}
    json.dump(res, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
