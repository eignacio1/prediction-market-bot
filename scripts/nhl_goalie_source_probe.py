#!/usr/bin/env python3
"""GG-401 / W52.D (T-657): one-shot, read-only probe -- does the official NHL web API name the
confirmed starting goalie before puck drop, inside the EXP-036 T3 window (15-60 min pre-start)?

Not a watcher or sampler: one pass per invocation, no loop, no schedule. A terminal session runs
it by hand at T3-relevant times (e.g. ~60, ~30 and ~15 min before a slate's first puck drop) and
compares the JSONL rows. Reads only api-web.nhle.com (same host and User-Agent as nhl_ingest.py);
writes only the --out JSONL. Does not touch nhl_pregame.py, nhl_shadow_eval.py, any ledger, any
score, or any pre-registered parameter.

Per game it records: minutes to start, gameState, and for both the boxscore and the gamecenter
landing payload whether a goalie flagged ``starter`` is present (and which playerId). A starter
flag seen with minutes_to_start >= 15 is the evidence a StarterProvider would need.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://api-web.nhle.com/v1"
UA = {"User-Agent": "pmbot-nhl-shadow/1"}


def _get(url: str, timeout: float = 15.0) -> tuple[int, dict | None, str]:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8")), ""
    except Exception as exc:  # noqa: BLE001 - record the failure, never retry
        return getattr(exc, "code", 0) or 0, None, f"{type(exc).__name__}: {exc}"[:300]


def starters(payload: dict | None) -> dict:
    """{'home': playerId|None, 'away': playerId|None} from any goalies list carrying a starter flag.

    Looks in playerByGameStats.{homeTeam,awayTeam}.goalies (boxscore; the shape nhl_ingest.py
    parses post-game) -- the field this probe exists to time."""
    out = {"home": None, "away": None}
    pbg = (payload or {}).get("playerByGameStats") or {}
    for side, key in (("home", "homeTeam"), ("away", "awayTeam")):
        for g in (pbg.get(key) or {}).get("goalies") or []:
            if g.get("starter"):
                out[side] = g.get("playerId")
    return out


def probe_row(game: dict, box: tuple, landing: tuple, now: datetime) -> dict:
    start = datetime.fromisoformat(game["startTimeUTC"].replace("Z", "+00:00"))
    b_status, b_json, b_err = box
    l_status, l_json, l_err = landing
    return {
        "probed_at_utc": now.isoformat(timespec="seconds"),
        "game_id": game.get("id"),
        "matchup": f"{(game.get('awayTeam') or {}).get('abbrev')}@{(game.get('homeTeam') or {}).get('abbrev')}",
        "start_time_utc": game["startTimeUTC"],
        "minutes_to_start": round((start - now).total_seconds() / 60, 1),
        "game_state": (b_json or {}).get("gameState") or game.get("gameState"),
        "boxscore_http": b_status, "boxscore_err": b_err, "boxscore_starters": starters(b_json),
        "landing_http": l_status, "landing_err": l_err, "landing_starters": starters(l_json),
        "landing_keys": sorted((l_json or {}).keys())[:40],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--date", default=datetime.now(timezone.utc).date().isoformat())
    ap.add_argument("--out", default="exp_output/NHL/goalie_source_probe.jsonl")
    a = ap.parse_args(argv)
    now = datetime.now(timezone.utc)
    st, sched, err = _get(f"{BASE}/schedule/{a.date}")
    if sched is None:
        print(f"schedule fetch failed: http={st} {err}", file=sys.stderr)
        return 1
    games = [g for wk in sched.get("gameWeek", []) if wk.get("date") == a.date for g in wk.get("games", [])]
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as fh:
        for g in games:
            row = probe_row(g, _get(f"{BASE}/gamecenter/{g['id']}/boxscore"),
                            _get(f"{BASE}/gamecenter/{g['id']}/landing"), now)
            fh.write(json.dumps(row) + "\n")
            print(f"{row['matchup']:<10} t-{row['minutes_to_start']:>7}m state={row['game_state']:<6} "
                  f"box={row['boxscore_starters']} landing={row['landing_starters']}")
    print(f"{len(games)} game(s) probed -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
