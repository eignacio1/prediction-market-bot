"""EXP-034 candle parser + D1(b) matcher. Implements D1B_TOLERANCE_PREREG.md as frozen (commit 38b8490).
Read-only; public endpoints; no orders. Handles live (`*_dollars`) and historical (bare) candle schemas."""
from __future__ import annotations
import math
from datetime import datetime

TOL, MISS_MAX, GATE_PASS = 0.01, 0.03, 0.95


def _num(v):
    return None if v in (None, "", {}) else float(v)


def field(d, name):
    """Value of `name` from either schema: bare (historical) or `<name>_dollars` (live)."""
    if not d:
        return None
    v = d.get(name)
    return _num(v if v is not None else d.get(name + "_dollars"))


def parse_candle(c: dict) -> dict:
    """Normalise one candle to identical values across schemas. Null `price` falls back to `previous`."""
    ask, bid, px = c.get("yes_ask") or {}, c.get("yes_bid") or {}, c.get("price") or {}
    vol = c.get("volume", c.get("volume_fp"))
    oi = c.get("open_interest", c.get("open_interest_fp"))
    return {
        "end_ts": int(c["end_period_ts"]),
        **{f"bid_{k}": field(bid, k) for k in ("open", "high", "low", "close")},
        **{f"ask_{k}": field(ask, k) for k in ("open", "high", "low", "close")},
        "price_close": field(px, "close"), "price_prev": field(px, "previous"),
        "volume": _num(vol), "open_interest": _num(oi),
    }


def parse_settlement(m: dict):
    """Scalar settlement from either schema -> 1.0/0.0/None. Accepts result yes/no or settlement value."""
    r = m.get("result")
    if r in ("yes", "no"):
        return 1.0 if r == "yes" else 0.0
    v = m.get("settlement_value_dollars", m.get("settlement_value"))
    if v in (None, ""):
        return None
    f = float(v)
    return f if f in (0.0, 1.0) else f / 100.0 if f in (100.0,) else f


def to_epoch(ts: str) -> float:
    return datetime.fromisoformat(ts).timestamp()


def match(candles: list[dict], t: float):
    """Frozen rule: candle with end_ts == ceil(t/60)*60; if absent, the nearest EARLIER candle's close.
    Returns (kind, candle) kind in exact|prior|unmatched."""
    want = math.ceil(t / 60) * 60
    by = {c["end_ts"]: c for c in candles}
    if want in by:
        return "exact", by[want]
    earlier = [c for c in candles if c["end_ts"] < want]
    if earlier:
        return "prior", max(earlier, key=lambda c: c["end_ts"])
    return "unmatched", None


def side_miss(read, kind, c, side):
    """Distance outside the pass band (0 if passing); None if unmatched."""
    if c is None or read is None:
        return None
    if kind == "exact":
        lo, hi = c[f"{side}_low"], c[f"{side}_high"]
        if lo is None or hi is None:
            return None
        return max(0.0, lo - read, read - hi)
    prior = c[f"{side}_close"]
    return None if prior is None else abs(read - prior)


def compare(row: dict, candles: list[dict]) -> dict:
    kind, c = match(candles, to_epoch(row["ts"]))
    out = {"ticker": row["ticker"], "round": row["round"], "kind": kind}
    ok = kind != "unmatched"
    for side in ("bid", "ask"):
        read = _num(row[f"yes_{side}"])
        d = side_miss(read, kind, c, side)
        out[f"{side}_read"], out[f"{side}_miss"] = read, d
        # pass iff within TOL of band (exact) or |read-prior close|<=TOL (prior); rounding guard 1e-9
        ok = ok and d is not None and d <= TOL + 1e-9
    out["pass"] = ok
    return out


def gate(results: list[dict]) -> dict:
    n = len(results)
    p = sum(r["pass"] for r in results)
    worst = max((m for r in results for m in (r["bid_miss"], r["ask_miss"]) if m is not None), default=0.0)
    unmatched = sum(r["kind"] == "unmatched" for r in results)
    # a pair that is unmatched counts as a fail; "miss > 0.03" is judged on measurable misses
    verdict = n > 0 and p / n >= GATE_PASS and worst <= MISS_MAX + 1e-9 and unmatched == 0
    return {"n": n, "pass": p, "rate": p / n if n else 0.0, "worst_miss": worst, "unmatched": unmatched,
            "gate": "PASS" if verdict else "FAIL"}
