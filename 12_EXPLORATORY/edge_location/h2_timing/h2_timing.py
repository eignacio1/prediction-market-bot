#!/usr/bin/env python3
"""H2 timing (W123.2): closing-line value of arm orders, and is the drift to the close predictable?

READ-ONLY over the price archive, the order log and the shadow ledgers. Definitions are frozen in OPERATIONALIZATION.md
(committed before any result was read). Pure Python 3.9 (no numpy / pandas on the box or the CI image).

Applies when: a price series has snapshots near known start times and the unit of independence is the game.
Does not apply: markets with no start time, or with no qualifying snapshot at the point asked for (they are counted, not imputed).
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import math
import os
import random
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence, Tuple

MAX_SPREAD = 0.10
CLOSE_WINDOW_H = 2.0
EARLY = {"24h": (24.0, 2.0), "6h": (6.0, 1.0)}  # target hours, half-window
SIGNAL_TOL_S = 3600.0
BOOT = 2000
LEVEL = 0.90

_TS_CACHE: Dict[str, float] = {}


def ts_epoch(s: str) -> Optional[float]:
    """Tolerant ISO parse to epoch seconds (box is Python 3.9: no trailing Z, 5-digit fractions)."""
    if not s:
        return None
    v = _TS_CACHE.get(s)
    if v is not None:
        return v
    t = s.strip()
    if t.endswith("Z"):
        t = t[:-1] + "+00:00"
    main, tz = t, ""
    for sep in ("+", "-"):
        i = t.rfind(sep)
        if i > 10:
            main, tz = t[:i], t[i:]
            break
    frac = 0.0
    if "." in main:
        main, f = main.split(".", 1)
        frac = float("0." + f) if f.isdigit() else 0.0
    try:
        dt = datetime.strptime(main, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return None
    off = 0
    if tz:
        sign = 1 if tz[0] == "+" else -1
        hh, mm = tz[1:].split(":") if ":" in tz else (tz[1:3], tz[3:5] or "0")
        off = sign * (int(hh) * 3600 + int(mm) * 60)
    v = dt.replace(tzinfo=timezone.utc).timestamp() - off + frac
    _TS_CACHE[s] = v
    return v


def game_key(sport: str, event_ticker: str) -> str:
    parts = (event_ticker or "").split("-")
    return "%s|%s" % (sport, parts[1] if len(parts) > 1 else event_ticker)


# ---------------------------------------------------------------- statistics
def cluster_boot_mean(groups: Dict[str, List[float]], rng: random.Random, b: int = BOOT) -> Tuple[float, float, float, int, int]:
    """Mean of all values, with a game-clustered percentile interval. Returns mean, lo, hi, n_values, n_games."""
    keys = list(groups)
    stats = [(len(groups[k]), sum(groups[k])) for k in keys]
    n = sum(s[0] for s in stats)
    if n == 0:
        return (float("nan"),) * 3 + (0, 0)
    mean = sum(s[1] for s in stats) / n
    g = len(keys)
    reps: List[float] = []
    for _ in range(b):
        sn = ss = 0.0
        for _j in range(g):
            c, t = stats[rng.randrange(g)]
            sn += c
            ss += t
        if sn:
            reps.append(ss / sn)
    reps.sort()
    lo = reps[int((1 - LEVEL) / 2 * len(reps))]
    hi = reps[min(len(reps) - 1, int((1 + LEVEL) / 2 * len(reps)))]
    return mean, lo, hi, n, g


def solve(a: List[List[float]], y: List[float]) -> Optional[List[float]]:
    """Gaussian elimination with partial pivoting; None when singular."""
    n = len(y)
    m = [row[:] + [y[i]] for i, row in enumerate(a)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(m[r][c]))
        if abs(m[p][c]) < 1e-12:
            return None
        m[c], m[p] = m[p], m[c]
        for r in range(c + 1, n):
            f = m[r][c] / m[c][c]
            for k in range(c, n + 1):
                m[r][k] -= f * m[c][k]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        x[r] = (m[r][n] - sum(m[r][k] * x[k] for k in range(r + 1, n))) / m[r][r]
    return x


def _game_xtx(rows: Sequence[Tuple[str, List[float], float]]) -> Dict[str, Tuple[List[List[float]], List[float], int]]:
    out: Dict[str, Tuple[List[List[float]], List[float], int]] = {}
    for g, x, y in rows:
        k = len(x)
        if g not in out:
            out[g] = ([[0.0] * k for _ in range(k)], [0.0] * k, 0)
        xtx, xty, n = out[g]
        for i in range(k):
            xty[i] += x[i] * y
            for j in range(k):
                xtx[i][j] += x[i] * x[j]
        out[g] = (xtx, xty, n + 1)
    return out


def ols_cluster(rows: Sequence[Tuple[str, List[float], float]], idx: int, rng: random.Random, b: int = BOOT):
    """OLS (x already carries the intercept), game-clustered bootstrap for coefficient `idx`.
    Returns (coef, lo, hi, n_rows, n_games) or None when the design is singular."""
    per = _game_xtx(rows)
    keys = list(per)
    if not keys:
        return None
    k = len(rows[0][1])

    def fit(sel: Sequence[str]):
        xtx = [[0.0] * k for _ in range(k)]
        xty = [0.0] * k
        for g in sel:
            gx, gy, _ = per[g]
            for i in range(k):
                xty[i] += gy[i]
                for j in range(k):
                    xtx[i][j] += gx[i][j]
        return solve(xtx, xty)

    beta = fit(keys)
    if beta is None:
        return None
    reps: List[float] = []
    g = len(keys)
    for _ in range(b):
        r = fit([keys[rng.randrange(g)] for _ in range(g)])
        if r is not None:
            reps.append(r[idx])
    if len(reps) < b // 2:
        return None
    reps.sort()
    lo = reps[int((1 - LEVEL) / 2 * len(reps))]
    hi = reps[min(len(reps) - 1, int((1 + LEVEL) / 2 * len(reps)))]
    return beta[idx], lo, hi, len(rows), g


def fee(p: float) -> float:
    return 0.07 * p * (1.0 - p)


# ---------------------------------------------------------------- data loading
def load_jsonl(path: str):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if isinstance(r, dict):
                yield r


class Point:
    __slots__ = ("ts", "mid", "spread", "dist")

    def __init__(self, ts: float, mid: float, spread: float, dist: float):
        self.ts, self.mid, self.spread, self.dist = ts, mid, spread, dist


def scan_archive(archive_dir: str, starts: Dict[str, float], first_day: str):
    """One pass over the price archive. For every ticker with a known start keeps, online:
    the snapshot nearest 24 h and 6 h before start (inside the windows) and the last one at or before start (inside 2 h)."""
    state: Dict[str, Dict[str, Point]] = {}
    files = sorted(glob.glob(os.path.join(archive_dir, "prices_*.jsonl")) + glob.glob(os.path.join(archive_dir, "prices_*.jsonl.gz")))
    seen_days = set()
    for f in files:
        day = os.path.basename(f).split("_")[1][:10]
        if day < first_day or day in seen_days:
            continue
        if f.endswith(".gz") and os.path.exists(f[:-3]):
            continue  # same day stored plain and compressed
        seen_days.add(day)
        for r in load_jsonl(f):
            t = r.get("ticker")
            st = starts.get(t)
            if st is None:
                continue
            ts = ts_epoch(r.get("run_ts", ""))
            if ts is None:
                continue
            h = (st - ts) / 3600.0
            if h < 0 or h > 26.5:
                continue
            try:
                bid, ask = float(r["yes_bid"]), float(r["yes_ask"])
            except (KeyError, TypeError, ValueError):
                continue
            if not (bid > 0 and ask > bid and ask - bid <= MAX_SPREAD + 1e-9):
                continue
            mid, sp = (bid + ask) / 2.0, ask - bid
            s = state.setdefault(t, {})
            if h <= CLOSE_WINDOW_H:
                c = s.get("close")
                if c is None or ts > c.ts:
                    s["close"] = Point(ts, mid, sp, 0.0)
            for name, (target, half) in EARLY.items():
                d = abs(h - target)
                if d <= half:
                    c = s.get(name)
                    if c is None or d < c.dist:
                        s[name] = Point(ts, mid, sp, d)
    return state


# ---------------------------------------------------------------- Part A
def bucket(h: float) -> str:
    for hi, name in ((1, "<1h"), (6, "1-6h"), (24, "6-24h"), (48, "24-48h")):
        if h < hi:
            return name
    return "48h+"


BUCKETS = ["<1h", "1-6h", "6-24h", "24-48h", "48h+"]


def part_a(orders: List[dict], starts_by_event: Dict[str, float], state, now: float, rng: random.Random):
    cells: Dict[Tuple[str, str], Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    drop = defaultdict(int)
    detail = []
    for o in orders:
        ev = o.get("event_ticker", "")
        st = ts_epoch(o.get("start_time_utc") or "") or starts_by_event.get(ev)
        if st is None:
            drop["no_start_time"] += 1
            continue
        if st > now:
            drop["game_not_started"] += 1
            continue
        c = (state.get(o.get("ticker")) or {}).get("close")
        if c is None:
            drop["no_close_snapshot"] += 1
            continue
        if o.get("side") not in ("yes", "no") or o.get("entry_price") is None:
            drop["bad_order_row"] += 1
            continue
        h = o.get("hours_to_start")
        if h is None:
            sub = ts_epoch(o.get("submit_ts_utc") or o.get("ts") or "")
            if sub is None:
                drop["no_submit_time"] += 1
                continue
            h = (st - sub) / 3600.0
        close_side = c.mid if o["side"] == "yes" else 1.0 - c.mid
        clv = close_side - float(o["entry_price"])
        arm = o.get("arm") or "?"
        g = game_key(o.get("sport", "?"), ev)
        cells[(arm, bucket(float(h)))][g].append(clv)
        cells[(arm, "all")][g].append(clv)
        cells[("ALL", bucket(float(h)))][g].append(clv)
        cells[("ALL", "all")][g].append(clv)
        detail.append((arm, bucket(float(h)), clv))
    table = []
    for (arm, bk), groups in sorted(cells.items()):
        m, lo, hi, n, g = cluster_boot_mean(groups, rng)
        table.append({"arm": arm, "bucket": bk, "orders": n, "games": g, "clv": m, "lo": lo, "hi": hi})
    return table, dict(drop)


# ---------------------------------------------------------------- Part B
def build_drift_rows(shadow: List[dict], state, horizon: str):
    """One row per market: drift, signal, arm, family, game, start. Nearest shadow row to the early snapshot (within 1 h)."""
    by_market: Dict[str, List[Tuple[float, dict]]] = defaultdict(list)
    for r in shadow:
        ts = ts_epoch(r.get("ts_utc", ""))
        if ts is not None and r.get("p_yes") is not None:
            by_market[r["market_ticker"]].append((ts, r))
    rows, drop = [], defaultdict(int)
    for t, lst in by_market.items():
        s = state.get(t)
        if not s or "close" not in s:
            drop["no_close"] += 1
            continue
        e = s.get(horizon)
        if e is None:
            drop["no_early_snapshot"] += 1
            continue
        ts, r = min(lst, key=lambda x: abs(x[0] - e.ts))
        if abs(ts - e.ts) > SIGNAL_TOL_S:
            drop["no_shadow_row_within_1h"] += 1
            continue
        st = ts_epoch(r.get("start_time_utc") or "")
        rows.append({
            "ticker": t, "game": game_key(r["sport"], r["event_ticker"]), "start": st, "family": r["market_type"],
            "arm": r.get("arm") or "NONE", "signal": float(r["p_yes"]) - e.mid, "drift": s["close"].mid - e.mid,
            "early_mid": e.mid, "spread": e.spread, "sport": r["sport"],
        })
    return rows, dict(drop)


def split_by_date(rows: List[dict]):
    games: Dict[str, float] = {}
    for r in rows:
        games[r["game"]] = min(games.get(r["game"], 9e18), r["start"] or 0)
    order = sorted(games, key=lambda g: games[g])
    cut = int(len(order) * 2 / 3)
    train = set(order[:cut])
    return [r for r in rows if r["game"] in train], [r for r in rows if r["game"] not in train]


def analyse_horizon(rows: List[dict], rng: random.Random):
    train, test = split_by_date(rows)
    out = {"rows": len(rows), "games": len({r["game"] for r in rows}), "train_rows": len(train), "test_rows": len(test),
           "train_games": len({r["game"] for r in train}), "test_games": len({r["game"] for r in test})}
    if len(test) < 30 or len({r["game"] for r in test}) < 8 or len(train) < 30:
        out["note"] = "too few held-out rows to fit"
        return out

    def design(rs, arms=None):
        return [(r["game"], [1.0, r["signal"]] + ([1.0 if r["arm"] == a else 0.0 for a in arms] if arms else []), r["drift"]) for r in rs]

    trf = ols_cluster(design(train), 1, rng)
    tef = ols_cluster(design(test), 1, rng)
    out["train_b"] = trf[:3] if trf else None
    out["test_b"] = tef[:3] if tef else None
    # implied CLV on the held-out third: trade in the direction of the signal at the early mid
    groups, gross_half, costs, costs_half = defaultdict(list), [], [], []
    for r in test:
        sgn = 1.0 if r["signal"] > 0 else -1.0
        groups[r["game"]].append(sgn * r["drift"])
    m, lo, hi, n, g = cluster_boot_mean(groups, rng)
    cost = sum(r["spread"] + fee(r["early_mid"]) for r in test) / len(test)
    cost_half = sum(r["spread"] / 2.0 + fee(r["early_mid"]) for r in test) / len(test)
    out["implied_clv"] = {"gross": m, "lo": lo, "hi": hi, "round_cost": cost, "half_spread_cost": cost_half,
                          "net_round": m - cost, "net_half": m - cost_half, "net_lo_round": lo - cost, "net_hi_round": hi - cost}
    mean_abs = sum(abs(r["signal"]) for r in test) / len(test)
    out["mean_abs_signal"] = mean_abs
    if tef:
        se = (tef[2] - tef[1]) / (2 * 1.645)
        b_be = cost / mean_abs if mean_abs else float("nan")
        out["breakeven_slope"] = b_be
        out["se_test_b"] = se
    # arm-adjusted model
    arms = sorted({r["arm"] for r in rows})
    ref = "NO_BET" if "NO_BET" in arms else arms[0]
    use = [a for a in arms if a != ref]
    arm_f = ols_cluster(design(test, use), 1, rng)
    out["test_b_arm_adjusted"] = arm_f[:3] if arm_f else None
    out["arm_ref"] = ref
    # per-arm test slopes (descriptive)
    per_arm = {}
    for a in arms:
        sub = [r for r in test if r["arm"] == a]
        if len(sub) >= 30 and len({r["game"] for r in sub}) >= 8:
            f = ols_cluster(design(sub), 1, rng)
            if f:
                per_arm[a] = {"b": f[0], "lo": f[1], "hi": f[2], "rows": f[3], "games": f[4]}
    out["per_arm_test_b"] = per_arm
    # mean drift (is there drift at all, unconditional)
    dg = defaultdict(list)
    for r in test:
        dg[r["game"]].append(r["drift"])
    out["mean_drift_test"] = cluster_boot_mean(dg, rng)[:3]
    return out


# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--orders", required=True)
    ap.add_argument("--shadow", required=True, help="gz jsonl of slim shadow rows")
    ap.add_argument("--archive", required=True)
    ap.add_argument("--first-day", default="2026-11-04")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=20261120)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    now = datetime.now(timezone.utc).timestamp()

    orders = [r for r in load_jsonl(a.orders) if r.get("event") == "arm_order"]
    shadow = list(load_jsonl(a.shadow))
    starts_by_event: Dict[str, float] = {}
    for r in shadow:
        st = ts_epoch(r.get("start_time_utc") or "")
        if st:
            starts_by_event[r["event_ticker"]] = st
    ticker_start: Dict[str, float] = {}
    for r in shadow:
        st = ts_epoch(r.get("start_time_utc") or "")
        if st:
            ticker_start[r["market_ticker"]] = st
    for o in orders:
        st = ts_epoch(o.get("start_time_utc") or "") or starts_by_event.get(o.get("event_ticker", ""))
        if st:
            ticker_start[o["ticker"]] = st
    state = scan_archive(a.archive, ticker_start, a.first_day)
    res = {"generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "n_orders_total": len(orders),
           "n_shadow_rows": len(shadow), "tickers_with_start": len(ticker_start), "tickers_with_any_snapshot": len(state)}
    table, drop = part_a(orders, starts_by_event, state, now, rng)
    res["part_a"], res["part_a_dropped"] = table, drop
    res["part_b"] = {}
    for hz in EARLY:
        rows, dr = build_drift_rows(shadow, state, hz)
        res["part_b"][hz] = analyse_horizon(rows, rng)
        res["part_b"][hz]["dropped"] = dr
        by_fam = defaultdict(list)
        for r in rows:
            by_fam[r["family"]].append(r)
        res["part_b"][hz]["families_rows"] = {k: len(v) for k, v in by_fam.items()}
    with open(a.out, "w") as fh:
        json.dump(res, fh, indent=1, default=lambda o: None)
    print("wrote", a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
