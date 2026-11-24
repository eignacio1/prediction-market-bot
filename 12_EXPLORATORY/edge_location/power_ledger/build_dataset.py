#!/usr/bin/env python3
"""W124.1 dataset: reference snapshots + yield + cost from the price archive (READ-ONLY; no settlement, no network).

Per ticker whose event ticker encodes a game date gd (KXNBAGAME-26NOV20BOSNYK): the last snapshot at or before 15:00Z on gd-2 (P0),
gd-1 (E, entry) and gd (R, reference). 15:00Z = 10:00 ET, the W123.1 snapshot rule. R is NOT the true close: the archive has no start
time, so R is the game-morning line, and every CLV built on it is labelled descriptive. Also per series: games per week, the share of
events with a pre-15:00Z snapshot on game day (coverage) and the mean round cost (half spread + fee 0.07 p(1-p)) at R.
Applies: tickers with a parsable game date. Does not apply: futures, undated markets.
"""
import re, sys, os
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src"))
import json  # noqa: E402
from prediction_market_bot import io_jsonl  # noqa: E402

MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
RX = re.compile(r"-(\d{2})([A-Z]{3})(\d{2})")
RS = re.compile(r'"series_ticker": "([^"]+)"')
RE = re.compile(r'"event_ticker": "([^"]+)"')
SPORTS = ("NBA", "NFL", "NHL", "MLB")
WINDOW_DAYS = 28


def parse_game(event):
    m = RX.search(event or "")
    if not m or m.group(2) not in MON:
        return None, None
    try:
        return date(2000 + int(m.group(1)), MON[m.group(2)], int(m.group(3))), event.split("-", 1)[1]
    except ValueError:
        return None, None


def fee(p):
    return 0.07 * p * (1 - p)


def build(archive, today):
    slots, meta, gdcache = {}, {}, {}
    events = {}      # series -> {event: gd}   (files in the yield window only)
    pre = {}         # series -> set(event) with a 13-15Z snapshot on game day
    cost = {}        # series -> [sum, n] round cost at the last game-day snapshot per ticker
    lo = today - timedelta(days=WINDOW_DAYS + 7)
    files = io_jsonl.glob_files(f"{archive}/prices_*.jsonl")
    for f in files:
        fd = date.fromisoformat(os.path.basename(f)[7:17])
        recent = fd >= lo
        for l in io_jsonl.open_jsonl(f):
            hh = l[23:31]
            inwin = "13:00:00" <= hh <= "15:00:00"
            if not inwin and not recent:
                continue
            ms, me = RS.search(l), RE.search(l)
            if not ms or not me:
                continue
            st, ev = ms.group(1), me.group(1)
            if not st.startswith("KX") or st[2:5] not in SPORTS:
                continue
            if ev not in gdcache:
                gdcache[ev] = parse_game(ev)
            gd, gk = gdcache[ev]
            if gd is None:
                continue
            if recent:
                events.setdefault(st, {})[ev] = gd
            if not inwin:
                continue
            d = json.loads(l)
            rd = date.fromisoformat(d["run_ts"][:10]); off = (gd - rd).days
            if off not in (0, 1, 2):
                continue
            try:
                bid, ask = float(d["yes_bid"]), float(d["yes_ask"])
            except (KeyError, TypeError, ValueError):
                continue
            if not (0 < bid <= ask < 1):
                continue
            if off == 0:
                pre.setdefault(st, set()).add(ev)
            t = d["ticker"]; cur = slots.setdefault(t, {}); prev = cur.get(off)
            if prev is None or d["run_ts"] > prev[0]:
                cur[off] = (d["run_ts"], bid, ask, (bid + ask) / 2)
            meta[t] = (st, gk, gd.isoformat())
    rows = []
    for t, s in slots.items():
        st, gk, gd = meta[t]
        if 0 in s:
            m = s[0][3]; c = cost.setdefault(st, [0.0, 0]); c[0] += (s[0][2] - s[0][1]) / 2 + fee(m if m < 0.5 else 1 - m); c[1] += 1
        if 1 in s and 0 in s:
            row = {"ticker": t, "series": st, "game": gk, "gd": gd}
            for off, name in ((2, "p0"), (1, "e"), (0, "r")):
                if off in s:
                    row[name] = {"ts": s[off][0], "bid": s[off][1], "ask": s[off][2], "mid": s[off][3]}
            rows.append(row)
    win_lo, win_hi = today - timedelta(days=WINDOW_DAYS), today - timedelta(days=1)
    yld = {}
    for st, evs in events.items():
        inwin_ev = {e for e, g in evs.items() if win_lo <= g <= win_hi}
        if not inwin_ev:
            continue
        yld[st] = {"events_28d": len(inwin_ev), "events_per_week": len(inwin_ev) / (WINDOW_DAYS / 7),
                   "coverage_pre15z": len(inwin_ev & pre.get(st, set())) / len(inwin_ev),
                   "pre_events_per_week": len(inwin_ev & pre.get(st, set())) / (WINDOW_DAYS / 7),
                   "round_cost_at_R": (cost[st][0] / cost[st][1]) if st in cost else None}
    return rows, yld, {"window": [win_lo.isoformat(), win_hi.isoformat()], "files": len(files)}
