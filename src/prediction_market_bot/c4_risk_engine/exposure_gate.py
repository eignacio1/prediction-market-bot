"""GG-441: kill-switch exposure that sees ALL stake, with persisted state that fails closed.

exposure = realized loss + open stake + settled-but-unresolved stake, per book and system-wide.

The drawdown input the existing limit reads is the *worst case*: realized loss plus every
settled-but-unresolved stake treated as lost, over the book's initial bankroll. Open stake on
markets still live is reported (it is exposure) but is not treated as lost. No limit VALUE is
changed here: the gate compares against ``_HARD_LIMITS["max_drawdown_pct"]`` as it stands.

State is written atomically to ``logs/exposure_gate_state.json`` and reloaded before the first
order. A missing, corrupt or unreadable state file is a HALT, never an open. A trip writes the
existing global flag (``kill_switch_state``), so the <=60 s order-path check (NFR-03) is reused.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional

try:  # POSIX only; the box is Linux
    import fcntl
    _HAS_FCNTL = True
except ImportError:  # pragma: no cover
    _HAS_FCNTL = False

from prediction_market_bot.atomic_io import atomic_write_json
from prediction_market_bot.c4_risk_engine.risk import _HARD_LIMITS
from prediction_market_bot.c5_execution import kill_switch_state as ks

STATE_FILE = "exposure_gate_state.json"
LOGONLY_FILE = "exposure_gate_logonly.jsonl"
SETTLED_FILE = "exposure_gate_settled.json"
SYSTEM = "SYSTEM"
SCHEMA = 1

# W87.2 / GG-1082: the books that can place a demo order. ``band`` is the kill-switch band label
# submit_order receives; ``portfolio`` is the ledger file name PaperTrader saves. ``frozen`` books are
# reported but excluded from breach and system sums (the old NBA book's 24.9% is adjudicated
# history, GG-034/GG-037). SHADOW has no ledger: its exposure comes from the shadow order log.
BOOKS: dict[str, dict[str, Any]] = {
    "MLB_T1": {"band": "t1_mlb", "portfolio": "paper_portfolio_mlb.json", "frozen": False},
    "MLB_T4": {"band": "t4_mlb", "portfolio": "paper_portfolio_mlb_t4.json", "frozen": False},
    "NBA_T1": {"band": "t1_nba", "portfolio": "paper_portfolio.json", "frozen": True},
    "SHADOW": {"band": "shadow", "portfolio": None, "frozen": False, "advisory": True},
}
# GG-1240: an ``advisory`` book is reported and must have a live writer, but it is excluded from breach
# and system sums. SHADOW stakes are hypothetical (no ledger, never resolve), so against the $1,000
# notional they would otherwise reach the limit and halt every real book once enforcing.
SHADOW_NOTIONAL_USD = 1000.0  # denominator for the ledger-less shadow book (same default as a paper book)

# Switch-on order (W87.2 Part B): "log" records every would-halt, "enforce" refuses the order.
# Flipped by a reviewed PR after a full game day of the log is read, never by env on the box.
GATE_MODE = "enforce"
MODE_ENV = "EXPOSURE_GATE_MODE"  # tests / drills only
LOG_MODE_FLAG_BOOKS = frozenset({"MLB_T1"})  # books whose breach already wrote the flag in W85.3


def gate_mode() -> str:
    m = os.environ.get(MODE_ENV) or GATE_MODE
    return m if m in ("log", "enforce") else "enforce"  # unknown value fails closed


def book_for_portfolio(path: Any) -> Optional[str]:
    name = Path(str(path)).name
    for b, meta in BOOKS.items():
        if meta["portfolio"] == name:
            return b
    return None


def book_for_band(band: Optional[str]) -> Optional[str]:
    for b, meta in BOOKS.items():
        if band is not None and meta["band"] == band:
            return b
    return None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def book_exposure(state: Mapping[str, Any], settled_tickers: Iterable[str] = ()) -> dict[str, float]:
    """Exposure of one paper book from its portfolio state dict (``PaperTrader.get_state``).

    A position counts as settled-but-unresolved when it is still OPEN and its ticker is in
    ``settled_tickers`` or it carries ``market_settled`` true."""
    settled = set(settled_tickers)
    initial = float(state.get("initial_bankroll_usd", 0.0) or 0.0)
    realized_loss = max(0.0, -float(state.get("total_realized_pnl", 0.0) or 0.0))
    open_stake = 0.0
    unresolved = 0.0
    for pos in state.get("open_positions", []) or []:
        if str(pos.get("status", "OPEN")) != "OPEN":
            continue
        size = float(pos.get("size_usd", 0.0) or 0.0)
        if pos.get("kalshi_ticker") in settled or pos.get("market_settled"):
            unresolved += size
        else:
            open_stake += size
    worst = (realized_loss + unresolved) / initial if initial > 0 else 1.0
    return {
        "initial_bankroll_usd": initial,
        "realized_loss_usd": round(realized_loss, 4),
        "open_stake_usd": round(open_stake, 4),
        "settled_unresolved_stake_usd": round(unresolved, 4),
        "total_exposure_usd": round(realized_loss + open_stake + unresolved, 4),
        "worst_case_drawdown_pct": round(worst, 6),
    }


def system_exposure(books: Mapping[str, Mapping[str, float]]) -> dict[str, float]:
    keys = ("initial_bankroll_usd", "realized_loss_usd", "open_stake_usd",
            "settled_unresolved_stake_usd", "total_exposure_usd")
    out = {k: round(sum(b[k] for b in books.values()), 4) for k in keys}
    init = out["initial_bankroll_usd"]
    out["worst_case_drawdown_pct"] = round(
        (out["realized_loss_usd"] + out["settled_unresolved_stake_usd"]) / init, 6) if init > 0 else 1.0
    return out


def state_path(logs_dir: Optional[Path] = None) -> Path:
    return ks._logs_dir(logs_dir) / STATE_FILE


def load_state(logs_dir: Optional[Path] = None) -> tuple[Optional[dict], Optional[str]]:
    """(state, None) when readable; (None, reason) when missing/corrupt. Never raises."""
    p = state_path(logs_dir)
    try:
        raw = p.read_text()
    except FileNotFoundError:
        return None, "exposure_state_missing"
    except OSError as e:
        return None, f"exposure_state_unreadable:{type(e).__name__}"
    try:
        st = json.loads(raw)
        if not isinstance(st, dict) or st.get("schema") != SCHEMA or "books" not in st \
                or "system" not in st or not isinstance(st["books"], dict):
            return None, "exposure_state_corrupt:shape"
        float(st["system"]["worst_case_drawdown_pct"])
    except (ValueError, KeyError, TypeError):
        return None, "exposure_state_corrupt:parse"
    return st, None


def _write_halt(reason: str, logs_dir: Optional[Path]) -> None:
    path = ks.global_flag_path(logs_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(path, {"reason": reason, "at": _now(), "source": "exposure_gate"})


def update(books: Mapping[str, Mapping[str, Any]], settled_tickers: Iterable[str] = (),
           logs_dir: Optional[Path] = None) -> dict:
    """Recompute exposure for every book, persist atomically, and trip the global flag if the
    system-wide or any single book's worst-case drawdown reaches the existing limit."""
    t0 = time.monotonic()
    settled = list(settled_tickers)
    per_book = {name: book_exposure(st, settled) for name, st in books.items()}
    sysx = system_exposure(per_book) if per_book else {"worst_case_drawdown_pct": 1.0}
    limit = _HARD_LIMITS["max_drawdown_pct"]
    breaches = [n for n, b in per_book.items() if b["worst_case_drawdown_pct"] >= limit]
    if sysx["worst_case_drawdown_pct"] >= limit:
        breaches.append(SYSTEM)
    state = {"schema": SCHEMA, "updated_at": _now(), "limit_max_drawdown_pct": limit,
             "books": per_book, "system": sysx, "breaches": breaches}
    atomic_write_json(state_path(logs_dir), state)
    if breaches:
        _write_halt("exposure_gate_breach:" + ",".join(breaches), logs_dir)
    state["elapsed_ms"] = round((time.monotonic() - t0) * 1000.0, 3)
    return state


def _lock(logs_dir: Optional[Path]):
    from contextlib import contextmanager

    @contextmanager
    def cm():
        if not _HAS_FCNTL:  # pragma: no cover
            yield
            return
        lp = state_path(logs_dir).with_suffix(".lock")
        lp.parent.mkdir(parents=True, exist_ok=True)
        fd = open(lp, "w")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            fd.close()
    return cm()


def log_logonly(event: dict, logs_dir: Optional[Path] = None) -> None:
    """Append one would-halt / would-trip record. Never raises."""
    try:
        p = ks._logs_dir(logs_dir) / LOGONLY_FILE
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a") as fh:
            fh.write(json.dumps({"at": _now(), **event}, sort_keys=True) + "\n")
    except OSError:
        pass


def _recompute(books: dict, mode: str, logs_dir: Optional[Path]) -> dict:
    live = {n: b for n, b in books.items() if not b.get("frozen") and not b.get("advisory")
            and "worst_case_drawdown_pct" in b}
    sysx = system_exposure(live) if live else {"worst_case_drawdown_pct": 0.0}
    limit = _HARD_LIMITS["max_drawdown_pct"]
    breaches = [n for n, b in live.items() if b["worst_case_drawdown_pct"] >= limit]
    if sysx["worst_case_drawdown_pct"] >= limit:
        breaches.append(SYSTEM)
    return {"schema": SCHEMA, "updated_at": _now(), "limit_max_drawdown_pct": limit,
            "books": books, "system": sysx, "breaches": breaches}


def _persist(state: dict, mode: str, logs_dir: Optional[Path]) -> dict:
    atomic_write_json(state_path(logs_dir), state)
    breaches = state["breaches"]
    if breaches:
        trips = breaches if mode == "enforce" else [b for b in breaches if b in LOG_MODE_FLAG_BOOKS]
        if trips:
            _write_halt("exposure_gate_breach:" + ",".join(trips), logs_dir)
        if mode != "enforce" and set(breaches) - set(trips):
            log_logonly({"event": "would_trip", "breaches": breaches}, logs_dir)
    return state


def record_book(name: str, portfolio_state: Mapping[str, Any], settled_tickers: Iterable[str] = (),
                logs_dir: Optional[Path] = None) -> dict:
    """Merge ONE book into the persisted state (other books untouched) under a file lock.
    ``update`` replaces every book; per-book writers must use this so one book never erases another."""
    t0 = time.monotonic()
    ex = book_exposure(portfolio_state, settled_tickers)
    ex["frozen"] = bool(BOOKS.get(name, {}).get("frozen", False))
    ex["advisory"] = bool(BOOKS.get(name, {}).get("advisory", False))
    ex["recorded_at"] = _now()
    with _lock(logs_dir):
        st, _ = load_state(logs_dir)
        books = dict(st["books"]) if st else {}
        books[name] = ex
        out = _persist(_recompute(books, gate_mode(), logs_dir), gate_mode(), logs_dir)
    out["elapsed_ms"] = round((time.monotonic() - t0) * 1000.0, 3)
    return out


def mark_feed_failed(name: str, why: str, logs_dir: Optional[Path] = None) -> None:
    """A book's writer errored: record it so orders for that book are refused (never left stale-open)."""
    with _lock(logs_dir):
        st, _ = load_state(logs_dir)
        books = dict(st["books"]) if st else {}
        books[name] = {**books.get(name, {}), "feed_error": why, "recorded_at": _now()}
        _persist(_recompute(books, gate_mode(), logs_dir), gate_mode(), logs_dir)


def shadow_state(log_path: Path, notional: float = SHADOW_NOTIONAL_USD) -> dict:
    """Portfolio-shaped state for the ledger-less SHADOW book: every placed shadow order whose
    market has not settled counts as open stake. Realized P&L is not tracked here (GG-1175)."""
    pos = []
    try:
        for line in log_path.read_text().splitlines():
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("event") == "shadow_order" and e.get("ok") and e.get("order_id"):
                pos.append({"kalshi_ticker": e.get("ticker"), "size_usd": float(e.get("stake_usd") or 0.0),
                            "status": "OPEN"})
    except FileNotFoundError:
        pass
    return {"initial_bankroll_usd": notional, "total_realized_pnl": 0.0, "open_positions": pos}


def load_settled(logs_dir: Optional[Path] = None) -> tuple[set[str], float]:
    """(tickers known settled, age in seconds of the cache). Missing cache = (empty, inf)."""
    p = ks._logs_dir(logs_dir) / SETTLED_FILE
    try:
        d = json.loads(p.read_text())
        return set(d["settled"]), max(0.0, time.time() - float(d["fetched_epoch"]))
    except (OSError, ValueError, KeyError, TypeError):
        return set(), float("inf")


SETTLED_STATUSES = frozenset({"settled", "finalized", "determined", "closed"})


def refresh_settled(tickers: Iterable[str], status_fn: Callable[[str], Optional[str]],
                    logs_dir: Optional[Path] = None, ttl_s: float = 600.0, max_calls: int = 60) -> set[str]:
    """Settled-ticker feed. ``status_fn(ticker)`` returns the venue market status or None on failure.
    Tickers already known settled stay settled (settlement is final). A failed GET leaves the ticker
    out of the set: its stake then counts as plain open stake, which is the weaker reading, so the
    failure is logged and the cache age is exposed to the caller."""
    known, age = load_settled(logs_dir)
    want = [t for t in dict.fromkeys(tickers) if t and t not in known]
    if age < ttl_s or not want:
        return known
    errs = 0
    for t in want[:max_calls]:
        try:
            st = status_fn(t)
        except Exception:  # noqa: BLE001 - feed must never break an order path
            st = None
        if st is None:
            errs += 1
        elif str(st).lower() in SETTLED_STATUSES:
            known.add(t)
    try:
        atomic_write_json(ks._logs_dir(logs_dir) / SETTLED_FILE,
                          {"settled": sorted(known), "fetched_epoch": time.time(), "fetch_errors": errs})
    except OSError:
        pass
    if errs:
        log_logonly({"event": "settled_feed_errors", "errors": errs, "asked": len(want[:max_calls])}, logs_dir)
    return known


def check_before_order(logs_dir: Optional[Path] = None, book: Optional[str] = None) -> Optional[str]:
    """Reload persisted state before the first order. Returns a halt reason, or None to proceed.

    Fail closed: no state, corrupt state, a recorded breach, or (when ``book`` is named) a book
    with no writer / a failed writer all return a reason."""
    st, why = load_state(logs_dir)
    if st is None:
        return why
    if st.get("breaches"):
        return "exposure_gate_breach:" + ",".join(st["breaches"])
    if float(st["system"]["worst_case_drawdown_pct"]) >= _HARD_LIMITS["max_drawdown_pct"]:
        return "exposure_gate_breach:SYSTEM"
    if book is not None:
        b = st["books"].get(book)
        if b is None:
            return f"exposure_book_no_writer:{book}"
        if "feed_error" in b:
            return f"exposure_book_feed_error:{book}"
    return None


def gate_for_order(band: Optional[str], logs_dir: Optional[Path] = None) -> Optional[str]:
    """The order-path call (submit_order). Returns a refusal reason to ENFORCE, or None to place.
    In log mode a would-halt is recorded and None is returned."""
    book = book_for_band(band)
    reason = check_before_order(logs_dir, book=book) if book else f"exposure_band_unmapped:{band}"
    if reason is None:
        return None
    if gate_mode() == "enforce":
        return reason
    log_logonly({"event": "would_halt", "reason": reason, "band": band, "book": book}, logs_dir)
    return None
