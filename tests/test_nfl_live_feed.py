"""W129.6 known-answer test of the NFL live feed on a saved game (ARI @ KC, ESPN event 401873067, final 7-34)."""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from prediction_market_bot.c1_signal_ingestion import nfl_live_feed as f

FX = json.loads((Path(__file__).parent / "fixtures" / "nfl_game_401873067_plays.json").read_text())
FT = "2026-11-23T00:00:00Z"


def _states(replay=True):
    return f.states_from_plays(FX["plays"], FX["event_id"], FX["home_id"], FX["home"], FX["away"], FT, replay=replay)


def test_final_state_matches_final_score():
    s = _states()
    assert (s[-1].away_score, s[-1].home_score) == tuple(FX["final"])
    assert len(s) == 173


def test_opening_state_known_answer():
    s = _states()
    kick = [x for x in s if x.play_type == "Kickoff"][0]
    assert (kick.period, kick.clock_s, kick.secs_left_reg) == (1, 900.0, 3600.0)
    assert (kick.home_score, kick.away_score) == (0, 0)
    first_snap = [x for x in s if x.down == 1][0]
    assert (first_snap.down, first_snap.distance, first_snap.possession) == (1, 10, "home")


def test_point_in_time_monotone():
    s = _states()
    assert all(b.secs_left_reg <= a.secs_left_reg + 1e-9 for a, b in zip(s, s[1:]) if b.period <= 4 and a.period <= 4)
    assert all(b.home_score >= a.home_score and b.away_score >= a.away_score for a, b in zip(s, s[1:]))


def test_timeouts_derived_and_reset_per_half():
    s = _states()
    h1 = [x for x in s if x.period <= 2][-1]
    assert h1.home_timeouts == 0 and h1.away_timeouts == 3       # KC called 3 in the first half, ARI none
    h2 = [x for x in s if x.period == 3][0]
    assert (h2.home_timeouts, h2.away_timeouts) == (3, 3)
    last = s[-1]
    assert last.home_timeouts == 2 and last.away_timeouts == 2   # ARZ alias maps to ARI; KC 1, ARI 1 used in the 2nd half
    assert last.timeouts_source == "derived_from_timeout_plays"


def test_replay_has_no_lag_live_lag_measured():
    assert all(x.feed_lag_s is None for x in _states(replay=True))
    live = [x for x in _states(replay=False) if x.wallclock_utc]
    assert live and all(x.feed_lag_s is not None and x.feed_lag_s > 0 for x in live)


def test_staleness():
    s = _states()
    ft = datetime.strptime(FT, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    assert f.is_stale(s, ft + timedelta(seconds=10), True) == "newest_play_old"   # fetch fresh, newest play hours old
    assert f.is_stale(s, ft + timedelta(seconds=10), False) is None                # game not live: nothing expected
    assert f.is_stale(s, ft + timedelta(seconds=500), False) == "fetch_old"
    assert f.is_stale([], ft, True) == "no_plays"
