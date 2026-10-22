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
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

from prediction_market_bot.atomic_io import atomic_write_json
from prediction_market_bot.c4_risk_engine.risk import _HARD_LIMITS
from prediction_market_bot.c5_execution import kill_switch_state as ks

STATE_FILE = "exposure_gate_state.json"
SYSTEM = "SYSTEM"
SCHEMA = 1


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


def check_before_order(logs_dir: Optional[Path] = None) -> Optional[str]:
    """Reload persisted state before the first order. Returns a halt reason, or None to proceed.

    Fail closed: no state, corrupt state, or a recorded breach all return a reason."""
    st, why = load_state(logs_dir)
    if st is None:
        return why
    if st.get("breaches"):
        return "exposure_gate_breach:" + ",".join(st["breaches"])
    if float(st["system"]["worst_case_drawdown_pct"]) >= _HARD_LIMITS["max_drawdown_pct"]:
        return "exposure_gate_breach:SYSTEM"
    return None
