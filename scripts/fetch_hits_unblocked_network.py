#!/usr/bin/env python3
"""
T-422 repair tool, phase A (fetch). Run this from a network NOT subject to
GG-084's escalating Fastly-CDN block — i.e. NOT the VPS (157.230.91.33).
Confirmed live this session: a batch of ~20 sequential MLB Stats API calls
from the VPS degrades from 100% success to 100% 406 partway through the
run; the same batch from an unblocked network stays 200 throughout.

Fetches actual hits for each stuck position using gameType="R" only (never
"P" — confirmed separately to 406 100% of the time mid-season regardless of
network), with the finality check re-routed to `schedule?sportId=1&date=X`
instead of the `schedule?gamePk=X` shape. The gamePk-keyed shape 406s
deterministically from the VPS's datacenter IP specifically (GG-161); it is
not needed here since this network isn't blocked either way, but the fixed
shape is used regardless for consistency with the phase-B apply step's
expectations.

Falls back to ESPN boxscore lookup by player name when no MLB Stats API
split exists for the date.

Writes results to a JSON file for `apply_resolved_hits.py`, which runs ON
the VPS and makes zero further network calls.

Usage:
    python3 scripts/fetch_hits_unblocked_network.py stuck_positions.json resolved_hits.json

Input JSON: a list of objects with position_id, player_id, player_name,
game_date (each stuck position to attempt). Output JSON: the same list with
hits/source/reason attached per position — see `apply_resolved_hits.py` for
the schema it consumes (`hits is not None` marks a position as resolvable).
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

_MLB_BASE = "https://statsapi.mlb.com"
_ESPN_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
_ESPN_SUMMARY = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/summary"
_RATE_LIMIT_S = 0.6
_TIMEOUT_S = 15

_day_schedule_cache: dict[str, dict[int, str]] = {}


def finality_via_date_schedule(game_pk: int, game_date: str) -> bool:
    if game_date not in _day_schedule_cache:
        states = {}
        try:
            r = requests.get(f"{_MLB_BASE}/api/v1/schedule",
                              params={"sportId": 1, "date": game_date}, timeout=_TIMEOUT_S)
            r.raise_for_status()
            for d in r.json().get("dates", []):
                for g in d.get("games", []):
                    pk = g.get("gamePk")
                    if pk is not None:
                        states[pk] = g.get("status", {}).get("abstractGameState", "")
        except Exception as exc:
            print(f"  [FINALITY] {game_date}: {type(exc).__name__}: {exc}", file=sys.stderr)
        _day_schedule_cache[game_date] = states
    return _day_schedule_cache[game_date].get(game_pk) == "Final"


def fetch_hits_r(player_id: int, game_date: str):
    year = int(game_date[:4])
    try:
        time.sleep(_RATE_LIMIT_S)
        r = requests.get(f"{_MLB_BASE}/api/v1/people/{player_id}/stats",
                          params={"stats": "gameLog", "group": "hitting",
                                  "season": str(year), "gameType": "R"},
                          timeout=_TIMEOUT_S)
        r.raise_for_status()
        stats_arr = r.json().get("stats", [])
        if not stats_arr:
            return None, "no_stats_block"
        for split in stats_arr[0].get("splits", []):
            if split.get("date", "") == game_date:
                game_pk = split.get("game", {}).get("gamePk")
                if game_pk is None:
                    return None, "split_no_gamepk"
                if not finality_via_date_schedule(game_pk, game_date):
                    return None, "not_final"
                return float(split.get("stat", {}).get("hits", 0)), "ok"
        return None, "no_split_for_date"
    except Exception as exc:
        return None, f"exception:{type(exc).__name__}:{exc}"


def espn_game_ids_for_date(game_date: str):
    try:
        date_str = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y%m%d")
        r = requests.get(_ESPN_SCOREBOARD, params={"dates": date_str, "limit": 30}, timeout=_TIMEOUT_S)
        r.raise_for_status()
        return [e["id"] for e in r.json().get("events", [])]
    except Exception as exc:
        print(f"  [ESPN] {game_date}: scoreboard fetch failed: {exc}", file=sys.stderr)
        return []


def espn_fetch_hits(player_name: str, game_date: str):
    norm_target = player_name.lower().replace(" ", "")
    if not norm_target:
        return None
    for game_id in espn_game_ids_for_date(game_date):
        try:
            r = requests.get(_ESPN_SUMMARY, params={"event": game_id}, timeout=_TIMEOUT_S)
            r.raise_for_status()
            data = r.json()
        except Exception:
            continue
        comps = data.get("header", {}).get("competitions", [{}])
        if not comps:
            continue
        status_name = comps[0].get("status", {}).get("type", {}).get("name", "")
        if status_name not in ("STATUS_FINAL", "STATUS_POSTPONED"):
            continue
        for team_data in data.get("boxscore", {}).get("players", []):
            for stat_group in team_data.get("statistics", []):
                labels = stat_group.get("labels", [])
                if not labels or "AB" not in labels or "IP" in labels:
                    continue
                try:
                    h_idx = labels.index("H")
                except ValueError:
                    continue
                for athlete_entry in stat_group.get("athletes", []):
                    athlete = athlete_entry.get("athlete", {})
                    name = athlete.get("displayName", "")
                    if name.lower().replace(" ", "") != norm_target:
                        continue
                    stats = athlete_entry.get("stats", [])
                    try:
                        return float(stats[h_idx])
                    except (IndexError, ValueError, TypeError):
                        return None
    return None


def main():
    stuck_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])
    stuck = json.loads(stuck_path.read_text())
    print(f"{len(stuck)} stuck position(s) loaded.\n")
    results = []
    for pos in stuck:
        player_id = int(pos.get("player_id", 0))
        player_name = pos.get("player_name", "unknown")
        game_date = pos.get("game_date", "")
        position_id = pos.get("position_id", "")

        hits, reason = fetch_hits_r(player_id, game_date)
        source = "MLB-R"
        if hits is None:
            espn_hits = espn_fetch_hits(player_name, game_date)
            if espn_hits is not None:
                hits, reason, source = espn_hits, "ok", "ESPN"

        status = "FOUND" if hits is not None else "STUCK"
        print(f"  [{status}] {player_name:<20} {game_date}  {position_id}  "
              f"hits={hits}  source={source if hits is not None else '-'}  reason={reason}")
        results.append({
            "position_id": position_id, "player_id": player_id, "player_name": player_name,
            "game_date": game_date, "hits": hits, "source": source if hits is not None else None,
            "reason": reason,
        })

    out_path.write_text(json.dumps(results, indent=2))
    n_found = sum(1 for r in results if r["hits"] is not None)
    print(f"\nFound: {n_found} / {len(results)}. Written to {out_path}")


if __name__ == "__main__":
    main()
