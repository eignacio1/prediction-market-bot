#!/usr/bin/env python3
"""W81.3: pre-kickoff order-book snapshot for KXNFLPASSYDS (thin-market pre-registration section 6).

Why: the fillability floor (section 5) rests on IN-GAME depth (n=238). The cell trades PRE-game, so the floor has to be
re-checked against depth measured in the 30 minutes before each kickoff. Kalshi keeps no historical book, so this is
recorded forward or lost. The hourly thin capture (:51) is backlog-bound and in-game; it is left unchanged.

One run (cron, every 20 min at :04/:24/:44; deploy/cron.passyds_prekickoff): lists OPEN KXNFLPASSYDS markets, resolves each
game's real kickoff from the nflverse schedule (falls back to occurrence_datetime - 3 h, flagged), and for every strike
whose game kicks off inside a snapshot slot writes one row:
    pre30 : kickoff in (0, 30] min   (the pre-registration section 6 snapshot; a 20-min cadence always lands one inside)
    pre2h : kickoff in [105, 135] min (optional second look, same job, same caps)
Row = ticker, event_time, secs_to_kickoff_est, best bid/ask, contracts within 1/2/5 cents of mid per side, spread,
model_p (None until the frozen model exists) with factor inputs + as-of times, and whether the section 5 floor was met.

Bounds: MAX_BOOKS_PER_RUN, MAX_DAILY_BYTES, MAX_STORE_BYTES, flock (one run at a time), idempotent per (ticker, slot,
8-min bucket). Public unauthenticated GETs only; no order endpoint, no credentials, no ledger or model-fitting path.

Store (git-ignored): exp_output/PREGAME_SHADOW_PASSYDS/snap_YYYY-MM-DD.jsonl
Usage: python3 scripts/passyds_prekickoff_snapshot.py [--store DIR] [--dry-run] [--pause S]
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board_survey_sports_store as bs  # noqa: E402
import thin_market_depth_capture as tc  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "exp_output" / "PREGAME_SHADOW_PASSYDS"
SCHEDULE = ROOT / "exp_output" / "NFL" / "cache_w47" / "schedule_extended.parquet"
SERIES = "KXNFLPASSYDS"
WRITER = "passyds_prekickoff_snapshot/1"
SLOTS = {"pre30": (0, 30), "pre2h": (105, 135)}      # minutes before kickoff, inclusive upper bound
KICKOFF_LEAD_S = tc.KICKOFF_LEAD_S                   # occurrence_datetime ~ kickoff + 3 h (fallback only)
FLOOR_CONTRACTS, FLOOR_WITHIN_C, FLOOR_SPREAD_C = 10, 2, 6   # pre-registration section 5
WITHIN_C = (1, 2, 5)
MAX_BOOKS_PER_RUN = 400
MAX_DAILY_BYTES = 20 * 1024 * 1024
MAX_STORE_BYTES = 1024 ** 3
DEDUP_S = 8 * 60
PAUSE_S = 0.3


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _levels(side) -> list[tuple[float, float]]:
    out = []
    for p, q in side or []:
        try:
            out.append((float(p), float(q)))
        except (TypeError, ValueError):
            continue
    return out


def depth_fields(book: dict) -> dict:
    """Kalshi orderbook_fp -> bid/ask in dollars and contracts within 1/2/5 cents of mid, per side.

    yes bids = resting YES buyers; no bids = resting NO buyers = YES sellers at 1 - price. 'within' counts, per side,
    the contracts a taker on the OTHER side could hit at a YES price within k cents of mid:
      yes_ask_within_k : YES contracts for sale at <= mid + k  (a YES buyer's depth)
      no_ask_within_k  : NO contracts for sale (= YES bids) at >= mid - k  (a NO buyer's depth)
    """
    fp = (book or {}).get("orderbook_fp") or {}
    yes_bids, no_bids = _levels(fp.get("yes_dollars")), _levels(fp.get("no_dollars"))
    yb = max((p for p, _ in yes_bids), default=None)
    nb = max((p for p, _ in no_bids), default=None)
    ya = None if nb is None else round(1.0 - nb, 4)
    out = {"yes_bid": yb, "yes_ask": ya, "no_bid": nb, "no_ask": None if yb is None else round(1.0 - yb, 4),
           "mid": None, "spread": None, "two_sided": yb is not None and ya is not None and ya >= yb}
    if not out["two_sided"]:
        out.update({f"yes_ask_within_{k}c": 0.0 for k in WITHIN_C}, **{f"no_ask_within_{k}c": 0.0 for k in WITHIN_C},
                   cheaper_side=None, cheaper_within_2c=0.0, floor_met=False)
        return out
    mid = (yb + ya) / 2.0
    out["mid"], out["spread"] = round(mid, 4), round(ya - yb, 4)
    eps = 1e-9
    for k in WITHIN_C:
        out[f"yes_ask_within_{k}c"] = round(sum(q for p, q in no_bids if 1.0 - p <= mid + k / 100 + eps), 2)
        out[f"no_ask_within_{k}c"] = round(sum(q for p, q in yes_bids if p >= mid - k / 100 - eps), 2)
    cheaper = "yes" if mid < 0.5 else "no"           # the side that costs less per contract (the longshot side)
    out["cheaper_side"] = cheaper
    out["cheaper_within_2c"] = out[f"{cheaper}_ask_within_{FLOOR_WITHIN_C}c"]
    out["floor_met"] = bool(out["cheaper_within_2c"] >= FLOOR_CONTRACTS and out["spread"] * 100 <= FLOOR_SPREAD_C + eps)
    return out


def slot_for(secs_to_kickoff: float) -> Optional[str]:
    m = secs_to_kickoff / 60.0
    for name, (lo, hi) in SLOTS.items():
        if lo < m <= hi if lo == 0 else lo <= m <= hi:
            return name
    return None


def load_kickoffs(path: Path = SCHEDULE) -> dict:
    """{frozenset(home, away) + gameday -> kickoff UTC} via the same index the NFL shadow arms use."""
    from prediction_market_bot.pregame_shadow.nfl_forecaster import NFLScheduleIndex
    import pandas as pd
    return NFLScheduleIndex(pd.read_parquet(path))


def kickoff_of(m: dict, sched) -> tuple[float, str]:
    """(kickoff epoch seconds, source). Real schedule first; occurrence_datetime - 3 h only when the schedule misses."""
    ev = m.get("event_ticker", "")
    if sched is not None and ev.startswith(SERIES + "-"):
        try:
            got = sched.kickoff_for_event("KXNFLGAME-" + ev[len(SERIES) + 1:])
        except Exception:
            got = None
        if got:
            return got[0].timestamp(), "nflverse_schedule"
    return tc.event_ts(m) - KICKOFF_LEAD_S, "occurrence_minus_3h_est"


def qb_name(m: dict) -> str:
    return (m.get("no_sub_title") or m.get("yes_sub_title") or "").split(":")[0].strip()


def model_fields(m: dict, now: float) -> dict:
    """Part B plugs the frozen strike model in here. No market price may enter it."""
    try:
        from prediction_market_bot.pregame_shadow import passyds_model as hook  # noqa: WPS433
    except ImportError:
        return {"model_p": None, "model_id": None, "model_sha256": None, "factor_inputs": None, "factor_as_of": None}
    return hook.model_fields(m, datetime.fromtimestamp(now, timezone.utc))


def _recent_keys(store: Path, day: str, now: float) -> set:
    keys = set()
    p = store / f"snap_{day}.jsonl"
    if p.exists():
        for ln in p.read_text().splitlines():
            try:
                r = json.loads(ln)
                if now - bs.iso_ts(r["ts_utc"]) < DEDUP_S:
                    keys.add((r["ticker"], r["slot"]))
            except (ValueError, KeyError):
                continue
    return keys


def run(client, store: Path, now: Optional[float] = None, sha: Optional[str] = None, sched="auto",
        dry_run: bool = False) -> dict:
    store.mkdir(parents=True, exist_ok=True)
    lock = open(store / ".lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("PASSYDS_SNAP SKIP another run holds the lock", flush=True)
        return {"skipped": True}
    now = now if now is not None else datetime.now(timezone.utc).timestamp()
    sha = sha if sha is not None else bs.runtime_commit_sha()
    if sched == "auto":
        try:
            sched = load_kickoffs()
        except Exception as e:  # noqa: BLE001 - missing schedule degrades to the flagged estimate, never a crash
            print(f"PASSYDS_SNAP WARN schedule unreadable ({type(e).__name__}); using occurrence-3h estimate", flush=True)
            sched = None
    day = datetime.fromtimestamp(now, timezone.utc).strftime("%Y-%m-%d")
    out_path = store / f"snap_{day}.jsonl"
    bytes_today = out_path.stat().st_size if out_path.exists() else 0
    bytes_total = sum(p.stat().st_size for p in store.glob("snap_*.jsonl"))
    seen = _recent_keys(store, day, now)
    c = {"listed": 0, "in_slot": 0, "written": 0, "dup": 0, "errors": 0, "est_kickoff": 0, "floor_met": 0, "cap": "none"}
    try:
        markets = tc._list_open(client, SERIES)
    except bs.FetchFailed as e:
        print(f"PASSYDS_SNAP ALARM list failed: {e}", flush=True)
        c["errors"] += 1
        markets = []
    c["listed"] = len(markets)
    for m in sorted(markets, key=lambda x: (x.get("event_ticker", ""), x["ticker"])):
        ko, src = kickoff_of(m, sched)
        slot = slot_for(ko - now)
        if slot is None:
            continue
        c["in_slot"] += 1
        if (m["ticker"], slot) in seen:
            c["dup"] += 1
            continue
        if c["written"] >= MAX_BOOKS_PER_RUN:
            c["cap"] = f"per-run cap {MAX_BOOKS_PER_RUN}"
            break
        try:
            book, url = client.get(f"/markets/{m['ticker']}/orderbook")
        except bs.FetchFailed as e:
            c["errors"] += 1
            print(f"WARN book {m['ticker']}: {e}", flush=True)
            continue
        row = {"kind": "passyds_prekickoff", "ts_utc": _iso(now), "slot": slot, "ticker": m["ticker"],
               "event_ticker": m.get("event_ticker"), "qb": qb_name(m), "strike": m.get("floor_strike"),
               "event_time": _iso(tc.event_ts(m)), "kickoff_utc": _iso(ko), "kickoff_source": src,
               "secs_to_kickoff_est": int(ko - now), **depth_fields(book), **model_fields(m, now),
               "source_url": url, "content_sha256": bs.canon_hash(book), "runtime_commit_sha": sha, "writer": WRITER}
        line = json.dumps(row, separators=(",", ":")) + "\n"
        n = len(line.encode())
        if bytes_today + n > MAX_DAILY_BYTES or bytes_total + n > MAX_STORE_BYTES:
            c["cap"] = "daily/store byte cap"
            print("PASSYDS_SNAP CAP byte cap reached; nothing deleted", flush=True)
            break
        if dry_run:
            print("DRY " + line.rstrip(), flush=True)
        else:
            with open(out_path, "a") as fh:
                fh.write(line)
                fh.flush()
                os.fsync(fh.fileno())
        bytes_today += n
        bytes_total += n
        c["written"] += 1
        c["est_kickoff"] += src != "nflverse_schedule"
        c["floor_met"] += bool(row["floor_met"])
    c.update(ts=_iso(now), bytes_today=bytes_today, dry_run=int(dry_run))
    print("PASSYDS_SNAP " + " ".join(f"{k}={v}" for k, v in c.items()), flush=True)
    return c


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--store", default=str(STORE))
    ap.add_argument("--pause", type=float, default=PAUSE_S)
    ap.add_argument("--dry-run", action="store_true", help="read and print rows; write nothing")
    a = ap.parse_args(argv)
    run(bs.Client(pause=a.pause), Path(a.store), dry_run=a.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
