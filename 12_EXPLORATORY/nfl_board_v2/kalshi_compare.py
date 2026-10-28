"""W93.4 Part A: engine price vs Kalshi quote vs settlement, per strike off the main line (last pre-kickoff snapshot)."""
import json, re, sys, collections
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd
sys.path.insert(0, "src")
sys.path.insert(0, "12_EXPLORATORY")
from _fence import safe_out
from prediction_market_bot.nfl_engine.board_v2 import build_library, price_board
from prediction_market_bot.quant.money import fee
from prediction_market_bot.quant.inference import cluster_bootstrap
PR = sys.argv[1]; OFF = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
CONV = sys.argv[3] if len(sys.argv) > 3 else "ge"   # ge: yes = value >= N ; gt: yes = value > N
s = pd.read_parquet("exp_output/NFL_EVENTS/raw/schedules/schedules_20261020T001136Z.parquet")
cur = s[(s.season == 2026) & s.home_score.notna()].copy()
lib = build_library(s, before_season=2026)
alias = {"LA": "LAR"}
k = lambda c: alias.get(c, c)
MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
games = {}
for r in cur.itertuples():
    d = pd.Timestamp(r.gameday)
    ev = f"{d:%y}{[m for m,i in MON.items() if i==d.month][0]}{d:%d}{k(r.away_team)}{k(r.home_team)}"
    ko = pd.Timestamp(f"{r.gameday} {r.gametime}", tz="America/New_York").tz_convert("UTC")
    games[ev] = dict(home=k(r.home_team), away=k(r.away_team), m=int(r.home_score - r.away_score), t=int(r.home_score + r.away_score),
                     hp=int(r.home_score), ap=int(r.away_score), ko=ko)
snap = {}   # (event, ticker) -> last row before kickoff
for l in open(PR):
    r = json.loads(l); et = r["event_ticker"].split("-", 1)[1]
    g = games.get(et)
    if not g: continue
    if pd.Timestamp(r["run_ts"]) >= g["ko"]: continue
    snap[(r["series_ticker"], et, r["ticker"].rsplit("-", 1)[1])] = r
byev = collections.defaultdict(dict)
for (ser, et, suf), r in snap.items(): byev[et].setdefault(ser, {})[suf] = r
mid = lambda r: float(r["yes_mid"])
def centre(points):   # points: {threshold h (P(X>h)): p}; 0.5 crossing, linear
    hs = sorted(points)
    for a, b in zip(hs, hs[1:]):
        if points[a] >= .5 >= points[b] and points[a] > points[b]:
            return a + (points[a] - .5) / (points[a] - points[b]) * (b - a)
    return None
rows = []
for et, fam in byev.items():
    g = games[et]; sp, tt, tm, gm = fam.get("KXNFLSPREAD", {}), fam.get("KXNFLTOTAL", {}), fam.get("KXNFLTEAMTOTAL", {}), fam.get("KXNFLGAME", {})
    off = 0.5 if CONV == "ge" else 0.0     # yes iff X >= N (>= N -> threshold N-0.5) ; gt -> threshold N
    hp = {}
    for suf, r in sp.items():
        mm = re.match(r"([A-Z]+?)(\d+)$", suf); team, n = mm.group(1), int(mm.group(2)); th = n - off
        if team == g["home"]: hp[th - 0.0] = mid(r)                          # P(home margin > th)
        elif team == g["away"]: hp[-th] = 1 - mid(r)                         # away margin > th  <=> home margin < -th
    tp = {int(re.sub(r"\D", "", suf)) - off: mid(r) for suf, r in tt.items()}
    Lc, Tc = centre(hp), centre(tp)
    if Lc is None or Tc is None: continue
    b = price_board(lib, Lc, Tc)
    def add(fam_, key, q_eng, r, y, dist):
        rows.append(dict(event=et, fam=fam_, key=key, eng=q_eng, kal=mid(r), ask=float(r["yes_ask"]), bid=float(r["yes_bid"]), y=y, dist=dist, ser=r["series_ticker"]))
    for suf, r in sp.items():
        mm = re.match(r"([A-Z]+?)(\d+)$", suf); team, n = mm.group(1), int(mm.group(2)); th = n - off
        if team == g["home"]: pe = b.p_margin_ge(int(np.floor(th)) + 1); y = int(g["m"] > th); dist = abs(th - Lc)
        elif team == g["away"]: pe = float(b.p[b.m < -th].sum()); y = int(-g["m"] > th); dist = abs(-th - Lc)
        else: continue
        if dist >= OFF: add("spread", suf, pe, r, y, dist)
    for suf, r in tt.items():
        th = int(re.sub(r"\D", "", suf)) - off; pe = b.p_total_ge(int(np.floor(th)) + 1); y = int(g["t"] > th); dist = abs(th - Tc)
        if dist >= OFF: add("total", suf, pe, r, y, dist)
    for suf, r in tm.items():
        mm = re.match(r"([A-Z]+?)(\d+)$", suf); team, n = mm.group(1), int(mm.group(2)); th = n - off
        if team not in (g["home"], g["away"]): continue
        ish = team == g["home"]; pe = b.p_team_ge(ish, int(np.floor(th)) + 1); y = int((g["hp"] if ish else g["ap"]) > th)
        add("teamtotal", suf, pe, r, y, 99)
    for suf, r in gm.items():
        if suf == g["home"]: add("game", suf, b.p_home_win(), r, int(g["m"] > 0), 99)
        elif suf == g["away"]: add("game", suf, 1 - b.p_home_win(), r, int(g["m"] < 0), 99)
d = pd.DataFrame(rows)
out = {"conv": CONV, "off": OFF, "games": int(d.event.nunique()), "fam": {}}
for f, x in d.groupby("fam"):
    x = x.assign(be=(x.eng - x.y) ** 2, bk=(x.kal - x.y) ** 2)
    diff = {e: list((g.bk - g.be)) for e, g in x.groupby("event")}   # +ve = engine better
    m, lo, hi = cluster_bootstrap(diff, b=2000)
    # net-of-fee: buy YES at ask if eng - ask > fee/contract + 0 ; buy NO at (1-bid) if bid - eng > fee
    pnl = []
    for r in x.itertuples():
        fy = fee(r.ser, r.ask, 1); fn = fee(r.ser, 1 - r.bid, 1)
        if r.eng - r.ask > fy: pnl.append((r.event, r.y - r.ask - fy))
        elif r.bid - r.eng > fn: pnl.append((r.event, (1 - r.y) - (1 - r.bid) - fn))
    pc = collections.defaultdict(list)
    for e, v in pnl: pc[e].append(v)
    pm = cluster_bootstrap(pc, b=2000) if pc else (float("nan"),) * 3
    out["fam"][f] = dict(n=len(x), games=int(x.event.nunique()), brier_engine=round(float(x.be.mean()), 4), brier_kalshi=round(float(x.bk.mean()), 4),
                         kalshi_minus_engine=[round(m, 4), round(lo, 4), round(hi, 4)], fired=len(pnl), fire_games=len(pc),
                         pnl_per_contract=[round(v, 4) for v in pm])
    print(f, out["fam"][f])
json.dump(out, open(safe_out(f"12_EXPLORATORY/nfl_board_v2/kalshi_compare_{CONV}_off{OFF:g}.json"), "w"), indent=1)
