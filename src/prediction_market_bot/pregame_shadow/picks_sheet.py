"""The picks sheet (W97.3, B-026): one plain-English line per pick, built from the arms' own logs.

Read-only over every ledger; writes one JSON. The pick rule mirrors the demo-order rule in
c5_execution/shadow_flat_stake.maybe_place: the gate is net-of-fee edge > 0 and the side is the one with the larger
net edge. Edge uses the exact Kalshi taker fee (quant.money.fee_rate). Files are read by tailing a bounded byte window,
never whole (the box has under 1 GB of memory).
"""
from __future__ import annotations

import datetime as dt
import json
import os
from typing import Iterable, Iterator, Optional

from prediction_market_bot.pregame_shadow.settled_schema import settled_y
from prediction_market_bot.quant.money import fee_rate

NO_REASONS = "no reasons available"
SCHEMA = 1


def parse_ts(s) -> Optional[dt.datetime]:
    """Tolerant ISO parse (py3.9: Kalshi sends 5-digit fractional seconds and a trailing Z)."""
    if not s:
        return None
    s = str(s).strip().replace("Z", "+00:00")
    if "." in s:
        head, rest = s.split(".", 1)
        frac, tz = rest, ""
        for i, ch in enumerate(rest):
            if not ch.isdigit():
                frac, tz = rest[:i], rest[i:]
                break
        s = f"{head}.{(frac + '000000')[:6]}{tz}"
    try:
        t = dt.datetime.fromisoformat(s)
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def tail_rows(path: str, max_bytes: int = 6_000_000) -> Iterator[dict]:
    """Rows from the last `max_bytes` of a JSONL file (partial first line dropped). Missing file -> nothing."""
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as fh:
            start = max(0, size - max_bytes)
            fh.seek(start)
            data = fh.read()
    except OSError:
        return
    lines = data.split(b"\n")
    if start > 0:
        lines = lines[1:]
    for ln in lines:
        if not ln.strip():
            continue
        try:
            row = json.loads(ln)
        except ValueError:
            continue
        if isinstance(row, dict):
            yield row


def edge_both(p_yes: float, yes_bid: float, yes_ask: float, ticker: str) -> dict:
    """Net edge per contract on each side at the exact taker fee. Needs a two-sided, uncrossed quote."""
    q_no = 1.0 - yes_bid
    ey = p_yes - yes_ask - fee_rate(ticker, yes_ask)
    en = (1.0 - p_yes) - q_no - fee_rate(ticker, q_no)
    return {"yes": ey, "no": en, "side": "yes" if ey >= en else "no", "edge": max(ey, en)}


def _f(v) -> Optional[float]:
    try:
        return None if v is None else float(v)
    except (TypeError, ValueError):
        return None


def describe(row: dict, side: str) -> str:
    """Plain words for the pick. Engine rows carry team/subject/strike; ledger rows carry the market type and ticker."""
    if row.get("subject") and row.get("strike_n") is not None:
        return f"{row['subject']} {row['strike_n']}+: {side.upper()}"
    mt = str(row.get("market_type") or row.get("family") or "market").replace("_", " ").lower()
    sport = row.get("sport") or ""
    tail = str(row.get("market_ticker") or row.get("ticker") or "").split("-")[-1]
    return f"{sport} {mt} {tail}: {side.upper()}".strip()


def pick_from_row(row: dict, arm: str) -> Optional[dict]:
    """One decision row -> a pick dict (or None when there is no usable two-sided quote or no positive edge)."""
    ticker = row.get("market_ticker") or row.get("ticker")
    p = _f(row.get("p_yes", row.get("p_engine")))
    bid, ask = _f(row.get("yes_bid")), _f(row.get("yes_ask"))
    if bid is None or ask is None:
        mkt, hs = _f(row.get("p_market")), _f(row.get("half_spread"))
        if mkt is not None and hs is not None:
            bid, ask = mkt - hs, mkt + hs
    if not ticker or p is None or bid is None or ask is None or not (0.0 < bid <= ask < 1.0):
        return None
    e = edge_both(p, bid, ask, ticker)
    if e["edge"] <= 0:
        return None
    side = e["side"]
    price_yes = ask if side == "yes" else bid
    return {
        "arm": arm,
        "game": row.get("event_ticker") or ticker,
        "ticker": ticker,
        "pick": describe(row, side),
        "side": side,
        "p_yes": round(p, 4),
        "bot_prob_for_pick": round(p if side == "yes" else 1.0 - p, 4),
        "kalshi_price_yes": round(price_yes, 4),
        "edge_after_fee": round(e["edge"], 4),
        "reasons": [NO_REASONS],
        "decided_utc": row.get("ts_utc") or row.get("logged_at"),
        "demo_order": None,
        "result": None,
    }


def latest_picks(rows: Iterable[dict], arm: str, since: dt.datetime) -> dict:
    """Latest decision per ticker at or after `since`. A later row with no edge retracts an earlier pick."""
    best: dict = {}
    for r in rows:
        t = parse_ts(r.get("ts_utc") or r.get("logged_at"))
        tk = r.get("market_ticker") or r.get("ticker")
        if t is None or t < since or not tk:
            continue
        if tk not in best or t >= best[tk][0]:
            best[tk] = (t, r)
    out = {}
    for tk, (_, r) in best.items():
        pk = pick_from_row(r, arm)
        if pk:
            out[tk] = pk
    return out


def orders_by_ticker(rows: Iterable[dict], since: dt.datetime) -> dict:
    """Demo-order evidence per ticker from demo_fill_policy rows: placed order (stake) or the skip reason.
    'placed' is an order sent, not a fill (resting orders are cancelled after about a minute)."""
    out: dict = {}
    for r in rows:
        ev = r.get("event")
        t = parse_ts(r.get("ts"))
        if ev not in ("shadow_order", "shadow_skip") or t is None or t < since:
            continue
        tk = r.get("ticker") or str(r.get("row_id", "")).split("|")[-1]
        if not tk:
            continue
        if ev == "shadow_order" and r.get("ok"):
            out[tk] = {"placed": True, "stake_usd": r.get("stake_usd"), "side": r.get("side"), "price_yes": r.get("price_yes")}
        elif tk not in out or not out[tk].get("placed"):
            out[tk] = {"placed": False, "reason": r.get("reason") or r.get("error") or "skipped"}
    return out


def attach_orders(picks: list, orders: dict) -> None:
    for p in picks:
        p["demo_order"] = orders.get(p["ticker"])


def attach_results(picks: list, settled_rows: Iterable[dict]) -> None:
    """Hit/miss and P&L per contract at the logged price (fill price is not known to the sheet; flagged as such)."""
    ys = {}
    for r in settled_rows:
        tk = r.get("market_ticker") or r.get("ticker")
        y = settled_y(r)
        if tk and y is not None:
            ys[tk] = y
    for p in picks:
        y = ys.get(p["ticker"])
        if y is None:
            continue
        won = (y == 1.0) if p["side"] == "yes" else (y == 0.0)
        push = y == 0.5
        q = p["kalshi_price_yes"] if p["side"] == "yes" else 1.0 - p["kalshi_price_yes"]
        gross = (y if p["side"] == "yes" else 1.0 - y) - q
        p["result"] = {"outcome": "push" if push else ("hit" if won else "miss"),
                       "pnl_per_contract": round(gross - fee_rate(p["ticker"], q), 4), "basis": "logged price, not the fill"}


def group_by_game(picks: list) -> list:
    """One entry per game; arms that disagree on the same game (different sides on one ticker) are flagged."""
    games: dict = {}
    for p in picks:
        games.setdefault(p["game"], []).append(p)
    out = []
    for g, ps in sorted(games.items()):
        sides: dict = {}
        for p in ps:
            sides.setdefault(p["ticker"], set()).add(p["side"])
        out.append({"game": g, "arms_disagree": any(len(s) > 1 for s in sides.values()),
                    "picks": sorted(ps, key=lambda x: (x["ticker"], x["arm"]))})
    return out


def build(sheet_date: str, picks: list, notes: Optional[list] = None) -> dict:
    return {"schema": SCHEMA, "date": sheet_date, "built_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "n_picks": len(picks), "games": group_by_game(picks), "notes": notes or []}
