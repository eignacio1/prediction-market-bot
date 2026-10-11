"""W66.2 / ADR-0072 R1: persisted-cancel sweeper. DEMO ONLY.

demo_fill_policy.schedule_cancel writes a durable `cancel_scheduled` record (with due_ts) and an in-process
daemon Timer. Short cron processes (T1 MLB paper run) exit before the Timer fires, so the cancel never
happens. This sweeper, run every minute from cron, finishes every overdue cancel from that log. It loops
for ~55 s, sweeping every INTERVAL s, so a 60 s cancel lands ~60-70 s after submit rather than up to 120 s.
Single instance (flock). Refuses unless BOT_ENV=paper and the demo host. Does nothing when the log has
no overdue record, so it is safe to leave installed with the switch OFF.
"""
from __future__ import annotations

import fcntl
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
os.environ["BOT_ENV"] = "paper"
from prediction_market_bot import t4_fill_status as tf  # noqa: E402

tf._load_dotenv_if_needed(REPO / ".env")
os.environ["BOT_ENV"] = "paper"  # .env must not flip the host
from prediction_market_bot.c5_execution import demo_fill_policy as pol  # noqa: E402
from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient, _kalshi_base_url  # noqa: E402

DURATION_S = 55.0
INTERVAL_S = 10.0


def overdue_pending(now_ts: float | None = None) -> bool:
    """Cheap check so an idle minute never builds a client or touches the network."""
    import json
    from datetime import datetime, timezone
    p = pol.log_path()
    if not p.exists():
        return False
    now_ts = now_ts if now_ts is not None else datetime.now(timezone.utc).timestamp()
    sched, done = {}, set()
    for line in p.read_text().splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("event") == "cancel_scheduled":
            sched[r["order_id"]] = r.get("due_ts", 0)
        elif r.get("event") in ("cancel_ok", "cancel_failed"):
            done.add(r.get("order_id"))
    return any(o not in done for o in sched)


def main() -> int:
    if os.environ.get("BOT_ENV") != "paper" or "demo" not in _kalshi_base_url():
        print("REFUSED: not the demo host / BOT_ENV!=paper", file=sys.stderr)
        return 2
    lock = open(REPO / "logs" / "demo_cancel_sweeper.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return 0  # previous minute's sweeper still running
    client = None
    end = time.time() + DURATION_S
    swept = 0
    while True:
        if overdue_pending():
            if client is None:
                client = KalshiMarketClient.from_env()
            swept += pol.sweep_overdue(client)
        if time.time() + INTERVAL_S >= end:
            break
        time.sleep(INTERVAL_S)
    if swept:
        print(f"demo_cancel_sweeper: attempted {swept} cancel(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
