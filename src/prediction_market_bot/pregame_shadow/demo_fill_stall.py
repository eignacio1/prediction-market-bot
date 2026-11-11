"""W109.6 Part C: demo-fill stall alarm.

The ADR-0072 forward test went five days (2026-11-05 .. 11-10) with zero demo orders because a turn-off tripped and
wrote both switches ``off`` to deploy/demo_fill.override.env; every health signal stayed green (the arms kept
logging forecasts, the orders just stopped). This asks the one question none of them asked: did the box place any
demo order in the last 24h while the shadow arms were writing rows? Alarm-only; reads files, writes nothing.

Orders = ``shadow_order`` events in logs/demo_fill_policy.jsonl. Arms logging = any game-market ledger under
exp_output/PREGAME_SHADOW with a row in the window. Fires only when orders == 0 AND arms logged, so an off-day or the
off-season (no rows) is never an alarm.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from prediction_market_bot.pregame_shadow.silent_arms import (
    GAME_CELLS, _aware, _parse, _tail_lines, cell_files, last_ts_in_files)

WINDOW_H = 24
POLICY_TAIL_BYTES = 16 * 1024 * 1024


def _orders_since(policy_log: Path, since: datetime) -> Optional[int]:
    if not policy_log.exists():
        return None
    n = 0
    for ln in _tail_lines(policy_log, POLICY_TAIL_BYTES):
        if '"shadow_order"' not in ln:
            continue
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        t = _parse(r.get("ts"))
        if r.get("event") == "shadow_order" and t and t >= since:
            n += 1
    return n


def _override_reason(override: Path) -> str:
    try:
        lines = override.read_text().splitlines()
    except OSError:
        return ""
    head = next((l for l in lines if l.startswith("#")), "").lstrip("# ").strip()
    off = [l.split("=")[0] for l in lines if l.strip().endswith("=off")]
    return f"{override.name} present ({', '.join(off) or 'no switch off'}): {head}"


def stall(repo: Path, now: Optional[datetime] = None) -> dict:
    repo = Path(repo)
    now = _aware(now or datetime.now(timezone.utc))
    since = now - timedelta(hours=WINDOW_H)
    orders = _orders_since(repo / "logs" / "demo_fill_policy.jsonl", since)
    led = repo / "exp_output" / "PREGAME_SHADOW"
    logging = []
    for sport in GAME_CELLS:
        # Real ledger names are {SPORT}_{CELL}_{band}.jsonl (silent_arms passes the same prefix); NHL lives
        # under data/shadow/nhl with no prefix. The first cut omitted the prefix and read 0 files on the box.
        files = (cell_files(repo / "data" / "shadow" / "nhl", sport) if sport == "NHL"
                 else cell_files(led, sport, f"{sport}_"))
        last = last_ts_in_files(files, until=now)
        if last and last >= since:
            logging.append(sport)
    if orders is None:
        return {"status": "unknown", "orders_24h": None, "arms_logging": logging,
                "text": "demo_fill_policy.jsonl unreadable; cannot count demo orders"}
    override = repo / "deploy" / "demo_fill.override.env"
    if orders == 0 and logging:
        why = _override_reason(override) if override.exists() else "no override file; check the placement rule / cron / cancel sweeper"
        return {"status": "stalled", "orders_24h": 0, "arms_logging": logging,
                "text": f"DEMO ORDERS = 0 in the last {WINDOW_H}h while arms logged rows ({', '.join(logging)}): {why}"}
    return {"status": "ok", "orders_24h": orders, "arms_logging": logging,
            "text": f"{orders} demo order(s) in the last {WINDOW_H}h" if orders else "no demo orders and no arm logging (off-day)"}


if __name__ == "__main__":  # pragma: no cover
    import sys
    r = stall(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd())
    print(f"{r['status'].upper()}: {r['text']}")
