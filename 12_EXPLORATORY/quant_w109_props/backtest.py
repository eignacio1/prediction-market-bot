"""W109.3 Part B: engine-priced NBA props vs the market's pre-game mid on settled markets (walk-forward, no leakage).

Inputs (scratchpad, public data): markets.jsonl + candles.jsonl from fetch_markets.py, box_2627.json (ESPN box scores).
Engine: engine_v2 with FIXED league constants (hca/tbias/sd are not fitted on any tested game) and team ratings from games
dated strictly before the game; player means from the player's prior games only. Player availability is NOT known.
Usage: PYTHONPATH=src python3 backtest.py markets.jsonl candles.jsonl box.json out.json
"""
import calendar, collections, datetime as dt, json, re, sys, time
import numpy as np
from prediction_market_bot.c1_signal_ingestion.nba_ingest import kalshi_code
from prediction_market_bot.nba_engine import engine_v2 as E2
from prediction_market_bot.nba_engine import props as P
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
from _fence import safe_out  # noqa: E402

FAM = {"KXNBAPTS": "points", "KXNBAREB": "rebounds", "KXNBAAST": "assists", "KXNBA3PT": "threes"}
LEAGUE = 114.0
PARAMS = E2.V2Params(hca=2.0, tbias=0.0, sd_margin=13.0, sd_total=19.0)   # league constants, not fitted on tested games
MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}


def ts(s):
    return int(calendar.timegm(time.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")))


def load_box(path):
    games, pl = {}, collections.defaultdict(list)
    for gid, g in json.load(open(path)).items():
        teams = {}
        for t in g["box"]["players"]:
            code = kalshi_code(t["team"]["abbreviation"])
            ks = t["statistics"][0]["keys"]
            ix = {k: i for i, k in enumerate(ks)}
            rows = []
            for a in t["statistics"][0]["athletes"]:
                st = a.get("stats") or []
                if not st or a.get("didNotPlay"):
                    continue
                try:
                    mins = float(st[ix["minutes"]])
                except ValueError:
                    continue
                if mins <= 0:
                    continue
                r = dict(name=a["athlete"]["displayName"], min=mins, points=float(st[ix["points"]]), rebounds=float(st[ix["rebounds"]]),
                         assists=float(st[ix["assists"]]), threes=float(st[ix["threePointFieldGoalsMade-threePointFieldGoalsAttempted"]].split("-")[0]))
                rows.append(r)
            teams[code] = rows
        hdr = {h.split(":")[0]: (h.split(":")[1], float(h.split(":")[2])) for h in g["hdr"]}
        pts = {kalshi_code(k): v[1] for k, v in hdr.items()}
        home = [kalshi_code(k) for k, v in hdr.items() if v[0] == "home"][0]
        games[gid] = dict(date=g["date"], home=home, away=[c for c in teams if c != home][0], pts=pts, teams=teams)
        for code, rows in teams.items():
            for r in rows:
                pl[(code, r["name"])].append((g["date"], r))
    return games, pl


def ratings(games, before):
    f, a = collections.defaultdict(list), collections.defaultdict(list)
    for g in games.values():
        if g["date"] < before:
            for t in (g["home"], g["away"]):
                o = g["away"] if t == g["home"] else g["home"]
                f[t].append(g["pts"][t]); a[t].append(g["pts"][o])
    sh = lambda v: (sum(v) + 8 * LEAGUE) / (len(v) + 8)
    return (lambda t: sh(f[t])), (lambda t: sh(a[t]))


def roster(pl, team, before):
    out = []
    for (tm, name), rows in pl.items():
        prior = [r for d, r in rows if d < before]
        if tm == team and len(prior) >= 4 and np.mean([r["min"] for r in prior]) >= 10:
            out.append((np.mean([r["min"] for r in prior]), name, {s: float(np.mean([r[s] for r in prior])) for s in P.STATS}))
    out.sort(reverse=True)
    return out[:10]


def entry_price(c, close):
    best = None
    for k in c.get("candlesticks", []):
        if k["end_period_ts"] > close - 5 * 3600:
            continue
        b, a = float(k["yes_bid"].get("close_dollars") or 0), float(k["yes_ask"].get("close_dollars") or 0)
        if b > 0 and a > 0 and a >= b:
            best = (k["end_period_ts"], b, a)
    return best


def main(mp, cp, bp, out):
    games, pl = load_box(bp)
    byk = {(g["date"], frozenset((g["home"], g["away"]))): (gid, g) for gid, g in games.items()}
    cand = {}
    for l in open(cp):
        x = json.loads(l); cand[x["market_ticker"]] = x
    rows, skipped = [], collections.Counter()
    cache = {}
    for l in open(mp):
        m = json.loads(l)
        mt = re.match(r"KX\w+-(\d\d)([A-Z]{3})(\d\d)([A-Z]{3})([A-Z]{3})-([A-Z]{3})", m["ticker"])
        if not mt or m["ticker"] not in cand:
            skipped["unparsed_or_no_candle"] += 1; continue
        yy, mon, dd, away, home = int(mt[1]), MON[mt[2]], int(mt[3]), mt[4], mt[5]
        d0 = dt.date(2000 + yy, mon, dd)
        g = next((byk.get(((d0 + dt.timedelta(days=o)).isoformat(), frozenset((home, away)))) for o in (0, 1, -1)
                  if byk.get(((d0 + dt.timedelta(days=o)).isoformat(), frozenset((home, away))))), None)
        ep = entry_price(cand[m["ticker"]], ts(m["close_time"]))
        if g is None or ep is None:
            skipped["no_game_in_box" if g is None else "no_two_sided_quote"] += 1; continue
        gid, game = g
        stat = FAM[m["s"]]
        name = m["title"].split(":")[0]
        team = mt[6]
        if gid not in cache:
            af, aa = ratings(games, game["date"])
            mu_h, mu_a = (af(game["home"]) + aa(game["away"])) / 2, (af(game["away"]) + aa(game["home"])) / 2
            mm, tt = E2.game_means(PARAMS, mu_h, mu_a)
            h, a = E2.simulate(PARAMS, mm, tt, 4000, seed=int(gid) % 100003)
            cache[gid] = (h, a, {})
        h, a, dr = cache[gid]
        ros = roster(pl, team, game["date"])
        names = [n for _, n, _ in ros]
        if name not in names:
            skipped["player_not_in_prior_rotation"] += 1; continue
        key = (team, stat)
        if key not in dr:
            R = P.TeamRoster(tuple(names), {s: [r[2][s] for r in ros] for s in P.STATS}, float((h if team == game["home"] else a).mean()))
            dd_, _ = P.player_draws((h if team == game["home"] else a), R, stat, np.random.default_rng(int(gid) % 99991))
            dr[key] = (names, dd_)
        names2, dd_ = dr[key]
        n = int(round(float(m["floor_strike"]) + 0.5))
        p = P.strike_probs(dd_[:, names2.index(name)], [n])[n]
        rows.append(dict(t=m["ticker"], ev=gid, fam=stat, n=n, y=int(m["result"] == "yes"), p=p, mid=(ep[1] + ep[2]) / 2, spread=ep[2] - ep[1]))
    json.dump(dict(skipped=dict(skipped), rows=rows), open(safe_out(out), "w"))
    print(len(rows), dict(skipped))


if __name__ == "__main__":
    main(*sys.argv[1:5])
