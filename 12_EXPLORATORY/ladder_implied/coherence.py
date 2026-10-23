"""W86.2 Part B helpers: single-snapshot coherence checks on Kalshi strike ladders (arithmetic only).

Pure functions. A *leg* is (ticker, side, price): side 'buy' = buy YES at ask, 'sell' = sell YES at bid
(selling YES at b is economically buying NO at 1-b; fee is symmetric in p). Fee per leg is the k007
schedule 0.07*p*(1-p) at the price traded (ADR-0016, same convention as EXP-033).

Applies to: one run_ts snapshot of one event. Does not apply across time (that is EXP-033's persistence
test) and does not model fills, queue position, or leg-in risk: a 'net>0' count is an arithmetic upper bound.
"""
from __future__ import annotations

from ladder import parse_ticker


def fee(p: float) -> float:
    return 0.07 * p * (1.0 - p)


def _ok_ask(a):
    return a is not None and 0.0 < a < 1.0


def _ok_bid(b):
    return b is not None and 0.0 < b < 1.0


def violation(vtype, event, legs, gross):
    """Attach fee-adjusted net to a gross locked-in credit. legs: list[(ticker, side, price)]."""
    f = sum(fee(p) for _, _, p in legs)
    return {"type": vtype, "event": event, "legs": tuple((t, s) for t, s, _ in legs), "gross": gross,
            "fees": f, "net": gross - f}


def monotonic(event, team, rows):
    """rows: dicts ticker,bid,ask for ONE ladder (one event, one team/side). Higher strike must not be
    worth more than a lower one: violation if bid(hi) > ask(lo) (sell hi, buy lo, locked credit)."""
    r = sorted(rows, key=lambda x: parse_ticker(x["ticker"])[2])
    out = []
    for i in range(len(r)):
        for j in range(i + 1, len(r)):
            lo, hi = r[i], r[j]
            if _ok_bid(hi["bid"]) and _ok_ask(lo["ask"]) and hi["bid"] > lo["ask"]:
                out.append(violation("monotonic", event, [(hi["ticker"], "sell", hi["bid"]), (lo["ticker"], "buy", lo["ask"])],
                                     hi["bid"] - lo["ask"]))
    return out


def adjacent_monotonic(event, team, rows):
    """Adjacent strikes only (dedupes the O(n^2) pairs: any non-adjacent violation implies an adjacent
    one only if the in-between prices are monotone, so this is a lower bound; used for persistence keys)."""
    r = sorted(rows, key=lambda x: parse_ticker(x["ticker"])[2])
    return [v for a, b in zip(r, r[1:]) for v in monotonic(event, team, [a, b])]


def same_contract(row):
    """YES+NO on one contract pays exactly $1. Violation if yes_ask+no_ask<1 (buy both) or
    yes_bid+no_bid>1 (sell both). row needs bid, ask, no_bid, no_ask."""
    out = []
    t = row["ticker"]
    if _ok_ask(row["ask"]) and _ok_ask(row.get("no_ask")) and row["ask"] + row["no_ask"] < 1.0:
        out.append(violation("yes_no_buy", row["event"], [(t, "buy", row["ask"]), (t + "#NO", "buy", row["no_ask"])],
                             1.0 - row["ask"] - row["no_ask"]))
    if _ok_bid(row["bid"]) and _ok_bid(row.get("no_bid")) and row["bid"] + row["no_bid"] > 1.0:
        out.append(violation("yes_no_sell", row["event"], [(t, "sell", row["bid"]), (t + "#NO", "sell", row["no_bid"])],
                             row["bid"] + row["no_bid"] - 1.0))
    return out


def exclusive_set(event, rows, exhaustive: bool):
    """Mutually exclusive legs. sum(bids)>1 -> sell all (always valid). If the set is also exhaustive,
    sum(asks)<1 -> buy all. NFL moneyline is NOT exhaustive (ties), so exhaustive=False there."""
    out = []
    if rows and all(_ok_bid(r["bid"]) for r in rows):
        s = sum(r["bid"] for r in rows)
        if s > 1.0:
            out.append(violation("excl_sum_gt1", event, [(r["ticker"], "sell", r["bid"]) for r in rows], s - 1.0))
    if exhaustive and rows and all(_ok_ask(r["ask"]) for r in rows):
        s = sum(r["ask"] for r in rows)
        if s < 1.0:
            out.append(violation("excl_sum_lt1", event, [(r["ticker"], "buy", r["ask"]) for r in rows], 1.0 - s))
    return out


def dominates(event, weaker, stronger):
    """Contract `stronger` pays whenever `weaker` pays, so price(stronger) >= price(weaker).
    Used for moneyline >= spread(zero strike). Violation if bid(weaker) > ask(stronger)."""
    if _ok_bid(weaker["bid"]) and _ok_ask(stronger["ask"]) and weaker["bid"] > stronger["ask"]:
        return [violation("ml_vs_spread", event, [(weaker["ticker"], "sell", weaker["bid"]), (stronger["ticker"], "buy", stronger["ask"])],
                          weaker["bid"] - stronger["ask"])]
    return []


def sized(v, depth):
    """depth: {ticker: {'yes': n, 'no': n}} at the same run_ts. A buy leg consumes the opposite-side
    resting book (we lift the YES ask = take 'no' bids), a sell leg hits the YES bid ('yes' side).
    Returns min contracts across legs, or None if ANY leg has no depth sample (unknown, never imputed)."""
    sizes = []
    for t, s in v["legs"]:
        base = t.split("#")[0]
        d = depth.get(base)
        if d is None:
            return None
        yes_leg = not t.endswith("#NO")
        key = ("no" if s == "buy" else "yes") if yes_leg else ("yes" if s == "buy" else "no")
        sizes.append(d[key])
    return min(sizes) if sizes else None
