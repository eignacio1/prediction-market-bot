"""W110.5 retro-route: score settled shadow rows by ARM (ride/fade/model-fade/momentum/no bet) per leaf, net after
exact taker fee, fit on the earlier 70% of games and tested on the later 30%. Spec: 12_EXPLORATORY/retro_route/SPEC.md."""
from __future__ import annotations

import random
from collections import defaultdict
from typing import Iterable

from prediction_market_bot.quant.money import fee

ARMS = ("RIDE", "FADE", "MODEL_FADE", "MOMENTUM")
MIN_FIT_ROWS, MIN_FIT_GAMES = 60, 20
MIN_TEST_GAMES, DRAFT_TEST_GAMES = 10, 15
FLAT_BAND = 0.005
BOOT_N, BOOT_SEED, ALPHA, BH_Q = 2000, 110, 0.10, 0.10
FAV_BINS = (0.35, 0.5, 0.65, 0.8)


def _series(ticker: str) -> str:
    return ticker.split("-")[0]


def side_net(row: dict, side: str) -> float:
    """Net P&L per contract for buying `side` at the taker price, held to settlement (y in 0, .5, 1)."""
    y = float(row["y"])
    s = _series(row["market_ticker"])
    if side == "YES":
        q = float(row["yes_ask"])
        return y - q - fee(s, q, 1)
    q = 1.0 - float(row["yes_bid"])
    return (1.0 - y) - q - fee(s, q, 1)


def game_id(row: dict) -> str:
    ev = row["event_ticker"]
    return row["sport"] + ":" + (ev.split("-", 1)[1] if "-" in ev else ev)


def dedupe(rows: Iterable[dict]) -> list[dict]:
    """One row per (market_ticker, run_id); MONEYLINE keeps the higher-mid ticker per (event, run_id)."""
    seen: dict = {}
    for r in rows:
        if r.get("yes_bid") is None or r.get("yes_ask") is None or r.get("y") is None:
            continue
        if not (0.0 < float(r["yes_bid"]) < float(r["yes_ask"]) < 1.0):  # two-sided, uncrossed quote only
            continue
        k = (r["market_ticker"], r["run_id"])
        seen.setdefault(k, r)
    out: dict = {}
    for r in seen.values():
        if r["market_type"].endswith("MONEYLINE"):
            k = (r["event_ticker"], r["run_id"])
            if k not in out or float(r["mid"]) > float(out[k]["mid"]):
                out[k] = r
        else:
            out[(r["market_ticker"], r["run_id"])] = r
    return list(out.values())


def add_moves(rows: list[dict]) -> None:
    """Annotate `move` = mid minus the same ticker's previous row mid (None when first), and `move_open` vs first row."""
    by = defaultdict(list)
    for r in rows:
        by[r["market_ticker"]].append(r)
    for lst in by.values():
        lst.sort(key=lambda r: r["ts_utc"])
        first = float(lst[0]["mid"])
        prev = None
        for r in lst:
            m = float(r["mid"])
            r["move"] = None if prev is None else m - prev
            r["move_open"] = None if prev is None else m - first
            prev = m


def fav_side(r: dict) -> str:
    return "YES" if float(r["mid"]) >= 0.5 else "NO"


def fav_price(r: dict) -> float:
    m = float(r["mid"])
    return m if m >= 0.5 else 1.0 - m


def _bin(v: float, edges=FAV_BINS) -> int:
    return sum(v >= e for e in edges)


def move_bin(r: dict) -> str:
    m = r.get("move")
    if m is None:
        return "na"
    return "up" if m >= FLAT_BAND else "down" if m <= -FLAT_BAND else "flat"


def leaf_key(r: dict) -> tuple:
    return (r["sport"], r["market_type"], r["band"], _bin(fav_price(r)), move_bin(r))


def arm_nets(r: dict) -> dict:
    """Net per contract by arm for this row (None = the arm takes no position on this row)."""
    fs = fav_side(r)
    other = "NO" if fs == "YES" else "YES"
    out = {"RIDE": side_net(r, fs), "FADE": side_net(r, other), "MODEL_FADE": None, "MOMENTUM": None}
    p = r.get("p_yes")
    if p is not None:
        ey, en = side_net({**r, "y": float(p)}, "YES"), side_net({**r, "y": float(p)}, "NO")
        if max(ey, en) > 0:
            out["MODEL_FADE"] = side_net(r, "YES" if ey >= en else "NO")
    m = r.get("move")
    if m is not None and abs(m) >= FLAT_BAND:
        out["MOMENTUM"] = side_net(r, "YES" if m > 0 else "NO")
    return out


def split_games(rows: list[dict], frac: float = 0.7) -> tuple[set, set]:
    first = {}
    for r in rows:
        g = game_id(r)
        t = r["start_time_utc"]
        if g not in first or t < first[g]:
            first[g] = t
    order = sorted(first, key=lambda g: (first[g], g))
    cut = int(len(order) * frac)
    return set(order[:cut]), set(order[cut:])


def boot_ci(vals_by_game: dict, n: int = BOOT_N, seed: int = BOOT_SEED, alpha: float = ALPHA):
    """Game-clustered bootstrap of the row-pooled mean. Returns (mean, lo, hi, p_one_sided_gt0)."""
    games = list(vals_by_game)
    tot = sum(sum(v) for v in vals_by_game.values())
    cnt = sum(len(v) for v in vals_by_game.values())
    mean = tot / cnt
    rng = random.Random(seed)
    sums = [(sum(vals_by_game[g]), len(vals_by_game[g])) for g in games]
    ms = []
    k = len(games)
    for _ in range(n):
        s = c = 0
        for _ in range(k):
            a, b = sums[rng.randrange(k)]
            s += a
            c += b
        ms.append(s / c)
    ms.sort()
    lo, hi = ms[int(n * alpha / 2)], ms[min(n - 1, int(n * (1 - alpha / 2)))]
    p = (sum(1 for m in ms if m <= 0) + 1) / (n + 1)
    return mean, lo, hi, p


def bh_reject(pvals: dict, q: float = BH_Q) -> set:
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    kmax = 0
    for i, (_, p) in enumerate(items, 1):
        if p <= q * i / m:
            kmax = i
    return {k for k, _ in items[:kmax]}


def route(rows: list[dict]) -> dict:
    """Fit/test. Returns {'leaves': [...], 'fit_games': n, 'test_games': n}. Each leaf record carries the fit arm table,
    chosen arm, held-out mean/CI/n for that arm (and for RIDE as the reference), BH flag and draft flag."""
    fit_g, test_g = split_games(rows)
    fit, test = defaultdict(list), defaultdict(list)
    for r in rows:
        (fit if game_id(r) in fit_g else test)[leaf_key(r)].append(r)
    leaves, pv = [], {}
    for k in sorted(set(fit) | set(test)):
        f, t = fit.get(k, []), test.get(k, [])
        fg = len({game_id(r) for r in f})
        rec = {"leaf": k, "fit_rows": len(f), "fit_games": fg, "arm": "NO_BET", "thin": False,
               "fit": {}, "test_rows": len(t), "test_games": len({game_id(r) for r in t})}
        if len(f) < MIN_FIT_ROWS or fg < MIN_FIT_GAMES:
            rec["thin"] = True
        else:
            for a in ARMS:
                v = [x for x in (arm_nets(r)[a] for r in f) if x is not None]
                if v:
                    rec["fit"][a] = (sum(v) / len(v), len(v))
            best = max(((m, a) for a, (m, n) in rec["fit"].items() if n >= MIN_FIT_ROWS), default=None)
            if best and best[0] > 0:
                rec["arm"] = best[1]
        if rec["arm"] != "NO_BET" and rec["test_games"] >= MIN_TEST_GAMES:
            by = defaultdict(list)
            for r in t:
                x = arm_nets(r)[rec["arm"]]
                if x is not None:
                    by[game_id(r)].append(x)
            if len(by) >= MIN_TEST_GAMES:
                mean, lo, hi, p = boot_ci(by)
                rec.update(test_mean=mean, test_lo=lo, test_hi=hi, test_p=p,
                           test_n=sum(len(v) for v in by.values()), test_n_games=len(by))
                pv[k] = p
        leaves.append(rec)
    keep = bh_reject(pv) if pv else set()
    for rec in leaves:
        rec["bh"] = rec["leaf"] in keep
        rec["draft"] = bool(rec["bh"] and rec.get("test_lo", -1) > 0 and rec.get("test_n_games", 0) >= DRAFT_TEST_GAMES)
    return {"leaves": leaves, "fit_games": len(fit_g), "test_games": len(test_g)}


def whole_arm_table(rows: list[dict], games: set) -> dict:
    """Unrouted reference: each arm taken on every row in `games`, grouped by (sport, market_type)."""
    out = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for r in rows:
        g = game_id(r)
        if g not in games:
            continue
        for a, x in arm_nets(r).items():
            if x is not None:
                out[(r["sport"], r["market_type"])][a][g].append(x)
    return out
