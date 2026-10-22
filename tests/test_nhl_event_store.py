"""NHL event store: pure parse functions and cache round-trip on synthetic payloads. No network."""
from prediction_market_bot.c1_signal_ingestion import nhl_event_store as s

PBP = {
    "homeTeam": {"id": 10}, "awayTeam": {"id": 20},
    "plays": [
        {"eventId": 1, "periodDescriptor": {"number": 1, "periodType": "REG"}, "timeInPeriod": "01:30",
         "timeRemaining": "18:30", "situationCode": "1551", "typeCode": 506, "typeDescKey": "shot-on-goal",
         "sortOrder": 10, "details": {"xCoord": 60, "yCoord": -5, "zoneCode": "O", "shotType": "wrist",
                                      "shootingPlayerId": 7, "goalieInNetId": 31, "eventOwnerTeamId": 10}},
        {"eventId": 2, "periodDescriptor": {"number": 1, "periodType": "REG"}, "timeInPeriod": "bad",
         "situationCode": "0651", "typeCode": 505, "typeDescKey": "goal", "sortOrder": 20,
         "details": {"scoringPlayerId": 8, "eventOwnerTeamId": 20}},
    ],
    "rosterSpots": [{"teamId": 10, "playerId": 7, "firstName": {"default": "A"}, "lastName": {"default": "B"},
                     "sweaterNumber": 9, "positionCode": "C"}],
}


def test_mmss():
    assert s.mmss("12:34") == 754 and s.mmss(None) is None and s.mmss("bad") is None


def test_situation_code_order_and_garbage():
    assert s.parse_situation("0651") == {"away_goalie": 0, "away_skaters": 6, "home_skaters": 5, "home_goalie": 1}
    assert s.parse_situation("x")["home_skaters"] is None


def test_parse_events_sides_and_missing_fields():
    ev = s.parse_events(99, 2020, PBP)
    assert [e["owner_is_home"] for e in ev] == [True, False]
    assert ev[0]["x"] == 60 and ev[0]["time_in_period_s"] == 90 and ev[0]["shooter_id"] == 7
    assert ev[1]["shooter_id"] == 8 and ev[1]["time_in_period_s"] is None and ev[1]["x"] is None


def test_parse_rosters():
    r = s.parse_rosters(99, 2020, PBP)
    assert r[0]["is_home"] is True and r[0]["last"] == "B"


def test_parse_shifts_keeps_only_typecode_517():
    p = {"data": [{"playerId": 1, "typeCode": 517, "period": 1, "shiftNumber": 2, "startTime": "00:10",
                   "endTime": "00:50", "duration": "00:40", "teamId": 10},
                  {"playerId": 1, "typeCode": 505, "period": 1}]}
    r = s.parse_shifts(99, 2020, p)
    assert len(r) == 1 and r[0]["duration_s"] == 40


def test_parse_box_players_and_team():
    p = {"homeTeam": {"id": 10, "sog": 31, "score": 3}, "awayTeam": {"id": 20, "sog": 22, "score": 2},
         "playerByGameStats": {"homeTeam": {"forwards": [{"playerId": 7, "toi": "18:00", "goals": 1, "sog": 4}],
                                            "defense": [], "goalies": [{"playerId": 31, "saves": 20, "starter": True}]},
                               "awayTeam": {"forwards": [], "defense": [], "goalies": []}}}
    rows = s.parse_box_players(99, 2020, p)
    assert {r["group"] for r in rows} == {"forwards", "goalies"} and rows[0]["toi_s"] == 1080
    assert s.parse_box_team(p) == {"home_sog": 31, "away_sog": 22, "home_score": 3, "away_score": 2}


def test_schedule_week_keeps_only_counting_games():
    g = lambda i, t: {"id": i, "season": 20202021, "gameType": t, "startTimeUTC": "2021-01-14T00:00:00Z",
                      "homeTeam": {"id": 1, "abbrev": "A", "score": 1}, "awayTeam": {"id": 2, "abbrev": "B", "score": 0}}
    out = s.parse_schedule_week({"gameWeek": [{"date": "2021-01-13", "games": [g(1, 2), g(2, 1), g(3, 3)]}]})
    assert [x["game_id"] for x in out] == [1, 3] and out[0]["season"] == 2020


def test_cache_round_trip(tmp_path):
    path = s.cache_path(tmp_path, "pbp", 2020, 99)
    s.write_cache(path, "http://x", {"a": 1})
    assert s.read_cache(path)["payload"] == {"a": 1}
    assert not list(tmp_path.rglob("*.tmp"))
