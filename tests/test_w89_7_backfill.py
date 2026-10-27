"""Known-answer tests for the W89.7 backfill helpers (event parse, team-pair join, outcome-independent sampling)."""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "12_EXPLORATORY" / "market_history"))
import w89_7_backfill as w  # noqa: E402


def test_parse_event():
    assert w.parse_event("KXNBAGAME-26OCT26GSWDEN") == (date(2026, 10, 26), "GSWDEN")
    assert w.parse_event("garbage") is None


def test_team_pair_alias():
    assert w.team_pair_matches("GSWDEN", "GS", "DEN") or w.team_pair_matches("GSWDEN", "GSW", "DEN")
    assert not w.team_pair_matches("GSWDEN", "LAL", "DEN")


def test_match_event_unique_and_missing():
    g = [{"start_utc": "2026-10-27T02:00Z", "away": "GSW", "home": "DEN"}]
    assert w.match_event("GSWDEN", date(2026, 10, 26), g)[1] == "matched"
    assert w.match_event("LALDEN", date(2026, 10, 26), g) == (None, "no_team_pair")


def test_pick_sample_ignores_outcomes():
    ms = [{"ticker": f"T{i}", "floor_strike": float(i), "result": "yes" if i % 2 else "no"} for i in range(9)]
    flipped = [dict(m, result="no") for m in ms]
    assert [m["ticker"] for m in w.pick_sample(ms, "team")] == [m["ticker"] for m in w.pick_sample(flipped, "team")]
    assert len(w.pick_sample(ms, "team")) == w.SAMPLE_STRIKES
    assert len(w.pick_sample(ms, "game")) == 1


def test_season_label():
    assert w.season_label("nfl", "2026-01-10T00:00:00Z") == "2025"
    assert w.season_label("nba", "2026-10-27T00:00:00Z") == "2026-27"
    assert w.season_label("nba", "2026-03-01T00:00:00Z") == "2025-26"
