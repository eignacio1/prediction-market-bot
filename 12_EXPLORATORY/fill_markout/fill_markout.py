#!/usr/bin/env python3
"""W94.3 Part C: what a fill costs. Markout of resting (maker) fills, and of a taker entry at the quote.

Applies when: prices are held-side (YES -> yes quote, NO -> 1 - yes quote), the unit of independence is the game
(rows within a game are dependent, so every interval is a game-clustered bootstrap), and the question is whether the
"taker at the quote" entry the frozen forward tests assume (EXP-042 .. 045) escapes the adverse selection that
resting demo orders show (E3).
Read-only: reads the markout collector output, the demo policy log and the price/depth archive. Places nothing.

  Task 1  maker_report():   markouts after fill for the shadow books, by sport x arm x fill latency
  Task 2  taker_report():   for a taker at the quote, from consecutive archive snapshots: is the quote still there,
                            the markout of an immediate take (spread cost + drift), and the depth at the quote
  Known   simulate_book():  a simulated book with informed flow; maker markout is negative, a taker's drift is ~0
"""
from __future__ import annotations

import json
import math
import random
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from prediction_market_bot.quant.inference import cluster_bootstrap  # noqa: E402
sys.path.insert(0, str(REPO / "12_EXPLORATORY"))
from _fence import safe_out  # noqa: E402

HORIZONS = ("h1", "h5", "h30")
SNAP_MIN_GAP_S = 120     # closer than this is the same snapshot burst
SNAP_MAX_GAP_S = 1800    # farther than this is not "the next snapshot"
LATENCY_EDGES = ((60.0, "<=60s"), (600.0, "60s-10m"), (float("inf"), ">10m"))


def parse_ts(s: Any) -> Optional[datetime]:
    """Tolerant ISO parse for the box's Python 3.9 (no 'Z', variable fractional digits)."""
    if not s:
        return None
    t = re.sub(r"Z$", "+00:00", str(s).strip())
    m = re.match(r"^(.*?)(?:\.(\d+))?([+-]\d\d:\d\d)?$", t)
    if not m:
        return None
    head, frac, off = m.group(1), m.group(2) or "", m.group(3) or ""
    frac = ("." + frac[:6].ljust(6, "0")) if frac else ""
    try:
        d = datetime.fromisoformat(f"{head}{frac}{off}")
    except ValueError:
        return None
    return d if d.tzinfo else datetime.combine(d.date(), d.time(), tzinfo=timezone.utc)


def sport_of(ticker: str) -> str:
    for pre, name in (("KXNFL", "NFL"), ("KXNBA", "NBA"), ("KXNHL", "NHL"), ("KXMLB", "MLB")):
        if ticker.startswith(pre):
            return name
    return "OTHER"


def game_of(ticker: str) -> str:
    parts = ticker.split("-")
    return f"{sport_of(ticker)}|{parts[1]}" if len(parts) > 1 else ticker


def latency_bucket(sec: Optional[float]) -> str:
    if sec is None:
        return "unknown"
    for edge, name in LATENCY_EDGES:
        if sec <= edge:
            return name
    return ">10m"


def signed_markout(side: str, price: float, yes_mid_later: float) -> float:
    """Held-side mid later minus the held-side price paid: positive = the market moved toward the order.
    YES pays `price` for a yes contract; NO pays `price` (= 1 - yes quote) for a no contract."""
    held_mid = yes_mid_later if side == "YES" else 1.0 - yes_mid_later
    return held_mid - price


def summarize(rows: Iterable[dict], field: str, b: int = 2000) -> dict:
    """n rows, n games, mean and game-clustered 95% interval of `field` (None values skipped)."""
    by_game: Dict[str, List[float]] = defaultdict(list)
    for r in rows:
        v = r.get(field)
        if v is not None:
            by_game[r["game"]].append(float(v))
    n = sum(len(v) for v in by_game.values())
    if n == 0:
        return {"n": 0, "games": 0, "mean": None, "lo": None, "hi": None}
    mean, lo, hi = cluster_bootstrap(by_game, b=b)
    return {"n": n, "games": len(by_game), "mean": round(mean, 5), "lo": round(lo, 5), "hi": round(hi, 5)}


# ---------------------------------------------------------------- Task 1: maker markouts

def load_jsonl(path: Path) -> Iterable[dict]:
    with open(path) as fh:
        for line in fh:
            try:
                yield json.loads(line)
            except ValueError:
                continue


def order_times(policy_path: Path) -> Dict[str, datetime]:
    """order_id -> submit time, from the shadow_order events that succeeded."""
    out: Dict[str, datetime] = {}
    for r in load_jsonl(policy_path):
        if r.get("event") == "shadow_order" and r.get("ok") and r.get("order_id"):
            d = parse_ts(r.get("ts"))
            if d:
                out[r["order_id"]] = d
    return out


def attach_latency(markouts: Iterable[dict], submits: Dict[str, datetime]) -> List[dict]:
    rows = []
    for m in markouts:
        r = dict(m)
        fill, sub = parse_ts(r.get("fill_ts")), submits.get(r.get("order_id"))
        lat = (fill - sub).total_seconds() if fill and sub else None
        r["latency_s"] = lat if lat is None or lat >= 0 else None
        r["lat_bucket"] = latency_bucket(r["latency_s"])
        rows.append(r)
    return rows


def maker_report(rows: List[dict], b: int = 2000) -> dict:
    """Markout by sport x arm and by sport x fill-latency bucket. `control` rests until filled; `treatment`
    cancels after 60 s, so its fills are the quick ones (those that crossed or met an existing taker)."""
    rep: Dict[str, dict] = {}
    for label, keyf in (("sport_arm", lambda r: f"{r['sport']}|{r['arm']}"),
                        ("sport_latency", lambda r: f"{r['sport']}|{r['lat_bucket']}"),
                        ("all_latency", lambda r: f"ALL|{r['lat_bucket']}"),
                        ("all", lambda r: "ALL")):
        groups: Dict[str, List[dict]] = defaultdict(list)
        for r in rows:
            groups[keyf(r)].append(r)
        rep[label] = {k: {h: summarize(g, h, b) for h in HORIZONS} for k, g in sorted(groups.items())}
    return rep


# ---------------------------------------------------------------- Task 2: taker at the quote

def two_sided(rec: dict) -> Optional[Tuple[float, float]]:
    try:
        bid, ask = float(rec["yes_bid"]), float(rec["yes_ask"])
    except (KeyError, TypeError, ValueError):
        return None
    return (bid, ask) if 0.0 < bid < ask < 1.0 else None


def snapshot_pairs(archive_dir: Path, first_day: str, families: Tuple[str, ...]) -> Iterable[Tuple[dict, dict]]:
    """Consecutive snapshots of one ticker, SNAP_MIN_GAP_S..SNAP_MAX_GAP_S apart, both two-sided."""
    last: Dict[str, dict] = {}
    for path in sorted(archive_dir.glob("prices_20??-??-??.jsonl")):
        if path.name[7:17] < first_day:
            continue
        for rec in load_jsonl(path):
            tk = rec.get("ticker", "")
            if not tk.startswith(families) or rec.get("status") not in (None, "active"):
                continue
            ts = parse_ts(rec.get("run_ts"))
            q = two_sided(rec)
            prev = last.get(tk)
            if ts and q:
                rec["_ts"], rec["_q"] = ts, q
                if prev is not None:
                    gap = (ts - prev["_ts"]).total_seconds()
                    if SNAP_MIN_GAP_S <= gap <= SNAP_MAX_GAP_S:
                        yield prev, rec
                last[tk] = rec
            elif tk in last:
                del last[tk]  # a one-sided or missing snapshot breaks the chain


def take_row(prev: dict, nxt: dict, side: str) -> dict:
    """One immediate take at the quote in `prev`, valued at the mid of `nxt`."""
    bid, ask = prev["_q"]
    nbid, nask = nxt["_q"]
    mid_now, mid_next = (bid + ask) / 2, (nbid + nask) / 2
    price = ask if side == "YES" else 1.0 - bid
    held_mid_now = mid_now if side == "YES" else 1.0 - mid_now
    return {
        "game": game_of(prev["ticker"]), "sport": sport_of(prev["ticker"]), "side": side,
        "family": prev.get("series_ticker", ""), "price": price,
        # the quote is still there if the next snapshot offers the same or a better price to the same taker
        "still_there": 1.0 if (nask <= ask if side == "YES" else nbid >= bid) else 0.0,
        "markout": signed_markout(side, price, mid_next),
        "spread_cost": held_mid_now - price,                # known cost of crossing: -half-spread
        "drift": signed_markout(side, held_mid_now, mid_next),  # what the mid did after: the adverse-selection part
        "gap_s": (nxt["_ts"] - prev["_ts"]).total_seconds(),
    }


def price_bucket(p: float) -> str:
    return "<=10c" if p <= 0.10 else "10-30c" if p <= 0.30 else "30-70c" if p < 0.70 else "70-90c" if p < 0.90 else ">=90c"


def taker_report(archive_dir: Path, first_day: str, families: Tuple[str, ...], b: int = 1000) -> dict:
    rows: List[dict] = []
    for prev, nxt in snapshot_pairs(archive_dir, first_day, families):
        for side in ("YES", "NO"):
            rows.append(take_row(prev, nxt, side))
    rep: Dict[str, Any] = {"n_pairs": len(rows) // 2}
    for label, keyf in (("sport", lambda r: r["sport"]), ("sport_side", lambda r: f"{r['sport']}|{r['side']}"),
                        ("price_bucket", lambda r: price_bucket(r["price"])), ("all", lambda r: "ALL")):
        groups: Dict[str, List[dict]] = defaultdict(list)
        for r in rows:
            groups[keyf(r)].append(r)
        rep[label] = {k: {f: summarize(g, f, b) for f in ("still_there", "markout", "spread_cost", "drift")}
                      for k, g in sorted(groups.items())}
    return rep


def depth_report(archive_dir: Path, first_day: str, families: Tuple[str, ...], stake_usd: float = 1.0) -> dict:
    """Share of depth samples where the touch holds a flat stake, per taker side. A YES taker lifts the NO bids
    (top_of_book_contracts['no']); a NO taker lifts the YES bids (['yes'])."""
    tot, ok, sizes = defaultdict(int), defaultdict(int), defaultdict(list)
    for path in sorted(archive_dir.glob("depth_20??-??-??.jsonl")):
        if path.name[6:16] < first_day:
            continue
        for r in load_jsonl(path):
            tk = r.get("ticker", "")
            if not tk.startswith(families) or not r.get("usable"):
                continue
            mid = r["mid_cents"] / 100.0
            for side, price, key in (("YES", mid, "no"), ("NO", 1.0 - mid, "yes")):
                need = stake_usd / max(price, 0.01)
                top = float(r["top_of_book_contracts"][key])
                k = f"{sport_of(tk)}|{side}"
                tot[k] += 1
                ok[k] += top >= need
                sizes[k].append(top)
    out = {}
    for k in sorted(tot):
        s = sorted(sizes[k])
        out[k] = {"n": tot[k], "share_touch_holds_stake": round(ok[k] / tot[k], 4), "median_touch_contracts": s[len(s) // 2]}
    return out


# ---------------------------------------------------------------- Known answer: simulated book with informed flow

def simulate_book(n: int = 200_000, half_spread: float = 0.01, jump: float = 0.04, p_informed: float = 0.5,
                  p_uninformed: float = 0.5, seed: int = 7) -> dict:
    """Each step the mid is m. The next mid is m + e, e = +/-jump with equal odds. One market order arrives: with
    weight p_informed it knows e and trades with it (buys if e > 0), otherwise it is a coin-flip direction.
    A resting maker bid at m - h fills when the arrival SELLS; a resting maker ask at m + h fills when it BUYS.
    The maker's markout is (held-side mid after the step) - (fill price).
    A taker who lifts the ask at m + h at a random time, knowing nothing, has drift E[e] = 0 and markout -h.
    Closed form for the maker: h - jump * p_informed / (p_informed + p_uninformed)."""
    rng = random.Random(seed)
    w_inf = p_informed / (p_informed + p_uninformed)
    maker, taker, drift = [], [], []
    for _ in range(n):
        e = jump if rng.random() < 0.5 else -jump
        informed = rng.random() < w_inf
        buys = (e > 0) if informed else (rng.random() < 0.5)
        # an arriving buy lifts the maker's ask (maker sold at m+h: markout h - e); a sell hits the bid (e + h)
        maker.append(half_spread + (-e if buys else e))
        # an uninformed taker's own independent take at the ask
        taker.append(e - half_spread)
        drift.append(e)
    mean = lambda xs: sum(xs) / len(xs)  # noqa: E731
    def sd(xs: List[float]) -> float:
        m = mean(xs)
        return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))
    return {
        "maker_markout": mean(maker), "maker_markout_theory": half_spread - jump * w_inf,
        "maker_se": sd(maker) / math.sqrt(n),
        "taker_markout": mean(taker), "taker_markout_theory": -half_spread,
        "taker_drift": mean(drift), "taker_drift_se": sd(drift) / math.sqrt(n), "n": n,
    }


def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--markouts", type=Path, required=True)
    ap.add_argument("--policy", type=Path, required=True)
    ap.add_argument("--archive", type=Path, required=True)
    ap.add_argument("--first-day", default="2026-10-11")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    rows = attach_latency(load_jsonl(a.markouts), order_times(a.policy))
    fams = ("KXNFL", "KXNBA", "KXNHL", "KXMLB")
    rep = {
        "maker": maker_report(rows),
        "taker": taker_report(a.archive, a.first_day, fams),
        "depth": depth_report(a.archive, a.first_day, fams),
        "simulated": simulate_book(),
        "first_day": a.first_day,
    }
    safe_out(a.out).write_text(json.dumps(rep, indent=1, sort_keys=True))
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
