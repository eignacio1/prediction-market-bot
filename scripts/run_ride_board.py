#!/usr/bin/env python3
"""W105.5 / B-054: the ride/fade board runner. One short-lived process per game-window tick.

Reads the live NBA / NHL / NFL game books, builds a Situation per market (mid, spread, last 1h move from the price
archive), asks decision_trees.router.route(), logs EVERY decision (NO_BET included) to
logs/ride_board/decisions.jsonl, and hands RIDE / FADE / MOMENTUM_* decisions to ride_orders.act(): a flat DEMO order
(book RIDE_BOARD, kelly 0) on a HELD_OUT / FORWARD_PASSED cell, a paper-only row on an IN_SAMPLE one.
ride_cells.toml is read at run time, so new cells appear on their own. Orders need RIDE_BOARD_ORDERS=on; default OFF.

  PYTHONPATH=src python3 scripts/run_ride_board.py [--dry-run] [--fixture markets.json] [--now ISO]
"""
from __future__ import annotations

import argparse
import json
import re
import resource
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "12_EXPLORATORY" / "longshot_bias"))

from prediction_market_bot import io_jsonl  # noqa: E402  B-103: archive days may be .gz
from prediction_market_bot.decision_trees import ride, ride_orders  # noqa: E402
from prediction_market_bot.decision_trees.router import (  # noqa: E402
    NO_BET, Evidence, Situation, book_classes, route)

DEFAULT_SERIES = ("KXNBAGAME", "KXNBASPREAD", "KXNBATOTAL", "KXNHLGAME", "KXNHLSPREAD", "KXNHLTOTAL",
                  "KXNFLGAME", "KXNFLSPREAD", "KXNFLTOTAL")
SPORTS = {"KXNBA": "nba", "KXNHL": "nhl", "KXNFL": "nfl", "KXMLB": "mlb"}
LOG_DIR = ROOT / "logs" / "ride_board"
ARCHIVE_DIR = ROOT / "exp_output" / "PRICE_ARCHIVE"
TAIL_BYTES = 3_000_000  # recent snapshots only: bounded memory


def sport_of(series: str) -> str:
    return next((v for k, v in SPORTS.items() if series.startswith(k)), "other")


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def recent_mids(archive_dir: Path, tickers: set, now_ts: float, tail_bytes: int = TAIL_BYTES) -> dict:
    """ticker -> [(epoch, yes_mid)] from the tail of the newest price-archive day file. No future rows."""
    from calib import parse_ts
    out: dict = {}
    files = io_jsonl.jsonl_paths(archive_dir, "prices_*.jsonl") if archive_dir.exists() else []  # B-103: plain or .gz
    for p in files[-1:]:
        with io_jsonl.open_jsonl(p, "rb") as fh:
            if io_jsonl.resolve(p).endswith(io_jsonl.GZ):
                # a gzip stream cannot seek from the end: keep the last tail_bytes of the decompressed stream
                tail = b""
                while True:
                    chunk = fh.read(1 << 20)
                    if not chunk:
                        break
                    tail = (tail + chunk)[-tail_bytes:]
                lines = tail.split(b"\n")[1:] if len(tail) >= tail_bytes else tail.split(b"\n")
            else:
                fh.seek(0, 2)
                fh.seek(max(0, fh.tell() - tail_bytes))
                fh.readline()
                lines = fh
            for line in lines:
                try:
                    r = json.loads(line)
                    t = r["ticker"]
                    if t in tickers and r.get("yes_mid") is not None:
                        ts = parse_ts(r["run_ts"])
                        if ts <= now_ts:
                            out.setdefault(t, []).append((ts, float(r["yes_mid"])))
                except (ValueError, KeyError, TypeError):
                    continue
    return out


def move_1h(hist: list, now_ts: float, mid: float):
    """mid now minus the mid of the snapshot nearest 1h ago (must lie within 45-75 min), else None."""
    best = None
    for ts, m in hist:
        age = now_ts - ts
        if 2700 <= age <= 4500 and (best is None or abs(age - 3600) < abs(best[0] - 3600)):
            best = (age, m)
    return None if best is None else round(mid - best[1], 4)


def decide_market(m: dict, series: str, now_ts: float, ev: Evidence, hist: list, tier_fn) -> dict:
    """One market -> one decision row (route, cell, why, book state). Pure given its inputs."""
    yb, ya = _f(m.get("yes_bid_dollars")), _f(m.get("yes_ask_dollars"))
    ev_t = m.get("event_ticker") or ""
    tier = tier_fn(ev_t, now_ts)
    hs = round((ya - yb) / 2.0, 4) if yb is not None and ya is not None else None
    s = Situation(sport=sport_of(series), family=series, ticker=m.get("ticker", ""), event=ev_t, tier=tier,
                  yes_bid=yb, yes_ask=ya, half_spread=hs)
    mid = s.mid
    if mid is not None:
        s = Situation(**{**s.__dict__, "move_1h": move_1h(hist, now_ts, mid)})
    r = route(s, ev)
    cell = None
    if r.cell is not None:  # POT_OF_GOLD carries its own longshot cell, so the order gate sees its real status
        cell = r.cell
    elif r.tree != NO_BET and mid is not None:
        cell = ride.decide(series, tier, mid, hs, ev.ride, book_classes(s)).cell
    depth = {k: m.get(k) for k in ("volume_fp", "open_interest_fp", "liquidity_dollars") if k in m}
    return {"decision_id": f"{m.get('ticker')}|{int(now_ts)}", "ts": datetime.fromtimestamp(now_ts, timezone.utc)
            .strftime("%Y-%m-%dT%H:%M:%SZ"), "ticker": s.ticker, "event_ticker": ev_t, "family": series,
            "sport": s.sport, "tier": tier, "route": r.tree, "side": r.side, "why": list(r.reasons),
            "agreed": r.agreed, "cell_status": getattr(cell, "status", None),
            "cell": None if cell is None else {"tier": cell.tier, "bucket": cell.bucket, "book": cell.book,
                                               "kind": getattr(cell, "kind", "LONGSHOT"), "net_lo": cell.net_lo},
            "yes_bid": yb, "yes_ask": ya, "mid": mid, "half_spread": hs, "move_1h": s.move_1h, "book": depth}


# W119.3 / Part A: decisions.jsonl grew 1.0 GB in a week. No code reads it (checked src/ scripts/ tests/ deploy/ .claude/
# 12_EXPLORATORY/: only tests/test_run_ride_board.py), so the log keeps what a human or a join needs and drops the rest.
# KEPT: decision_id (join key to ride_board/orders.jsonl), ts, ticker, family, tier, route, side, why, cell_status, yes_bid,
# yes_ask, move_1h. DROPPED (derivable or not a decision): event_ticker, sport (from family), mid / half_spread (from bid / ask),
# agreed, cell {tier,bucket,book,kind,net_lo} (from cell_status + the ride_cells table), book depth (volume / OI / liquidity;
# the price archive keeps those). The full row still goes to ride_orders.act(); only the LOG is compact.
LOG_FIELDS = ("decision_id", "ts", "ticker", "family", "tier", "route", "side", "why", "cell_status", "yes_bid", "yes_ask",
              "move_1h")
HEARTBEAT_S = 3600      # a repeated NO_BET row is re-logged at most this often, so a reader sees the market is still being seen
STATE_FILE = "last_state.json"
STATE_KEEP_S = 2 * 86400


def compact_row(row: dict) -> dict:
    return {k: row.get(k) for k in LOG_FIELDS}


def _state_key(row: dict) -> str:
    """What makes a NO_BET row 'new': its route, reasons, cell status and tier. Prices are NOT in the key (they change every
    cycle and the price archive holds them); an hourly heartbeat row carries the then-current prices."""
    why = [re.sub(r"-?\d+(?:\.\d+)?", "#", w) for w in row["why"]]  # reasons quote the live price ("price 0.320 ..."): numbers out
    return json.dumps([row["route"], row["side"], why, row["cell_status"], row["tier"]], sort_keys=True)


def _load_state(log_dir: Path) -> dict:
    try:
        d = json.loads((log_dir / STATE_FILE).read_text())
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_state(log_dir: Path, state: dict, now_ts: float) -> None:
    keep = {t: v for t, v in state.items() if now_ts - v[1] <= STATE_KEEP_S}
    tmp = log_dir / (STATE_FILE + ".tmp")
    tmp.write_text(json.dumps(keep, sort_keys=True))
    tmp.replace(log_dir / STATE_FILE)


def should_log(row: dict, state: dict, now_ts: float) -> bool:
    """Always log a row that routes to an order (orders.jsonl joins on its decision_id). A NO_BET row is skipped when it repeats
    the last logged one for that ticker (same route / reasons with numbers masked / cell status / tier) inside the heartbeat window."""
    if row["route"] != NO_BET:
        return True
    prev = state.get(row["ticker"])
    return not (prev and prev[0] == _state_key(row) and now_ts - prev[1] < HEARTBEAT_S)


def append_decision(row: dict, log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    with open(log_dir / "decisions.jsonl", "a") as fh:
        fh.write(json.dumps(compact_row(row), sort_keys=True, separators=(",", ":")) + "\n")


def run(markets_by_series: dict, now_ts: float, ev: Evidence, tier_fn, log_dir: Path, client=None,
        archive_dir: Path = ARCHIVE_DIR, order_log: Path = None, place: bool = True) -> dict:
    tickers = {m.get("ticker") for ms in markets_by_series.values() for m in ms}
    mids = recent_mids(archive_dir, tickers, now_ts)
    counts: dict = {}
    log_dir.mkdir(parents=True, exist_ok=True)
    state = _load_state(log_dir)
    for series, ms in markets_by_series.items():
        for m in ms:
            row = decide_market(m, series, now_ts, ev, mids.get(m.get("ticker"), []), tier_fn)
            if should_log(row, state, now_ts):
                append_decision(row, log_dir)
                state[row["ticker"]] = [_state_key(row), now_ts]
            else:
                counts["log_skipped_repeat"] = counts.get("log_skipped_repeat", 0) + 1
            counts[row["route"]] = counts.get(row["route"], 0) + 1
            if row["route"] != NO_BET and place and row["side"] in ("yes", "no"):
                act = ride_orders.act(row, client, log=order_log, now=datetime.fromtimestamp(now_ts, timezone.utc))
                key = f"action_{act['action']}"
                counts[key] = counts.get(key, 0) + 1
    _save_state(log_dir, state, now_ts)
    return counts


def make_client():
    from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient
    from prediction_market_bot.c5_execution.venue_adapter import KalshiVenueAdapter
    try:
        ad = KalshiVenueAdapter.from_env()
    except Exception:  # noqa: BLE001  public reads need no key; no key = no order path
        ad = KalshiVenueAdapter(KalshiMarketClient("public-read-only-no-auth"))
    return ad


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--series", default=",".join(DEFAULT_SERIES))
    ap.add_argument("--fixture", help="JSON {series: [raw markets]} instead of a live read (tests, fixture night)")
    ap.add_argument("--now", help="ISO UTC override")
    ap.add_argument("--log-dir", default=str(LOG_DIR))
    ap.add_argument("--dry-run", action="store_true", help="decisions only: no order call")
    a = ap.parse_args(argv)
    now = datetime.fromisoformat(a.now.replace("Z", "+00:00")) if a.now else datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    from calib import tier as tier_fn
    table = ride.load()
    ev = Evidence(ride=table)  # skill record: none exists yet, so FADE gets no traffic; momentum: no table yet
    series = [s for s in dict.fromkeys(list(a.series.split(",")) + sorted({c.family for c in table.c.values()
                                                                           if c.family.startswith(("KXNBA", "KXNHL", "KXNFL"))})) if s]
    ad = None
    if a.fixture:
        mk = json.loads(Path(a.fixture).read_text())
    else:
        ad = make_client()
        mk = {}
        for s in series:
            ok, ms = ad.list_series_markets_raw(s)
            if ok:
                mk[s] = ms
    client = getattr(ad, "_client", None)
    counts = run(mk, now.timestamp(), ev, tier_fn, Path(a.log_dir), client=client, place=not a.dry_run and client is not None)
    rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024 if sys.platform == "darwin" else 1024)
    print(json.dumps({"now": now.isoformat(), "markets": sum(len(v) for v in mk.values()), "counts": counts,
                      "peak_rss_mb": round(rss_mb, 1)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
