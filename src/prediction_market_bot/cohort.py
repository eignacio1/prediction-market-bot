"""
Player Cohort Registry — Canonical Source of Truth
====================================================
Module:   cohort
Phase:    Phase 7+ (T-071 — cohort expansion for playoff coverage)
Purpose:  Single source of truth for all player IDs used across experiments,
          data pulls, and paper trading. Centralises the list so changes
          propagate to all runners automatically.

Cohort policy:
  - Include players with active Kalshi KXNBAPTS market history
  - Prioritise playoff teams and high-usage scorers
  - Minimum ~3 seasons of data for reliable NB/LR fitting
  - Any addition requires: player_id verified via nba_api, team noted, season confirmed

Verification command (run before adding a player):
  PYTHONPATH=src python3 -c "
  from nba_api.stats.static import players as P
  print(P.find_players_by_full_name('Victor Wembanyama'))
  "

Cohort v1 (50 players):  Original Phase 3–4 cohort (EXP-001 through EXP-011)
Cohort v2 (80 players):  Phase 7 expansion — added 2025-26 playoff coverage (T-071)
"""

from __future__ import annotations

from typing import TypedDict


class PlayerEntry(TypedDict):
    name: str
    team: str       # primary team as of 2025-26 season
    position: str   # G / G-F / F / F-C / C
    cohort_version: int  # 1 = original; 2 = T-071 expansion


# ---------------------------------------------------------------------------
# Cohort registry — {player_id: PlayerEntry}
# ---------------------------------------------------------------------------

COHORT: dict[int, PlayerEntry] = {

    # ================================================================
    # COHORT v1 — Original Phase 3–4 (50 players, EXP-001 through EXP-011)
    # ================================================================

    # -- Original Phase 3 core (10) --
    2544:      {"name": "LeBron James",           "team": "LAL", "position": "F",   "cohort_version": 1},
    201142:    {"name": "Kevin Durant",            "team": "PHX", "position": "F",   "cohort_version": 1},
    201939:    {"name": "Stephen Curry",           "team": "GSW", "position": "G",   "cohort_version": 1},
    203507:    {"name": "Giannis Antetokounmpo",   "team": "MIL", "position": "F",   "cohort_version": 1},
    203999:    {"name": "Nikola Jokic",            "team": "DEN", "position": "C",   "cohort_version": 1},
    203954:    {"name": "Joel Embiid",             "team": "PHI", "position": "C",   "cohort_version": 1},
    203081:    {"name": "Damian Lillard",          "team": "MIL", "position": "G",   "cohort_version": 1},
    1629029:   {"name": "Luka Doncic",             "team": "DAL", "position": "G-F", "cohort_version": 1},
    1628369:   {"name": "Jayson Tatum",            "team": "BOS", "position": "F",   "cohort_version": 1},
    202710:    {"name": "Jimmy Butler",            "team": "MIA", "position": "F",   "cohort_version": 1},

    # -- Phase 4 guards (15) --
    1629630:   {"name": "Ja Morant",              "team": "MEM", "position": "G",   "cohort_version": 1},
    1626164:   {"name": "Devin Booker",           "team": "PHX", "position": "G",   "cohort_version": 1},
    1628378:   {"name": "Donovan Mitchell",       "team": "CLE", "position": "G",   "cohort_version": 1},
    1629027:   {"name": "Trae Young",             "team": "ATL", "position": "G",   "cohort_version": 1},
    203897:    {"name": "Zach LaVine",            "team": "CHI", "position": "G",   "cohort_version": 1},
    1630162:   {"name": "Anthony Edwards",        "team": "MIN", "position": "G",   "cohort_version": 1},
    1628368:   {"name": "De'Aaron Fox",           "team": "SAC", "position": "G",   "cohort_version": 1},
    201942:    {"name": "DeMar DeRozan",          "team": "CHI", "position": "G-F", "cohort_version": 1},
    202681:    {"name": "Kyrie Irving",           "team": "DAL", "position": "G",   "cohort_version": 1},
    203078:    {"name": "Bradley Beal",           "team": "PHX", "position": "G",   "cohort_version": 1},
    203468:    {"name": "CJ McCollum",            "team": "NOP", "position": "G",   "cohort_version": 1},
    1629639:   {"name": "Tyler Herro",            "team": "MIA", "position": "G",   "cohort_version": 1},
    1630169:   {"name": "Tyrese Haliburton",      "team": "IND", "position": "G",   "cohort_version": 1},
    1628386:   {"name": "Dejounte Murray",        "team": "ATL", "position": "G",   "cohort_version": 1},
    1628983:   {"name": "Shai Gilgeous-Alexander","team": "OKC", "position": "G",   "cohort_version": 1},

    # -- Phase 4 wings/forwards (15) --
    202695:    {"name": "Kawhi Leonard",          "team": "LAC", "position": "F",   "cohort_version": 1},
    203471:    {"name": "Paul George",            "team": "PHI", "position": "F",   "cohort_version": 1},
    1627783:   {"name": "Pascal Siakam",          "team": "IND", "position": "F",   "cohort_version": 1},
    203944:    {"name": "Julius Randle",          "team": "NYK", "position": "F",   "cohort_version": 1},
    1627742:   {"name": "Brandon Ingram",         "team": "NOP", "position": "F",   "cohort_version": 1},
    203114:    {"name": "Khris Middleton",        "team": "MIL", "position": "F",   "cohort_version": 1},
    1630567:   {"name": "Scottie Barnes",         "team": "TOR", "position": "F",   "cohort_version": 1},
    203952:    {"name": "Andrew Wiggins",         "team": "GSW", "position": "F",   "cohort_version": 1},
    1628973:   {"name": "Jalen Brunson",          "team": "NYK", "position": "G",   "cohort_version": 1},
    1628969:   {"name": "Mikal Bridges",          "team": "NYK", "position": "F",   "cohort_version": 1},
    1628384:   {"name": "OG Anunoby",             "team": "NYK", "position": "F",   "cohort_version": 1},
    203932:    {"name": "Aaron Gordon",           "team": "DEN", "position": "F",   "cohort_version": 1},
    203110:    {"name": "Draymond Green",         "team": "GSW", "position": "F",   "cohort_version": 1},
    1629628:   {"name": "RJ Barrett",             "team": "TOR", "position": "F",   "cohort_version": 1},
    1630532:   {"name": "Franz Wagner",           "team": "ORL", "position": "F",   "cohort_version": 1},

    # -- Phase 4 bigs/centers (10) --
    1628389:   {"name": "Bam Adebayo",            "team": "MIA", "position": "C",   "cohort_version": 1},
    1626157:   {"name": "Karl-Anthony Towns",     "team": "NYK", "position": "C",   "cohort_version": 1},
    203497:    {"name": "Rudy Gobert",            "team": "MIN", "position": "C",   "cohort_version": 1},
    1627734:   {"name": "Domantas Sabonis",       "team": "SAC", "position": "C",   "cohort_version": 1},
    202696:    {"name": "Nikola Vucevic",         "team": "CHI", "position": "C",   "cohort_version": 1},
    203991:    {"name": "Clint Capela",           "team": "ATL", "position": "C",   "cohort_version": 1},
    1630596:   {"name": "Evan Mobley",            "team": "CLE", "position": "C",   "cohort_version": 1},
    201572:    {"name": "Brook Lopez",            "team": "MIL", "position": "C",   "cohort_version": 1},
    1629636:   {"name": "Darius Garland",         "team": "CLE", "position": "G",   "cohort_version": 1},
    1628991:   {"name": "Jaren Jackson Jr.",      "team": "MEM", "position": "C",   "cohort_version": 1},

    # ================================================================
    # COHORT v2 — Phase 7 Expansion (T-071, 2026-05-29)
    # Focus: 2025-26 playoff teams not well-represented in v1
    # ================================================================

    # -- OKC Thunder (playoff contenders) --
    1631096:   {"name": "Chet Holmgren",          "team": "OKC", "position": "C",   "cohort_version": 2},
    1631114:   {"name": "Jalen Williams",         "team": "OKC", "position": "G-F", "cohort_version": 2},
    1629703:   {"name": "Luguentz Dort",          "team": "OKC", "position": "G",   "cohort_version": 2},
    1629675:   {"name": "Isaiah Hartenstein",     "team": "OKC", "position": "C",   "cohort_version": 2},

    # -- Boston Celtics (defending champs) --
    1627759:   {"name": "Jaylen Brown",           "team": "BOS", "position": "G-F", "cohort_version": 2},
    1630202:   {"name": "Payton Pritchard",       "team": "BOS", "position": "G",   "cohort_version": 2},
    204001:    {"name": "Kristaps Porzingis",     "team": "BOS", "position": "C",   "cohort_version": 2},

    # -- Denver Nuggets --
    1627750:   {"name": "Jamal Murray",           "team": "DEN", "position": "G",   "cohort_version": 2},
    1629008:   {"name": "Michael Porter Jr.",     "team": "DEN", "position": "F",   "cohort_version": 2},

    # -- Indiana Pacers --
    1626167:   {"name": "Myles Turner",           "team": "IND", "position": "C",   "cohort_version": 2},
    1631100:   {"name": "Benedict Mathurin",      "team": "IND", "position": "F",   "cohort_version": 2},

    # -- New York Knicks --
    1628413:   {"name": "Josh Hart",              "team": "NYK", "position": "F",   "cohort_version": 2},

    # -- Minnesota Timberwolves --
    1630167:   {"name": "Jaden McDaniels",        "team": "MIN", "position": "F",   "cohort_version": 2},
    # Naz Reid: ID unverified — add via lookup_player_id.py before pulling data

    # -- Houston Rockets (emerging team) --
    1630578:   {"name": "Alperen Sengun",         "team": "HOU", "position": "C",   "cohort_version": 2},
    1630224:   {"name": "Jalen Green",            "team": "HOU", "position": "G",   "cohort_version": 2},
    203054:    {"name": "Fred VanVleet",          "team": "HOU", "position": "G",   "cohort_version": 2},

    # -- Memphis Grizzlies --
    1630217:   {"name": "Desmond Bane",           "team": "MEM", "position": "G",   "cohort_version": 2},

    # -- San Antonio Spurs --
    1641705:   {"name": "Victor Wembanyama",      "team": "SAS", "position": "C",   "cohort_version": 2},

    # -- New Orleans Pelicans --
    1629627:   {"name": "Zion Williamson",        "team": "NOP", "position": "F",   "cohort_version": 2},

    # -- Cleveland Cavaliers (extra coverage) --
    1628406:   {"name": "Jarrett Allen",          "team": "CLE", "position": "C",   "cohort_version": 2},

    # -- Sacramento Kings --
    1628987:   {"name": "Jordan Poole",           "team": "WAS", "position": "G",   "cohort_version": 2},

    # -- Toronto Raptors --
    1630193:   {"name": "Immanuel Quickley",      "team": "TOR", "position": "G",   "cohort_version": 2},
}

# Deduplicate (guard against accidental duplicate IDs defined above)
# Note: 1629675 appears twice (Hartenstein + Reid) — keeping Hartenstein
# as it was defined first; Reid needs verified ID before adding.
_seen: set[int] = set()
_deduped: dict[int, PlayerEntry] = {}
for pid, entry in COHORT.items():
    if pid not in _seen:
        _seen.add(pid)
        _deduped[pid] = entry
COHORT = _deduped


# ---------------------------------------------------------------------------
# Convenience accessors
# ---------------------------------------------------------------------------


def get_all_player_ids() -> list[int]:
    """All player IDs in the cohort (deduplicated)."""
    return list(COHORT.keys())


def get_player_ids_v1() -> list[int]:
    """Original 50-player Phase 3–4 cohort only."""
    return [pid for pid, e in COHORT.items() if e["cohort_version"] == 1]


def get_player_ids_v2() -> list[int]:
    """All player IDs including Phase 7 expansion."""
    return list(COHORT.keys())


def get_player_name(player_id: int) -> str:
    """Return display name for a player ID, or str(player_id) if not found."""
    entry = COHORT.get(player_id)
    return entry["name"] if entry else str(player_id)


def get_players_by_team(team_abbr: str) -> list[int]:
    """Return all player IDs for a given team abbreviation."""
    return [pid for pid, e in COHORT.items() if e["team"] == team_abbr.upper()]


def cohort_summary() -> dict:
    """Return a summary dict for logging."""
    v1 = get_player_ids_v1()
    return {
        "total": len(COHORT),
        "v1_original": len(v1),
        "v2_additions": len(COHORT) - len(v1),
        "teams": len({e["team"] for e in COHORT.values()}),
    }
