"""W129.7 Part A: known-answer test on a saved live game + staleness + write-recency (no network)."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from prediction_market_bot.c1_signal_ingestion import nhl_live as nl

FIX = Path(__file__).parent / "fixtures" / "nhl_pbp_live_2026020386.json"
T0 = datetime(2026, 11, 25, 23, 0, tzinfo=timezone.utc)


def _state(**kw):
    s = nl.state_from_pbp(json.loads(FIX.read_text()), T0, 120.0)
    s.update(kw)
    return s


def test_known_answer_saved_game():
    s = _state()
    assert (s["home"], s["away"]) == ("BOS", "WPG")
    assert (s["score_h"], s["score_a"]) == (0, 1)
    assert s["period"] == 1 and s["period_type"] == "REG"
    assert s["clock_s"] == 1035
    assert s["minutes_left_reg"] == 57.25
    assert s["strength"] == "H_PP" and s["empty_net"] is False
    assert s["pp_secs_left"] == 69
    assert s["fetched_at_utc"] == T0.isoformat() and s["latency_ms"] == 120.0


def test_fresh_live_state_ok():
    assert nl.staleness(_state(game_state="LIVE"), None, T0 + timedelta(seconds=5)) is None


def test_stale_cases():
    live = _state(game_state="LIVE")
    assert nl.staleness(live, None, T0 + timedelta(seconds=60)) == "fetch_age"
    assert nl.staleness(_state(game_state="FINAL"), None, T0) == "not_live"
    assert nl.staleness(_state(game_state="LIVE", strength=None), None, T0) == "incomplete_state"
    assert nl.staleness(_state(game_state="LIVE", score_h=None), None, T0) == "no_score"
    prev = _state(game_state="LIVE", clock_running=True,
                  fetched_at_utc=(T0 - timedelta(seconds=100)).isoformat())
    cur = _state(game_state="LIVE", clock_running=True)
    assert nl.staleness(cur, prev, T0) == "clock_frozen"
    later = _state(game_state="LIVE", clock_running=True, clock_s=900)
    assert nl.staleness(cur, later, T0) == "state_regressed"


def test_write_recency():
    assert nl.write_recency([], None, T0)[0] == "IDLE"
    assert nl.write_recency([1], None, T0)[0] == "FAIL"
    assert nl.write_recency([1], T0 - timedelta(seconds=700), T0)[0] == "FAIL"
    assert nl.write_recency([1], T0 - timedelta(seconds=100), T0)[0] == "OK"
