#!/usr/bin/env python3
"""W80R.2 (80P Task 2, step 4): efficiency + fillability per Kalshi family, game moneyline vs each thinner family.

EXPLORATORY. Read-only on the thin-market raw store(s) written by scripts/kalshi_thin_history_fetch.py
(rows: kind=markets_page | candles; candles key "<ticker>|<period>|<start>|<end>"). Writes only --out-json / --out-md.

Rules fixed before computing (see results.md "Method"):
  * 2025-and-earlier only: a market is analysed iff close_time < 2026-08-01 (2026-season rows are custody-only).
  * Kickoff/tip is NOT stored by Kalshi; approximated as close_time - KICKOFF_LAG[sport] (NFL 3h15m, NBA 2h30m; checked on
    one London NFL game: kickoff 13:30Z, close 16:44Z). Pre-game window = [kickoff-24h, kickoff-15min].
  * Quote = close of the latest candle with end_period_ts <= t (1-minute first, hourly fallback). A quote counts only
    when 0 < bid <= ask < 1. mid = (bid+ask)/2.
  * Per market: median bid-ask spread (cents) and median hourly volume (contracts) over pre-game hours; open interest at
    kickoff; fillable-hour share = share of pre-game hours whose volume >= (STAKE_USD / mid) / X, i.e. the flat demo
    stake is under X of that hour's volume (STAKE_USD = $1, X = 10%).
  * Moves: NFL Friday report = Fri 16:00 America/New_York before a Sun/Mon kickoff: |mid(t+60m) - mid(t)| on hourly
    candles, placebo the same 24h earlier. Late window (NFL inactives ko-90m; NBA lineups tip-30m): |mid(t+25m) - mid(t)|
    on 1-minute candles, placebo t-60m.
  * Family statistic = median over markets (fillable share: mean). 95% CI = percentile bootstrap over EVENTS
    (event_ticker clusters), B = 1000, seed 20261016.
"""
from __future__ import annotations

import argparse
import glob
import json
import random
import statistics
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

CUSTODY_FROM = datetime(2026, 8, 1, tzinfo=timezone.utc)
KICKOFF_LAG = {"NFL": timedelta(hours=3, minutes=15), "NBA": timedelta(hours=2, minutes=30)}
STAKE_USD = 1.0
X_SHARE = 0.10
B = 1000
SEED = 20261016
ET = ZoneInfo("America/New_York")
GAME_FAMILY = {"NFL": "KXNFLGAME", "NBA": "KXNBAGAME"}


def iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def sport_of(series: str) -> str:
    return "NFL" if series.startswith("KXNFL") else "NBA"


def series_of(ticker: str) -> str:
    return ticker.split("-", 1)[0]


def _f(v):
    try:
        return None if v in (None, "") else float(v)
    except (TypeError, ValueError):
        return None


def norm(c: dict) -> dict:
    def side(n):
        s = c.get(n) or {}
        return _f(s.get("close", s.get("close_dollars")))
    return {"t": int(c["end_period_ts"]), "bid": side("yes_bid"), "ask": side("yes_ask"),
            "vol": _f(c.get("volume", c.get("volume_fp"))) or 0.0,
            "oi": _f(c.get("open_interest", c.get("open_interest_fp")))}


def load(paths: list[str]) -> tuple[dict, dict]:
    """markets: ticker -> market dict; candles: (ticker, period) -> sorted unique candle list."""
    markets, candles = {}, defaultdict(dict)
    for p in paths:
        with open(p) as fh:
            for line in fh:
                if not line.strip():
                    continue
                r = json.loads(line)
                if r["kind"] == "markets_page":
                    for m in r["payload"].get("markets") or []:
                        markets[m["ticker"]] = m
                elif r["kind"] == "candles":
                    t, period = r["key"].split("|")[:2]
                    for c in r["payload"].get("candlesticks") or []:
                        n = norm(c)
                        candles[(t, int(period))][n["t"]] = n
    return markets, {k: [v[t] for t in sorted(v)] for k, v in candles.items()}


def quote_at(cs: list, ts: int):
    last = None
    for c in cs:
        if c["t"] > ts:
            break
        last = c
    if not last:
        return None
    b, a = last["bid"], last["ask"]
    if b is None or a is None or not (0 < b <= a < 1):
        return None
    return {"bid": b, "ask": a, "mid": (b + a) / 2, "oi": last["oi"]}


def analysed(m: dict) -> bool:
    return bool(m.get("result") in ("yes", "no") and m.get("close_time") and iso(m["close_time"]) < CUSTODY_FROM)


def kickoff(m: dict) -> datetime:
    return iso(m["close_time"]) - KICKOFF_LAG[sport_of(series_of(m["ticker"]))]


def friday_report(ko: datetime):
    """Fri 16:00 ET before a Sunday/Monday (ET) kickoff, else None."""
    k = ko.astimezone(ET)
    if k.weekday() not in (6, 0):
        return None
    back = (k.weekday() - 4) % 7
    d = (k - timedelta(days=back)).date()
    return datetime(d.year, d.month, d.day, 16, 0, tzinfo=ET).astimezone(timezone.utc)


def move(cs, t: datetime, dt: timedelta):
    a, b = quote_at(cs, int(t.timestamp())), quote_at(cs, int((t + dt).timestamp()))
    return None if a is None or b is None else abs(b["mid"] - a["mid"])


def per_market(m: dict, c1: list, c60: list) -> dict | None:
    ko = kickoff(m)
    lo, hi = ko - timedelta(hours=24), ko - timedelta(minutes=15)
    base = c1 or c60
    spreads, hours = [], defaultdict(float)
    for c in base:
        ts = datetime.fromtimestamp(c["t"], timezone.utc)
        if not (lo < ts <= hi):
            continue
        if c["bid"] is not None and c["ask"] is not None and 0 < c["bid"] <= c["ask"] < 1:
            spreads.append(c["ask"] - c["bid"])
        hours[int((ko - ts).total_seconds() // 3600)] += c["vol"]
    if not spreads:
        return None
    fill = []
    for h, vol in hours.items():
        q = quote_at(base, int((ko - timedelta(hours=h)).timestamp()))
        if q:
            fill.append(1.0 if vol * X_SHARE >= STAKE_USD / q["mid"] else 0.0)
    qk = quote_at(base, int(ko.timestamp()))
    out = {"ticker": m["ticker"], "event": m.get("event_ticker") or m["ticker"],
           "spread_c": 100 * statistics.median(spreads),
           "vol_hr": statistics.median(hours.values()) if hours else 0.0,
           "oi_ko": qk["oi"] if qk else None,
           "fill_share": statistics.mean(fill) if fill else None}
    sport = sport_of(series_of(m["ticker"]))
    if sport == "NFL":
        rep = friday_report(ko)
        if rep and c60:
            out["report_move"] = move(c60, rep, timedelta(minutes=60))
            out["report_placebo"] = move(c60, rep - timedelta(hours=24), timedelta(minutes=60))
        late = ko - timedelta(minutes=90)
    else:
        late = ko - timedelta(minutes=30)
    if c1:
        out["late_move"] = move(c1, late, timedelta(minutes=25))
        out["late_placebo"] = move(c1, late - timedelta(minutes=60), timedelta(minutes=25))
    return out


def _stat(vals, how):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return statistics.median(vals) if how == "median" else statistics.mean(vals)


def boot(rows: list, key: str, how: str, b: int = B, seed: int = SEED):
    by_ev = defaultdict(list)
    for r in rows:
        if r.get(key) is not None:
            by_ev[r["event"]].append(r[key])
    evs = sorted(by_ev)
    if not evs:
        return None
    point = _stat([v for e in evs for v in by_ev[e]], how)
    rng = random.Random(seed)
    sims = sorted(_stat([v for e in (rng.choice(evs) for _ in evs) for v in by_ev[e]], how) for _ in range(b))
    return {"est": point, "lo": sims[int(0.025 * b)], "hi": sims[int(0.975 * b) - 1], "n_mkts": sum(map(len, by_ev.values())),
            "n_events": len(evs)}


def summarize(markets: dict, candles: dict, b: int = B) -> dict:
    fam = defaultdict(list)
    excluded = defaultdict(int)
    for t, m in markets.items():
        c1, c60 = candles.get((t, 1), []), candles.get((t, 60), [])
        if not (c1 or c60):
            continue
        s = series_of(t)
        if not analysed(m):
            excluded[s] += 1
            continue
        r = per_market(m, c1, c60)
        if r:
            fam[s].append(r)
    out = {}
    for s, rows in sorted(fam.items()):
        d = {"sport": sport_of(s), "n_markets": len(rows), "n_events": len({r["event"] for r in rows}),
             "custody_excluded": excluded.get(s, 0)}
        for key, how in (("spread_c", "median"), ("vol_hr", "median"), ("oi_ko", "median"), ("fill_share", "mean"),
                         ("report_move", "median"), ("report_placebo", "median"), ("late_move", "median"),
                         ("late_placebo", "median")):
            d[key] = boot(rows, key, how, b)
        out[s] = d
    return out


def rank(summary: dict) -> list:
    """Thinnest first: widest median spread, ties broken by lower hourly volume."""
    def k(item):
        s, d = item
        return (-(d["spread_c"] or {}).get("est", 0), (d["vol_hr"] or {}).get("est", 0))
    return [s for s, _ in sorted(summary.items(), key=k)]


def _ci(x, fmt="{:.2f}"):
    if not x:
        return "n/a"
    return f"{fmt.format(x['est'])} [{fmt.format(x['lo'])}, {fmt.format(x['hi'])}]"


def render(summary: dict, order: list) -> str:
    L = ["| Rank | Family | mkts / events | spread ¢ [CI] | vol/hr [CI] | OI at ko [CI] | fillable-hour share [CI] | "
         "report move vs placebo | late move vs placebo |", "|" + "---|" * 9]
    for i, s in enumerate(order, 1):
        d = summary[s]
        rep = (f"{_ci(d['report_move'], '{:.3f}')} vs {_ci(d['report_placebo'], '{:.3f}')}" if d["sport"] == "NFL" else "n/a (NBA)")
        L.append(f"| {i} | {s}{' (game ML)' if s in GAME_FAMILY.values() else ''} | {d['n_markets']} / {d['n_events']} | "
                 f"{_ci(d['spread_c'], '{:.1f}')} | {_ci(d['vol_hr'], '{:.0f}')} | {_ci(d['oi_ko'], '{:.0f}')} | "
                 f"{_ci(d['fill_share'])} | {rep} | {_ci(d['late_move'], '{:.3f}')} vs {_ci(d['late_placebo'], '{:.3f}')} |")
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--store", nargs="+", required=True, help="store dirs holding raw_*.jsonl")
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    a = ap.parse_args(argv)
    paths = sorted(p for d in a.store for p in glob.glob(str(Path(d) / "raw_*.jsonl")))
    markets, candles = load(paths)
    summ = summarize(markets, candles)
    order = rank(summ)
    Path(a.out_json).write_text(json.dumps({"rank": order, "families": summ, "files": [Path(p).name for p in paths],
                                            "rules": {"stake_usd": STAKE_USD, "x_share": X_SHARE, "B": B, "seed": SEED}},
                                           indent=1, sort_keys=True))
    Path(a.out_md).write_text(render(summ, order))
    print(render(summ, order))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
