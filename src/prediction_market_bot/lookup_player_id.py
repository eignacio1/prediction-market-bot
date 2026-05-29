"""
Player ID Lookup Utility
=========================
Usage:
  PYTHONPATH=src python3 src/prediction_market_bot/lookup_player_id.py "Victor Wembanyama"
  PYTHONPATH=src python3 src/prediction_market_bot/lookup_player_id.py --team OKC

Use this to verify player IDs before adding them to cohort.py.
"""

from __future__ import annotations

import sys


def lookup_by_name(name: str) -> None:
    from nba_api.stats.static import players as P
    results = P.find_players_by_full_name(name)
    if not results:
        print(f"No players found for '{name}'")
        return
    for p in results:
        status = "ACTIVE" if p.get("is_active") else "inactive"
        print(f"  {p['id']:>10}  {p['full_name']:<30}  [{status}]")


def lookup_by_team(team_abbr: str) -> None:
    from nba_api.stats.static import teams as T, players as P
    teams = T.get_teams()
    team = next((t for t in teams if t["abbreviation"].upper() == team_abbr.upper()), None)
    if not team:
        print(f"Team '{team_abbr}' not found")
        return
    print(f"Team: {team['full_name']} ({team['id']})")
    # Note: player-team mapping requires a live API call — use LeagueDashPlayerStats
    print("For current roster, use: nba_api CommonTeamRoster endpoint")


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("Usage: lookup_player_id.py <player name>")
        print("       lookup_player_id.py --team <ABBR>")
        sys.exit(1)

    if args[0] == "--team" and len(args) > 1:
        lookup_by_team(args[1])
    else:
        lookup_by_name(" ".join(args))


if __name__ == "__main__":
    main()
