"""W98.2 Part B: what does the forward test's entry rule cost? READ-ONLY. Places nothing, changes no rule.

For each shadow order (post top-up, armed): P&L per contract AS ENTERED (control: resting at the model mid;
treatment: posted at the book, cancelled after 60 s) versus the counterfactual TAKEN AT THE QUOTE at decision time
(archive quote, exact fee, depth at the quote). Per (sport, arm), game-clustered 95% intervals.

Inputs (all already on the box): logs/demo_fill_policy.jsonl, exp_output/FORWARD_TEST/demo_fill_forward_cache.json
(fills + outcomes; no API call), exp_output/PRICE_ARCHIVE/{prices,depth}_YYYY-MM-DD.jsonl.
"""
from __future__ import annotations

import argparse
import bisect
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from prediction_market_bot.quant.inference import cluster_bootstrap  # noqa: E402
from prediction_market_bot.quant.money import fee_rate  # noqa: E402

TOPUP_TS = datetime(2026, 10, 16, 5, 40, tzinfo=timezone.utc)  # same split as demo_fill_forward_report (verdict window)
JUDGED_N = 550          # per arm, ADR-0072
MAX_QUOTE_AGE_S = 300   # a quote older than this is stale: excluded and counted, never used
MAX_DEPTH_AGE_S = 900


def parse_ts(s: Any) -> Optional[datetime]:
    try:
        d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def sport_of(tk: str) -> str:
    for k, v in (("KXNFL", "NFL"), ("KXNBA", "NBA"), ("KXNHL", "NHL"), ("KXMLB", "MLB")):
        if tk.upper().startswith(k):
            return v
    return "OTHER"


def game_of(tk: str) -> str:
    p = tk.upper().split("-")
    return f"{sport_of(tk)}|{p[1] if len(p) > 1 else p[0]}"


def load_jsonl(path: Path) -> Iterable[dict]:
    with open(path) as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if isinstance(r, dict):
                yield r


class Series:
    """Time-sorted records per ticker with a 'latest at-or-before t' lookup."""

    def __init__(self) -> None:
        self.ts: Dict[str, List[float]] = defaultdict(list)
        self.rec: Dict[str, List[dict]] = defaultdict(list)

    def add(self, tk: str, t: datetime, rec: dict) -> None:
        self.ts[tk].append(t.timestamp())
        self.rec[tk].append(rec)

    def sort(self) -> None:
        for tk in self.ts:
            order = sorted(range(len(self.ts[tk])), key=self.ts[tk].__getitem__)
            self.ts[tk] = [self.ts[tk][i] for i in order]
            self.rec[tk] = [self.rec[tk][i] for i in order]

    def before(self, tk: str, t: datetime) -> tuple[Optional[dict], Optional[float]]:
        ts = self.ts.get(tk)
        if not ts:
            return None, None
        i = bisect.bisect_right(ts, t.timestamp()) - 1
        return (None, None) if i < 0 else (self.rec[tk][i], t.timestamp() - ts[i])


def load_archives(archive: Path, tickers: set, first_day: str) -> tuple[Series, Series]:
    q, d = Series(), Series()
    for path in sorted(archive.glob("prices_20??-??-??.jsonl")):
        if path.name[7:17] < first_day:
            continue
        for r in load_jsonl(path):
            tk, t = r.get("ticker"), parse_ts(r.get("run_ts"))
            if tk in tickers and t:
                try:
                    bid, ask = float(r["yes_bid"]), float(r["yes_ask"])
                except (KeyError, TypeError, ValueError):
                    continue
                if 0.0 < bid < ask < 1.0 and r.get("status") in (None, "active"):
                    q.add(tk, t, {"bid": bid, "ask": ask})
    for path in sorted(archive.glob("depth_20??-??-??.jsonl")):
        if path.name[6:16] < first_day:
            continue
        for r in load_jsonl(path):
            tk, t = r.get("ticker"), parse_ts(r.get("run_ts") or r.get("ts"))
            if tk in tickers and t and r.get("usable"):
                d.add(tk, t, {"top": r.get("top_of_book_contracts") or {}})
    q.sort()
    d.sort()
    return q, d


def orders_from_log(events: Iterable[dict], since: datetime) -> List[dict]:
    out = []
    for r in events:
        if r.get("event") != "shadow_order" or not r.get("ok") or not r.get("order_id"):
            continue
        if r.get("arm") not in ("control", "treatment"):
            continue
        t = parse_ts(r.get("ts"))
        if t is None or t < since:
            continue
        out.append({"oid": r["order_id"], "ticker": r["ticker"], "side": r["side"], "arm": r["arm"], "ts": t,
                    "price_yes": r.get("price_yes"), "stake": r.get("stake_usd")})
    return out


def entry_price(o: dict) -> Optional[float]:
    """Per-contract price of the order as posted (the side's own price)."""
    p = o.get("price_yes")
    if p is None:
        return None
    return float(p) if o["side"] == "yes" else 1.0 - float(p)


def outcome_of(c: dict) -> Optional[bool]:
    """Did the order's side win? Known for filled+settled (won) and unfilled+resolved (nf_won)."""
    if c.get("fills", 0) > 0:
        return c.get("won") if c.get("settled") else None
    return c.get("nf_won") if "nf_won" in c else None


def build_rows(orders: List[dict], cache: dict, quotes: Series, depth: Series) -> tuple[List[dict], dict]:
    rows, drop = [], defaultdict(int)
    for o in orders:
        c = cache.get(o["oid"])
        if not c:
            drop["no_cache"] += 1
            continue
        win = outcome_of(c)
        if win is None:
            drop["outcome_pending"] += 1
            continue
        tk, side = o["ticker"], o["side"]
        row = {"game": game_of(tk), "sport": sport_of(tk), "arm": o["arm"], "ts": o["ts"], "ticker": tk,
               "win": 1.0 if win else 0.0, "filled": c.get("fills", 0) > 0, "contracts": float(c.get("fills", 0) or 0)}
        # as entered: the price actually paid on a fill (resting = maker; headline fee side is taker, maker is sensitivity)
        if row["filled"]:
            paid = c.get("price") if c.get("price") is not None else entry_price(o)
            if paid is not None:
                row["paid"] = float(paid)
                for side_fee in ("taker", "maker"):
                    row[f"asent_{side_fee}"] = row["win"] - paid - fee_rate(tk, paid, side_fee)
        # counterfactual: taken at the archive's quote at decision time
        qr, age = quotes.before(tk, o["ts"])
        if qr is None or age is None or age > MAX_QUOTE_AGE_S:
            row["stale_quote"] = True
        else:
            px = qr["ask"] if side == "yes" else 1.0 - qr["bid"]
            row["quote_px"], row["quote_age_s"] = px, age
            row["cf_net"] = row["win"] - px - fee_rate(tk, px, "taker")
            row["half_spread"] = (qr["ask"] - qr["bid"]) / 2
            dr, dage = depth.before(tk, o["ts"])
            need = (float(o["stake"]) / max(px, 0.01)) if o.get("stake") else 1.0
            if dr is not None and dage is not None and dage <= MAX_DEPTH_AGE_S:
                top = (dr["top"] or {}).get("no" if side == "yes" else "yes")  # a taker lifts the opposite bids
                row["depth_holds"] = None if top is None else bool(float(top) >= need)
            else:
                row["depth_holds"] = None
        rows.append(row)
    return rows, dict(drop)


def ci(rows: List[dict], field: str, b: int = 2000) -> dict:
    by: Dict[str, List[float]] = defaultdict(list)
    for r in rows:
        if r.get(field) is not None:
            by[r["game"]].append(float(r[field]))
    n = sum(len(v) for v in by.values())
    if not n:
        return {"n": 0, "games": 0, "mean": None, "lo": None, "hi": None}
    m, lo, hi = cluster_bootstrap(by, b=b)
    return {"n": n, "games": len(by), "mean": round(m, 5), "lo": round(lo, 5), "hi": round(hi, 5)}


def summarize(rows: List[dict], days: float, b: int = 2000) -> dict:
    """One (sport, arm) cell."""
    n = len(rows)
    filled = [r for r in rows if r["filled"]]
    games = {r["game"] for r in rows}
    fgames = {r["game"] for r in filled}
    quoted = [r for r in rows if "cf_net" in r]
    holds = [r for r in quoted if r.get("depth_holds") is True]
    unk = [r for r in quoted if r.get("depth_holds") is None]
    out = {
        "orders": n, "games": len(games), "fills": len(filled), "fill_rate": round(len(filled) / n, 4) if n else None,
        "fills_per_game": round(len(filled) / len(games), 3) if games else None,
        "stale_quote_excluded": sum(1 for r in rows if r.get("stale_quote")),
        "as_entered_per_contract_taker_fee": ci(filled, "asent_taker", b),
        "as_entered_per_contract_maker_fee": ci(filled, "asent_maker", b),
        "taken_at_quote_per_contract": ci(quoted, "cf_net", b),
        "taken_at_quote_depth_holds_only": ci(holds, "cf_net", b),
        "mean_half_spread": round(sum(r["half_spread"] for r in quoted) / len(quoted), 5) if quoted else None,
        "depth_holds_share": round(len(holds) / max(1, len(quoted) - len(unk)), 4) if quoted else None,
        "depth_unknown": len(unk),
    }
    # verdict timeline: fills accrue at (fills / days). Taking would fill every order the quote and depth allow.
    cf_fills = len(holds) + len(unk)  # unknown depth counted as holding (upper bound); stated in the report
    for label, k in (("as_entered", len(filled)), ("taken_at_quote_upper", cf_fills)):
        rate = k / days if days > 0 else 0
        out[f"days_to_judged_n_{label}"] = round(max(0, JUDGED_N - k) / rate, 1) if rate > 0 else None
    return out


def build(orders: List[dict], cache: dict, quotes: Series, depth: Series, b: int = 2000) -> dict:
    rows, dropped = build_rows(orders, cache, quotes, depth)
    days = 1.0
    if orders:
        days = max(1.0, (max(o["ts"] for o in orders) - min(o["ts"] for o in orders)) / timedelta(days=1))
    cells: Dict[str, Any] = {}
    groups: Dict[tuple, List[dict]] = defaultdict(list)
    for r in rows:
        groups[(r["sport"], r["arm"])].append(r)
        groups[("ALL", r["arm"])].append(r)
    for (sport, arm), g in sorted(groups.items()):
        cells[f"{sport}|{arm}"] = summarize(g, days, b)
    return {"window_days": round(days, 2), "orders_considered": len(orders), "rows_with_outcome": len(rows),
            "dropped": dropped, "judged_n_per_arm": JUDGED_N, "cells": cells,
            "notes": ["book = shadow (the demo-order flat-stake book); paper rows record no arm and are not in this test",
                      "P&L per contract = outcome - price - fee; fee exact (quant.money.fee_rate), taker headline, maker sensitivity",
                      "taken-at-quote uses the archive quote at/before the decision time, excluded if older than "
                      f"{MAX_QUOTE_AGE_S}s; depth unknown is counted as holding in the timeline upper bound",
                      "an unfilled order has no as-entered P&L (zero contracts); its outcome is used only for the counterfactual"]}


def render(rep: dict) -> str:
    L = [f"# Forward-test entry cost (W98.2 Part B)  window={rep['window_days']}d  orders={rep['orders_considered']}  "
         f"with outcome={rep['rows_with_outcome']}  dropped={rep['dropped']}", "",
         "| cell | orders | fills | fills/game | as entered (taker fee) | as entered (maker fee) | taken at quote | +depth holds | days to 550: now / taking |",
         "|---|---|---|---|---|---|---|---|---|"]

    def f(c: dict) -> str:
        return "n/a" if not c.get("n") else f"{c['mean']:+.4f} [{c['lo']:+.4f},{c['hi']:+.4f}] n={c['n']}"
    for k, c in rep["cells"].items():
        L.append(f"| {k} | {c['orders']} | {c['fills']} | {c['fills_per_game']} | {f(c['as_entered_per_contract_taker_fee'])} | "
                 f"{f(c['as_entered_per_contract_maker_fee'])} | {f(c['taken_at_quote_per_contract'])} | "
                 f"{f(c['taken_at_quote_depth_holds_only'])} | {c['days_to_judged_n_as_entered']} / {c['days_to_judged_n_taken_at_quote_upper']} |")
    L += ["", *[f"- {n}" for n in rep["notes"]]]
    return "\n".join(L)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--log", type=Path, default=REPO / "logs/demo_fill_policy.jsonl")
    ap.add_argument("--cache", type=Path, default=REPO / "exp_output/FORWARD_TEST/demo_fill_forward_cache.json")
    ap.add_argument("--archive", type=Path, default=REPO / "exp_output/PRICE_ARCHIVE")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--report", action="store_true", help="print the table")
    a = ap.parse_args(argv)
    cache = json.loads(a.cache.read_text())
    orders = orders_from_log(load_jsonl(a.log), TOPUP_TS)
    first_day = min((o["ts"] for o in orders), default=TOPUP_TS).date().isoformat()
    quotes, depth = load_archives(a.archive, {o["ticker"] for o in orders}, first_day)
    rep = build(orders, cache, quotes, depth)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(rep, indent=1, sort_keys=True))
    print(render(rep) if a.report or not a.out else f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
