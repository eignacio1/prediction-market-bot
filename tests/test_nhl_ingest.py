"""Tests for C1 NHL ingestion (T-607 / EXP-036). No network: the ``opener`` seam is used."""
import json
from pathlib import Path

import pytest

from prediction_market_bot.c1_signal_ingestion import nhl_ingest as ni


def _box(state="OFF", end="REG", hs=3, as_=2, home_goalies=None, away_goalies=None, gtype=2):
    def side(ab, score, goalies):
        return {"abbrev": ab, "score": score, "sog": 30}, {
            "forwards": [{"goals": max(score - (1 if end == "SO" and ab == "H" else 0), 0) if ab == "H" else 0,
                          "powerPlayGoals": 0, "pim": 2}],
            "defense": [], "goalies": goalies if goalies is not None else []}
    h, hp = side("H", hs, home_goalies)
    a, ap = side("A", as_, away_goalies)
    return {"id": 1, "season": 20252026, "gameType": gtype, "gameState": state,
            "gameDate": "2025-10-10", "startTimeUTC": "2025-10-10T23:00:00Z",
            "venue": {"default": "X"}, "homeTeam": h, "awayTeam": a,
            "periodDescriptor": {"periodType": end},
            "gameOutcome": {"lastPeriodType": end},
            "playerByGameStats": {"homeTeam": hp, "awayTeam": ap}}


G = lambda pid, starter, toi="60:00": {"playerId": pid, "starter": starter, "toi": toi,
                                       "shotsAgainst": 30, "saves": 28, "powerPlayGoalsAgainst": 0}


def test_regulation_game_row():
    r = ni.parse_game_row(_box(home_goalies=[G(1, True)], away_goalies=[G(2, True)]), "t")
    assert r["home_starter_id"] == 1 and r["away_starter_id"] == 2
    assert r["home_score_ex_so"] == 3 and r["away_score_ex_so"] == 2
    assert r["end_period_type"] == "REG"


def test_shootout_removes_winner_goal():
    r = ni.parse_game_row(_box(end="SO", hs=3, as_=2, home_goalies=[G(1, True)], away_goalies=[G(2, True)]), "t")
    assert (r["home_score_ex_so"], r["away_score_ex_so"]) == (2, 2)
    r = ni.parse_game_row(_box(end="SO", hs=2, as_=3, home_goalies=[G(1, True)], away_goalies=[G(2, True)]), "t")
    assert (r["home_score_ex_so"], r["away_score_ex_so"]) == (2, 2)


def test_missing_goalie_gives_none_not_crash():
    r = ni.parse_game_row(_box(home_goalies=[], away_goalies=None), "t")
    assert r["home_starter_id"] is None and r["away_starter_id"] is None
    assert r["home_goalies_used"] == []


def test_pulled_goalie_both_recorded():
    r = ni.parse_game_row(_box(home_goalies=[G(1, True, "20:00"), G(3, False, "40:00")],
                               away_goalies=[G(2, True)]), "t")
    assert r["home_starter_id"] == 1 and r["home_goalies_used"] == [1, 3]


@pytest.mark.parametrize("state", ["FUT", "LIVE", "PRE", "CRIT"])
def test_unfinished_game_returns_none(state):
    assert ni.parse_game_row(_box(state=state), "t") is None


def test_non_regular_season_returns_none():
    assert ni.parse_game_row(_box(gtype=3), "t") is None
    assert ni.parse_game_row(_box(gtype=1), "t") is None


def test_postponed_detection():
    base = {"id": 9, "season": 20252026, "gameType": 2, "gameDate": "d", "startTimeUTC": "s",
            "gameState": "FUT", "homeTeam": {"abbrev": "A"}, "awayTeam": {"abbrev": "B"}}
    assert not ni.is_postponed(ni.parse_schedule_game(base))
    assert ni.is_postponed(ni.parse_schedule_game({**base, "gameScheduleState": "PPD"}))
    assert ni.is_postponed(ni.parse_schedule_game({**base, "gameState": "CNCL"}))


def test_429_halves_rate_then_succeeds(monkeypatch):
    monkeypatch.setattr(ni.time, "sleep", lambda s: None)
    calls = []

    def opener(url):
        calls.append(url)
        return (429, b"") if len(calls) == 1 else (200, b'{"ok": 1}')
    th = ni.Throttle(interval_s=0.0, base_s=0.0)
    th.interval_s = 1.0
    assert ni.http_get_json("u", th, opener=opener) == {"ok": 1}
    assert len(calls) == 2
    assert th.interval_s > 1.0  # doubled on the 429 (relaxes only 2% after the success)


def test_404_raises_and_boxscore_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(ni.time, "sleep", lambda s: None)
    th = ni.Throttle(interval_s=0.0, base_s=0.0)
    assert ni.fetch_boxscore(5, th, root=tmp_path, opener=lambda u: (404, b"nf")) is None
    assert not ni.box_path(5, tmp_path).exists()


def test_boxscore_cached_and_timestamped(tmp_path, monkeypatch):
    monkeypatch.setattr(ni.time, "sleep", lambda s: None)
    th = ni.Throttle(interval_s=0.0, base_s=0.0)
    n = []

    def opener(u):
        n.append(u)
        return 200, json.dumps(_box()).encode()
    w = ni.fetch_boxscore(1, th, root=tmp_path, opener=opener)
    assert "fetched_at_utc" in w and w["payload"]["id"] == 1
    ni.fetch_boxscore(1, th, root=tmp_path, opener=opener)
    assert len(n) == 1  # second call served from disk
    assert len(ni.load_games(tmp_path)) == 1


def test_season_schedule_dedupes_and_filters(monkeypatch):
    monkeypatch.setattr(ni.time, "sleep", lambda s: None)
    g = lambda i, t: {"id": i, "season": 20252026, "gameType": t, "gameDate": "d",
                      "startTimeUTC": "s", "gameState": "FUT",
                      "homeTeam": {"abbrev": "A"}, "awayTeam": {"abbrev": "B"}}
    body = json.dumps({"games": [g(1, 2), g(2, 3), g(3, 1)]}).encode()
    out = ni.fetch_season_schedule(2025, ni.Throttle(0.0, base_s=0.0), opener=lambda u: (200, body),
                                   teams=["A", "B"])
    assert list(out) == [1]


def test_arizona_override_for_old_seasons():
    assert ni.SEASON_TEAM_OVERRIDES[2022]["UTA"] == "ARI"
    assert "UTA" not in ni.SEASON_TEAM_OVERRIDES.get(2025, {})
