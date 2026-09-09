"""
Tests for nfl_espn_results.py (T-527).

Mocks requests.get against ESPN's real scoreboard JSON shape (confirmed live
during T-527 via direct `curl` against
https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard).
Network-marked tests separately verify the fetcher against three real
completed 2025-season games.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from prediction_market_bot.c1_signal_ingestion.nfl_espn_results import (
    NFLGameResult,
    fetch_nfl_final_score,
)


def _scoreboard_response(events: list[dict]) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {"events": events}
    return resp


def _event(
    status_name: str,
    home_abbr: str,
    home_score: str,
    away_abbr: str,
    away_score: str,
) -> dict:
    return {
        "competitions": [
            {
                "status": {"type": {"name": status_name}},
                "competitors": [
                    {
                        "homeAway": "home",
                        "team": {"abbreviation": home_abbr},
                        "score": home_score,
                    },
                    {
                        "homeAway": "away",
                        "team": {"abbreviation": away_abbr},
                        "score": away_score,
                    },
                ],
            }
        ]
    }


@patch("prediction_market_bot.c1_signal_ingestion.nfl_espn_results.requests.get")
def test_fetch_final_score_success(mock_get):
    mock_get.return_value = _scoreboard_response(
        [_event("STATUS_FINAL", "PIT", "24", "MIN", "21")]
    )
    result = fetch_nfl_final_score("2025-09-28", "PIT", "MIN")
    assert result == NFLGameResult(
        home_team_code="PIT",
        away_team_code="MIN",
        home_score=24.0,
        away_score=21.0,
        status="STATUS_FINAL",
    )
    # No User-Agent header sent (GG-163).
    _args, kwargs = mock_get.call_args
    assert kwargs["headers"] == {}


@patch("prediction_market_bot.c1_signal_ingestion.nfl_espn_results.requests.get")
def test_fetch_final_score_case_insensitive_team_codes(mock_get):
    mock_get.return_value = _scoreboard_response(
        [_event("STATUS_FINAL", "PIT", "24", "MIN", "21")]
    )
    result = fetch_nfl_final_score("2025-09-28", "pit", "min")
    assert result is not None
    assert result.home_team_code == "PIT"
    assert result.away_team_code == "MIN"


@patch("prediction_market_bot.c1_signal_ingestion.nfl_espn_results.requests.get")
def test_fetch_final_score_game_still_live_returns_none(mock_get):
    mock_get.return_value = _scoreboard_response(
        [_event("STATUS_IN_PROGRESS", "PIT", "10", "MIN", "7")]
    )
    assert fetch_nfl_final_score("2025-09-28", "PIT", "MIN") is None


@patch("prediction_market_bot.c1_signal_ingestion.nfl_espn_results.requests.get")
def test_fetch_final_score_postponed_returns_none(mock_get):
    mock_get.return_value = _scoreboard_response(
        [_event("STATUS_POSTPONED", "PIT", "0", "MIN", "0")]
    )
    assert fetch_nfl_final_score("2025-09-28", "PIT", "MIN") is None


@patch("prediction_market_bot.c1_signal_ingestion.nfl_espn_results.requests.get")
def test_fetch_final_score_no_matching_game_on_date_returns_none(mock_get):
    mock_get.return_value = _scoreboard_response(
        [_event("STATUS_FINAL", "DAL", "40", "GB", "40")]
    )
    assert fetch_nfl_final_score("2025-09-28", "PIT", "MIN") is None


@patch("prediction_market_bot.c1_signal_ingestion.nfl_espn_results.requests.get")
def test_fetch_final_score_tie_game(mock_get):
    mock_get.return_value = _scoreboard_response(
        [_event("STATUS_FINAL", "DAL", "40", "GB", "40")]
    )
    result = fetch_nfl_final_score("2025-09-28", "DAL", "GB")
    assert result is not None
    assert result.home_score == 40.0
    assert result.away_score == 40.0


@patch("prediction_market_bot.c1_signal_ingestion.nfl_espn_results.requests.get")
def test_fetch_final_score_picks_correct_event_among_multiple(mock_get):
    mock_get.return_value = _scoreboard_response(
        [
            _event("STATUS_FINAL", "DAL", "40", "GB", "40"),
            _event("STATUS_FINAL", "HOU", "26", "TEN", "0"),
        ]
    )
    result = fetch_nfl_final_score("2025-09-28", "HOU", "TEN")
    assert result == NFLGameResult(
        home_team_code="HOU",
        away_team_code="TEN",
        home_score=26.0,
        away_score=0.0,
        status="STATUS_FINAL",
    )


@patch(
    "prediction_market_bot.c1_signal_ingestion.nfl_espn_results.requests.get",
    side_effect=ConnectionError("boom"),
)
@patch("prediction_market_bot.c1_signal_ingestion.nfl_espn_results.time.sleep")
def test_fetch_final_score_api_failure_retries_then_returns_none(mock_sleep, mock_get):
    result = fetch_nfl_final_score("2025-09-28", "PIT", "MIN")
    assert result is None
    # 3 retry delays (5, 10, 30) + 1 final attempt = 4 calls.
    assert mock_get.call_count == 4
    assert mock_sleep.call_count == 3
