#!/usr/bin/env python3
"""W123.3 H3 news latency (PREREG.md, frozen d698f99 before any price read). Reads data/ (Muse pinned bf892b8), the price archive, and
Kalshi public trades (read-only; cached in data/trades/). Writes results.json and prints a summary."""
from __future__ import annotations

import argparse, bisect, glob, json, math, os, random, re, statistics, sys, time, urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "src"))
from prediction_market_bot.io_jsonl import open_jsonl  # noqa: E402

API = "https://api.elections.kalshi.com/trade-api/v2/markets/trades"
ET = timezone(timedelta(hours=-5))  # Nov 2026 is after DST ends (Nov 1)
GRID = list(range(1, 31))
STALE = 600  # seconds: a trade older than this is not a price


def ts(s):
    s = s.split(".")[0].rstrip("Z")
    return datetime.strptime(s + "+0000", "%Y-%m-%dT%H:%M:%S%z")


# ---------------------------------------------------------------- archive (tickers, half-spreads)
def load_archive(arch, series):
    tick = defaultdict(set)  # (event_ticker) -> {tickers}
    hs = defaultdict(list)  # ticker -> [(epoch, mid, half_spread)]
    for p in sorted(glob.glob(os.path.join(arch, "prices_2026-*.jsonl*"))):
        base = p[:-3] if p.endswith(".gz") else p
        if base != p and os.path.exists(base):
            continue
        with open_jsonl(base) as f:
            for line in f:
                if not any(f'"{s}"' in line[:130] for s in series):
                    continue
                r = json.loads(line)
                if r.get("series_ticker") not in series or r.get("yes_mid") is None:
                    continue
                tick[r["event_ticker"]].add(r["ticker"])
                hs[r["ticker"]].append((ts(r["run_ts"]).timestamp(), float(r["yes_mid"]), float(r["half_spread"])))
    for v in hs.values():
        v.sort()
    return tick, hs


# ---------------------------------------------------------------- trades (cached)
def fetch_trades(ticker, mn, mx):
    path = os.path.join(DATA, "trades", ticker + ".json")
    if os.path.exists(path):
        return json.load(open(path))
    out, cur = [], None
    while True:
        u = f"{API}?ticker={ticker}&min_ts={int(mn)}&max_ts={int(mx)}&limit=1000" + (f"&cursor={cur}" if cur else "")
        for k in range(4):
            try:
                d = json.load(urllib.request.urlopen(u, timeout=40))
                break
            except Exception as e:  # noqa: BLE001
                time.sleep(2 * (k + 1))
        else:
            raise RuntimeError("fetch failed " + ticker)
        out += [(ts(t["created_time"]).timestamp(), float(t["yes_price_dollars"]), float(t["count_fp"])) for t in d["trades"]]
        cur = d.get("cursor")
        if not cur or not d["trades"]:
            break
    out.sort()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(out, open(path, "w"))
    return out


class Px:
    def __init__(self, trades):
        self.t = [x[0] for x in trades]
        self.p = [x[1] for x in trades]

    def at(self, t):
        i = bisect.bisect_right(self.t, t) - 1
        if i < 0 or t - self.t[i] > STALE:
            return None
        return self.p[i]


def round_cost(hs_rows, t, p):
    if not hs_rows:
        return None
    i = bisect.bisect_left([r[0] for r in hs_rows], t)
    cand = [hs_rows[j] for j in (i - 1, i) if 0 <= j < len(hs_rows)]
    r = min(cand, key=lambda r: abs(r[0] - t))
    return r[2] + 0.07 * p * (1 - p)


# ---------------------------------------------------------------- events
def nba_events():
    games, rows = {}, defaultdict(list)
    for f in sorted(glob.glob(os.path.join(DATA, "*nba_lineups-*.jsonl"))):
        for l in open(f):
            r = json.loads(l)
            rows[r["game_id"]].append(r)
    for g, v in rows.items():
        v.sort(key=lambda r: r["snapshot_at_utc"])
        games[g] = {"away": g.split("@")[0], "home": g.split("@")[1].split("-")[0], "date": g.split("-", 1)[1],
                    "start": ts(v[0]["tipoff_utc"]).timestamp(), "sport": "NBA"}
    ev = []
    for g, v in rows.items():
        c = [r["confirmed_at_utc"] for r in v if r["confirmed_at_utc"]]
        if c:
            ev.append({"type": "NBA_CONFIRM", "game": g, "t": ts(min(c)).timestamp()})
        for a, b in zip(v, v[1:]):
            if (a["away_starters"], a["home_starters"]) != (b["away_starters"], b["home_starters"]):
                ev.append({"type": "NBA_STARTER_CHANGE", "game": g, "t": ts(b["status_at_utc"] or b["snapshot_at_utc"]).timestamp()})
    # injury lines, deduplicated, first-seen snapshot gives the date
    seen = {}
    for g, v in rows.items():
        for r in v:
            for s in r["late_scratches"]:
                if s not in seen or r["snapshot_at_utc"] < seen[s]:
                    seen[s] = r["snapshot_at_utc"]
    by_team_date = defaultdict(list)
    for g, m in games.items():
        for side in ("away", "home"):
            by_team_date[(m[side], m["date"])].append(g)
    for s, snap in seen.items():
        m = re.match(r"(\d+):(\d+) (AM|PM) ET - (.+?) \(([A-Z]{2,3})\) (.*)", s)
        if not m:
            continue
        hh, mm, ap, who, team, rest = m.groups()
        hh = int(hh) % 12 + (12 if ap == "PM" else 0)
        sn = ts(snap).astimezone(ET)
        t = sn.replace(hour=hh, minute=int(mm), second=0, microsecond=0)
        if t > sn:
            t -= timedelta(days=1)
        kind = "RULED_OUT" if "ruled out" in rest else "DAY_TO_DAY" if "day-to-day" in rest else "OTHER"
        for g in by_team_date.get((team, t.strftime("%Y-%m-%d")), []):
            ev.append({"type": "NBA_INJURY_" + kind, "game": g, "t": t.timestamp(), "who": who})
    return games, ev


def nfl_events():
    games, ev = {}, []
    for f in sorted(glob.glob(os.path.join(DATA, "*nfl_inactives-*.jsonl"))):
        for l in open(f):
            r = json.loads(l)
            m = re.match(r"([A-Z]+)@([A-Z]+) (\d{4}-\d{2}-\d{2}) (\d+):(\d+) ET", r["game_id"])
            if not m:
                continue
            a, h, d, hh, mm = m.groups()
            start = datetime.strptime(f"{d} {hh}:{mm}", "%Y-%m-%d %H:%M").replace(tzinfo=ET).timestamp()
            g = f"{a}@{h}-{d}"
            games[g] = {"away": a, "home": h, "date": d, "start": start, "sport": "NFL"}
            ev.append({"type": "NFL_INACTIVES", "game": g, "t": ts(r["announced_at_utc"]).timestamp()})
    return games, ev


def ticker_for(game, m, tick):
    d = datetime.strptime(m["date"], "%Y-%m-%d")
    pref = "KXNBAGAME" if m["sport"] == "NBA" else "KXNFLGAME"
    for dd in (d, d + timedelta(days=1)):
        et = f"{pref}-{dd.strftime('%y%b%d').upper()}{m['away']}{m['home']}"
        if et in tick:
            return [t for t in tick[et] if t.endswith("-" + m["home"])][:1] or None
    return None


# ---------------------------------------------------------------- stats
def boot(vals_by_game, n=2000, seed=7):
    rng = random.Random(seed)
    gs = list(vals_by_game)
    flat = [x for g in gs for x in vals_by_game[g]]
    if not flat:
        return None
    pt = sum(flat) / len(flat)
    ms = []
    for _ in range(n):
        s = [x for g in (rng.choice(gs) for _ in gs) for x in vals_by_game[g]]
        ms.append(sum(s) / len(s))
    ms.sort()
    return {"mean": pt, "lo": ms[int(.05 * n)], "hi": ms[int(.95 * n) - 1], "n": len(flat), "games": len(gs)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True)
    a = ap.parse_args()
    ng, ne = nba_events()
    fg, fe = nfl_events()
    games = {**ng, **fg}
    events = ne + fe
    tick, hs = load_archive(a.archive, {"KXNBAGAME", "KXNFLGAME"})
    funnel = defaultdict(lambda: defaultdict(int))
    px, tk = {}, {}
    for g, m in games.items():
        t = ticker_for(g, m, tick)
        if t:
            tk[g] = t[0]
    # fetch
    for g, t in tk.items():
        m = games[g]
        px[g] = Px(fetch_trades(t, m["start"] - 3 * 86400, m["start"] + 3600))
    # event index per game for placebo exclusion
    ev_t = defaultdict(list)
    for e in events:
        ev_t[e["game"]].append(e["t"])
    rows = []
    for e in events:
        f = funnel[e["type"]]
        f["events"] += 1
        g = e["game"]
        if g not in tk:
            f["no_market_match"] += 1
            continue
        if e["t"] + 1800 > games[g]["start"]:
            f["window_runs_past_start"] += 1
            continue
        P = px[g]
        p0 = P.at(e["t"])
        pr = {L: P.at(e["t"] + 60 * L) for L in GRID}
        if p0 is None or any(v is None for v in pr.values()):
            f["no_print_coverage"] += 1
            continue
        cost = round_cost(hs.get(tk[g]), e["t"], p0)
        if cost is None:
            f["no_spread"] += 1
            continue
        rows.append({**e, "p0": p0, "move": {L: abs(pr[L] - p0) for L in GRID}, "rem": {L: abs(pr[30] - pr[L]) for L in GRID}, "cost": cost})
        f["scored"] += 1
    # placebo: per game, t0 every 5 min, no event of any type within +-2h
    plc = defaultdict(lambda: defaultdict(list))
    for g in tk:
        m, P = games[g], px[g]
        t = m["start"] - 12 * 3600
        while t + 1800 <= m["start"] - 1800:
            if all(abs(t - x) > 7200 for x in ev_t.get(g, [])):
                p0 = P.at(t)
                p30 = P.at(t + 1800)
                if p0 is not None and p30 is not None and all(P.at(t + 60 * L) is not None for L in (1, 5, 15)):
                    for L in GRID:
                        pl = P.at(t + 60 * L)
                        if pl is not None:
                            plc[g][("rem", L)].append(abs(p30 - pl))
                            plc[g][("move", L)].append(abs(pl - p0))
            t += 300
    pooled = defaultdict(list)
    for g, d in plc.items():
        for k, v in d.items():
            pooled[k] += v
    pm = {k: statistics.median(v) for k, v in pooled.items()}

    def plmed(g, k):
        v = plc.get(g, {}).get(k)
        return statistics.median(v) if v else pm.get(k, 0.0)

    out = {"pinned_muse_sha": "bf892b818874f2a86f721cc8c5a053ea71dcc4fd", "funnel": {k: dict(v) for k, v in funnel.items()},
           "placebo_windows": sum(len(v[("rem", 5)]) for v in plc.values() if ("rem", 5) in v), "placebo_games": len(plc), "types": {}}
    types = sorted({r["type"] for r in rows})
    groups = {t: [r for r in rows if r["type"] == t] for t in types}
    groups["NBA_INJURY_ALL"] = [r for r in rows if r["type"].startswith("NBA_INJURY")]
    groups["NBA_ALL"] = [r for r in rows if r["type"].startswith("NBA")]
    for t, rs in groups.items():
        if not rs:
            continue
        # one event per game per type for independence at the game level: clustering handles it
        res = {"n_events": len(rs), "n_games": len({r["game"] for r in rs}), "mean_round_cost": sum(r["cost"] for r in rs) / len(rs)}
        for L in (1, 5, 15):
            for kind in ("rem", "move"):
                by = defaultdict(list)
                for r in rs:
                    by[r["game"]].append(r[kind][L] - plmed(r["game"], (kind, L)))
                res[f"D_{kind}_{L}"] = boot(by)
        # minutes to reprice: last minute at which the remaining move exceeds one round cost
        mtr = []
        for r in rs:
            last = 0
            for L in GRID:
                if r["rem"][L] > r["cost"]:
                    last = L
            mtr.append(last)
        mtr.sort()
        res["minutes_to_reprice"] = {"median": statistics.median(mtr), "p75": mtr[int(.75 * (len(mtr) - 1))], "p90": mtr[int(.9 * (len(mtr) - 1))],
                                     "share_repriced_by_1": sum(1 for x in mtr if x <= 1) / len(mtr),
                                     "share_repriced_by_5": sum(1 for x in mtr if x <= 5) / len(mtr),
                                     "share_repriced_by_15": sum(1 for x in mtr if x <= 15) / len(mtr)}
        d5 = res["D_rem_5"]
        res["verdict"] = ("UNDERPOWERED" if res["n_events"] < 30 else
                          "SUPPORTED" if d5["lo"] > 0 and d5["mean"] > res["mean_round_cost"] else
                          "NOT SUPPORTED" if d5["mean"] <= res["mean_round_cost"] or res["minutes_to_reprice"]["median"] <= 1 else "UNDERPOWERED")
        out["types"][t] = res
    json.dump(out, open(os.path.join(HERE, "results.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
