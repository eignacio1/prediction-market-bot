#!/usr/bin/env python3
"""W105.5 / B-054: the ride/fade router wired to live markets. One short-lived process per run (cron, under the shared
T1/T2/T3 lock); reads the live book for each NBA / NHL / NFL family that ride_cells.toml has a cell for, builds a
Situation, asks decision_trees.router.route(), logs EVERY decision (NO_BET included) to logs/ride_board/decisions.jsonl,
and hands the route to ride_orders.maybe_order (DEMO order only on a HELD_OUT / FORWARD_PASSED cell; IN_SAMPLE logs only).

It reads ride_cells.toml at run time, so a new cell appears on the next run with no code change. It never edits that file.

  PYTHONPATH=src:. venv/bin/python scripts/run_ride_board.py [--sports nba nhl nfl] [--no-orders] [--fixture FILE]

Memory: no pandas, no model load; markets are processed one family at a time and dropped. Peak RSS (ru_maxrss) is written
on the run_summary row of every run so the number is measured, not asserted.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from prediction_market_bot.decision_trees import ride, ride_orders  # noqa: E402
from prediction_market_bot.decision_trees.router import Evidence, MomentumCell, Situation, Skill, route  # noqa: E402

DECISIONS = Path("logs/ride_board/decisions.jsonl")
SKILL_FILE = Path("logs/ride_board/skill.json")  # optional {"nba|KXNBATOTAL": {"weight":..,"ci_lo":..,"n":..}}; absent = no FADE
ARCHIVE_DIR = Path("exp_output/PRICE_ARCHIVE")
SPORT_PREFIX = {"nba": "KXNBA", "nhl": "KXNHL", "nfl": "KXNFL", "mlb": "KXMLB"}
TAIL_BYTES = 4_000_000  # bound on the archive read per run (memory)
PAUSE_S = 0.30


def utc_iso(now: datetime) -> str:
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_ts(v: Any) -> Optional[datetime]:
    """Tolerant of Kalshi's 5-digit fractional seconds (box is Python 3.9)."""
    if not v or not isinstance(v, str):
        return None
    s = v.strip().replace("Z", "+00:00")
    if "." in s:
        head, rest = s.split(".", 1)
        frac = "".join(ch for ch in rest if ch.isdigit())[:6].ljust(6, "0")
        tz = rest[len("".join(ch for ch in rest if ch.isdigit())):]
        s = head + "." + frac + tz
    try:
        d = datetime.fromisoformat(s)
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def tier_of(start: Optional[datetime], now: datetime) -> Optional[str]:
    """Time-to-start tier (same cut points as the W90.1 hold-out scan). None = started / no start time (-> NO_BET)."""
    if start is None:
        return None
    h = (start - now).total_seconds() / 3600.0
    if h <= 0:
        return None
    return "T>24h" if h >= 24 else "T6-24h" if h >= 6 else "T2-6h" if h >= 2 else "T0-2h"


def _f(v: Any) -> Optional[float]:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if x > 0 else None


def game_start(m: dict) -> Optional[datetime]:
    for k in ("occurrence_datetime", "expected_start_time", "game_start_time"):
        d = parse_ts(m.get(k))
        if d:
            return d
    return None


def move_1h(ticker: str, yes_mid: Optional[float], now: datetime, tails: dict) -> Optional[float]:
    """Change in YES mid vs the archive snapshot nearest 1h ago (+-20 min). None if the archive has no such row."""
    if yes_mid is None:
        return None
    best = None
    want = now - timedelta(hours=1)
    for r in tails.get(ticker, ()):
        t = parse_ts(r.get("run_ts"))
        m = _f(r.get("yes_mid"))
        if t is None or m is None:
            continue
        gap = abs((t - want).total_seconds())
        if gap <= 1200 and (best is None or gap < best[0]):
            best = (gap, m)
    return None if best is None else round(yes_mid - best[1], 4)


def archive_tails(archive_dir: Path, tickers: Iterable[str], now: datetime) -> dict:
    """Read only the TAIL of today's (and yesterday's) archive file; keep rows for the wanted tickers only."""
    want = set(tickers)
    out: dict = {}
    for day in (now, now - timedelta(days=1)):
        p = archive_dir / ("prices_%s.jsonl" % day.strftime("%Y-%m-%d"))
        try:
            with p.open("rb") as fh:
                fh.seek(0, 2)
                size = fh.tell()
                fh.seek(max(0, size - TAIL_BYTES))
                data = fh.read().decode("utf-8", "ignore")
        except OSError:
            continue
        for line in data.splitlines()[1:]:  # first line may be cut
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("ticker") in want:
                out.setdefault(r["ticker"], []).append(r)
    return out


def situation(m: dict, family: str, sport: str, now: datetime, tails: dict) -> Optional[Situation]:
    yb, ya = _f(m.get("yes_bid_dollars", m.get("yes_bid"))), _f(m.get("yes_ask_dollars", m.get("yes_ask")))
    two_sided = yb is not None and ya is not None and ya > yb
    mid = (yb + ya) / 2.0 if two_sided else None
    return Situation(sport=sport, family=family, ticker=str(m.get("ticker")), event=str(m.get("event_ticker")),
                     tier=tier_of(game_start(m), now), yes_bid=yb, yes_ask=ya,
                     half_spread=round((ya - yb) / 2.0, 4) if two_sided else None,
                     move_1h=move_1h(str(m.get("ticker")), mid, now, tails))


def load_skill(path: Path = SKILL_FILE) -> dict:
    try:
        raw = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    out = {}
    for k, v in raw.items():
        try:
            sport, fam = k.split("|", 1)
            out[(sport, fam)] = Skill(float(v["weight"]), v.get("ci_lo"), int(v["n"]))
        except (KeyError, TypeError, ValueError):
            continue
    return out


def families(table: Any, sports: Iterable[str], skill: Optional[dict] = None) -> list:
    """Series to read: every family with a ride cell, plus every family with a measured skill record (FADE needs no cell)."""
    pref = {SPORT_PREFIX[s]: s for s in sports}
    fams = sorted({k[1] for k in table.c} | {k[1] for k in (skill or {})})
    return [(f, pref[p]) for f in fams for p in pref if f.startswith(p)]


def log_decision(row: dict, path: Path = DECISIONS) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")


def peak_rss_mb() -> float:
    import resource
    v = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(v / (1024.0 * 1024.0) if sys.platform == "darwin" else v / 1024.0, 1)


def run(markets_by_family: Callable[[str], list], table: Any, client: Any, *, sports=("nba", "nhl", "nfl"),
        orders: bool = True, now: Optional[datetime] = None, decisions: Path = DECISIONS,
        archive_dir: Path = ARCHIVE_DIR, evidence_skill: Optional[dict] = None,
        momentum: tuple = (), stake_fn=None, host_ok=None, schedule_cancel: bool = True) -> dict:
    now = now or datetime.now(timezone.utc)
    ev_skill = load_skill() if evidence_skill is None else evidence_skill
    ev = Evidence(skill=ev_skill, ride=table, momentum=list(momentum))
    counts = {"markets": 0, "decisions": 0, "orders": 0, "paper": 0, "skips": 0}
    by_route: dict = {}
    if orders:
        ride_orders.feed_exposure_gate()  # the gate refuses a book that has never reported (exposure_book_no_writer)
        ride_orders.sweep_cancels(client, schedule_cancel)  # finish any cancel a prior short-lived run could not
    for family, sport in families(table, sports, ev_skill):
        ms = [m for m in markets_by_family(family) if isinstance(m, dict)]
        tails = archive_tails(archive_dir, [str(m.get("ticker")) for m in ms], now) if ms else {}
        for m in ms:
            counts["markets"] += 1
            s = situation(m, family, sport, now, tails)
            if s is None:
                continue
            r = route(s, ev)
            row = {"ts": utc_iso(now), "ticker": s.ticker, "event": s.event, "sport": sport, "family": family,
                   "route": r.tree, "side": r.side, "reasons": list(r.reasons), "agreed": r.agreed, "tier": s.tier,
                   "yes_bid": s.yes_bid, "yes_ask": s.yes_ask, "mid": s.mid, "half_spread": s.half_spread,
                   "move_1h": s.move_1h, "depth": m.get("liquidity_dollars", m.get("liquidity")),
                   "volume_24h": m.get("volume_24h_fp", m.get("volume_24h"))}
            cell = ride_orders.cell_for(s, r, table)
            if cell is not None:
                row.update(cell_status=cell.status, cell_bucket=cell.bucket, cell_book=cell.book)
            by_route[r.tree] = by_route.get(r.tree, 0) + 1
            if orders and r.tree != "NO_BET":
                kw = {} if stake_fn is None else {"stake_fn": stake_fn}
                o = ride_orders.maybe_order(s, r, table, client, host_ok=host_ok, now=now,
                                            schedule_cancel=schedule_cancel, **kw)
                row["order_event"], row["order_reason"] = o.get("event"), o.get("reason")
                row["order_id"] = o.get("order_id")
                key = {"ride_order": "orders", "ride_paper": "paper"}.get(o.get("event"), "skips")
                counts[key] += 1 if o.get("ok") or key != "orders" else 0
            log_decision(row, decisions)
            counts["decisions"] += 1
        del ms, tails
    if orders and counts["orders"]:
        ride_orders.sweep_cancels(client, schedule_cancel, wait=True)  # the process must not exit with a resting order
    summary = {"ts": utc_iso(now), "event": "run_summary", "by_route": by_route, "peak_rss_mb": peak_rss_mb(),
               "orders_enabled": orders, **counts}
    log_decision(summary, decisions)
    return summary


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sports", nargs="+", default=["nba", "nhl", "nfl"], choices=sorted(SPORT_PREFIX))
    ap.add_argument("--no-orders", action="store_true", help="log decisions only; never call the order path")
    ap.add_argument("--fixture", help="JSON {family: [market,...]}: offline run (no network, no client)")
    a = ap.parse_args(argv)
    table = ride.load()
    if a.fixture:
        fx = json.loads(Path(a.fixture).read_text())
        s = run(lambda f: fx.get(f, []), table, None, sports=a.sports, orders=False)
    else:
        from archive_market_prices import _fetch_series_markets
        from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient
        client = KalshiMarketClient.from_env()
        s = run(lambda f: _fetch_series_markets(client, f, PAUSE_S), table, client, sports=a.sports,
                orders=not a.no_orders)
    print(json.dumps(s, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
