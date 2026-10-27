"""W90.3 core: follow-vs-fade P&L after pre-game moves (Strategy J), net of half-spreads and the k007 fee.

A *signal* is a mid move >= 3c over a 40-80 min look-back (archive, ~20-min cadence) or one hourly step (candles).
Entry is at the NEXT snapshot's quote, in the direction of the move (follow) or against it (fade). Exits: +1h, +3h
(sold at the later snapshot's bid / 1-ask) or settlement. Both legs pay k007. Applies to pre-game two-sided quotes;
does not apply to in-play markets or to one-sided books (those snapshots are dropped).
"""
from __future__ import annotations

import math
import os
import sys
from collections import defaultdict
from datetime import datetime
from statistics import NormalDist
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
from prediction_market_bot.quant.inference import benjamini_hochberg, cluster_bootstrap  # noqa: E402
from prediction_market_bot.quant.money import fee_k007  # noqa: E402

ET = ZoneInfo("America/New_York")
_N = NormalDist()
SEED = 20261027
MIN_GAMES = 30
BH_Q = 0.10
BUCKETS = ((0.03, 0.05, "3-5c"), (0.05, 0.10, "5-10c"), (0.10, 9.0, "10c+"))
HOLDS = ("1h", "3h", "settle")
H = 3600.0
LOCKOUT = 3 * H  # one signal per ticker per 3h


def size_bucket(a: float):
    for lo, hi, lab in BUCKETS:
        if lo <= a < hi:
            return lab
    return None


def tta_tier(h: float) -> str:
    return "T>24h" if h >= 24 else "T6-24h" if h >= 6 else "T2-6h" if h >= 2 else "T0-2h"


def side_leg_pnl(side: str, entry: tuple, exit_: tuple | None, y: float | None) -> float:
    """Per-contract net P&L of one side. entry=(bid, ask) YES quote. exit_=(bid, ask) at the later snapshot, or
    None to hold to settlement outcome y (1.0 = YES). YES enters at the ask, NO at 1-bid."""
    eb, ea = entry
    if side == "yes":
        q = ea
        if exit_ is None:
            return y - q - fee_k007(q)
        v = exit_[0]
    else:
        q = 1.0 - eb
        if exit_ is None:
            return (1.0 - y) - q - fee_k007(q)
        v = 1.0 - exit_[1]
    return v - q - fee_k007(q) - fee_k007(v)


def find_signals(pts: list, start: float, lb: tuple = (2400.0, 4800.0), step_max: float = 2700.0,
                 hold_tol: float = 1500.0) -> list:
    """pts: sorted [(ts, bid, ask)] two-sided snapshots. Returns signal dicts (follow/fade net per hold).
    lb = accepted look-back span; step_max = max gap from signal to entry snapshot; hold_tol = slack on the hold."""
    out = []
    mids = [(b + a) / 2.0 for _, b, a in pts]
    i, n = 1, len(pts)
    while i < n - 1:
        ts = pts[i][0]
        if ts >= start:
            break
        j = next((k for k in range(i - 1, -1, -1) if lb[0] <= ts - pts[k][0] <= lb[1]), None)
        if j is None:
            i += 1
            continue
        d = mids[i] - mids[j]
        lab = size_bucket(abs(d))
        e = i + 1
        if lab is None or pts[e][0] - ts > step_max or pts[e][0] >= start:
            i += 1
            continue
        sgn = 1 if d > 0 else -1
        entry = (pts[e][1], pts[e][2])
        sig = {"ts": ts, "entry_ts": pts[e][0], "dir": sgn, "size": lab, "move": abs(d), "hs": (entry[1] - entry[0]) / 2.0,
               "tta_h": (start - ts) / H, "look_ts": pts[j][0], "ex": {}}
        for hold, secs in (("1h", H), ("3h", 3 * H)):
            x = next((k for k in range(e + 1, n) if pts[k][0] - pts[e][0] >= secs), None)
            if x is not None and pts[x][0] - pts[e][0] <= secs + hold_tol and pts[x][0] < start:
                sig["ex"][hold] = (pts[x][1], pts[x][2], (mids[x] - mids[e]) * sgn)
        sig["entry"] = entry
        sig["entry_mid"] = mids[e]
        out.append(sig)
        nxt = next((k for k in range(i + 1, n) if pts[k][0] - ts >= LOCKOUT), n)
        i = nxt
    return out


def realize(sig: dict, y: float | None) -> dict:
    """follow / fade / gross by hold for one signal. Follow = side of the move (up -> YES)."""
    f_side, a_side = ("yes", "no") if sig["dir"] > 0 else ("no", "yes")
    res = {}
    for hold in HOLDS:
        if hold == "settle":
            if y is None:
                continue
            ex = None
            gross = (y - sig["entry_mid"]) * sig["dir"]
        else:
            if hold not in sig["ex"]:
                continue
            ex = sig["ex"][hold][:2]
            gross = sig["ex"][hold][2]
        res[hold] = {"gross": gross,
                     "follow": side_leg_pnl(f_side, sig["entry"], ex, y),
                     "fade": side_leg_pnl(a_side, sig["entry"], ex, y)}
    return res


# ---------------------------------------------------------------- news proxy (calendar, NOT true report times)
def _iv_et(dt_date, h0, m0, h1, m1):
    a = datetime(dt_date.year, dt_date.month, dt_date.day, h0, m0, tzinfo=ET).timestamp()
    b = datetime(dt_date.year, dt_date.month, dt_date.day, h1, m1, tzinfo=ET).timestamp()
    return (a, b)


def news_intervals(sport: str, start: float) -> list:
    """Scheduled public-news windows before `start` (epoch). A CALENDAR PROXY -- not observed report timestamps
    (those are not archived; see GG filed with this block). MLB: lineup posting [start-4h, start-1.5h]. NFL: Wed-Fri
    17:00-18:30 ET practice/injury reports of the game week + inactives [start-1.75h, start-1.25h]. NBA: 17:00-18:30 ET
    prior-day report, game-day 13:00-14:30 and 17:00-18:30 ET updates, final [start-1.25h, start-0.5h]. NHL: game-day
    morning-skate lineup news 11:00-13:00 ET and final [start-1.25h, start-0.5h]."""
    from datetime import timedelta
    gd = datetime.fromtimestamp(start, ET).date()
    iv = []
    if sport == "mlb":
        iv.append((start - 4 * H, start - 1.5 * H))
    elif sport == "nfl":
        for k in range(1, 6):
            d = gd - timedelta(days=k)
            if d.weekday() in (2, 3, 4):
                iv.append(_iv_et(d, 17, 0, 18, 30))
        iv.append((start - 1.75 * H, start - 1.25 * H))
    elif sport == "nba":
        iv += [_iv_et(gd - timedelta(days=1), 17, 0, 18, 30), _iv_et(gd, 13, 0, 14, 30), _iv_et(gd, 17, 0, 18, 30),
               (start - 1.25 * H, start - 0.5 * H)]
    elif sport == "nhl":
        iv += [_iv_et(gd, 11, 0, 13, 0), (start - 1.25 * H, start - 0.5 * H)]
    return [(a, b) for a, b in iv if b <= start]


def news_flag(sport: str, start: float, t0: float, t1: float) -> str:
    """'news' if the move window (t0, t1] overlaps a scheduled-news window, else 'quiet'."""
    return "news" if any(a < t1 and b > t0 for a, b in news_intervals(sport, start)) else "quiet"


# ---------------------------------------------------------------- statistics
def cell_stats(rows: list, key: str, boot: int = 600) -> dict:
    """rows: dicts with game, gross, follow, fade. Game-clustered net mean + 95% interval + two-sided cluster z for
    `key` ('follow' or 'fade'); testable only with >= MIN_GAMES games."""
    games = defaultdict(list)
    for r in rows:
        games[r["game"]].append(r[key])
    n = sum(len(v) for v in games.values())
    g = len(games)
    mean, lo, hi = cluster_bootstrap(games, b=boot, seed=SEED) if g >= 2 else (sum(sum(v) for v in games.values()) / n, float("nan"), float("nan"))
    out = {"n": n, "games": g, "gross": sum(r["gross"] for r in rows) / n, "net": mean, "lo": lo, "hi": hi,
           "p": None, "testable": g >= MIN_GAMES}
    if g >= MIN_GAMES:
        s2 = sum((sum(v) - len(v) * mean) ** 2 for v in games.values())
        se = math.sqrt(s2) / n
        if se > 0:
            out["z"] = mean / se
            out["p"] = 2 * (1 - _N.cdf(abs(mean / se)))
    return out


def bh(cells: dict, q: float = BH_Q) -> dict:
    keys = [k for k, c in cells.items() if c["p"] is not None]
    flags = benjamini_hochberg([cells[k]["p"] for k in keys], q) if keys else []
    for c in cells.values():
        c["bh"] = False
    for k, f in zip(keys, flags):
        cells[k]["bh"] = bool(f)
    return {"tested": len(keys), "flagged": int(sum(flags)), "q": q}
