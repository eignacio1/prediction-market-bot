"""W64.2 / ADR-0072 (PROPOSED): demo fill placement policy. DEMO ONLY, OFF BY DEFAULT.

Why: 63.3 found resting demo orders fill mostly when the market moves against us (fills win
24-28% vs 49-52% for never-filled; settle-minus-price -0.25 T4 / -0.39 T1 on fills). Orders rest
40-100 min at the model mid.

R1  cancel an unfilled order after N seconds (DEMO_FILL_CANCEL_AFTER_S, default 60).
R2  price from the live venue book at submit, not the model mid: rest at OUR side's best bid
    (join the queue, never cross), because a stale model mid is the price most likely to be hit
    only after the market has already moved. Skip when the book is one-sided or the model mid
    and the book mid differ by more than DEMO_FILL_MAX_MID_GAP (the model and market disagree
    about where the market is, so neither price is trustworthy).

Switch: DEMO_FILL_PLACEMENT_RULE. Only the exact value ``book_anchor_cancel`` turns it ON; unset,
empty or anything else is OFF (fail closed) and the caller's behaviour is byte-identical to today.
Assignment: DEMO_FILL_ASSIGN_SHARE of eligible orders (default 1.0), chosen by a seeded hash of
position_id, so the arm is reproducible and the rest are an untouched control.

Sizing is never touched here. Every skip / cancel is appended to a JSONL log with its reason.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

SWITCH_ENV = "DEMO_FILL_PLACEMENT_RULE"
SWITCH_ON_VALUE = "book_anchor_cancel"
CANCEL_AFTER_ENV = "DEMO_FILL_CANCEL_AFTER_S"
MAX_GAP_ENV = "DEMO_FILL_MAX_MID_GAP"
SHARE_ENV = "DEMO_FILL_ASSIGN_SHARE"
SEED_ENV = "DEMO_FILL_SEED"
LOG_ENV = "DEMO_FILL_POLICY_LOG"

DEFAULT_CANCEL_AFTER_S = 60.0
DEFAULT_MAX_MID_GAP = 0.05
DEFAULT_SHARE = 1.0
DEFAULT_SEED = "w64-2"
DEFAULT_LOG = Path("logs/demo_fill_policy.jsonl")

LISTING_TTL_ENV = "DEMO_LISTING_TTL_S"
DEFAULT_LISTING_TTL_S = 300.0
_LISTING_CACHE: dict[str, tuple[bool, float]] = {}  # ticker -> (listed, monotonic ts); unknown is never cached


OVERRIDE_FILE_ENV = "DEMO_FILL_OVERRIDE_FILE"
OVERRIDE_NAME = "demo_fill.override.env"


def override_path() -> Path:
    """W69.1/GG-587: untracked, git-ignored override the turn-off writes. Read LAST: a key present
    here beats the tracked deploy/demo_fill.env and the process environment."""
    return Path(os.environ.get(OVERRIDE_FILE_ENV) or Path(__file__).resolve().parents[3] / "deploy" / OVERRIDE_NAME)


def read_override() -> dict[str, str]:
    try:
        text = override_path().read_text()
    except OSError:
        return {}
    out: dict[str, str] = {}
    for line in text.splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def switch_value(name: str) -> str:
    """Effective value of a switch: override file (if it sets the key) else the environment."""
    ov = read_override()
    return (ov[name] if name in ov else os.environ.get(name, "")).strip()


def is_enabled() -> bool:
    return switch_value(SWITCH_ENV) == SWITCH_ON_VALUE


def _float_env(name: str, default: float) -> float:
    try:
        v = float(os.environ.get(name, ""))
    except ValueError:
        return default
    return v if v == v and v >= 0 else default


def log_path() -> Path:
    return Path(os.environ.get(LOG_ENV) or DEFAULT_LOG)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_log(event: dict[str, Any]) -> None:
    """Best-effort append; a logging failure must never block or alter an order."""
    try:
        p = log_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a") as fh:
            fh.write(json.dumps({"ts": _utcnow(), **event}, default=str) + "\n")
    except OSError:
        pass


def assigned(position_id: str) -> bool:
    """Seeded, deterministic share assignment (same id + seed -> same arm)."""
    share = min(1.0, _float_env(SHARE_ENV, DEFAULT_SHARE))
    seed = os.environ.get(SEED_ENV) or DEFAULT_SEED
    h = hashlib.sha256(f"{seed}|{position_id}".encode()).digest()
    return int.from_bytes(h[:8], "big") / 2**64 < share


def listing_skip_reason(client: Any, ticker: str) -> Optional[str]:
    """W67.2/GG-564. None = the ticker is listed on the demo venue (go on). Otherwise the skip
    reason: ``not_listed_on_demo`` (404) or ``demo_listing_unknown`` (read failed -- fail closed,
    never assume listed). Call BEFORE ``assigned``: the skip is arm-blind, so both arms lose the
    same unlistable orders and E1 can be reported over all intended orders and demo-listed only.
    Cached per ticker for DEMO_LISTING_TTL_S (a listing changes rarely within a game)."""
    ttl = _float_env(LISTING_TTL_ENV, DEFAULT_LISTING_TTL_S)
    hit = _LISTING_CACHE.get(ticker)
    now = time.monotonic()
    if hit is not None and now - hit[1] < ttl:
        listed = hit[0]
    else:
        try:
            listed = client.is_listed_on_demo(ticker)
        except Exception:  # noqa: BLE001 - a failed read is a skip, never an order
            listed = None
        if listed is None:
            return "demo_listing_unknown"
        _LISTING_CACHE[ticker] = (listed, now)
    return None if listed else "not_listed_on_demo"


@dataclass
class Decision:
    action: str                 # "SUBMIT" | "SKIP"
    mid_price: float            # YES-frame price handed to submit_order (== caller's when unchanged)
    reason: str
    meta: dict[str, Any] = field(default_factory=dict)


def decide(client: Any, ticker: str, direction: str, mid_price: float, position_id: str) -> Decision:
    """R2. Pure given the book read. Never raises: a failed read is a skip, not a fallback order."""
    ok, book = client.get_market_book(ticker)
    if not ok:
        return Decision("SKIP", mid_price, "book_read_failed")
    bid, ask = float(book.get("yes_bid", 0)), float(book.get("yes_ask", 0))
    if bid <= 0 or ask <= 0 or ask <= bid:
        return Decision("SKIP", mid_price, "one_sided_or_crossed_book", {"yes_bid": bid, "yes_ask": ask})
    book_mid = (bid + ask) / 2.0
    gap = abs(mid_price - book_mid)
    max_gap = _float_env(MAX_GAP_ENV, DEFAULT_MAX_MID_GAP)
    meta = {"yes_bid": bid, "yes_ask": ask, "model_mid": mid_price, "book_mid": book_mid, "gap": gap}
    if gap > max_gap:
        return Decision("SKIP", mid_price, "mid_gap_above_threshold", {**meta, "max_gap": max_gap})
    # submit_order buys YES at mid_price, or NO at 1 - mid_price. Our side's best bid:
    # YES -> yes_bid; NO -> 1 - yes_ask  (so the YES-frame value to pass is yes_ask).
    anchored = bid if direction.lower() == "yes" else ask
    return Decision("SUBMIT", anchored, "book_anchored_best_bid", meta)


def schedule_cancel(client: Any, order_id: str, position_id: str, ticker: str) -> Optional[threading.Timer]:
    """R1. Durable pending record first (so sweep_overdue can finish the job after a restart),
    then an in-process timer. The timer is a daemon: it never keeps a process alive."""
    n = _float_env(CANCEL_AFTER_ENV, DEFAULT_CANCEL_AFTER_S)
    append_log({"event": "cancel_scheduled", "order_id": order_id, "position_id": position_id,
                "ticker": ticker, "cancel_after_s": n, "due_ts": datetime.now(timezone.utc).timestamp() + n})
    t = threading.Timer(n, cancel_now, args=(client, order_id, position_id, ticker, "unfilled_after_N"))
    t.daemon = True
    t.start()
    return t


TERMINAL_ORDER_STATUSES = frozenset({"executed", "filled", "canceled", "cancelled", "expired"})
CANCEL_DONE_EVENTS = ("cancel_ok", "cancel_failed", "cancel_already_terminal")


def _already_terminal_status(client: Any, order_id: str, data: Any) -> Optional[str]:
    """GG-596: a cancel answered HTTP 404 on an order that is already filled/canceled/expired is not a
    failure. Only a 404 whose follow-up GET shows a terminal status qualifies; anything else (other
    error, GET failed, order still resting) stays a failure. Returns the terminal status or None."""
    if not (isinstance(data, dict) and str(data.get("error")) == "HTTP 404"):
        return None
    try:
        ok, od = client.get_order(order_id)
    except Exception:  # noqa: BLE001 - a failed GET leaves the cancel classified as failed
        return None
    if not ok or not isinstance(od, dict):
        return None
    status = str((od.get("order", od) or {}).get("status") or "").lower()
    return status if status in TERMINAL_ORDER_STATUSES else None


def cancel_now(client: Any, order_id: str, position_id: str, ticker: str, reason: str) -> bool:
    try:
        ok, data = client.cancel_order(order_id, market_ticker=ticker or None)
    except Exception as e:  # noqa: BLE001 - a cancel failure is logged, never raised into the order path
        ok, data = False, {"error": type(e).__name__, "detail": str(e)}
    if not ok:
        terminal = _already_terminal_status(client, order_id, data)
        if terminal:
            append_log({"event": "cancel_already_terminal", "order_id": order_id, "position_id": position_id,
                        "ticker": ticker, "reason": reason, "order_status": terminal, "response": data})
            return True
    append_log({"event": "cancel_ok" if ok else "cancel_failed", "order_id": order_id,
                "position_id": position_id, "ticker": ticker, "reason": reason, "response": data})
    return ok


def sweep_overdue(client: Any, now_ts: Optional[float] = None) -> int:
    """Cancel scheduled orders whose due time passed with no cancel_ok/cancel_failed record
    (process restarted before the timer fired). Returns count attempted."""
    p = log_path()
    if not p.exists():
        return 0
    now_ts = now_ts if now_ts is not None else datetime.now(timezone.utc).timestamp()
    sched: dict[str, dict] = {}
    done: set[str] = set()
    for line in p.read_text().splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("event") == "cancel_scheduled":
            sched[r["order_id"]] = r
        elif r.get("event") in CANCEL_DONE_EVENTS:
            done.add(r.get("order_id"))
    n = 0
    for oid, r in sched.items():
        if oid not in done and r.get("due_ts", 0) <= now_ts:
            cancel_now(client, oid, r.get("position_id", ""), r.get("ticker", ""), "sweep_overdue")
            n += 1
    return n
