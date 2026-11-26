#!/usr/bin/env python3
"""W129.6 Part A: read-only reachability proof of the ESPN NFL live feed FROM THE BOX. Writes nothing.

One scoreboard call, the plays call for one event, one /situation call. Reports HTTP status, round-trip seconds,
play count, the fields the pricer needs, and how many plays carry a wallclock. Plain requests defaults, no UA
override (GG-163); a 403 or a challenge page is reported as BLOCKED and never worked around.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from prediction_market_bot.c1_signal_ingestion import nfl_live_feed as f  # noqa: E402


def _call(url: str, params=None) -> dict:
    t0 = time.time()
    try:
        r = requests.get(url, params=params, headers=f._HEADERS, timeout=f._TIMEOUT_S)
        body = r.text[:200] if r.status_code != 200 else ""
        return {"status": r.status_code, "rtt_s": round(time.time() - t0, 3), "bytes": len(r.content),
                "json": r.json() if r.status_code == 200 else None, "err_head": body,
                "blocked": r.status_code in (401, 403, 429)}
    except Exception as exc:  # noqa: BLE001
        return {"status": None, "rtt_s": round(time.time() - t0, 3), "json": None, "err_head": f"{type(exc).__name__}: {exc}", "blocked": False}


def main() -> int:
    out: dict = {"probe": "nfl_live_feed", "ua": "requests default (no override)"}
    sb = _call(f._SCOREBOARD)
    out["scoreboard"] = {k: v for k, v in sb.items() if k != "json"}
    events = (sb["json"] or {}).get("events", [])
    out["scoreboard"]["events"] = len(events)
    out["scoreboard"]["states"] = sorted({e.get("status", {}).get("type", {}).get("name", "?") for e in events})
    started = [e for e in events if e.get("status", {}).get("type", {}).get("name") in ("STATUS_IN_PROGRESS", "STATUS_FINAL")]
    # nothing started on today's board: fall back to the saved known-answer game so plays are still proven reachable
    eid = started[0]["id"] if started else "401873067"
    out["event_choice"] = "scoreboard" if started else "fallback_saved_game_401873067"
    if eid:
        pl = _call(f._CORE.format(eid=eid), {"limit": 500})
        items = (pl["json"] or {}).get("items", [])
        out["plays"] = {k: v for k, v in pl.items() if k != "json"}
        out["plays"].update({"event": eid, "n": len(items), "with_wallclock": sum(1 for p in items if p.get("wallclock")),
                             "with_start_down": sum(1 for p in items if (p.get("start") or {}).get("down") is not None)})
        sit = _call(f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/{eid}/competitions/{eid}/situation")
        out["situation"] = {k: v for k, v in sit.items() if k != "json"}
        out["situation"]["keys"] = sorted((sit["json"] or {}).keys())
    ok = bool(out.get("plays", {}).get("n")) and not any(out.get(k, {}).get("blocked") for k in ("scoreboard", "plays", "situation"))
    out["verdict"] = "REACHABLE" if ok else "FAIL_OR_BLOCKED"
    print(json.dumps(out, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
