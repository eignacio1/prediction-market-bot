#!/usr/bin/env python3
"""READ-ONLY (W114.2 / B-090): summarise the box's logs/arm_orders/orders.jsonl.

Per arm and sport: orders (placed), would-orders (dry run), skips and skip reasons. Per arm: fills (E1), P&L per filled contract
before fees (E2), win rate on fills vs the counterfactual win rate of unfilled orders (E3). Everything is split by the GG-1771
data epoch and the two halves are never mixed: `pre_epoch_yes_only` (NO-side orders before 2026-11-06T01:03:42Z were
mirror-priced and are dropped from fills / P&L) and `post_epoch_all_sides`.

Fill status comes from read-only GETs against the Kalshi DEMO API (same lookup as demo_fill_forward_report.lookup_fill, cache
held in memory only). If the host is not demo or there is no signing key, the order counts are still printed and the fill
fields say why they are missing. Writes nothing: stdout only. Python 3.9-safe (the box): timestamps parse with the tolerant
parse_ts, because 3.9 fromisoformat rejects a trailing "Z".
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
LOG = REPO / "logs" / "arm_orders" / "orders.jsonl"
EPOCH = datetime(2026, 11, 6, 1, 3, 42, tzinfo=timezone.utc)  # GG-1771 / GG-1784
PRE, POST = "pre_epoch_yes_only", "post_epoch_all_sides"


def parse_ts(s: Any) -> Optional[datetime]:
    """Tolerant ISO parse: trailing Z, 5-digit fractional seconds (Kalshi), naive -> UTC. None when unparseable."""
    if not s:
        return None
    t = str(s).strip().replace("Z", "+00:00")
    if "." in t:
        head, _, rest = t.partition(".")
        digits = ""
        while rest and rest[0].isdigit():
            digits, rest = digits + rest[0], rest[1:]
        t = head + "." + (digits + "000000")[:6] + rest
    try:
        d = datetime.fromisoformat(t)
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def load_rows(path: Path) -> List[dict]:
    out: List[dict] = []
    try:
        for line in path.read_text().splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if isinstance(r, dict):
                out.append(r)
    except OSError:
        pass
    return out


def epoch_of(r: dict, epoch: datetime = EPOCH) -> Optional[str]:
    ts = parse_ts(r.get("ts"))
    if ts is None:
        return None
    return POST if ts >= epoch else PRE


def counts(rows: List[dict], epoch: datetime = EPOCH) -> dict:
    """Orders / would / skips per (epoch, arm, sport) and skip reasons per (epoch, arm)."""
    ev = {"arm_order": "orders", "arm_would_order": "would", "arm_skip": "skips"}
    per: Dict[str, Counter] = {}
    reasons: Dict[str, Counter] = {}
    bad_ts = 0
    for r in rows:
        k = ev.get(r.get("event"))
        if k is None:
            continue
        ep = epoch_of(r, epoch)
        if ep is None:
            bad_ts += 1
            continue
        if k == "orders" and not r.get("ok"):
            k = "refused"  # submit returned not-ok: counted apart from placed orders
        key = f"{ep}|{r.get('arm')}|{r.get('sport')}"
        per.setdefault(key, Counter())[k] += 1
        if k == "skips":
            reasons.setdefault(f"{ep}|{r.get('arm')}", Counter())[str(r.get("reason"))] += 1
    return {"per_epoch_arm_sport": {k: dict(v) for k, v in sorted(per.items())},
            "skip_reasons_per_epoch_arm": {k: dict(v.most_common()) for k, v in sorted(reasons.items())},
            "rows_with_unparseable_ts": bad_ts}


def _mean(v: list) -> Optional[float]:
    return (sum(v) / len(v)) if v else None


def fills_report(rows: List[dict], fills_for: Optional[Callable[[str, str], dict]], epoch: datetime = EPOCH) -> dict:
    """E1 (fills), E2 (settle minus price per filled contract, before fees), E3 (win rate fills vs unfilled counterfactual), per arm and epoch.
    Pre-epoch NO-side orders are dropped (mirror-priced)."""
    acc: Dict[str, dict] = {}
    for r in rows:
        if r.get("event") != "arm_order" or not r.get("ok") or not r.get("order_id"):
            continue
        ep = epoch_of(r, epoch)
        if ep is None or (ep == PRE and r.get("side") != "yes"):
            continue
        c = acc.setdefault(f"{r.get('arm')}|{ep}", {"arm": r.get("arm"), "epoch": ep, "orders": 0, "fills": 0, "lookups_failed": 0,
                                                 "pnl": [], "won": [], "nf_won": []})
        c["orders"] += 1
        f = fills_for(r["order_id"], r.get("ticker")) if fills_for else None
        if f is None:
            continue
        if f.get("status") == "unretrievable":
            c["lookups_failed"] += 1
            continue
        if (f.get("fills") or 0) > 0:
            c["fills"] += 1
            if f.get("settled") and f.get("won") is not None:
                c["won"].append(1.0 if f["won"] else 0.0)
                price = f.get("price") if f.get("price") is not None else r.get("entry_price")
                if price is not None:
                    c["pnl"].append((1.0 - float(price)) if f["won"] else -float(price))
        elif f.get("nf_won") is not None:
            c["nf_won"].append(1.0 if f["nf_won"] else 0.0)
    out = {}
    for k, c in sorted(acc.items()):
        have = fills_for is not None
        out[k] = {"arm": c["arm"], "epoch": c["epoch"], "E1_orders": c["orders"],
                  "E1_fills": c["fills"] if have else None,
                  "fill_rate": (c["fills"] / c["orders"]) if have and c["orders"] else None,
                  "E2_pnl_per_filled_contract_before_fees": _mean(c["pnl"]), "n_settled_fills": len(c["pnl"]),
                  "E3_win_rate_fills": _mean(c["won"]), "E3_win_rate_nonfills_counterfactual": _mean(c["nf_won"]),
                  "n_nonfills_resolved": len(c["nf_won"]), "lookups_failed": c["lookups_failed"]}
    return out


def make_fills_for(rows: List[dict]):
    """(fills_for or None, note). Read-only demo GETs; in-memory cache; never writes."""
    try:
        spec = importlib.util.spec_from_file_location("demo_fill_forward_report", REPO / "scripts" / "demo_fill_forward_report.py")
        dfr = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dfr)
        os.environ["BOT_ENV"] = "paper"
        from prediction_market_bot import t4_fill_status as tf
        tf._load_dotenv_if_needed(REPO / ".env")
        os.environ["BOT_ENV"] = "paper"
        from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient
        from prediction_market_bot.c5_execution.shadow_flat_stake import demo_host_ok
        client = KalshiMarketClient.from_env()
        if not demo_host_ok():
            return None, "fills skipped: host is not demo"
        if not client.has_signing_key():
            return None, "fills skipped: no signing key"
        sides = {r["order_id"]: r["side"] for r in rows if r.get("event") == "arm_order" and r.get("order_id") and r.get("side")}
        cache: dict = {}
        return (lambda oid, tk: dfr.lookup_fill(client, oid, tk, cache, sides.get(oid))), ""
    except Exception as e:  # noqa: BLE001 - the counts must still print
        return None, "fills skipped: " + type(e).__name__


def build(rows: List[dict], fills_for, note: str, source: str, now: Optional[datetime] = None) -> dict:
    last = max((parse_ts(r.get("ts")) for r in rows if parse_ts(r.get("ts"))), default=None)
    return {"source": source, "read_utc": (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "rows": len(rows), "last_row_ts": last.strftime("%Y-%m-%dT%H:%M:%SZ") if last else None,
            "gg1771_epoch": EPOCH.strftime("%Y-%m-%dT%H:%M:%SZ"), "fills_note": note or "ok",
            "counts": counts(rows), "fills": fills_report(rows, fills_for)}


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=str(LOG))
    ap.add_argument("--no-fills", action="store_true")
    a = ap.parse_args(argv)
    rows = load_rows(Path(a.log))
    fills_for, note = (None, "fills skipped: --no-fills") if a.no_fills else make_fills_for(rows)
    print(json.dumps(build(rows, fills_for, note, str(a.log)), indent=1, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
