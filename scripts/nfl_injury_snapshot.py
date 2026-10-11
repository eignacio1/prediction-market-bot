#!/usr/bin/env python3
"""W66.3 / T-803: NFL injury-report point-in-time snapshot. CAPTURE ONLY.

Pulls ESPN's public league-wide injury feed and scoreboard (anonymous GETs) and
appends what the injury picture looked like BEFORE kickoff for every game on the
slate that has not started:

    exp_output/NFL/INJURY_SNAPSHOTS/
        snapshots.jsonl   append-only; a row only when the slate's injury content changed
        checks.jsonl      append-only; one heartbeat line per run (ts, hash, written/unchanged)

Semantics
  * Strictly pre-kickoff: only games whose scoreboard state is "pre" AND whose
    kickoff is after the capture instant are included; a team whose game has
    started is excluded. Nothing is ever backfilled or edited.
  * Per row: every non-"Active" designation for the teams playing, plus every
    QB on those teams (QB status first), with the game, kickoff and minutes to kickoff.
  * Source limits (disclosed): ESPN exposes the designation (Out / Doubtful /
    Questionable / IR / Active), injury type and return date. It does NOT expose
    Wed/Thu/Fri practice participation or the ~90-minute inactives list; those
    need a different source and are not captured here.
  * Feeds no model, adapter, sizing or run path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import requests
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STORE = ROOT / "exp_output" / "NFL" / "INJURY_SNAPSHOTS"
BASE = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/"


def fetch(path: str) -> dict:
    # No custom User-Agent: ESPN 403s spoofed/odd UAs; requests' default passes (GG-163 convention).
    r = requests.get(BASE + path, timeout=30)
    r.raise_for_status()
    return r.json()


def parse_ts(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)


def upcoming_games(scoreboard: dict, now: datetime) -> list[dict]:
    games = []
    for ev in scoreboard.get("events", []):
        st = ev.get("status", {}).get("type", {}).get("state")
        ko = parse_ts(ev["date"])
        if st != "pre" or ko <= now:
            continue
        comp = ev["competitions"][0]["competitors"]
        teams = {c["homeAway"]: c["team"]["abbreviation"] for c in comp}
        games.append({"event_id": ev["id"], "kickoff_utc": ev["date"], "home": teams.get("home"),
                      "away": teams.get("away"),
                      "minutes_to_kickoff": int((ko - now).total_seconds() // 60)})
    return sorted(games, key=lambda g: (g["kickoff_utc"], g["event_id"]))


def build_rows(injuries: dict, games: list[dict]) -> list[dict]:
    team_game = {}
    for g in games:
        team_game[g["home"]] = g
        team_game[g["away"]] = g
    rows = []
    for t in injuries.get("injuries", []):
        for x in t.get("injuries", []):
            a = x.get("athlete", {})
            abbr = a.get("team", {}).get("abbreviation")
            g = team_game.get(abbr)
            if g is None:
                continue
            pos = a.get("position", {}).get("abbreviation")
            status = x.get("status")
            if status == "Active" and pos != "QB":
                continue
            d = x.get("details") or {}
            rows.append({
                "team": abbr, "event_id": g["event_id"], "athlete_id": a.get("id"),
                "name": a.get("displayName"), "pos": pos, "status": status,
                "is_qb": pos == "QB", "injury_type": d.get("type"), "return_date": d.get("returnDate"),
                "status_updated": x.get("date"), "source": (x.get("source") or {}).get("description"),
            })
    return sorted(rows, key=lambda r: (r["team"], r["name"] or ""))


def content_hash(games: list[dict], rows: list[dict]) -> str:
    stable = {"games": [{k: g[k] for k in ("event_id", "kickoff_utc", "home", "away")} for g in games],
              "rows": rows}
    return hashlib.sha256(json.dumps(stable, sort_keys=True).encode()).hexdigest()


def last_hash(path: Path):
    if not path.exists():
        return None
    last = None
    with path.open() as fh:
        for line in fh:
            if line.strip():
                last = json.loads(line)
    return last["content_hash"] if last else None


def append(path: Path, row: dict) -> None:
    with path.open("a") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")


def run(store: Path, now: datetime, scoreboard: dict, injuries: dict) -> dict:
    store.mkdir(parents=True, exist_ok=True)
    ts = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    games = upcoming_games(scoreboard, now)
    if not games:
        out = {"ts": ts, "status": "no_upcoming_games", "games": 0}
        append(store / "checks.jsonl", out)
        return out
    rows = build_rows(injuries, games)
    h = content_hash(games, rows)
    prior = last_hash(store / "snapshots.jsonl")
    out = {"ts": ts, "content_hash": h, "games": len(games), "rows": len(rows),
           "qb_rows": sum(r["is_qb"] for r in rows),
           "min_minutes_to_kickoff": min(g["minutes_to_kickoff"] for g in games)}
    if h == prior:
        out["status"] = "unchanged"
    else:
        append(store / "snapshots.jsonl", {
            "captured_utc": ts, "content_hash": h, "week": scoreboard.get("week", {}).get("number"),
            "espn_injury_feed_ts": injuries.get("timestamp"), "games": games, "rows": rows})
        out["status"] = "written"
    append(store / "checks.jsonl", out)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--store", type=Path, default=DEFAULT_STORE)
    a = ap.parse_args(argv)
    try:
        sb = fetch("scoreboard")
        inj = fetch("injuries")
    except Exception as e:  # network/upstream failure: record nothing as captured
        print(f"REFUSED: upstream fetch failed: {e}", file=sys.stderr)
        return 2
    now = datetime.now(timezone.utc)
    print(json.dumps(run(a.store, now, sb, inj)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
