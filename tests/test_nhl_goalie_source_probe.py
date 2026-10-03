"""W52.D (T-657): offline tests for scripts/nhl_goalie_source_probe.py (no network)."""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import nhl_goalie_source_probe as p  # noqa: E402

BOX = {"gameState": "PRE", "playerByGameStats": {
    "homeTeam": {"goalies": [{"playerId": 1, "starter": True}, {"playerId": 2, "starter": False}]},
    "awayTeam": {"goalies": [{"playerId": 3}]}}}
GAME = {"id": 2026020001, "startTimeUTC": "2026-10-03T23:00:00Z", "gameState": "FUT",
        "homeTeam": {"abbrev": "TOR"}, "awayTeam": {"abbrev": "MTL"}}


def test_starters_reads_flag_per_side():
    assert p.starters(BOX) == {"home": 1, "away": None}
    assert p.starters(None) == {"home": None, "away": None}
    assert p.starters({}) == {"home": None, "away": None}


def test_probe_row_minutes_and_fields():
    now = datetime(2026, 10, 3, 22, 30, tzinfo=timezone.utc)
    row = p.probe_row(GAME, (200, BOX, ""), (0, None, "OSError: blocked"), now)
    assert row["minutes_to_start"] == 30.0 and row["matchup"] == "MTL@TOR"
    assert row["boxscore_starters"]["home"] == 1 and row["landing_err"] == "OSError: blocked"
    assert row["game_state"] == "PRE"
