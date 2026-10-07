import pytest
from prediction_market_bot.c1_signal_ingestion import nba_ingest as N


def _ev(h, a, stype=2, done=True):
    return {"id": "1", "date": "2024-01-01T00:00Z", "season": {"year": 2024, "type": stype},
            "status": {"type": {"name": "STATUS_FINAL", "completed": done}},
            "competitions": [{"neutralSite": False, "competitors": [
                {"homeAway": "home", "team": {"abbreviation": h}, "score": "100"},
                {"homeAway": "away", "team": {"abbreviation": a}, "score": "90"}]}]}


def test_maps_espn_codes():
    g = N.parse_event(_ev("GS", "NY"))
    assert (g["home"], g["away"], g["home_score"], g["away_score"]) == ("GSW", "NYK", 100, 90)


def test_all_star_both_unmapped_skipped_even_if_regular():
    assert N.parse_event(_ev("EAST", "WEST", stype=2)) is None


def test_regular_one_unmapped_raises():
    with pytest.raises(N.UnknownTeam):
        N.parse_event(_ev("BOS", "XXX", stype=2))


def test_preseason_exhibition_skipped():
    assert N.parse_event(_ev("BOS", "FUL", stype=1)) is None


def test_team_without_abbreviation_skipped_in_playoffs():
    e = _ev("BOS", "ZZZ", stype=3)
    e["competitions"][0]["competitors"][1]["team"] = {}
    assert N.parse_event(e) is None
