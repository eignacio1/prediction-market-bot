"""W81.2 Part B step 1 (EXPLORATORY, not a verdict): which priced KXNBAPTS markets have a rule-defined teammate absence?

Reuses the Part A rules unchanged (rotation player, injury/illness DNP, single absence, regular season) on the 2025-26 season
(store season label 2026), the only season with KXNBAPTS candles. Read-only. Outputs via _fence.safe_out().
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lineup_cross as lc  # noqa: E402
from _fence import safe_out  # noqa: E402

MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}


def parse_event(et):
    """KXNBAPTS-25DEC03PORCLE -> (date, away, home)."""
    s = et.split("-")[1]
    return pd.Timestamp(2000 + int(s[:2]), MON[s[2:5]], int(s[5:7])).date(), s[7:10], s[10:13]


def main(raw, scratch):
    lc.RAW = Path(raw)
    lc.SEASONS = [2026]
    pb, tb = lc.load()
    tg = lc.attach_opponent(lc.trailing_defense(lc.team_games(pb, tb)))
    ev = lc.build_events(pb, tg)
    pb["name"] = (pb.first_name.fillna("") + " " + pb.family_name.fillna("")).str.strip()
    mk, cd = {}, defaultdict(set)
    for line in open(scratch):
        o = json.loads(line)
        if o["kind"] == "markets_page":
            for m in o["payload"]["markets"]:
                mk[m["ticker"]] = m
        elif o["kind"] == "candles":
            cd[o["key"].split("|")[0]].add(o["key"].split("|")[1])
    rows = []
    for t in cd:
        m = mk[t]
        d, away, home = parse_event(m["event_ticker"])
        nm = m["yes_sub_title"].split(":")[0].strip()
        strike = m["floor_strike"]
        sub = pb[(pb.name.str.lower() == nm.lower()) & (pb.team_tricode.isin([away, home]))]
        r = dict(ticker=t, date=str(d), player=nm, strike=strike, result=m.get("result"), close=m["close_time"])
        if sub.empty:
            r["status"] = "player_not_in_box"
            rows.append(r)
            continue
        g = sub.sort_values("game_id")
        sched = pd.read_parquet(Path(raw) / "schedule/schedule_2026.parquet")[["game_id", "season_type"]]
        g = g.merge(sched, on="game_id")
        g["gd"] = pd.to_datetime(g.game_date).dt.date
        g = g[(g.gd >= d - pd.Timedelta(days=1)) & (g.gd <= d + pd.Timedelta(days=1))]
        if g.empty:
            r["status"] = "no_game_match"
            rows.append(r)
            continue
        g = g.iloc[0]
        r.update(game_id=g.game_id, team=g.team_tricode, season_type=str(g.season_type), played=bool(g.minutes not in (None, "")))
        e = ev[(ev.game_id == g.game_id) & (ev.b == g.person_id)]
        if e.empty:
            r["status"] = "absorber_not_analysable"
        elif (e.kind == "single").any():
            e = e[e.kind == "single"].iloc[0]
            r.update(status="single_absence", role=e.role, absent_pid=int(e.absent), d_pts=float(e.d_pts))
            r["absent_name"] = pb[pb.person_id == e.absent].name.iloc[0]
        else:
            r["status"] = "clean"
        rows.append(r)
    out = pd.DataFrame(rows)
    out.to_csv(safe_out(Path(__file__).resolve().parent / "price_join_markets.csv"), index=False)
    print(out.status.value_counts().to_string())
    print(out[out.status == "single_absence"].drop(columns=["close"]).to_string())


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
