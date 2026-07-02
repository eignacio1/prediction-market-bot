"""
F-FLOW-01: Retrospective score_diff/inning reconstruction from resolved ESPN boxscores.
=========================================================================================
Component:    Research (05_RESEARCH_EXPERIMENTS support script)
Governs:      EXP-FLOW-MLB-01 (T4M-FLOW blowout-multiplier calibration), ADR-0039 scope
Status:       Retrospective only — does NOT touch the live C1 pipeline (run_t4_mlb_live.py)
Scope note:   Live ESPN score_diff wiring into the T4 live loop is a separate, later-timeline
              task per EXP-FLOW-MLB-01's own Follow-Up table. This script exists solely to
              produce the score_diff/inning input EXP-FLOW-MLB-01's backtest runner needs to
              join against logs/t4_mlb_cycle_log.jsonl.

Why inning-level, not plate-appearance-level
----------------------------------------------
ESPN's public summary endpoint exposes per-team, per-inning run totals
(header.competitions[0].competitors[].linescores) for resolved games, not a
play-by-play run-expectancy feed. That is sufficient granularity for
EXP-FLOW-MLB-01's "sustained blowout window" thesis (a run-differential state
that persists across innings), which the design doc's Approach section frames
at inning granularity. It is not sufficient for at-bat-level state — that
would require play-by-play, which is out of scope here.

Method
------
For team T batting in half-inning N, score_diff is computed BEFORE any runs
scored in that half are added — i.e. cumulative runs each side had entering
that at-bat. Away bats top-of-N (has completed N-1 prior top-halves); home
bats bottom-of-N (has completed N-1 prior bottom-halves AND the away team has
already completed its top-of-N).

Output
------
One JSON file per game_date at
exp_output/EXP-FLOW-MLB-01/score_diff_reconstruction/{game_date}.json,
a list of records:
  {game_date, espn_event_id, away_abbr, home_abbr, inning, half
   ("top"/"bottom"), batting_team_abbr, defense_team_abbr, score_diff,
   is_batting_team_leading}

`load_score_diff_lookup(game_date)` reads that file (regenerating it via
ESPN if missing) and returns a dict keyed by
(away_abbr, home_abbr, inning, half) -> record, for the backtest runner to
join against cycle-log rows via `parse_mlb_ticker`.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import requests

_ESPN_MLB_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
_ESPN_MLB_SUMMARY = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/summary"
_ESPN_HEADERS = {"User-Agent": "Mozilla/5.0"}
_ESPN_STATUS_FINAL = "STATUS_FINAL"

_OUTPUT_DIR = (
    Path(__file__).resolve().parent.parent
    / "exp_output"
    / "EXP-FLOW-MLB-01"
    / "score_diff_reconstruction"
)

# KXMLBHIT ticker: KXMLBHIT-{CREATE_DD}{MON}{GAME_DD}{HHMM}{AWAYTEAM}{HOMETEAM}-{TEAMABBRV}{PLAYERID}-{THRESHOLD}
# e.g. KXMLBHIT-26JUL021235PITPHI-PITMOZUNA24-1 — confirmed against live cycle-log tickers
# 2026-07-02 (PIT@PHI, CIN@MIL). Segment[1] chars [0:2]=create_dd [2:5]=mon [5:7]=game_dd
# [7:11]=hhmm [11:14]=away_abbr [14:17]=home_abbr. Segment[2][:3] = player's team abbr.
_TICKER_SEG1_RE = re.compile(r"^\d{2}[A-Z]{3}\d{2}\d{4}([A-Z]{2,3})([A-Z]{2,3})$")


def parse_mlb_ticker(ticker: str) -> tuple[str, str, str] | None:
    """Return (away_abbr, home_abbr, player_team_abbr) or None on parse failure."""
    parts = ticker.split("-")
    if len(parts) < 3:
        return None
    m = _TICKER_SEG1_RE.match(parts[1])
    if not m:
        return None
    away_abbr, home_abbr = m.group(1), m.group(2)
    player_team_abbr = parts[2][:3]
    return away_abbr, home_abbr, player_team_abbr


def _espn_events_for_date(game_date: str) -> list[dict[str, str]]:
    """List ESPN event ids + team abbrs for a given YYYY-MM-DD, FINAL games only."""
    espn_date = game_date.replace("-", "")
    try:
        r = requests.get(
            _ESPN_MLB_SCOREBOARD,
            params={"dates": espn_date, "limit": 30},
            headers=_ESPN_HEADERS,
            timeout=10,
        )
        r.raise_for_status()
        events = r.json().get("events", [])
    except Exception as exc:
        print(f"[F-FLOW-01] ESPN scoreboard fetch failed date={game_date}: {exc}")
        return []

    out: list[dict[str, str]] = []
    for e in events:
        comp = e.get("competitions", [{}])[0]
        status_name = comp.get("status", {}).get("type", {}).get("name", "")
        if status_name != _ESPN_STATUS_FINAL:
            continue
        competitors = comp.get("competitors", [])
        away = next((c for c in competitors if c.get("homeAway") == "away"), None)
        home = next((c for c in competitors if c.get("homeAway") == "home"), None)
        if not away or not home:
            continue
        out.append(
            {
                "espn_event_id": e["id"],
                "away_abbr": away["team"]["abbreviation"],
                "home_abbr": home["team"]["abbreviation"],
            }
        )
    return out


def _fetch_linescores(espn_event_id: str) -> tuple[str, str, list[int], list[int]] | None:
    """Return (away_abbr, home_abbr, away_runs_per_inning, home_runs_per_inning).

    Returns None if the game is not FINAL or linescores are unavailable
    (postponed/suspended games can have incomplete linescore arrays).
    """
    try:
        r = requests.get(
            _ESPN_MLB_SUMMARY,
            params={"event": espn_event_id},
            headers=_ESPN_HEADERS,
            timeout=10,
        )
        r.raise_for_status()
        d = r.json()
    except Exception as exc:
        print(f"[F-FLOW-01] ESPN summary fetch failed event={espn_event_id}: {exc}")
        return None

    comps = d.get("header", {}).get("competitions", [{}])
    if not comps:
        return None
    comp = comps[0]
    if comp.get("status", {}).get("type", {}).get("name") != _ESPN_STATUS_FINAL:
        return None

    competitors = comp.get("competitors", [])
    away = next((c for c in competitors if c.get("homeAway") == "away"), None)
    home = next((c for c in competitors if c.get("homeAway") == "home"), None)
    if not away or not home:
        return None

    def _runs(c: dict[str, Any]) -> list[int]:
        return [int(ls.get("displayValue", 0) or 0) for ls in c.get("linescores", [])]

    away_runs = _runs(away)
    home_runs = _runs(home)
    if not away_runs or not home_runs:
        return None
    return away["team"]["abbreviation"], home["team"]["abbreviation"], away_runs, home_runs


def reconstruct_score_diff_table(
    away_abbr: str,
    home_abbr: str,
    away_runs: list[int],
    home_runs: list[int],
) -> list[dict[str, Any]]:
    """Per-half-inning score_diff from the batting team's perspective, at the
    moment that half-inning's first at-bat begins (before any of its own runs
    land)."""
    n_innings = max(len(away_runs), len(home_runs))
    rows: list[dict[str, Any]] = []
    for n in range(1, n_innings + 1):
        idx = n - 1  # 0-indexed into the linescore arrays

        # Top of inning n: away batting. Entering state = all completed prior
        # half-innings (top 1..n-1 for away, bottom 1..n-1 for home).
        away_before_top = sum(away_runs[:idx])
        home_before_top = sum(home_runs[:idx])
        if idx < len(away_runs):
            diff = away_before_top - home_before_top
            rows.append(
                {
                    "inning": n,
                    "half": "top",
                    "batting_team_abbr": away_abbr,
                    "defense_team_abbr": home_abbr,
                    "score_diff": diff,
                    "is_batting_team_leading": diff > 0,
                }
            )

        # Bottom of inning n: home batting. Away has now completed top of n.
        home_before_bottom = sum(home_runs[:idx])
        away_before_bottom = sum(away_runs[: idx + 1])
        if idx < len(home_runs):
            diff = home_before_bottom - away_before_bottom
            rows.append(
                {
                    "inning": n,
                    "half": "bottom",
                    "batting_team_abbr": home_abbr,
                    "defense_team_abbr": away_abbr,
                    "score_diff": diff,
                    "is_batting_team_leading": diff > 0,
                }
            )
    return rows


def reconstruct_game_date(game_date: str) -> list[dict[str, Any]]:
    """Reconstruct score_diff tables for every FINAL game on game_date."""
    records: list[dict[str, Any]] = []
    for ev in _espn_events_for_date(game_date):
        result = _fetch_linescores(ev["espn_event_id"])
        if result is None:
            print(
                f"[F-FLOW-01] Skipping {ev['away_abbr']}@{ev['home_abbr']} "
                f"({ev['espn_event_id']}) — not FINAL or missing linescores"
            )
            continue
        away_abbr, home_abbr, away_runs, home_runs = result
        for row in reconstruct_score_diff_table(away_abbr, home_abbr, away_runs, home_runs):
            records.append(
                {
                    "game_date": game_date,
                    "espn_event_id": ev["espn_event_id"],
                    "away_abbr": away_abbr,
                    "home_abbr": home_abbr,
                    **row,
                }
            )
    return records


def _output_path(game_date: str) -> Path:
    return _OUTPUT_DIR / f"{game_date}.json"


def load_score_diff_lookup(
    game_date: str, regenerate: bool = False
) -> dict[tuple[str, str, int, str], dict[str, Any]]:
    """Load (or build + cache) the score_diff lookup table for game_date.

    Keyed by (away_abbr, home_abbr, inning, half) so the backtest runner can
    join a cycle-log row via parse_mlb_ticker(row.ticker) + row.inning +
    (half derived from whether the player's team is the away or home team).
    """
    path = _output_path(game_date)
    if path.exists() and not regenerate:
        with open(path) as fh:
            records = json.load(fh)
    else:
        records = reconstruct_game_date(game_date)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as fh:
            json.dump(records, fh, indent=2)

    lookup: dict[tuple[str, str, int, str], dict[str, Any]] = {}
    for r in records:
        key = (r["away_abbr"], r["home_abbr"], r["inning"], r["half"])
        lookup[key] = r
    return lookup


def score_diff_for_cycle(
    ticker: str, inning: int, lookup: dict[tuple[str, str, int, str], dict[str, Any]]
) -> dict[str, Any] | None:
    """Resolve a single cycle-log row's score_diff via its ticker + inning.

    half is derived from the batter's team: away-team batters bat in "top",
    home-team batters bat in "bottom" — determined by the ticker's own
    embedded team codes, not by inning parity.
    """
    parsed = parse_mlb_ticker(ticker)
    if parsed is None:
        return None
    away_abbr, home_abbr, player_team_abbr = parsed
    if player_team_abbr == away_abbr:
        half = "top"
    elif player_team_abbr == home_abbr:
        half = "bottom"
    else:
        return None
    return lookup.get((away_abbr, home_abbr, inning, half))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--game-date", required=True, help="YYYY-MM-DD")
    ap.add_argument(
        "--regenerate", action="store_true", help="Re-fetch from ESPN even if cached"
    )
    args = ap.parse_args()

    lookup = load_score_diff_lookup(args.game_date, regenerate=args.regenerate)
    print(f"[F-FLOW-01] {args.game_date}: {len(lookup)} half-inning records reconstructed")
    print(f"[F-FLOW-01] Cached at {_output_path(args.game_date)}")


if __name__ == "__main__":
    main()
