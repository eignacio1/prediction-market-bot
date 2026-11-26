#!/usr/bin/env python3
"""W130.2 (EXP-NBAPROPS-002): place flat DEMO orders for the 14 kept NBA props leaves from the newest shadow rows.

Reads the T2 / T3 NBA player-prop ledgers written by scripts/run_nba_engine_props_shadow.py (cron :39) for rows logged in the last
--window-min minutes, and calls decision_trees.props_arm_orders.act on each. Switch PROPS_ARM_ORDERS: off (default; prints nothing
placed) / dry (logs would-orders, places none) / on. DEMO host only. Sweeps overdue 60 s cancels first (the cancel timer is a
daemon thread; this process exits). Prints a JSON summary: rows seen, outcome counts, skip reasons (they sum to rows seen).

  PROPS_ARM_ORDERS=dry PYTHONPATH=src:. python3 scripts/run_props_arm_orders.py [--window-min 20] [--now ISO] [--log PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from prediction_market_bot.decision_trees import props_arm_orders as pao  # noqa: E402


def recent_rows(ledger_dir: Path, now: datetime, window_min: float) -> list:
    out = []
    lo = now - timedelta(minutes=window_min)
    for p in sorted(ledger_dir.glob("*NBA_PLAYER_*_T[23].jsonl")):
        try:
            lines = p.read_text().splitlines()[-4000:]
        except OSError:
            continue
        for line in lines:
            try:
                r = json.loads(line)
                t = datetime.fromisoformat(str(r["ts_utc"]).replace("Z", "+00:00"))
            except (ValueError, KeyError):
                continue
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            if lo <= t <= now:
                out.append(r)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger-dir", default=str(ROOT / "exp_output" / "PREGAME_SHADOW_EXP047"))
    ap.add_argument("--window-min", type=float, default=20.0)
    ap.add_argument("--now", help="ISO UTC override (testing only)")
    ap.add_argument("--log", default=None, help="order log path (default logs/props_arm_orders/orders.jsonl)")
    a = ap.parse_args(argv)
    now = datetime.fromisoformat(a.now) if a.now else datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    m = pao.mode()
    summ = {"mode": m, "now": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "rows_seen": 0, "outcomes": {}, "skip_reasons": {}}
    if m == pao.OFF:
        summ["note"] = "PROPS_ARM_ORDERS is off: nothing read, nothing placed"
        print(json.dumps(summ, sort_keys=True))
        return 0
    import arm_orders_read as aor
    client, why = aor.demo_client()
    if client is None:
        summ["note"] = why
        print(json.dumps(summ, sort_keys=True))
        return 0
    if m == pao.ON:
        from prediction_market_bot.c5_execution import demo_fill_policy as pol
        summ["swept_overdue_cancels"] = pol.sweep_overdue(client)
    kept, sha = pao.kept_entries()
    log = Path(a.log) if a.log else None
    outc, skips = Counter(), Counter()
    rows = recent_rows(Path(a.ledger_dir), now, a.window_min)
    for r in rows:
        res = pao.act(r, client, now=now, log=log, kept=kept, map_sha=sha)
        if res is None:
            continue
        outc[res["event"]] += 1
        if res["event"] == pao.SKIP_EVENT:
            skips[str(res["reason"])] += 1
    summ.update(rows_seen=len(rows), outcomes=dict(outc), skip_reasons=dict(skips.most_common()),
                skips_sum_to_rows=(sum(skips.values()) + outc[pao.ORDER_EVENT] + outc[pao.WOULD_EVENT] == len(rows)))
    print(json.dumps(summ, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
